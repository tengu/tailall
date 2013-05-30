#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""todo: unit test here..
"""
import sys,os
import time

def commands(baker=None):
    """commands to drive testing
    """

    if not baker:
        import baker

    @baker.command
    def write(file_to_tail,niteration,msg):

        f=file(file_to_tail, 'w')

        for i in range(int(niteration)):
            line='{msg} {i}\n'.format(**locals())
            f.write(line)
            f.flush()
            print line.strip('\n')
            time.sleep(1)

        f.close()

    @baker.command
    def fail():
        """throw a traceback"""
        print 'about to FAIL..'
        ARRGGHH

    return baker

if __name__=='__main__':

    # todo: run unittest by default. helper commands otherwise.
    commands().run()
