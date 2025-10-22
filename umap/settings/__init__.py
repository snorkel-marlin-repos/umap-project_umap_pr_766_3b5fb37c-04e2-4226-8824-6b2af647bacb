import imp
import os
import sys

from django.utils.termcolors import colorize

from .base import *  # NOQA, default values

# Allow to override setting from any file, may be out of the PYTHONPATH,
# to make it easier for non python people.
path = os.environ.get('UMAP_SETTINGS')
if not path:
    # Retrocompat
    path = os.path.join('/etc', 'umap', 'umap.conf')
    if not os.path.exists(path):
        # Retrocompat
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'local.py')
        if not os.path.exists(path):
            msg = ('You must configure UMAP_SETTINGS or define '
                   '/etc/umap/umap.conf')
            print(colorize(msg, fg='red'))
            sys.exit(1)

d = imp.new_module('config')
d.__file__ = path
try:
    with open(path) as config_file:
        exec(compile(config_file.read(), path, 'exec'), d.__dict__)
except IOError as e:
    msg = 'Unable to import {} from UMAP_SETTINGS'.format(path)
    print(colorize(msg, fg='red'))
    sys.exit(e)
else:
    print('Loaded local config from', path)
    for key in dir(d):
        if key.isupper():
            value = getattr(d, key)
            if key.startswith('LEAFLET_STORAGE'):
                # Retrocompat pre 1.0, remove me in 1.1.
                globals()['UMAP' + key[15:]] = value
            elif key == 'UMAP_CUSTOM_TEMPLATES':
                globals()['TEMPLATES'][0]['DIRS'].insert(0, value)
            elif key == 'UMAP_CUSTOM_STATICS':
                globals()['STATICFILES_DIRS'].insert(0, value)
            else:
                globals()[key] = value
