import os
import sys

import rsetup.setup
from setuptools import setup, find_packages


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
VERSION_SUFFIX = ''


if '--dev' in sys.argv:
    VERSION_SUFFIX = rsetup.setup.git_version_suffix()
    sys.argv.remove('--dev')


setup(
    name='rsetup',
    version='0.0.1' + VERSION_SUFFIX,
    author='Grey Rook Entertainment',
    packages=find_packages(),
    install_requires=['configobj', 'PyYaml', 'GitPython==0.3.2.RC1', 'fpt'],
    entry_points={
        'console_scripts': [
            'rve = rsetup.cli:rve',
        ],
    },
    cmdclass={'sdist': rsetup.setup.sdist_with_version_suffic(VERSION_SUFFIX)}
)
