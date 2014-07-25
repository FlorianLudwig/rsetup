"""rook virtual env control"""
import atexit
import tempfile
import os
import sys
import re
import logging
import argparse
import glob
import shutil
import stat

import yaml
import subprocess
import fpt

from rsetup import proc, config


PACKAGE_NAME = re.compile('[a-zA-Z0-9-_]{1,64}$')

TEST_PKGS = [
             'setuptools>=0.8',
             'pip',
             'wheel'
]

# 'coverage==3.6',
# 'pytest-cov==1.6',
# 'pylint==0.28.0',
# 'behave==1.2.3',
# 'selenium==2.33.0',

ARG_PARSER = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)


SUB_PARSER = ARG_PARSER.add_subparsers(help='Command help')

LOG = logging.getLogger(__name__)


def guess_current_branch():
    # check for gitlab ci variable
    if 'CI_BUILD_REF_NAME' in os.environ:
        return os.environ['CI_BUILD_REF_NAME']

    # make sure GitPython is installed
    # proc.exe(['pip', 'install', 'GitPython==0.3.2.RC1'])

    from git import Repo

    repo = Repo()
    current_branch = []
    for ref in repo.references:
        if ref.commit == repo.head.commit:
            try:
                remote = ref.remote_name
            except NameError:
                continue
            if remote == 'origin' and ref.name != 'origin/HEAD':
                current_branch.append(ref.name[7:])
    if len(current_branch) == 0:
        return None
    elif len(current_branch) == 1:
        return current_branch[0]
    else:
        for preferred_branch in ('master', 'staging', 'production'):
            for branch in current_branch:
                if branch == preferred_branch:
                    return branch
        return sorted(current_branch, key=lambda b: b.name)[0]


def shellquote(path):
    """escape a path

    :rtype str:"""
    return "'" + path.replace("'", "'\\''") + "'"


def command(func):
    """Decorator for CLI exposed functions"""
    func.parser = SUB_PARSER.add_parser(func.func_name, help=func.__doc__)
    func.parser.set_defaults(func=func)

    # options for all commands
    func.parser.add_argument('--ci', action='store_true',
                             help='running in CI context')
    func.parser.add_argument('--config', help='path to config', default='.ci.yml')
    return func


def get_config_path(args):
    """get the path of the config file if existent

    :rtype: str
    """
    path = os.path.abspath('.ci.yml')
    if os.path.exists(path):
        return path


def get_module_path(name):
    """get the path of the module given by name

    This imports the named module and therefore might have side effects

    :param name: Name of the module
    :type name: str
    :rtype: str
    """
    return os.path.dirname(__import__(name).__file__)


def get_python_interpreter(args):
    if 'PYTHON_EXE' in os.environ:
        return os.environ['PYTHON_EXE']
    return 'python'


@command
def sdist(args):
    """create source distribution

    returns path
    :rtype: str
    """
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    python = get_python_interpreter(args)
    proc.exe([python, 'setup.py', 'sdist', '--dev'])
    dist = os.listdir('dist')
    assert len(dist) == 1
    return os.path.abspath('dist/' + dist[0])


@command
def test(args):
    # save state of virtualenv on testing start
    freeze = subprocess.check_output(['pip', 'freeze', '--local'])
    open('.rve-pip-freeze.txt', 'w').write(freeze)

    setup_data = fpt.get_setup_data('setup.py')
    pkgs = setup_data['packages']
    pkgs = set(pkg.split('.')[0] for pkg in pkgs)
    pkgs = list(pkgs)

    if args.cfg['test.pytest']:
        LOG.info('running py.test')

        py_test = ['py.test']
        for pkg in pkgs:
            py_test.extend(('--cov', pkg))

        if args.ci:
            py_test += ['--cov-report', 'xml', '--junitxml=junit.xml']

        py_test.extend(pkgs)

        LOG.info('starting' + repr(py_test))
        proc.exe(py_test)

        if args.ci:
            proc.exe(['coverage', 'html'])

    if args.cfg['test.pylint']:
        LOG.info('running pylint')
        pylint = ['pylint', '-f', 'parseable'] + pkgs
        # maybe check pylint return code
        # http://lists.logilab.org/pipermail/python-projects/2009-November/002068.html
        pylint_out = proc.read(pylint, check_exit_code=False)
        open('pylint.out', 'w').write(pylint_out)

    if args.cfg['test.behave']:
        LOG.info('running behave')
        for path in args.cfg['test.behave.features']:
            proc.exe(['behave', path])


@command
def setup(args):
    # ensure we have tox installed
    pkgs = TEST_PKGS[:]
    # if args.cfg['test.behave']:
    #     pkgs.append('rbehave>=0.0.0.git0')
    proc.exe(['pip', 'install', '-I'] + pkgs)


