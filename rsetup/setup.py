import os
import fnmatch
from datetime import datetime

from distutils.command.sdist import sdist


def find_package_data(package_path, dirs=None, excludes=['*.py', '*.pyc', '*.pyo']):
    if dirs is None:
        dirs = ['']
    elif isinstance(dirs, basestring):
        dirs = [dirs]
    results = []
    for src_dir in dirs:
        for path, dirs, files in os.walk(os.path.join(package_path, src_dir)):
            rel_path = path[len(package_path):].strip('/')
            for file in files:
                for exclude in excludes:
                    if fnmatch.fnmatch(file, exclude):
                        break
                else:
                    # this file does not match any exclude pattern
                    results.append(os.path.join(rel_path, file))
    return results


def git_version_suffix():
    # delay import of third party module
    from git import Repo
    repo = Repo()
    committed_date = repo.head.commit.committed_date
    return '.git' + datetime.fromtimestamp(committed_date).strftime('%Y%m%d%H%M%S')


def sdist_with_version_suffic(suffix):
    class sdist_cls(sdist):
        def make_release_tree(self, base_dir, files):
            sdist.make_release_tree(self, base_dir, files)
            # make sure we include the git version in the release
            setup_py = open(base_dir + '/setup.py').read()
            if not "\nVERSION_SUFFIX = ''\n" in setup_py:
                raise Exception('Variable for version suffix is missing.')
            setup_py = setup_py.replace("\nVERSION_SUFFIX = ''\n", "\nVERSION_SUFFIX = {}\n".format(repr(suffix)))
            f = open(base_dir + '/setup.py', 'w')
            f.write(setup_py)
            f.close()

    return sdist_cls