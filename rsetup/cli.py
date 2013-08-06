"""rook virtual env control"""
import os
import logging
import argparse

import subprocess
from rsetup.common import exe


ARG_PARSER = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)
SUB_PARSER = ARG_PARSER.add_subparsers(help='Command help')


def command(func):
    """Decorator for CLI exposed functions"""
    func.parser = SUB_PARSER.add_parser(func.func_name, help=func.__doc__)
    func.parser.set_defaults(func=func)
    return func


TEST_PKGS = ['GitPython==0.3.2.RC1',
             'pytest-cov',
             'behave',
             'selenium'
]


@command
def setup(args):
    proc = subprocess.Popen(['pip', 'install'] + TEST_PKGS)
    proc.wait()

    pkgs = exe(['pip', 'freeze'])
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