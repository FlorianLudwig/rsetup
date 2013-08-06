import sys
import subprocess


def read(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()
    if proc.wait() != 0:
        print 'executing ' + ' '.join(cmd), 'failed'
        sys.exit(proc.returncode)
    return stdout


def exe(cmd):
    proc = subprocess.Popen(cmd)
    if proc.wait() != 0:
        print 'executing ' + ' '.join(cmd), 'failed'
        sys.exit(proc.returncode)