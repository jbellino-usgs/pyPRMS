import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
except ImportError:
    plt = None

try:
    import shapefile
except ImportError:
    shapefile = None


def discrete_colormap(values, cmap='jet', colors=None, cmap_name=None):
    """
    Code to create a discrete colormap for use with integer values suitable
    for plotting with a legend.
    Taken from
    https://stackoverflow.com/questions/14777066/matplotlib-discrete
    -colorbar
    :param values:
    :param cmap:
    :param colors:
    :param cmap_name:
    :return:
    """
    if colors is not None:
        # Default to a list of user-specified colors
        cmaplist = colors
    else:
        # Define the colormap from which colors will be drawn
        cmap = plt.get_cmap(cmap)
        cmaplist = [cmap(i) for i in range(cmap.N)]

    # create the new map
    mycmap = LinearSegmentedColormap.from_list(
        cmap_name, cmaplist, len(cmaplist))

    # define the bins and normalize
    bounds = np.linspace(0, len(values), len(values) + 1)
    norm = BoundaryNorm(bounds, len(cmaplist))
    return mycmap, norm


def shapefile_to_patch_collection(shp, radius=500., idx=None):
    """
    Create a patch collection from the shapes in a shapefile
    Parameters
    ----------
    shp : string
        Name of the shapefile to convert to a PatchCollection.
    radius : float
        Radius of circle for points in the shapefile.  (Default is 500.)
    idx : iterable int
        A list or array that contains shape numbers to include in the
        patch collection.  Return all shapes if not specified.
    Returns
    -------
        pc : matplotlib.collections.PatchCollection
            Patch collection of shapes in the shapefile
    """
    if shapefile is None:
        s = 'Could not import shapefile.  Must install pyshp in order to ' \
            'plot shapefiles.'
        raise Exception(s)

    from matplotlib.patches import Polygon, Circle, Path, PathPatch
    from matplotlib.collections import PatchCollection
    if isinstance(shp, str):
        sf = shapefile.Reader(shp)
    else:
        sf = shp
    shapes = sf.shapes()
    nshp = len(shapes)
    ptchs = []
    if idx is None:
        idx = range(nshp)
    for n in idx:
        st = shapes[n].shapeType
        if st in [1, 8, 11, 21]:
            # points
            for p in shapes[n].points:
                ptchs.append(Circle( (p[0], p[1]), radius=radius))
        elif st in [3, 13, 23]:
            # line
            vertices = []
            for p in shapes[n].points:
                vertices.append([p[0], p[1]])
            vertices = np.array(vertices)
            path = Path(vertices)
            ptchs.append(PathPatch(path, fill=False))
        elif st in [5, 25, 31]:
            # polygons
            pts = np.array(shapes[n].points)
            prt = shapes[n].parts
            par = list(prt) + [pts.shape[0]]
            for pij in range(len(prt)):
                ptchs.append(Polygon(pts[par[pij]:par[pij+1]]))
    pc = PatchCollection(ptchs)
    return pc


def plot_shapefile(shp, ax=None, radius=500., cmap='Dark2', edgecolor='scaled',
                   facecolor='scaled', a=None, masked_values=None, idx=None,
                   **kwargs):
    """
    Generic function for plotting a shapefile.
    Parameters
    ----------
    shp : string
        Name of the shapefile to plot.
    ax : matplolib.pyplot.axes object
    radius : float
        Radius of circle for points.  (Default is 500.)
    cmap : string
        Name of colormap to use for polygon shading (default is 'Dark2')
    edgecolor : string
        Color name.  (Default is 'scaled' to scale the edge colors.)
    facecolor : string or list
        Color name or list of colors.  (Default is 'scaled' to scale the face
        colors.)
    a : numpy.ndarray
        Array to plot.
    masked_values : iterable of floats, ints
        Values to mask.
    idx : iterable int
        A list or array that contains shape numbers to include in the
        patch collection.  Return all shapes if not specified.
    kwargs : dictionary
        Keyword arguments that are passed to PatchCollection.set(``**kwargs``).
        Some common kwargs would be 'linewidths', 'linestyles', 'alpha', etc.
    Returns
    -------
    pc : matplotlib.collections.PatchCollection
    Examples
    --------
    """

    if shapefile is None:
        s = 'Could not import shapefile.  Must install pyshp in order to ' \
            'plot shapefiles.'
        raise Exception(s)

    if 'vmin' in kwargs:
        vmin = kwargs.pop('vmin')
    else:
        vmin = None

    if 'vmax' in kwargs:
        vmax = kwargs.pop('vmax')
    else:
        vmax = None

    if ax is None:
        ax = plt.gca()
    cm = plt.get_cmap(cmap)
    pc = shapefile_to_patch_collection(shp, radius=radius, idx=idx)
    pc.set(**kwargs)
    if a is None:
        nshp = len(pc.get_paths())
        cccol = cm(1. * np.arange(nshp) / nshp)
        if facecolor == 'scaled':
            pc.set_facecolor(cccol)
        else:
            pc.set_facecolor(facecolor)
        if edgecolor == 'scaled':
            pc.set_edgecolor(cccol)
        else:
            pc.set_edgecolor(edgecolor)
    else:
        pc.set_cmap(cm)
        if masked_values is not None:
            for mval in masked_values:
                a = np.ma.masked_equal(a, mval)
        if edgecolor == 'scaled':
            pc.set_edgecolor('none')
        else:
            pc.set_edgecolor(edgecolor)
        pc.set_array(a)
        pc.set_clim(vmin=vmin, vmax=vmax)
    # add the patch collection to the axis
    ax.add_collection(pc)
    return pc
