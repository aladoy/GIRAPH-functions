# shortestPaths.py

# LIBRARIES
import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
import numpy as np
import math
from shapely.geometry import Point, LineString, Polygon
import pandana
import os
import itertools

# SOURCE
# https://automating-gis-processes.github.io/site/notebooks/L6/network-analysis.html
# https://github.com/gboeing/osmnx-examples/blob/main/notebooks/02-routing-speed-time.ipynb

# EXTRACT A ROAD NETWORK FOR A SPECIFIC PLACE AND TYPE (DRIVE, WALK OR BIKE) AND REPROJECT IN A PLANAR SYSTEM
def import_graph(area, type, epsg, filepath=None):

    # Extract OSM road networks
    if isinstance(area, str):
        graph = ox.graph_from_place(
            area,
            network_type=type,
            simplify=False,
            retain_all=False,
            truncate_by_edge=True,
        )
    else:
        graph = ox.graph_from_polygon(
            area,
            network_type=type,
            simplify=False,
            retain_all=False,
            truncate_by_edge=True,
        )

    # Reproject the graph into specific srs
    graph_proj = ox.project_graph(graph, to_crs=epsg)

    # Save graph
    if filepath != None:
        output_file = os.sep.join(
            [filepath, "osmnx_graph" + type + "_" + str(epsg) + ".gpkg"]
        )
        ox.save_graph_geopackage(graph, output_file)

    return graph_proj


def add_travel_time(graph, graph_type="drive", driving_limits=None, walking_speed=3.6):
    """
    graph = OSM road network returned by import_graph()
    driving_limits = user defined speed limits provided in a dictionary {"residential": 35, "tertiary": 60, etc.}
    walking_speed = mean walking speed (in km/h)
    """

    match graph_type:

        case "drive":
            if driving_limits is None:
                graph = ox.add_edge_speeds(graph)
            else:
                graph = ox.add_edge_speeds(graph, driving_limits)
            # Calculate travel time for all edges
            graph = ox.add_edge_travel_times(graph)
            # Print stats of speed / travel time per edge type
            edges = ox.graph_to_gdfs(graph, nodes=False)
            edges["highway"] = edges["highway"].astype(str)
            edges.groupby("highway")[
                ["length", "speed_kph", "travel_time"]
            ].mean().round(1)

        case "walk":
            edges = ox.graph_to_gdfs(graph, nodes=False, fill_edge_geometry=False)
            edges["speed_kph"] = walking_speed
            nx.set_edge_attributes(graph, values=edges["speed_kph"], name="speed_kph")
            # Calculate travel time for all edges
            graph = ox.add_edge_travel_times(graph)

        case _:
            raise Exception("sorry, this graph type is not available.")

    return graph


# CREATE PANDANA NETWORK
def create_network(orig_gdf, dest_gdf, osmnx_graph, weight="travel_time"):
    """
    orig_gdf = geodataframe containing the origin points
    dest_gdf = geodataframe containing the destination points
    osmnx_graph = OSMNX graph (either walk or drive) created with import_graph()
    weight = "travel_time" or "length"
    filepath (optional) = filepath where to save the network
    """

    # Create network
    nodes, edges = ox.graph_to_gdfs(osmnx_graph, nodes=True, edges=True)
    edges = edges.reset_index(drop=False)
    try:
        network = pandana.Network(
            nodes["x"], nodes["y"], edges["u"], edges["v"], edges[[weight]]
        )
    except ValueError:
        print("Column " + weight + " was not in the geodataframe.")
        raise

    return network


# CREATE ORIGIN-DESTINATION DATAFRAME
def create_origdest_dataframe(orig_gdf, dest_gdf, orig_index, dest_index):

    orig_gdf["x_orig"], orig_gdf["y_orig"] = orig_gdf.geometry.x, orig_gdf.geometry.y
    dest_gdf["x_dest"], dest_gdf["y_dest"] = dest_gdf.geometry.x, dest_gdf.geometry.y

    # create pairwise origin-destination
    flows = pd.DataFrame(
        list(itertools.product(orig_gdf[orig_index], dest_gdf[dest_index]))
    ).rename(columns={0: "origin", 1: "destination"})

    flows = flows.merge(
        orig_gdf[[orig_index, "x_orig", "y_orig"]],
        how="left",
        left_on="origin",
        right_on=orig_index,
    )
    flows = flows.merge(
        dest_gdf[[dest_index, "x_dest", "y_dest"]],
        how="left",
        left_on="destination",
        right_on=dest_index,
    )

    return flows


# COMPUTE SHORTEST PATHS
def compute_shortest_paths(flows, network, weight="travel_time"):

    if weight == "travel_time":
        var_name = "travel_time_sec"
    else:
        var_name = "distance"

    # get nearest node ids
    flows["node_orig"] = network.get_node_ids(flows.x_orig, flows.y_orig).values
    flows["node_dest"] = network.get_node_ids(flows.x_dest, flows.y_dest).values
    # compute shortest path for each origin-destination pair
    flows[var_name] = pd.Series(
        network.shortest_path_lengths(
            flows.node_orig, flows.node_dest, imp_name="travel_time"
        )
    )
    if weight == "travel_time":
        flows["travel_time_mn"] = round(flows["travel_time_sec"] / 60, 2)

    # select min distance only
    flows = flows.loc[flows.groupby("origin").travel_time_sec.idxmin()]
    flows["shortest_dest_id"] = flows["destination"]
    flows.drop(["destination", "reli", "index"], axis=1, inplace=True)

    return flows