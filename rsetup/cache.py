""" Download cache for files

"""
import os
import hashlib
import urllib2

CACHE_PATH = os.path.expanduser('~/.cache/rsetup')

KNOWN = {
    'selenium-server-standalone-2.35.0.jar': {
        'url': 'http://selenium.googlecode.com/files/selenium-server-standalone-2.35.0.jar',
        'md5sum': 'bc34d2b9727c1ac3aa45fe98dd666cbf'
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

    cache_path = CACHE_PATH + '/' + target['name']
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)
    elif os.path.exists(cache_path):
        if target.get('md5sum'):
            # TODO don't hold full file in memory
            check = hashlib.md5(open(cache_path).read()).hexdigest()
            if check == target.get('md5sum'):
                return cache_path
        else:
            return cache_path

    # TODO don't hold full file in memory
    data = urllib2.urlopen(target['url']).read()
    open(cache_path, 'w').write(data)

    if target.get('md5sum'):
        check = hashlib.md5(open(cache_path).read()).hexdigest()
        if check != target.get('md5sum'):
            raise IOError('File md5sum does not match downloaded file')

    return cache_path
