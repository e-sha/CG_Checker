#!/usr/bin/env python

import subprocess, os, sys, shutil, tarfile, glob, threading, collections, codecs, time

from os import kill
from signal import alarm, signal, SIGALRM, SIGKILL

from subprocess import PIPE, Popen

SANDBOX_DIR = '/tmp/sandbox/'
TEST_DIR = os.path.join(SANDBOX_DIR, 'test/')
TREASURE_DIR = os.path.join(SANDBOX_DIR, 'gear_project/')
BUILD_BIN = os.path.join(TREASURE_DIR, 'build/bin/')
COMPILE_TIMELIMIT = 20
RUN_TIMELIMIT = 100
CHECKER = '/home/bagnikita/CG2015/compare.py'

def get_checker():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compare.py')

def find_solution():
    makefile_path = glob.glob(os.path.join(SANDBOX_DIR, '*/Makefile'))
    global TREASURE_DIR
    global BUILD_BIN
    TREASURE_DIR = os.path.dirname(makefile_path[0])
    BUILD_BIN = os.path.join(TREASURE_DIR, 'build/bin')

def execute_program(exe):
    p = Popen(exe, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    return {'return' : p.returncode, 'stdout' : out, 'stderr' : err}

def safeMkdir(dir_name):
    try:
        os.makedirs(dir_name)
    except Exception, e:
        #print("error mkdir %s, error %s" % (dir_name, repr(e)))
        pass

def safeRmdir(dir_name):
    try:
        shutil.rmtree(dir_name)
    except Exception, e:
        #print("error removing %s, error %s" % (dir_name, repr(e)))
        pass

def safeCopyfile(src, dst):
    try:
        shutil.copyfile(src, dst)
    except Exception, e:
        #print("error copyfile %s %s, error %s" % (src, dst, repr(e)))
        pass

def get_process_children(pid):
    p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell = True, stdout = PIPE, stderr = PIPE)
    stdout, stderr = p.communicate()
    return [int(p) for p in stdout.split()]

def execute_program(exe, CWD = None, Timelimit = 0):
    p = None

    class Alarm(Exception):
        pass

    def alarm_handler(signum, frame):
        raise Alarm

    signal(SIGALRM, alarm_handler)
    alarm(Timelimit)

    out = None
    err = None

    t = time.time()

    try:
        if CWD == None:
            p = Popen(exe, shell=True, stdout=PIPE, stderr=PIPE)
        else:
            p = Popen(exe, shell=True, stdout=PIPE, stderr=PIPE, cwd = CWD)
        out, err = p.communicate()
    except Alarm:
        pids = [p.pid]
        pids.extend(get_process_children(p.pid))
        for pid in pids:
            try: 
                kill(pid, SIGKILL)
            except OSError:
                pass

        t = time.time() - t
        return {'return' : 'TL', 'stdout' : out, 'stderr' : err, 'time' : t}

    t = time.time() - t
    return {'return' : p.returncode, 'stdout' : out, 'stderr' : err, 'time' : t}

def cleanup_sandbox():
    safeRmdir(SANDBOX_DIR)
    safeMkdir(SANDBOX_DIR)

def unpack_solution(solution_tgz):
    safe_solution = SANDBOX_DIR + '/solution.tgz'
    safeCopyfile(solution_tgz, safe_solution)
    tar_st = execute_program("tar -xvf %s -C %s" % (safe_solution, SANDBOX_DIR))
    execute_program("chmod -R 777 %s" % (SANDBOX_DIR))
    return tar_st

def compile_solution():
    make_clean = execute_program('make clean', TREASURE_DIR, COMPILE_TIMELIMIT)
    if make_clean['return'] != 0:
        return make_clean
    
    make_all = execute_program('make all', TREASURE_DIR, COMPILE_TIMELIMIT)
    if make_all['return'] != 0:
        return make_all

    return {'return' : 0}
    
