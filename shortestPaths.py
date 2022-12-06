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
            [filepath, "osmnx_graph" + "type_" + str(epsg) + ".gpkg"]
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
        var_name = "travel_time"
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
    # select min distance only
    flows = flows.loc[flows.groupby("origin").travel_time.idxmin()]
    flows["shortest_dest_id"] = flows["destination"]
    flows.drop(["destination", "reli", "index"], axis=1, inplace=True)

    return flows


# # IMPUTE SPEED LIMITS TO GRAPH EDGES (KM/H) AND COMPUTE TRAVEL TIME. ADD AN ATTRIBUTE "SPEED_KPH". BY DEFAULT, IMPUTATION OF FREE-FLOWS TRAVEL SPEED USING MEAN OF MAXSPEED FOR ALL EDGES, PER HIGHWAY TYPE.
# def add_travel_time_drive(graph, user_limits=None):
#     """
#     graph = OSM road network returned by import_graph()
#     user_limits = user defined speed limits provided in a dictionary {"residential": 35, "tertiary": 60, etc.}
#     """
#     if user_limits is None:
#         graph = ox.add_edge_speeds(graph)
#     else:
#         graph = ox.add_edge_speeds(graph, user_limits)
#     # Calculate travel time for all edges
#     graph = ox.add_edge_travel_times(graph)
#     # Print stats of speed / travel time per edge type
#     edges = ox.graph_to_gdfs(graph, nodes=False)
#     edges["highway"] = edges["highway"].astype(str)
#     edges.groupby("highway")[["length", "speed_kph", "travel_time"]].mean().round(1)
#     return graph


# # ADD WALKING SPEED TO GRAPH EDGES (KM/H) AND COMPUTE TRAVEL TIME
# def add_travel_time_walk(graph, speed_kph=4):
#     """
#     graph = OSM road network returned by import_graph()
#     speed_kph = mean walking distance (in km/h)
#     """
#     edges = ox.graph_to_gdfs(graph, nodes=False, fill_edge_geometry=False)
#     edges["speed_kph"] = speed_kph
#     nx.set_edge_attributes(graph, values=edges["speed_kph"], name="speed_kph")
#     return graph


# # FIND THE INTERSECTION BETWEEN A (FOREIGN) POLYGON AND A GRAPH NETWORK
# def find_intersect_poly_graph(row, graph, graph_edges):

#     edges_geom = graph_edges.reset_index().dissolve().geometry[0]
#     try:
#         intersect = row.geometry.intersection(edges_geom)

#         if intersect.geom_type == "MultiLineString":
#             intersect = intersect.geoms[0].coords[
#                 0
#             ]  # start point of (first) linestring
#         else:
#             intersect = intersect.coords[0]
#     except:
#         try:
#             point_row = row.copy()
#             point_row.geometry = point_row.geometry.centroid
#             intersect = find_intersect_point_graph(point_row, graph, graph_edges)
#         except:
#             intersect = np.nan

#     return intersect


# # FIND THE INTERSECTION BETWEEN A (FOREIGN) POINT AND A GRAPH NETWORK
# def find_intersect_point_graph(row, graph, graph_edges):

#     edges_geom = graph_edges.reset_index().dissolve().geometry[0]

#     nrst_edge = ox.distance.nearest_edges(
#         graph, row.geometry.x, row.geometry.y, return_dist=True
#     )

#     # create a buffer around point which includes nearest edge
#     buffer = row.geometry.buffer(math.ceil(nrst_edge[1] + 1))

#     try:
#         intersect = buffer.intersection(edges_geom)

#         if intersect.geom_type == "LineString":
#             intersect = intersect.coords[0]
#         else:  # multipoint
#             intersect = intersect.geoms[0].coords[0]
#     except:
#         intersect = np.nan

#     return intersect


# # UPDATE NETWORK WITH NEW NODES
# def add_nodes_to_graph(graph_nodes, graph_edges, list_x, list_y):
#     """
#     graph_nodes = geodataframe with graph's nodes
#     graph_nodes = geodataframe with graph's edges
#     list_x = list of x coordinates to add
#     list_x = list of y coordinates to add
#     """

#     new_nodes_coords = [[list_x[i], list_y[i]] for i in range(len(list_x))]

#     dictionary = dict()

#     min_id = max(graph_nodes.reset_index(drop=False).osmid) + 1

#     for i in range(len(list_x)):
#         node_id = min_id + i
#         dictionary[node_id] = {"x": list_x[i], "y": list_y[i]}

