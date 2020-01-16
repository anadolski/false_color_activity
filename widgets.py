import copy
from catalog import Catalog
from image import Image, ImageLayer
import ipywidgets as widgets
from ipywidgets import interact, interactive
import matplotlib.pyplot as plt
from IPython.display import display, clear_output


catalog = Catalog("images/catalog.yml")
skip_layer_plot = False


def get_layer_widget(layer, plot_function=None):
    color = widgets.ColorPicker(concise=False, description='Layer color',
                                value=layer.color, disabled=False)
    alpha = widgets.FloatSlider(value=1.0, min=0, max=1.0, continuous_update=False,
                                description='Opacity', readout=True)
    logscale = widgets.Checkbox(value=False, description='Logarithmic scaling')
    def wrapper(**kwargs):
        layer.update(object_name=layer.object, band=layer.band, **kwargs)
        if (plot_function is not None) and (not skip_layer_plot):
            plot_function()
    w = interactive(wrapper, color=color, alpha=alpha, logscale=logscale)
    return w


def get_image_widget():
    w_out = widgets.Output(layout=widgets.Layout(width='50%'))
    w_layers = widgets.Accordion()
    def wrapper(object_name, figwidth=10, fullres=False):
        if object_name.startswith('*'):
            print('Downloading fits files, this may take a few minutes.')
            object_name = object_name.strip('*')
        obj = Image(object_name, catalog=catalog)
        obj.widget_setup_complete = False
        def plot_function():
            if not obj.widget_setup_complete:
                return
            w_out.clear_output()
            with w_out:
                obj.plot(fullres=fullres,
                         figsize=(figwidth, figwidth))
        w_clr = []
        extra_colors = ['magenta', 'cyan', 'yellow', 'orange',
                        'purple', 'pink', 'turquoise', 'lavender']
        if 'optical_red' not in obj.bands:
            extra_colors = obj.default_colors + extra_colors
        for band in obj.bands:
            if band.split('optical_')[-1] in obj.default_colors:
                clr = band.split('optical_')[-1]
            else:
                clr = extra_colors.pop(0)
            new_layer = ImageLayer(obj.catalog, object_name=obj.object,
                                   band=band, color=clr)
            obj.append_layer(new_layer)
            w_clr.append(get_layer_widget(new_layer, plot_function=plot_function))
        w_layers.children = w_clr
        for i, band in enumerate(obj.bands):
            w_layers.set_title(i, band)
        obj.widget_setup_complete = True
        plot_function()
    object_list = catalog.local_objects + ['*' + x for x in catalog.remote_objects]
    w = interactive(wrapper,
                    object_name=widgets.Dropdown(
                        options=object_list, value='kepler',
                        description='Object', disabled=False),
                    figwidth=widgets.BoundedFloatText(
                        value=10, min=1, max=15,
                        description='Width (cm)'),
                    fullres=widgets.Checkbox(value=False, description='Display full resolution (slow)'))
    w_control = widgets.VBox([w, w_layers], layout=widgets.Layout(width='50%'))
    w_all = widgets.HBox([w_control, w_out])
    return w_all


def ImageWidget():
    global skip_layer_plot
    skip_layer_plot = True
    w = get_image_widget()
    display(w)
    skip_layer_plot = False
