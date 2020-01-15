import os
import yaml
import numpy as np
from astropy.utils.data import get_pkg_data_filename
from astropy.io import fits
import tempfile
import urllib


class Catalog(object):
    def __init__(self, filename):
        with open(filename, 'r') as fd:
            self.yaml = yaml.safe_load(fd)
        self.objects = list(self.yaml.keys())
        self.cache = {}
        
    def get_bands(self, object_name):
        return list(self.yaml[object_name].keys())
    
    def load_data(self, object_name, band, fname=None):
        if fname is None:
            if os.path.isfile(band):
                fname = band
            else:
                if self.yaml[object_name][band].startswith('https://chandra.harvard.edu'):
                    fname_url = self.yaml[object_name][band]
                    object_dir = os.path.join('images', object_name)
                    if not os.path.isdir(object_dir):
                        os.mkdir(object_dir)
                    fname = os.path.join(object_dir,
                                         os.path.basename(fname_url))
                    if not os.path.isfile(fname):
                        urllib.request.urlretrieve(fname_url, fname)
                    assert(os.path.isfile(fname))
                else:
                    fname = os.path.join('images', object_name, self.yaml[object_name][band])
        if fname not in self.cache:
            image_file = get_pkg_data_filename(fname)
            # fits.info(image_file)
            self.cache[fname] = fits.getdata(image_file, ext=0)
            if object_name == 'whirlpool_galaxy':
                self.cache[fname] = self.cache[fname].T
        out = self.cache[fname]
        return out