@command
def ci(args):
    args.ci = True

    # get info about package
    name = subprocess.check_output(['python', 'setup.py', '--name'])
    name = name.strip()
    if not PACKAGE_NAME.match(name):
        print 'invalid package name', name
        sys.exit(1)

    if args.branch:
        branch = args.branch
    else:
        branch = guess_current_branch()

    # read config
    LOG.info('Working path %s', os.path.abspath('.'))
    config_arg = ''
    cfg = get_config_path(args)
    if cfg:
        config_arg = '--config ' + shellquote(cfg)

    # setup(args)
    dist = sdist(args)

    if os.path.exists('tox.ini'):
        print("package tox.ini cannot be handled at this time")

    deps = ''
    if name != 'rsetup':
        # if we are not testing ourselves right now install rsetup into test environment
        deps = 'deps: rsetup>0.0.0.git0'

    tox = open('tox.ini', 'w')
    tox.write("""[tox]
envlist = {envist}

[testenv]
{deps}
sitepackages = {sitepackages}
commands =
  rve setup --ci {config_arg}
  pip install 'file://{path}#egg={name}[test]'
  rve test --ci {config_arg}
""".format(
        sitepackages=args.cfg['tox.sitepackages'],
        deps=deps,
        envist=args.cfg['envlist'],
        config_arg=config_arg,
        path=dist,
        name=name))
    tox.close()
    # delete tox dir if existent
    if os.path.exists('.tox'):
        shutil.rmtree('.tox')
    proc.exe(['tox'])

    ## alternative to tox:
    # initve(args)
    # setup(args)
    # test(args)

    # TODO
    # there will be more than one .rve-pip-freeze.txt be created if we run tox on multiple python versions

    ## upload result to devpi
    # on the ci the virtualenv containing rve might be read-only
    # the default build path (<venvpath>/build) is read-only
    # in this case as well so we specify an alternative build path
    build_dir = tempfile.mkdtemp('pip_build_')
    if 'DEVPI_SERVER' in os.environ:
        LOG.info('uploading to devpi server')
        # proc.exe(['pip', 'install', '-U', 'devpi-client==1.2.1'])
        proc.exe(['devpi', 'use', os.environ['DEVPI_SERVER']])
        proc.exe(['devpi', 'login', os.environ['DEVPI_USER'], '--password', os.environ['DEVPI_PASSWORD']])
        proc.exe(['devpi', 'use', os.environ['DEVPI_INDEX']])
        proc.exe(['devpi', 'upload', '--from-dir', 'dist'])
        proc.exe(['pip', 'wheel', '-r', '.rve-pip-freeze.txt',
                                  '-b', build_dir])
        proc.exe(['devpi', 'upload', '--from-dir', 'wheelhouse'])
    else:
        LOG.info('DEVPI_SERVER environment variable not set. not uploading')

    if os.path.exists('/srv/pypi-requirements/'):
        fname = '{}.{}.txt'.format(name, branch)
        LOG.info('updating requirements-txt.r0k.de/' + fname)
        shutil.copy('.rve-pip-freeze.txt', '/srv/pypi-requirements/' + fname)

ci.parser.add_argument('--branch', help='branch name we are running on')


def create_test_ve(args):
    """create a virtual env to run tests in"""
    ve_path = tempfile.mkdtemp()
    proc.exe(['virtual'])
    proc.exe(['pip', 'install'] + glob.glob('dist/*.tar.gz'))

    def rm_test_ve():
        shutil.rmtree(ve_path)
    atexit.register(rm_test_ve)
    return ve_path


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
    run_script_path = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'run')
    if os.path.exists(run_script_path):
        os.unlink(run_script_path)
    open(run_script_path, 'w').write(run_script)
    os.chmod(run_script_path, stat.S_IEXEC | stat.S_IREAD | stat.S_IWUSR)


def rve():
    """rve command line tool entry point"""
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    logging.basicConfig(level=getattr(logging, log_level),
                        format='%(asctime)s %(name)s[%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    args = ARG_PARSER.parse_args()
    args.git_root = proc.read('git', 'rev-parse', '--show-toplevel').strip()
    args.cfg = {'test.pytest': False,
                'test.pylint': False,
                'test.behave': False,
                'tox.sitepackages': False,
                'test.behave.features': set(),
                'envlist': 'py27'
                }

    # auto detect tests to run
    def walker(arg, dirpath, filenames):
        for dirname in filenames[:]:
            if dirname.startswith('.'):
                filenames.remove(dirname)

        for fname in filenames:
            if fname.endswith('.py'):
                args.cfg['test.pylint'] = True
            elif fname.endswith('.feature'):
                args.cfg['test.behave'] = True
                args.cfg['test.behave.features'].add(dirpath)

            if fname.startswith('test_') and fname.endswith('.py'):
                args.cfg['test.pytest'] = True

    os.path.walk('.', walker, None)

    cfg = get_config_path(args)
    if cfg:
        LOG.info('loading {}'.format(cfg))
        local_conf = yaml.load(open('.ci.yml'))
        args.cfg.update(local_conf)

    args.func(args)