def run_test(test):
    safeRmdir(TEST_DIR)
    safeMkdir(TEST_DIR)

    EXE = os.path.join(BUILD_BIN, 'main')
    in_image = os.path.join(TEST_DIR, 'in_image.bmp')
    in_image1 = os.path.join(TEST_DIR, 'in_image_1.bmp')
    in_image2 = os.path.join(TEST_DIR, 'in_image_2.bmp')
    in_image3 = os.path.join(TEST_DIR, 'in_image_3.bmp')

    out_image = os.path.join(TEST_DIR, 'out_image.bmp')
    out_path = os.path.join(TEST_DIR, 'out_labels.txt')

    safeCopyfile(test['image'], in_image)
    safeCopyfile(test[1], in_image1)
    safeCopyfile(test[2], in_image2)
    safeCopyfile(test[3], in_image3)

    run_st = execute_program("%s %s %s %s" % (EXE, in_image, out_image, out_path), TEST_DIR, RUN_TIMELIMIT)

    return {'return' : run_st['return'], 'exe' : EXE, 'out_image' : out_image, 'out_labels' : out_path, 'stdout' : run_st['stdout'], 'stderr' : run_st['stderr'], 'time' : run_st['time']}

def load_testcases(in_fle):
    imgs = glob.glob(in_fle + '/pic/*/*.bmp')
    labels = glob.glob(in_fle + '/labelling/*/*.txt')

    print(imgs)

    d = {'base' : {}, 'bonus' : {}}
    for im in imgs:
        if '_' in im.split('/')[-1]:
            continue
        im_sp = '.'.join(im.split('.')[:-1])
        p, s = im.split('/')[-2:]
        s = '.'.join(s.split('.')[:-1])
        d[p][s] = {'image' : im, 1 : im_sp + '_1.bmp', 2 : im_sp + '_2.bmp', 3 : im_sp + '_3.bmp'}

    for l in labels:
        if '_' in l.split('/')[-1]:
            continue
        p, s = l.split('/')[-2:]
        s = '.'.join(s.split('.')[:-1])
        d[p][s]['label'] = l

    return d

def writeStatistics(student, solution_stats, check_fail = False):
    stats_file = open(student['dir'] + '/stats.txt', 'w')

    score_base, score_bonus1, score_bonus2 = 0, 0.0, 0.0
    for key, st in sorted(solution_stats.items(), key = lambda (k,v) : k):
        stats_file.write("TEST #%s %s (%f) TIME=%.2fs\n" % (key, st['result'], st['score'], st['time']))
        if ('base' in key):
            score_base = score_base + int(st['result'] == 'OK')
        else:
            score_bonus1 = score_bonus1 + int(st['result'] == 'OK')
            score_bonus2 = score_bonus2 + int(st['score'] == 1.0)

    stats_file.write("BASE %d BONUS_1 %f BONUS_2 %f" % (score_base, score_bonus1, score_bonus2))

    global_stats2 = codecs.open('stats/stats2.txt', 'w', encoding='utf-8')

    was_found = False

    if os.path.isfile('stats/stats.txt'):
        global_stats = codecs.open('stats/stats.txt', 'r', encoding='utf-8').readlines()

        for line in global_stats:
            if line.split('\t')[:2] == [student['group'], student['id']]:
               xfmt = None
               if check_fail:
                   xfmt = "%s\t%s\tX X\n" % (student['group'], student['id'])
               else:
                   xfmt = "%s\t%s\t%d %f %f\n" % (student['group'], student['id'], score_base, score_bonus1, score_bonus2)
               global_stats2.write(xfmt)
               was_found = True
            else:
                global_stats2.write(line)

    if was_found == False:
        xfmt = None
        if check_fail:
            xfmt = "%s\t%s\tX X X\n" % (student['group'], student['id'])
        else:
            xfmt = "%s\t%s\t%d %f %f\n" % (student['group'], student['id'], score_base, score_bonus1, score_bonus2)
        global_stats2.write(xfmt)

    global_stats2.close()
    os.rename('stats/stats2.txt', 'stats/stats.txt')

