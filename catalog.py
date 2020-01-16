import os
import re
import yaml
import numpy as np
from astropy.utils.data import get_pkg_data_filename
from astropy.io import fits
import tempfile
import urllib


class Catalog(object):
    def __init__(self, filename):
        self.remote_objects = []
        self.cache = {}
        with open(filename, 'r') as fd:
            self.yaml = yaml.safe_load(fd)
        self.scrape_chandra()
        self.objects = list(self.yaml.keys())
        self.local_objects = list(set(self.objects) - set(self.remote_objects))
        
    def get_bands(self, object_name):
        return list(self.yaml[object_name].keys())

    def load_data(self, object_name, band, fname=None):
        if fname is None:
            if os.path.isfile(band):
                fname = band
            else:
                if self.yaml[object_name][band].startswith('https://chandra.harvard.edu'):
                    fname_url = self.yaml[object_name][band]
                    object_dir = os.path.join('data', object_name)
                    if not os.path.isdir(object_dir):
                        os.mkdir(object_dir)
                    fname = os.path.join(object_dir,
                                         fname_url.rsplit('/', 1)[-1])
                    if not os.path.isfile(fname):
                        urllib.request.urlretrieve(fname_url, fname)
                    assert(os.path.isfile(fname))
                else:
                    fname = os.path.join('data', object_name, self.yaml[object_name][band])
        if fname not in self.cache:
            image_file = get_pkg_data_filename(fname)
            # fits.info(image_file)
            self.cache[fname] = fits.getdata(image_file, ext=0)
            if object_name == 'whirlpool_galaxy':
                self.cache[fname] = self.cache[fname].T
        out = self.cache[fname]
        return out

    def convert_band(self, band):
        conversion_dict = {'R': 'red', 'G': 'green', 'B': 'blue',
                           'he': 'high_energy', 'le': 'low_energy',
                           'ir': 'infrared', 'opt': 'optical'}
        split = [conversion_dict.get(x, x) for x in band.split('_')]
        return '_'.join(split)

    def scrape_chandra(self):
        page = 'https://chandra.harvard.edu/photo/openFITS/multiwavelength_data.html'
        regex = r'<li><a href="(?P<path>(?P<directory>.*?)(?P<object>[^_/]*?)_(?P<band>.*?).fits)">(?P<description>.*?)</a></li>'
        index_file = 'chandra_index.html'
        alias_map = {'ngc6543': 'cats_eye_nebula',
                     'm51': 'whirlpool_galaxy'}
        if not os.path.isfile(index_file):
            urllib.request.urlretrieve(page, index_file)
            assert(os.path.isfile(index_file))
        with open(index_file, 'r') as fd:
            contents = fd.read()
        matches = re.findall(regex, contents)
        for match in re.finditer(regex, contents):
            grp = match.groupdict()
            grp['object'] = alias_map.get(grp['object'], grp['object'])
            grp['band'] = self.convert_band(grp['band'])
            if grp['object'] not in self.yaml:
                self.yaml[grp['object']] = {}
                self.remote_objects.append(grp['object'])
            if grp['band'] not in self.yaml[grp['object']]:
                self.yaml[grp['object']][grp['band']] = '/'.join(
                    ['https://chandra.harvard.edu', grp['path']])
