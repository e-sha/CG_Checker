#!/usr/bin/env python

import subprocess, os, sys, shutil, tarfile, glob, threading, collections, locale
from subprocess import PIPE, Popen

PROCESS_SOLUTION = '/home/bagnikita/CG2015/process_solution.py'

def get_process_solution():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'process_solution.py')

def safeMkdir(dir_name):
    try:
        os.makedirs(dir_name)
    except Exception, e:
        #print("error mkdir %s, error %s" % (dir_name, repr(e)))
        pass

def execute_program(exe):
    p = Popen(exe, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    return {'return' : p.returncode, 'stdout' : out, 'stderr' : err}

def main(argc, argv):
    in_dir = argv[1]
    TEST_DB = argv[2]
#    solutions = glob.glob(in_dir + '/' + '*.tar.gz')
    solutions = glob.glob(in_dir + '/' + '*.gz')

    safeMkdir('stats/')
    CF_log = open('stats/cf.txt', 'a+')
    ALL_log = open('stats/stats.txt', 'a+')

    for solution in solutions:
        print("Testing %s" % (solution))
        run = execute_program("python %s %s %s" % (PROCESS_SOLUTION, solution.replace(' ', '\\ '), TEST_DB))
        print(run)
        if run['return'] != 0:
            CF_log.write("%s\n%s\n%s\n" % (run['return'], run['stdout'], run['stderr']))
        else:
            res = run['stdout'].split('\n')
            #print(res)
            #sys.exit(1)
            #ALL_log.write("%s %s\n" % (res[0], res[-2]))

    return 0

if __name__ == "__main__":
    PROCESS_SOLUTION = get_process_solution()
    main(len(sys.argv), sys.argv)
