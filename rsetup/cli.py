"""rook virtual env control"""
import os
import logging
import argparse
import glob
import shutil

import setuptools
import subprocess
from rsetup import proc


ARG_PARSER = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)
SUB_PARSER = ARG_PARSER.add_subparsers(help='Command help')


def command(func):
    """Decorator for CLI exposed functions"""
    func.parser = SUB_PARSER.add_parser(func.func_name, help=func.__doc__)
    func.parser.set_defaults(func=func)
    return func


TEST_PKGS = ['GitPython==0.3.2.RC1',
             'coverage==3.6',
             'pytest-cov==1.6',
             'pylint==0.28.0',
             'behave==1.2.3',
             'selenium==2.33.0'
]


def get_setup_data(path):
    data = {}

    old_setup = setuptools.setup

    def s(**kwargs):
        data.update(kwargs)

    setuptools.setup = s
    exec compile(open(path).read(), path, 'exec') in {'__file__': path}, {}
    setuptools.setup = old_setup
    return data


def get_python_interpreter(args):
    if 'PYTHON_EXE' in os.environ:
        return os.environ['PYTHON_EXE']
    return 'python'


@command
def sdist(args):
    python = get_python_interpreter(args)
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    proc.exe([python, 'setup.py', 'sdist', '--dev'])
    if args.ci:
        proc.exe(['pip', 'install'] + glob.glob('dist/*.tar.gz'))

sdist.parser.add_argument('--ci', action='store_true',
                          help='running in CI context')


@command
def test(args):
    setup_data = get_setup_data('setup.py')
    pkgs = setup_data['packages']
    pkgs = set(pkg.split('.')[0] for pkg in pkgs)
    pkgs = list(pkgs)

    py_test = ['py.test', '--cov', '.']
    if args.ci:
        py_test += ['--cov-report', 'xml', '--junitxml=junit.xml']
    proc.exe(py_test)

    pylint = ['pylint', '-f', 'parseable'] + pkgs
    # maybe check pylint return code
    # http://lists.logilab.org/pipermail/python-projects/2009-November/002068.html
    pylint_out = proc.read(pylint, check_exit_code=False)
    open('pylint.out', 'w').write(pylint_out)

    proc.exe(['coverage', 'html'])
test.parser.add_argument('--ci', action='store_true',
                         help='running in CI context')


@command
def setup(args):
    p = subprocess.Popen(['pip', 'install'] + TEST_PKGS)
    p.wait()

    pkgs = proc.read(['pip', 'freeze'])
    before = open('pip_freeze_before_install.txt', 'w')
    for line in pkgs.split('\n'):
        if not line.startswith('rsetup') or line.startswith('configobj'):
            before.write(line + '\n')
    before.close()
setup.parser.add_argument('--ci', action='store_true',
                          help='running in CI context')


def rve():
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    logging.basicConfig(level=getattr(logging, log_level),
                        format='%(asctime)s %(name)s[%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    args = ARG_PARSER.parse_args()
    args.func(args)