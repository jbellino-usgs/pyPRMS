import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
except ImportError:
    plt = None


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
    bounds = np.linspace(1, len(values) + 1, len(values) + 1)
    norm = BoundaryNorm(bounds, len(cmaplist))
    return mycmap, norm
