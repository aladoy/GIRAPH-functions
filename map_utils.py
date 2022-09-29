import mapclassify as mc
import contextily as cx
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
import geopandas as gpd


def add_basemap(
    ax, crs, gdf=None, face="lightgray", edge="white", provider="OpenStreetMap.CH"
):

    cx_providers = cx.providers.flatten()

    if gdf is None:
        cx.add_basemap(ax, crs=crs, source=cx_providers[provider])
    else:
        gdf.plot(ax=ax, facecolor=face, edgecolor=edge)


def classify_values(var, method, k=5):

    classifiers = {
        'equal_interval': mc.EqualInterval,
        'fisher_jenks': mc.FisherJenks,
        'jenks_caspall': mc.JenksCaspall,
        'maximum_breaks': mc.MaximumBreaks,
        'natural_breaks': mc.NaturalBreaks,
        'quantiles': mc.Quantiles,
        'std_mean': mc.StdMean,
        'boxplot': mc.BoxPlot,
        'percentiles': mc.Percentiles,
        'user_def': mc.UserDefined
    }

    classifier = classifiers[method](var, k=k)

    return classifier


def choropleth_map(ax, classifier, gdf, cmap='viridis', legend=True, scalebar=True):
    '''
    ax: axis on which to plot the map
    classifier: mapclassify element
    gdf: geodataframe from which we extract geometry and crs
    cmap: color map palette, add _r at the end of palette name to reverse
    legend: add legend or not
    scalebar: add a scale bar 
    '''

    classifier.plot(gdf, cmap=cmap, legend=legend, axis_on=False, ax=ax)

    if scalebar is True:
        ax.add_artist(ScaleBar(1))
