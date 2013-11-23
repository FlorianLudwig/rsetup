"""rook virtual env control"""
import os
import sys
import logging
import argparse
import glob
import shutil
import subprocess as sp
import imp
import stat

import yaml
import setuptools
import subprocess
from rsetup import proc, config


TEST_PKGS = ['GitPython==0.3.2.RC1',
             'coverage==3.6',
             'pytest-cov==1.6',
             'pylint==0.28.0',
             'behave==1.2.3',
             'selenium==2.33.0']

ARG_PARSER = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)
SUB_PARSER = ARG_PARSER.add_subparsers(help='Command help')
LOG = logging.getLogger(__name__)


def command(func):
    """Decorator for CLI exposed functions"""
    func.parser = SUB_PARSER.add_parser(func.func_name, help=func.__doc__)
    func.parser.set_defaults(func=func)
    return func


def get_setup_data(path):
    data = {}

    old_setup = setuptools.setup
    old_modules = sys.modules.keys()

    def s(**kwargs):
        data.update(kwargs)

    setuptools.setup = s
    imp.load_source('fake-load-setup-py', path)

    for module in sys.modules.keys():
        if module not in old_modules:
            del sys.modules[module]

    setuptools.setup = old_setup
    return data


def get_python_interpreter(args):
    if 'PYTHON_EXE' in os.environ:
        return os.environ['PYTHON_EXE']
    return 'python'


@command
def sdist(args):
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    python = get_python_interpreter(args)
    proc.exe([python, 'setup.py', 'sdist', '--dev'])


sdist.parser.add_argument('--ci', action='store_true',
                          help='running in CI context')


@command
def test(args):
    setup_data = get_setup_data('setup.py')
    pkgs = setup_data['packages']
    pkgs = set(pkg.split('.')[0] for pkg in pkgs)
    pkgs = list(pkgs)

    if args.cfg['test.pytest']:
        py_test = ['py.test', '--cov', '.']
        if args.ci:
            py_test += ['--cov-report', 'xml', '--junitxml=junit.xml']

        proc.exe(py_test)
        if args.ci:
            proc.exe(['coverage', 'html'])

    if args.cfg['test.pylint']:
        pylint = ['pylint', '-f', 'parseable'] + pkgs
        # maybe check pylint return code
        # http://lists.logilab.org/pipermail/python-projects/2009-November/002068.html
        pylint_out = proc.read(pylint, check_exit_code=False)
        open('pylint.out', 'w').write(pylint_out)


test.parser.add_argument('--ci', action='store_true',
                         help='running in CI context')


@command
def setup(args):
    pkgs = TEST_PKGS[:]
    if args.cfg['test.behave']:
        pkgs.append('rbehave>=0.0.0.git0')
    p = subprocess.Popen(['pip', 'install'] + pkgs)
    p.wait()

    pkgs = proc.read(['pip', 'freeze'])
    before = open('pip_freeze_before_install.txt', 'w')
    for line in pkgs.split('\n'):
        if not line.startswith('rsetup') or line.startswith('configobj'):
            before.write(line + '\n')
    before.close()
setup.parser.add_argument('--ci', action='store_true',
                          help='running in CI context')


@command
def ci(args):
    args.ci = True

    # read config
    LOG.info('Working path %s', os.path.abspath('.'))
    if os.path.exists('.ci.yml'):
        LOG.info('loaded .ci.yml')
        args.cfg.update(yaml.load(open('.ci.yml')))

    setup(args)
    sdist(args)
    proc.exe(['pip', 'install'] + glob.glob('dist/*.tar.gz'))
    test(args)

@command
def initve(args):
    """initilize virtual env with rsetup default configuration"""
    if not 'VIRTUAL_ENV' in os.environ:
        LOG.error('mist be run inside active virtual env')
        return
    run_script = """#!{ve_path}/bin/python

VIRTUAL_ENV = '{ve_path}'

import os
import sys

os.environ['VIRTUAL_ENV'] = VIRTUAL_ENV
os.environ['PATH'] = VIRTUAL_ENV + '/bin:' + os.environ['PATH']

print 'running in ve ' + VIRTUAL_ENV
print sys.argv[1], sys.argv[2:]
sys.stdout.flush()
os.execvpe(sys.argv[1], sys.argv[1:], os.environ)
    """
    run_script = run_script.format(ve_path=os.environ['VIRTUAL_ENV'])
    run_script_path = os.path.join(os.environ['VIRTUAL_ENV'], 'run')
    if os.path.exists(run_script_path):
        os.unlink(run_script_path)
    open(run_script_path, 'w').write(run_script)
    os.chmod(run_script_path, stat.S_IEXEC | stat.S_IREAD | stat.S_IWUSR)


def rve():
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    logging.basicConfig(level=getattr(logging, log_level),
                        format='%(asctime)s %(name)s[%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    args = ARG_PARSER.parse_args()
    args.git_root = proc.read('git', 'rev-parse', '--show-toplevel').strip()
    args.cfg = {'test':
                    ['pytest', 'pylint'],
                'test.pytest': True,
                'test.pylint': True,
                'test.behave': True}

    args.func(args)