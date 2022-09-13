"""
This code builds GIS files for the state of Vaud's hectometric grid.
The input is a CSV file containing the geometric coordinates of the
bottom-left corners of each inhabited hectare (RELI) for the whole Switzerland.
The code then filters the hectares for the state of Vaud and create a GPKG
data file with statpop data at the: RELI point, RELI centroid, and RELI polygon.
"""

# LIBRARIES
import pandas as pd
import os
import sys
import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely import wkb
from shapely import speedups

try:
    import basic_utils as u
except FileNotFoundError:
    print("Wrong file or file path")

# DIRECTORIES
geosan_db_dir: str = (r"/mnt/data/GEOSAN/GEOSAN DB/data")
output_dir = os.sep.join([geosan_db_dir, "STATPOP/2021"])

# IMPORT DATA
statpop = pd.read_csv(
    os.sep.join([geosan_db_dir, "STATPOP/2021/STATPOP2021.csv"]), sep=";"
)

cantons = gpd.read_file(
    os.sep.join(
        [
            geosan_db_dir,
            "SWISS BOUNDARIES/June 2022/swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.shp",
        ]
    )
)
cantons = cantons.set_crs(2056, allow_override=True)
# Remove Z-dimension
cantons = u.convert_3D_to_2D(cantons)

# CONVERT STATPOP TO GEODATAFRAME
statpop = statpop.assign(
    geometry=statpop.apply(lambda row: Point(row.E_KOORD, row.N_KOORD), axis=1)
)
statpop_gdf = gpd.GeoDataFrame(
    statpop, geometry=statpop.geometry, crs={"init": "epsg:2056"}
)

# CREATE THE SWISS HECTOMETRIC GRID

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

ch_geom = cantons.geometry.unary_union
speedups.enable()
statpop_gdf = statpop_gdf[statpop_gdf.geometry.intersects(ch_geom)]

# Graphical result
# statpop_gdf_vd.plot(color="black", markersize=1)

# COMPUTE RELI POLYGONS
poly_geom = [
    Polygon(
        zip(
            [xy[0], xy[0], xy[0] + 100, xy[0] + 100],
            [xy[1], xy[1] + 100, xy[1] + 100, xy[1]],
        )
    )
    for xy in zip(statpop_gdf.E_KOORD, statpop_gdf.N_KOORD)
]
statpop_gdf_poly = statpop_gdf.copy()
statpop_gdf_poly.set_geometry(poly_geom, drop=True, inplace=True, crs=2056)

# Centroids
statpop_gdf_centroids = statpop_gdf_poly.copy()
statpop_gdf_centroids.geometry = statpop_gdf_poly.centroid

# SAVE RESULTS
# Point file (original RELI)
u.save_gdf(
    output_dir,
    "statpop.gpkg",
    statpop_gdf,
    driver="GPKG",
    layer="statpop_reli",
    del_exist=True,
)
# Point file (RELI centroids)
u.save_gdf(
    output_dir,
    "statpop.gpkg",
    statpop_gdf_centroids,
    driver="GPKG",
    layer="statpop_centroid",
    del_exist=False,
)
# Polygon file
u.save_gdf(
    output_dir,
    "statpop.gpkg",
    statpop_gdf_poly,
    driver="GPKG",
    layer="statpop_polygon",
    del_exist=False,
)
