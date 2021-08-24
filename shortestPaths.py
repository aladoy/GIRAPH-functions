#shortestPaths.py

#LIBRARIES
import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
import numpy as np

#SOURCE
#https://automating-gis-processes.github.io/site/notebooks/L6/network-analysis.html

#EXTRACT A ROAD NETWORK FOR A SPECIFIC PLACE AND TYPE (DRIVE, WALK OR BIKE) AND REPROJECT IN A PLANAR SYSTEM
def import_graph(place_name,type,epsg):
    #Extract OSM road networks
    graph = ox.graph_from_place(place_name, network_type=type)
    #Reproject the graph into specific srs
    crs='epsg:'+str(epsg)
    graph_proj = ox.project_graph(graph, to_crs=crs)
    return graph_proj


#RETURN THE SHORTEST PATH DISTANCE FROM AN ORIGIN POINT TO A TARGET POINT
def shortest_path(graph,originXY,targetXY):
    # Find the node in the graph that is closest to the origin point (here, we want to get the node id)
    orig_node = ox.get_nearest_node(graph, originXY, method='euclidean')
    # Find the node in the graph that is closest to the target point (here, we want to get the node id)
    target_node = ox.get_nearest_node(graph, targetXY, method='euclidean')
    # Calculate the shortest path length
    length = nx.shortest_path_length(G=graph, source=orig_node, target=target_node, weight='length')
    return length

#RETURN THE ID AND THE DISTANCE OF THE NEAREST TARGET FOR EACH ORIGIN POINT
def compute_nearest_target_distance(gdf_origins, gdf_targets, graph):
    #Iterrate across geodatframe with origins
    for i, row_orig in gdf_origins.iterrows():
        #Define origin x/y coordinats
        orig_xy = (row_orig.y, row_orig.x)
        #Create empty dataframe that will store the shortest path to each vaccination center
        res = pd.DataFrame()
        for j, row_targ in gdf_targets.iterrows():
            # Get target x and y coordinates
            targets_xy = (row_targ.y, row_targ.x)
            #Create dataframe to store results
            res.loc[j,'target_id']=row_targ.id
            try:
                res.loc[j,'target_dist']=shortest_path(graph,orig_xy,targets_xy)
            except:
                res.loc[j,'target_dist']=np.nan
        #Find the nearest target and associated distance for the specific origin
        if res.target_dist.isnull().all():
            gdf_origins.loc[i,'nearest_targ_id']='No reachable'
            gdf_origins.loc[i,'nearest_targ_dist']='No reachable'
        else:
            nearest_target=res.loc[res['target_dist'].idxmin(skipna=True)]
            #Add two variables with the id and distance of nearest center
            gdf_origins.loc[i,'nearest_targ_id']=nearest_target.target_id
            gdf_origins.loc[i,'nearest_targ_dist']=nearest_target.target_dist
        #Return geodataframe with origins + 2 columns with nearest target info
    return gdf_origins
