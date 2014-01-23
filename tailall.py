# -*- coding: utf-8 -*-
"""
### usages

* rate of total lines being logged
  tailall /var/log 2>/dev/null | pv -l > /dev/null

### todo:
* deal with ["error", "/var/log/auth.log", "IOError(13, 'Permission denied')"]

### bugs
* `echo hi >> logfile` does not work
* Log writers are assumed to do well-behaved line-oriented IO.
  If a writer does: write('OH'); flush(); write('HAI'); the message may 
  become interspersed with other items.
"""
import sys,os
import time
import json
import logging
from pyinotify import \
    WatchManager, Notifier, ProcessEvent, \
    IN_MOVED_TO, IN_CREATE, ALL_EVENTS, IN_MODIFY, IN_CLOSE_WRITE

logging.basicConfig(level = logging.INFO, format="%(message)s",)

log=logging.getLogger(__name__)

def ll(*words):
    """format a log line"""
    return json.dumps([int(time.time())]+map(str,words))

def ignore_sigpipe(f):
    """decorator to silenty ignore sigpipe"""

    def wrap(*args, **kw):
        try:
            return f(*args, **kw)
        except IOError, e:
            if e.errno==32:
                sys.exit(0)
            else:
                raise
    wrap.__name__=f.__name__
    wrap.func_name=f.func_name
    return wrap

def tsv_to_stdout(pair):
    """write the pair to stdout as tsv"""
    print '\t'.join(pair)
    sys.stdout.flush()

class Watcher(object):
    """monitor log files that get written. relay the lines to stdout."""

    def __init__(self, monitor, path, out=tsv_to_stdout):
        """start tracking this file.
        out: callable that takes a pair (path, line)
        """

        self.monitor=monitor
        self.path=path
        self.out=out

        # attach at the end of the file
        # todo: emit the last line of the pre-existing content.
        self.fh=file(self.path,'r')
        self.fh.seek(0,2)

        self.last_read=None

    def __repr__(self):
        return '%s("%s")' % (self.__class__.__name__, self.path)

    def close(self):
        self.fh.close()
        self.fh=None

    def emit(self, line):
        """deliver the captured log line downstream"""

        self.out( (self.path, line.strip('\n')) )
        
    def read_lines(self):

        start=time.time()

        while True:

            then=time.time()

            line=self.fh.readline()

            line_took=time.time()-then
            if line_took>0.1:
                log.warn(ll('slow', line_took, self.path))
            self.last_read=then

            if not line:
                break

            yield line

        drain_took=time.time()-start
        if drain_took>1.0:
            log.warn(ll('slow drain', drain_took, self.path))

    def read(self):
        """forward the newly added lines of my file"""

        # drain the file from current position to the end.
        for line in self.read_lines():
            self.emit(line)
        

class Monitor(object):
    """manage a bunch of log file Watchers"""

    def __init__(self, gc_interval=10000, gc_stale_age=180, watcher_opt=None):
        """
        * scan for stale watchers every gc_interval events
        * a watcher is considered stale and subject for gc 
          after gc_stale_age-seconds of inactivity.
        """
        self.watcher={}
        self.gc_interval=gc_interval
        self.gc_stale_age=gc_stale_age
        self.n=0
        self.watcher_opt=watcher_opt or {}

    def got_event(self, s):
        """ fs event callback. """
        self.n+=1
        notice=s.proc_fun()
        if notice.event:
            if notice.event.mask & IN_MODIFY:
                path=notice.event.pathname
                watcher=self.watcher.get(path)
                if not watcher:
                    try:
                        watcher=Watcher(self, path, **self.watcher_opt)
                        self.watcher[path]=watcher
                        log.info(ll('watch file', path))
                    except IOError, e:
                        log.error(ll('error', path, repr(e)))
                if watcher:
                    watcher.read()
            # todo: account for all events that tells me that I should stop
            #       tracking the file. see http://pyinotify.sourceforge.net/
            elif notice.event.mask & IN_CLOSE_WRITE:
                self.remove(notice.event.pathname, notice.event.maskname)
                    
        if self.n%self.gc_interval==0:
            self.gc()

    def remove(self, path, reason):
        
        watcher=self.watcher.pop(path,None)
        if watcher:
            watcher.close()
            log.info(ll('unwatch', watcher.path, reason))

    def gc(self):
        """garbage collect stale watchers"""
        now=time.time()
        for path,watcher in self.watcher.items():
            if now-watcher.last_read>self.gc_stale_age:
                self.remove(path, 'gc')

class FsEvent(ProcessEvent):

    def __init__(self):
        # event.mask, event.pathname, event.maskname, event.name, event.wd
        self.event=None

    def __repr__(self):
        if not self.event:
            return "%s()" % self.__class__.__name__
        return "%s('%s', %s)" % (self.__class__.__name__, 
                                 self.event.name, 
                                 self.event.maskname)

    """ 'callback' for fs event notification """
    def process_default(self, event):

        self.event=event

def watch_path(path, add_watch_opt=None, watcher_opt=None):
    """Tail all the files specify by path.
    
    path:  By default all files under the path, which should be a directory, are tailed.
           Path could also be list of paths or a glob pattern.
           The behavior can be modified by add_watch_opt. 
           See pyinotify.WatchManager.add_watch.

    output: defaults to stdout. 
            can be diverted any callable with:
                   watcher_opt=dict(out=got_log_line)
            where got_log_line() takes a tuple (log_path, log_line)

    *_opt: Are pass-through to pyinotify.WatchManager.add_watch and tailall.Monitor.
           See respective functions for detail.
    """

    wm = WatchManager()
    notifier = Notifier(wm, default_proc_fun=FsEvent())
    #mask=ALL_EVENTS
    #mask=IN_MOVED_TO|IN_CREATE|IN_MODIFY
    mask=IN_MODIFY|IN_CLOSE_WRITE
    kw=dict(rec=True, auto_add=False)
    kw.update(add_watch_opt or {})
    wm.add_watch(path, mask, **kw)

    monitor=Monitor(watcher_opt=watcher_opt)

    notifier.loop(callback=monitor.got_event)

# backwad compatibility
watch_directory=watch_path

@ignore_sigpipe
def main():
    """tail all log files under the given directory"""

    log_dirs=sys.argv[1:]
    for log_dir in log_dirs:
        log.info(ll('watch dir', log_dir))
        watch_path(log_dir)
    else:
        print >>sys.stderr, 'usage:', sys.argv[0], 'log_dir [...]'
        sys.exit(1)

if __name__=='__main__':

    main()