#     tmp_list = []
#     for item_key, item_value in dictionary.items():
#         tmp_list.append(
#             {
#                 "geometry": Point(item_value["x"], item_value["y"]),
#                 "osmid": item_key,
#                 "y": item_value["y"],
#                 "x": item_value["x"],
#             }
#         )
#     my_nodes = gpd.GeoDataFrame(tmp_list)

#     new_graph_nodes = graph_nodes.reset_index().append(my_nodes, ignore_index=True)

#     new_graph_nodes.set_index(["osmid"], inplace=True)

#     new_graph = ox.graph_from_gdfs(new_graph_nodes, graph_edges)

#     # Should be nice to remove duplicated geometries

#     return new_graph


# RETURN THE SHORTEST PATH DISTANCE / TRAVEL TIME FROM AN ORIGIN POINT TO A TARGET POINT
def shortest_path(graph, originXY, targetXY, weight_type="length"):
    # Find the node in the graph that is closest to the origin point (here, we want to get the node id)
    orig_node = ox.distance.nearest_nodes(graph, originXY[0], originXY[1])
    # print(orig_node)
    # Find the node in the graph that is closest to the target point (here, we want to get the node id)
    target_node = ox.distance.nearest_nodes(graph, targetXY[0], targetXY[1])
    # print(target_node)
    # Calculate the shortest path length
    distance = nx.shortest_path_length(
        G=graph, source=orig_node, target=target_node, weight=weight_type
    )
    print(distance)
    return distance


# # RETURN NEAREST TARGET FOR A GIVEN ORIGIN
# def find_nearest_target_distance(row, gdf_targets, graph, weight_type="length"):

#     if not hasattr("gdf_targets", "id"):
#         gdf_targets["id"] = gdf_targets.reset_index().index

#     res = pd.DataFrame()
#     orig_xy = (row.geometry.x, row.geometry.y)
#     # print(orig_xy)

#     for j, row_targ in gdf_targets.iterrows():
#         targets_xy = (row_targ.geometry.x, row_targ.geometry.y)

#         # print(targets_xy)

#         res.loc[j, "target_id"] = row_targ.id
#         try:
#             res.loc[j, "target_dist"] = shortest_path(
#                 graph, orig_xy, targets_xy, weight_type=weight_type
#             )
#         except:
#             res.loc[j, "target_dist"] = np.nan

#     # print(res["target_dist"])

#     if res.target_dist.isnull().all():
#         nearest_target_id = "Not reachable"
#         nearest_target_dist = "Not reachable"
#     else:
#         nearest_target = res.loc[res["target_dist"].idxmin(skipna=True)]
#         nearest_target_id = nearest_target.target_id
#         nearest_target_dist = nearest_target.target_dist

#     return nearest_target_id, nearest_target_dist


# # RETURN THE ID AND THE DISTANCE OF THE NEAREST TARGET FOR EACH ORIGIN POINT
# def compute_nearest_target_distance(
#     gdf_origins, gdf_targets, graph, weight="travel_time"
# ):
#     """
#     gdf_origins = geodataframe with all the origins
#     gdf_targets = geodataframe with all the targets
#     graph = OSM road network returned by import_graph()
#     weight = distance or time
#     """

#     if not hasattr("gdf_targets", "id"):
#         gdf_targets["id"] = gdf_targets.reset_index().index

#     # Iterrate across geodatframe with origins
#     for i, row_orig in gdf_origins.iterrows():
#         # Define origin x/y coordinats
#         orig_xy = (row_orig.geometry.y, row_orig.geometry.x)
#         # Create empty dataframe that will store the shortest path to each vaccination center
#         res = pd.DataFrame()
#         for j, row_targ in gdf_targets.iterrows():
#             # Get target x and y coordinates
#             targets_xy = (row_targ.geometry.y, row_targ.geometry.x)
#             # Create dataframe to store results
#             res.loc[j, "target_id"] = row_targ.id
#             try:
#                 res.loc[j, "target_dist"] = shortest_path(
#                     graph, orig_xy, targets_xy, weight
#                 )
#             except:
#                 res.loc[j, "target_dist"] = np.nan
#         # Find the nearest target and associated distance for the specific origin
#         if res.target_dist.isnull().all():
#             gdf_origins.loc[i, "nearest_targ_id"] = "No reachable"
#             gdf_origins.loc[i, "nearest_targ_dist"] = "No reachable"
#         else:
#             nearest_target = res.loc[res["target_dist"].idxmin(skipna=True)]
#             # Add two variables with the id and distance of nearest center
#             gdf_origins.loc[i, "nearest_targ_id"] = nearest_target.target_id
#             gdf_origins.loc[i, "nearest_targ_dist"] = nearest_target.target_dist
#         # Return geodataframe with origins + 2 columns with nearest target info
#     return gdf_origins
