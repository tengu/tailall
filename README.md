tailall
=======

tail every file under a directory

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
