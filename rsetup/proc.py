import sys
import os
import subprocess
import logging

LOG = logging.getLogger(__name__)


def read(*args, **kwargs):
    if len(args) == 1 and isinstance(args[0], list):
        args = args[0]
    cmd = args[0] + ' ' + ' '.join(repr(arg) for arg in args[1:])
    LOG.debug(cmd)
    sys.stdout.flush()
    sys.stderr.flush()
    proc = subprocess.Popen(args, env=os.environ, stdout=subprocess.PIPE)
    stdout = proc.stdout.read()
    exit_code = proc.wait()
    if exit_code != 0:
        LOG.error('FAILED')
        LOG.error(' cmd: ' + cmd)
        LOG.error(' cwd: ' + os.path.abspath('.'))
        LOG.error(' exit code: ' + str(exit_code))
        if kwargs.get('exit_on_error', False):
            sys.exit(exit_code)
    return stdout


def exe(cmd, check_exit_code=True):
    proc = subprocess.Popen(cmd)
    if check_exit_code and proc.wait() != 0:
        print 'executing ' + ' '.join(cmd), 'failed'
        sys.exit(proc.returncode)

