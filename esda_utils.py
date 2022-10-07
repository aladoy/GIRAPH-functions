# esda_utils.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from libpysal.weights import min_threshold_distance, Kernel, DistanceBand, Queen, Rook
from esda.moran import Moran, Moran_Local
from esda import fdr
from splot import esda as esdaplot
from matplotlib.collections import LineCollection
from matplotlib import patches, colors
import map_utils as map

sns.set_style("darkgrid")


def get_min_threshold(gdf):
    """This function computes the minimal threshold distance between points"""

    if gdf.geometry.geom_type.unique()[0] == "Polygon":
        centroid = gdf.centroid
        array = pd.DataFrame({"X": centroid.x, "Y": centroid.y}).values
    elif gdf.geometry.geom_type.unique()[0] == "Point":
        array = pd.DataFrame({"X": gdf.geometry.x, "Y": gdf.geometry.y}).values
    else:
        raise TypeError(
            "The geometry provided is neither a Polygon or a Point.")

    threshold = min_threshold_distance(array)

    if gdf.crs.is_projected is True:
        unit = "meters"
    else:
        unit = "degrees"

    print("Minimum threshold:", round(threshold, 3), unit)

    return threshold


def compute_spatial_weights(
    gdf, type, radius=None, ids=None, kernel_args=None, distanceband_args=None
):
    '''
    gdf: geodataframe
    type: DistanceBand or Kernel
    radius: bandwith expressed in the same unit than gdf
    ids: use a specific column for the index used in the spatial weights (e.g. "reli")
    kernel_args= function (gaussian, uniform, triangular, quadratic, quartic), k, fixed, eps
    distanceband_args= binary, alpha
    '''

    # matches polygons that are WITHIN the circles
    if type == "DistanceBand":

        if distanceband_args is None:
            distanceband_args = dict()

        w = DistanceBand.from_dataframe(
            gdf, threshold=radius, ids=ids, **distanceband_args)

    elif type == "Kernel":

        if kernel_args is None:
            kernel_args = dict()

        w = Kernel.from_dataframe(
            gdf, bandwidth=radius, ids=ids, **kernel_args
        )

    elif type == "Queen":
        w = Queen.from_dataframe(gdf, ids=ids)

    elif type == "Rook":
        w = Rook.from_dataframe(gdf, ids=ids)

    else:
        raise TypeError(
            "Other types of spatial weight are not integrated yet."
        )

    return w


def map_nb_neighbors(gdf, w, basemap):

    # Plot number of neighbors per observation
    gdf = gdf.reset_index()
    card = pd.DataFrame.from_dict(
        w.cardinalities, orient="index", columns=["n_nb"]
    ).reset_index()
    gdf = pd.merge(gdf, card, on="index")

    scheme = map.classify_values(gdf.n_nb, 'quantiles', k=5)
    fig, ax = plt.subplots(figsize=(15, 10))

    map.add_basemap(ax, gdf.crs.to_string(), basemap)
    map.choropleth_map(ax, scheme, gdf, cmap='inferno_r',
                       legend=True, scalebar=True)

    plt.title("Number of neighbors per location")


def map_spatial_neighbors(gdf, w, column_id, idx, bandwith=False):

    segments = []

    centroids = gdf.copy()
    centroids.geometry = centroids.centroid

    dict_index = dict(zip(gdf[column_id].values, range(len(gdf))))

    # Find the centroid of the polygon we're looking at now
    origin = np.array(centroids.loc[dict_index[idx]].geometry.coords)[0]

    for jdx in w.neighbors[idx]:
        dest = np.array(centroids.loc[dict_index[jdx]].geometry.coords)[0]
        segments.append([origin, dest])

    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_subplot(111)

    # Plot the polygons from the geodataframe as a base layer
    points_linked = w.neighbors[idx]
    weights = pd.DataFrame(np.column_stack(
        [w.neighbors[idx], w.weights[idx]]), columns=['reli', 'weight'])
    neighbors = centroids[centroids[column_id].isin(points_linked)]
    neighbors = neighbors.merge(weights, how='inner', on='reli')

    spatial_extent = centroids.loc[centroids[column_id].isin(
        points_linked)].unary_union.envelope.buffer(50)

    gdf[gdf.intersects(spatial_extent)].plot(
        ax=ax, color='#bababa', edgecolor='w', alpha=0.7)
    gdf[gdf.reli == idx].plot(ax=ax, color='red', edgecolor='w', alpha=0.2)
    neighbors.plot(
        ax=ax, color='red', edgecolor='w')

    segs_plot = LineCollection(np.array(segments), color='red')
    ax.add_collection(segs_plot)

    for i, row in neighbors.iterrows():
        plt.annotate(str(round(row['weight'], 3)), xy=row.geometry.coords[0],
                     horizontalalignment='center', verticalalignment='bottom')

    ax.set_axis_off()

    # Add OSM basemap
    map.add_basemap(ax, 2056)

    # Add information about the adaptative bandwith used for this observation
    if bandwith is True:
        bandwidth_used = round(w.bandwidth[dict_index[idx]][0])
        plt.title('Spatial neighbors of ' + column_id + ': ' +
                  str(idx) + ' (bandwidth= ' + str(bandwidth_used) + 'm)')


