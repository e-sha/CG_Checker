
#!/usr/bin/env python

import subprocess, os, sys, shutil, tarfile, glob, threading, collections, locale
from subprocess import PIPE, Popen

PROCESS_DIR = '/home/bagnikita/CG2015/process_solution.py'

def get_process_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'process_dir.py')

def execute_program(exe):
    p = Popen(exe, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    return {'return' : p.returncode, 'stdout' : out, 'stderr' : err}

def main(argc, argv):
    in_dir = argv[1]
    TEST_DB = argv[2]
    dirs = [ d for d in os.listdir(in_dir) if os.path.isdir(os.path.join(in_dir, d)) ]

    for dir in dirs:
        print("Testing group %s" % (dir))
        cur_dir = os.path.join(in_dir, dir)
        cmd = "python %s %s %s" % (PROCESS_DIR, cur_dir, TEST_DB)
        run = execute_program(cmd)
    return 0

if __name__ == "__main__":
    PROCESS_DIR = get_process_dir()
    main(len(sys.argv), sys.argv)
