""" Download cache for files

"""

import os
import hashlib
import urllib2
import shutil
import logging

LOG = logging.getLogger(__name__)


def chmod_chromedriver(dir):
    """ Set executable permission on chromedriver file after download. """
    os.chmod(os.path.join(dir, "chromedriver"), 0755)


CACHE_DIR = os.path.expanduser('~/.cache/rsetup')

KNOWN = {
    'selenium-server-standalone-2.35.0.jar': {
        'url': 'http://selenium.googlecode.com/files/selenium-server-standalone-2.35.0.jar',
        'md5sum': 'bc34d2b9727c1ac3aa45fe98dd666cbf'
    },
    'chromedriver_linux64_2.3': {
        'url': 'https://chromedriver.googlecode.com/files/chromedriver_linux64_2.3.zip',
        'md5sum': '1a816cc185a15af4d450805629790b0a',
        'unzip': True,
        "post-setup": chmod_chromedriver
    },
    'GeoLiteCity.dat': {
        'url': 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz',
        'md5sum': '840eb6ab24ddfb8ad63a79a12ef2e65e',
        'unzip': True
    }
}

for key, value in KNOWN.items():
    value['name'] = key


def get(target):
    if isinstance(target, basestring):
        if target in KNOWN:
            target = KNOWN[target]
        else:
            target = {'url': target,
                      'md5sum': None,
                      'name': target.split('/')[-1]}

    cache_path = CACHE_DIR + '/' + target['url'].split('/')[-1].split('#')[0].split('?')[0]
    return_path = CACHE_DIR + '/' + target['name']

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    elif os.path.exists(cache_path):
        if target.get('md5sum'):
            # TODO don't hold full file in memory
            check = hashlib.md5(open(cache_path).read()).hexdigest()
            if check == target.get('md5sum'):
                return return_path
            else:
                LOG.warning("Different md5 sums for file '{}' causing new download".format(target['name']))
        else:
            return return_path

    data = urllib2.urlopen(target['url'])
    shutil.copyfileobj(data, open(cache_path, 'w'))

    if target.get('unzip'):
        # Unzip archive
        if cache_path.endswith('.zip'):
            import zipfile
            zfile = zipfile.ZipFile(cache_path)
            for name in zfile.namelist():
                dirname, filename = os.path.split(name)
                print "Decompressing " + filename + " on " + os.path.join(CACHE_DIR, target['name'], dirname)
                if not os.path.exists(os.path.join(CACHE_DIR, target['name'], dirname)):
                    os.mkdir(os.path.join(CACHE_DIR, target['name'], dirname))
                    fd = open(os.path.join(CACHE_DIR, target['name'], name), "w")
                    shutil.copyfileobj(zfile, fd)
        # TODO .tar.gz
        elif cache_path.endswith('.gz'):
            import gzip
            dst = cache_path[:-3]
            shutil.copyfileobj(gzip.open(cache_path, 'rb'), open(dst, 'w'))

    if target.get('post-setup'):
        target['post-setup'](os.path.join(CACHE_DIR, target['name']))
    return return_path

