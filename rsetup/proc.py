import sys
import subprocess


def read(cmd, check_exit_code=True):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()
    if check_exit_code and proc.wait() != 0:
        print 'executing ' + ' '.join(cmd), 'failed'
        sys.exit(proc.returncode)
    return stdout


def exe(cmd, check_exit_code=True):
    proc = subprocess.Popen(cmd)
    if check_exit_code and proc.wait() != 0:
        print 'executing ' + ' '.join(cmd), 'failed'
        sys.exit(proc.returncode)