def writeCompilationError(student, error_log):
    stats_file = open(student['dir'] + '/stats.txt', 'w')
    stats_file.write(error_log)

def extract_student_info(in_tgz):
    try:
        in_tgz = in_tgz.decode('utf-8')
        student_group, student_id = in_tgz.split('/')[-2:]
        student_id = student_id.split('assignsubmission')[0]
        student_id = '_'.join(student_id.split('_')[:-2])

        return {'id' : student_id, 'group' : student_group, 'dir' : "stats/%s/%s/" % (student_group, student_id)}
    except:
        return {'id' : 'John_Doe', 'group' : 'CMC', 'dir' : 'stats/CMC/John_Doe/'}
        pass

def main(argc, argv):
    in_tgz = argv[1]
    in_fle = argv[2]

    testcases = load_testcases(in_fle)

    cleanup_sandbox()

    student = extract_student_info(in_tgz)
    safeRmdir(student['dir'])
    safeMkdir(student['dir'])

    unpack_res = unpack_solution(in_tgz)
    if unpack_res['return'] != 0:
        print("BROKEN ARCHIVE")
        writeStatistics(student, {}, True)
        print(unpack_res)
        sys.exit(0)

    find_solution()

    compile_res = compile_solution()
    if compile_res['return'] != 0:
        print('COMPILATION ERROR')
        print("%s" % (compile_res['stderr']))
        writeStatistics(student, {}, True)
        writeCompilationError(student, compile_res['stderr'])
        sys.exit(0)

    solution_stats = {}

    for group, tests in testcases.items():
	for test_id, test_info in tests.items():
            #print("Testing %s_%s" % (group, test_id))

            solution_ans = run_test(test_info)
 
            key = "%s_%s" %(group, test_id)

            solution_stats[key] = {'group' : group, 'id' : test_id, 'msg' : None, 'result' : None, 'time' : solution_ans['time']}

            if solution_ans['return'] == 'TL':
                solution_stats[key]['result'] = 'TL'
                solution_stats[key]['score'] = 0.
                solution_stats[key]['msg'] = 'Time limit exceeded'
            elif solution_ans['return'] != 0:
                solution_stats[key]['result'] = 'RT'
                solution_stats[key]['score'] = 0.
                solution_stats[key]['msg'] = solution_ans['stderr'].encode('string_escape')
            else:
                safeCopyfile(test_info['label'], os.path.join(TEST_DIR, 'correct.txt'))
                checker_ans = execute_program("python %s %s %s" % (CHECKER, os.path.join(TEST_DIR, 'correct.txt'), solution_ans['out_labels']), TEST_DIR, COMPILE_TIMELIMIT)
                if (checker_ans['return'] != 0) or (len(checker_ans['stdout'].split('\n')) != 3):
                    solution_stats[key]['result'] = 'CF'
                    solution_stats[key]['msg'] = checker_ans['stderr']
                    solution_stats[key]['score'] = 0.
                else:
                    verdict = checker_ans['stdout'].split('\n')[0]
                    solution_stats[key]['result'] = 'OK' if verdict != 'Fail' else 'WA'
                    solution_stats[key]['score'] = float(checker_ans['stdout'].split('\n')[1])
                safeCopyfile(solution_ans['out_image'], student['dir'] + key + '.' + solution_ans['out_image'].split('.')[-1])
                safeCopyfile(solution_ans['out_labels'], student['dir'] + key + '.' + solution_ans['out_labels'].split('.')[-1])

    print(("STUDENT \'%s\' GROUP \'%s\'" % (student['id'], student['group'])).encode('utf-8'))

    for key, st in sorted(solution_stats.items(), key = lambda (k,v) : k):
        print("TEST #%s %s (%f) T=%.2fs" % (key, st['result'], st['score'], st['time']))

    writeStatistics(student, solution_stats)

    return 0

if __name__ == "__main__":
    CHECKER = get_checker()
    main(len(sys.argv), sys.argv)
