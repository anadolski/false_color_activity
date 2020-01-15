import os
import numpy as np
from matplotlib import colors
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
import matplotlib.pyplot as plt
from astropy.visualization import astropy_mpl_style
plt.style.use(astropy_mpl_style)
from catalog import Catalog


def downsample_size(orig_size, size):
    if isinstance(size, tuple):
        size = float(min(size))/float(min(orig_size))
    if isinstance(size, float):
        if size > 1:
            # Only downsample
            size = orig_size
        else:
            size = tuple([int(x * size) for x in orig_size])
    steps = [int(orig_size[i]/size[i]) for i in range(len(size))]
    x_step = int(orig_size[0]/size[0])
    y_step = int(orig_size[1]/size[1])
    if all([x == 1 for x in steps]):
        return orig_size
    size = tuple([int(orig_size[i]/steps[i]) for i in range(len(size))])
    assert(all([(int(orig_size[i]/size[i]) == steps[i])
                for i in range(len(size))]))
    return size


class ImageLayer(object):
    def __init__(self, catalog, *args, **kwargs):
        self.catalog = catalog
        self.object = None
        self.band = None
        self.fname = None
        self.image_data = None
        self.shape = None
        self.color = None
        self.alpha = 1.0
        self.logscale = True
        self.vmin = None
        self.vmax = None
        self.norm = None
        self.cmap = None
        self.min_color = (0, 0, 0, 0)
        self.update(*args, **kwargs)

    def update(self, object_name=None, band=None, fname=None,
               color='white', alpha=1.0, logscale=False,
               vmin=None, vmax=None, min_color=(0, 0, 0, 0)):
        new_data = False
        if (fname, object_name, band) != (self.fname, self.object, self.band):
            self.object = object_name
            self.band = band
            self.fname = fname
            self.image_data = self.catalog.load_data(self.object, self.band, fname=self.fname)
            self.shape = self.image_data.shape
            new_data = True
        self.alpha = alpha
        new_norm = False
        if ((logscale, vmin, vmax) != (self.logscale, self.vmin, self.vmax)
            or (self.norm is None)):
            self.logscale = logscale
            self.vmin = vmin
            self.vmax = vmax
            if logscale:
                self.norm = colors.LogNorm(vmin=vmin, vmax=vmax)
            else:
                self.norm = colors.Normalize(vmin=vmin, vmax=vmax)
            new_norm = True
        new_cmap = False
        if ((min_color, color) != (self.min_color, self.color)
            or (self.cmap is None)):
            self.min_color = min_color
            self.color = color
            self.cmap = LinearSegmentedColormap.from_list(fname, [min_color, color])
            new_cmap = True
        if new_norm or new_cmap:
            self.smap = ScalarMappable(norm=self.norm, cmap=self.cmap)
            
    def get_rgba(self, size=None):
        return self.smap.to_rgba(self.get_image_data(size=size),
                                 alpha=self.alpha)
    
    def plot(self, size=None, ax=None):
        if ax is None:
            ax = plt
        return ax.imshow(self.get_image_data(size=size), alpha=self.alpha,
                         norm=self.norm, cmap=self.cmap, origin='lower')

    def get_color_data(self, size=None):
        return self.norm(self.get_image_data(size=size))
            
    def get_image_data(self, size=None):
        out = self.image_data
        if size is not None:
            orig_size = out.shape
            size = downsample_size(out.shape, size)
            x_step = int(orig_size[0]/size[0])
            y_step = int(orig_size[1]/size[1])
            x_samp = np.vstack(size[1] * [x_step * np.arange(0, size[0])]).T
            y_samp = np.vstack(size[0] * [y_step * np.arange(0, size[1])])
            out = out[x_samp, y_samp]
        return out

    
class Image(object):
    def __init__(self, object_name, catalog=None):
        if catalog is None:
            catalog = Catalog("images/catalog.yml")
        self.object = object_name
        self.layers = []
        self.default_colors = ['red', 'green', 'blue']
        self.shape = None
        self.catalog = catalog
        self.image = None
        
    @property
    def bands(self):
        return self.catalog.get_bands(self.object)

    def add_layer(self, band, color=None, **kwargs):
        if color is None:
            color = self.default_colors[len(self.layers) % len(self.default_colors)]
        new_layer = ImageLayer(self.catalog, object_name=self.object,
                               band=band, color=color, **kwargs)
        self.append_layer(new_layer)

    def append_layer(self, new_layer):
        if self.shape:
            assert(new_layer.shape == self.shape)
        else:
            self.shape = new_layer.shape
        self.layers.append(new_layer)

    def plot(self, fullres=False, size=None, ax=None, figsize=(6, 6)):
        if self.shape is None:
            return
        if ax is None:
            plt.clf()
            f = plt.figure(figsize=figsize)
            ax = f.add_subplot()
        else:
            ax.clear()
        if size is None:
            if fullres:
                size = self.shape
            else:
                factor = 400.0/float(max(self.shape))
                size = downsample_size(self.shape, factor)
        ax.imshow(np.zeros(tuple(list(size) + [3])))
        rgb_layers = {}
        oth_layers = []
        for layer in self.layers:
            if (((layer.color in self.default_colors + ['r', 'g', 'b'])
                 and (layer.color[0] not in rgb_layers))):
                rgb_layers[layer.color[0]] = layer.get_color_data(
                    size=size) * layer.alpha
            else:
                oth_layers.append(layer)
        if rgb_layers:
            rgb_data = np.stack([rgb_layers.get(x, np.zeros(size)) for x in ['r', 'g', 'b']], 2)
            self.image = ax.imshow(rgb_data, origin='lower')
        for layer in oth_layers:
            layer.plot(size=size, ax=ax)
        ax.axis("off")
        plt.show()
