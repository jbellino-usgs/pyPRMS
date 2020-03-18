import os
import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib.colors
    from matplotlib.patches import Patch
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import Polygon
except ImportError:
    plt = None

try:
    import geopandas as gpd
except ImportError:
    gpd = None

from . import plotutil
from ..parfile import ParameterFile
from ..parbase import Parameter


class PlotMapView(object):
    """
    Class to create a map of the model. Delegates plotting
    functionality based on model grid type.
    Parameters
    ----------
    parameterfile : str or pyPRMS.ParameterFile object
        The parameter file  (Default is None)
    hru_shapefile : str
        Name/path to the shapefile containing HRU geometry
    hru_id_col : str
        Name of the column in the HRU shapefile indicating HRU numbers
    ax : matplotlib.pyplot axis
        The plot axis.  If not provided it, plt.gca() will be used.
        If there is not a current axis then a new one will be created.
    extent : tuple of floats
        (xmin, xmax, ymin, ymax) will be used to specify axes limits.  If None
        then these will be calculated based on grid, coordinates, and rotation.
    Notes
    -----
    """

    def __init__(self, parameterfile, hru_shapefile,
                 hru_id_col='hru_id_reg',
                 ax=None, extent=None):

        if plt is None:
            s = 'Could not import matplotlib.  Must install matplotlib ' + \
                ' in order to use PlotMapView class'
            raise ImportError(s)

        if isinstance(parameterfile, str):
            self.__parameter_file = ParameterFile(parameterfile)
        else:
            self.__parameter_file = parameterfile

        assert os.path.exists(hru_shapefile), f'Shapefile not found: ' \
                                              f'{hru_shapefile}'
        self.__shapefile = hru_shapefile
        self.__hru_id_col = hru_id_col

        if ax is None:
            try:
                self.ax = plt.gca()
                self.ax.set_aspect('equal')
            except:
                self.ax = plt.subplot(1, 1, 1, aspect='equal', axisbg="white")
        else:
            self.ax = ax

        if extent is not None:
            self._extent = extent
        else:
            self._extent = None

    @property
    def extent(self):
        return self._extent

    def plot_shapefile(self, shp, **kwargs):
        """
        Plot a shapefile.  The shapefile must be in the same coordinates as
        the rotated and offset grid.
        Parameters
        ----------
        shp : string or pyshp shapefile object
            Name of the shapefile to plot
        kwargs : dictionary
            Keyword arguments passed to plotutil.plot_shapefile()
        """
        if 'ax' in kwargs:
            ax = kwargs.pop('ax')
        else:
            ax = self.ax

        if 'idx' in kwargs:
            idx = kwargs.pop('idx')
        else:
            idx = None

        patch_collection = plotutil.plot_shapefile(shp, ax, idx=idx, **kwargs)
        ax.autoscale()
        return patch_collection

    def plot_parameter_testing(self, param, **kwargs):
        """
        Plot parameter data values using the input shapefile geometry.

        Parameters
        ----------
        param : str or pyPRMS.Parameter
            Name or parameter object whose data are to be plotted.

        """
        # WARNING:
        # This code assumes the shapes are sorted in the same order as the
        # parameter data. Implement some safety measures to ensure correct
        # ordering.
        if isinstance(param, str):
            param = self.__parameter_file.parameters.get(param)
        s = 'Input parameter must be a valid parameter name or ' \
            'pyPRMS.Parameter object.'
        assert isinstance(param, Parameter), s
        values = param.data
        mn, mx = values.min(), values.max()

        if 'cmap' in kwargs:
            cmap = kwargs.pop('cmap')
        else:
            cmap = plt.get_cmap('viridis')

        if 'norm' in kwargs:
            norm = kwargs.pop('norm')
        else:
            norm = matplotlib.colors.Normalize(vmin=mn, vmax=mx)

        # Cheesy implementation of levels for chloropleth output
        if 'levels' in kwargs:
            levels = kwargs.pop('levels')
            plotable = np.zeros_like(values, dtype=np.int32)
            for i, level in enumerate(levels):
                if i == 0:
                    plotable[(values <= level)] = i
                else:
                    plotable[((values > levels[i - 1]) & (values <= level))]\
                        = i
            plotable[values > levels[-1]] = len(levels)
            cmap, norm = plotutil.discrete_colormap(sorted(np.unique(
                plotable)), cmap=cmap)
            values = plotable

        colors = [cmap(norm(v)) for v in values]
        pc = self.plot_shapefile(self.__shapefile, facecolor=colors, **kwargs)
        return pc

    def plot_parameter(self, param, **kwargs):
        assert gpd is not None, 'Geopandas must be installed to use this ' \
                                'function.'
        if isinstance(param, str):
            param = self.__parameter_file.parameters.get(param)
        s = 'Input parameter must be a valid parameter name or ' \
            'pyPRMS.Parameter object.'
        assert isinstance(param, Parameter), s
        values = param.data
        mn, mx = values.min(), values.max()

        if 'cmap' in kwargs:
            cmap = kwargs.pop('cmap')
        else:
            cmap = plt.get_cmap('viridis')

        if 'norm' in kwargs:
            norm = kwargs.pop('norm')
        else:
            norm = matplotlib.colors.Normalize(vmin=mn, vmax=mx)

        if 'ax' in kwargs:
            ax = kwargs.pop('ax')
        else:
            ax = self.ax

        if 'idx' in kwargs:
            idx = kwargs.pop('idx')
        else:
            idx = None

        gdf = gpd.read_file(self.__shapefile)
        gdf = gdf.set_index(self.__hru_id_col)
        values = param.as_dataframe

        if idx is None:
            idx = gdf.index
        gdf = gdf.loc[idx]
        values = values.loc[idx]

        gdf.loc[:, param.name] = values.loc[:, param.name]
        ax = gdf.plot(column=param.name, cmap=cmap, norm=norm, ax=ax, **kwargs)
        pc = ax.collections[0]
        return pc

    def legend(self, pc, values, labels=None, **kwargs):

        if 'ax' in kwargs:
            ax = kwargs.pop('ax')
        else:
            ax = self.ax

        if 'edgecolor' in kwargs:
            ec = kwargs.pop('edgecolor')
        elif 'ec' in kwargs:
            ec = kwargs.pop('ec')
        else:
            ec = 'darkgrey'

        if labels is None:
            labels = [str(v) for v in values]

        # print(list(zip(values, labels, [pc.cmap(pc.norm(val)) for val in
        #                              values])))

        legend_elements = [Patch(facecolor=pc.cmap(pc.norm(val)),
                                 edgecolor=ec, label=lab) for val, lab in
                           zip(values, labels)]
        legend = ax.legend(handles=legend_elements, **kwargs)
        return legend
