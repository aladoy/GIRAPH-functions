
'''
This code builds GIS files for the state of Vaud's hectometric grid.
The input a CSV file containing the geometric coordinates of the
bottom-left corners of each inhabited hectare (RELI) for the whole Switzerland.
The code then filters the hectares for the state of Vaud and create a Point
data file representing the centroid of each hectare, and a Polygon data file
representing the spatial extent of each hectare.
'''

# LIBRARIES
import pandas as pd
import os
import sys
import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

# GIRAPH-functions REPOSITORY
sys.path.append(os.path.dirname(sys.path[0]))
try:
    import basic_utils as u
except FileNotFoundError:
    print("Wrong file or file path")

# DIRECTORIES
data_dir: str = (r"/mnt/data/GEOSAN/GEOSAN DB/data")
output_dir = os.sep.join([data_dir, 'STATPOP 2020/processed_data'])

# IMPORT DATA
statpop = pd.read_csv(
    os.sep.join([data_dir, 'STATPOP 2020/STATPOP2020.csv']), sep=';')

cantons = gpd.read_file(
    os.sep.join([data_dir, 'SWISS BOUNDARIES 2021/swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.shp']))
cantons = cantons.set_crs(2056, allow_override=True)

# CONVERT STATPOP TO GEODATAFRAME
statpop = statpop.assign(geometry=statpop.apply(
    lambda row: Point(row.E_KOORD, row.N_KOORD), axis=1))
statpop_gdf = gpd.GeoDataFrame(statpop, geometry=statpop.geometry,
                               crs={'init': 'epsg:2056'})

# FILTER FOR THE CANTON OF VAUD

# Select point candidates (intersecting the bounding boxes of VD geometry)
# vd_bounds = list(cantons[cantons.NAME == 'Vaud'].bounds.values[0])
# sindex = statpop_gdf.sindex  # create R-tree indexes
# candidates_idx = list(sindex.intersection(vd_bounds))  # point candidates idx
# candidates = statpop_gdf.loc[candidates_idx]
# Graphical result
# ax = cantons[cantons.NAME == 'Vaud'].plot(color='red', alpha=0.5)
# ax = point_candidates.plot(ax=ax, color='black', markersize=2)
# Use candidates to find points matching the VD geometry (not its bounding box)
# vd_geom = cantons[cantons.NAME == 'Vaud'].geometry.unary_union
# statpop_gdf_vd = candidates.loc[candidates.intersects(vd_geom)]

vd_geom = cantons[cantons.NAME == 'Vaud'].geometry.unary_union
%time statpop_gdf_vd = statpop_gdf[statpop_gdf.geometry.intersects(vd_geom)]

# Graphical result
statpop_gdf_vd.plot(color='black', markersize=1)


# COMPUTE RELI POLYGONS
poly_geom = [Polygon(zip([xy[0], xy[0], xy[0]+100, xy[0]+100],
                         [xy[1], xy[1]+100, xy[1]+100, xy[1]]))
             for xy in zip(statpop_gdf_vd.E_KOORD, statpop_gdf_vd.N_KOORD)]
statpop_gdf_vd_poly = statpop_gdf_vd.copy()
statpop_gdf_vd_poly.set_geometry(poly_geom, drop=True, inplace=True, crs=2056)

# SAVE RESULTS
# Point file
u.save_gdf(output_dir, 'statpopVD_point.gpkg', statpop_gdf_vd, 'GPKG')
# Polygon file
u.save_gdf(output_dir, 'statpopVD_poly.gpkg', statpop_gdf_vd_poly, 'GPKG')