def global_moran(var, weight, perms=9999):

    I = Moran(var, weight, transformation="r", permutations=perms)
    # print("Global Moran's I:", I.I, "\np-val:", I.p_sim)

    fig, axs = plt.subplots(2, 1, figsize=(
        5, 12), subplot_kw=dict(box_aspect=1))
    sns.kdeplot(I.sim, fill=True, ax=axs[0])
    ylim = axs[0].get_ylim()[1]
    axs[0].vlines(I.sim, 0, ylim / 15, "black")
    axs[0].vlines(I.I, 0, ylim, "red")
    axs[0].set_title('Reference Distribution')
    axs[0].set_xlabel('Moran I: ' + str(round(I.I, 2)) +
                      '\nPermutations: ' + str(perms) + '\nP-value: ' + str(I.p_sim))
    esdaplot.moran_scatterplot(I, ax=axs[1])
    plt.show()


def local_moran(gdf, var, weight, perms=9999, seed=None, alpha=0.05, fdr_adj=True):

    LMo = Moran_Local(gdf[var], weight, transformation='r', permutations=perms, geoda_quads=True,
                      n_jobs=-1, keep_simulations=True, seed=seed, island_weight=np.nan)

    LMo_df = pd.DataFrame(np.column_stack(
        (LMo.Is, LMo.q, LMo.p_sim)), columns=['Is', 'quads', 'p_sim'])

    # Identify islands and replace Moran statistics by np.nan (default is Is=0)
    islands = []
    for key in weight.islands:
        islands.append(weight.id2i[key])
    LMo_df.loc[islands, :] = np.nan

    if fdr_adj is True:
        p_threshold = fdr(LMo_df.p_sim, alpha=alpha)
    else:
        p_threshold = alpha

    print('p-value threshold: ', p_threshold)

    LMo_df = gdf.merge(LMo_df, how='left', left_index=True, right_index=True)

    LMo_df['lisa_cluster'] = LMo_df.quads
    LMo_df.loc[LMo_df.p_sim > p_threshold, 'lisa_cluster'] = 0

    labels = {1: 'HH', 2: 'LL', 3: 'LH', 4: 'HL',
              0: 'Not significant', np.nan: 'Neighborless'}
    LMo_df['lisa_labels'] = LMo_df['lisa_cluster'].map(labels)
    print(LMo_df.groupby(by='lisa_labels').size())

    return LMo_df, p_threshold


def map_lisa(ax, LMo, legend=True, **kwargs):

    x = np.array(LMo.lisa_labels)
    y = np.unique(x)

    colors6 = {'HH': '#e50000',
               'LL': '#0000e5',
               'LH': '#8080ff',
               'HL': '#ff8080',
               'Not significant': '#d8d8d8',
               'Neighborless': '#404040'}
    colors6 = [colors6[i] for i in y]
    hmap = colors.ListedColormap(colors6)

    if LMo.geometry.geom_type.isin(['Polygon', 'MultiPolygon']).any():
        LMo.plot(column='lisa_labels', categorical=True,
                 k=2, cmap=hmap, linewidth=0.1, ax=ax,
                 edgecolor='grey', legend=legend, **kwargs)
    else:
        LMo.plot(column='lisa_labels', categorical=True,
                 k=2, cmap=hmap, linewidth=1.5, ax=ax,
                 legend=legend, **kwargs)

    ax.set_axis_off()
    return ax
