#!/usr/bin/env python

from subprocess import Popen, PIPE
from threading import Thread
from time import time

class runProcess(Thread):
    def __init__(self, cmd, cwd = None, timeout = 60):
        Thread.__init__(self)
        self.cmd = cmd
        self.cwd = cwd
        self.timeout = timeout
        
        self.stdout = None
        self.stderr = None
        self.returncode = None
        self.time = 0

    def run(self):
        self.time = time()
        self.p = Popen(self.cmd, shell=True, cwd = self.cwd, stdout=PIPE, stderr=PIPE)
        self.stdout, self.stderr = self.p.communicate()

    def execute(self):
        self.start()
        self.join(self.timeout)

        if self.is_alive():
            self.p.terminate()
            self.p.returncode = 'TL'
            self.join()
            
        self.time = time() - self.time
        self.returncode = self.p.returncode
            

def run_process(cmd, cwd, timeout = 60):
    st = runProcess(cmd, cwd, timeout)
    st.execute()
    return {'return' : st.returncode, 'stdout' : st.stdout, 'stderr' : st.stderr, 'time' : st.time, 'memory' : None}