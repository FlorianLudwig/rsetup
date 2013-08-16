"""Load configs. Copy paste from rueckenwind"""
from configobj import ConfigObj
import os
import pkg_resources
import logging

LOG = logging.getLogger(__name__)


def update_config(cfg, update):
    for key, value in update.items():
        if key in cfg and isinstance(value, dict):
            update_config(cfg[key], value)
        else:
            cfg[key] = value


def load_config(module_name, extra_files=None):
    """Load configuration for given module and return config dict


     """
    if isinstance(extra_files, basestring):
        extra_files = [extra_files]
    cfg_name = module_name + '.cfg'
    CONFIG_FILES = [pkg_resources.resource_filename(module_name, cfg_name)]
    CONFIG_FILES += ['/etc/' + cfg_name, os.path.expanduser('~/.')  + cfg_name]
    if 'VIRTUAL_ENV' in os.environ:
        CONFIG_FILES.append(os.environ['VIRTUAL_ENV'] + '/etc/' + cfg_name)
    if extra_files:
        CONFIG_FILES.extend(extra_files)
        # read config
    config = {}
    for config_path in CONFIG_FILES:
        if os.path.exists(config_path):
            LOG.info('reading config: ' + config_path)
            config_obj = ConfigObj(config_path)
            update_config(config, config_obj)
        else:
            LOG.debug('config does not exist: ' + config_path)

    return ConfigObj(config)