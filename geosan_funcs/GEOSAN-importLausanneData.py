'''
Import geodata corresponding to the 
statistical sectors in Lausanne to GEOSAN DB.
'''

import pandas as pd
import geopandas as gpd
import datetime
from shapely.geometry import Point
import sys
import os

sys.path.append(r"/mnt/data/GEOSAN/FUNCTIONS/GIRAPH-functions/")
try:
    import db_utils as db
except FileNotFoundError:
    print("Wrong file or file path")


project_dir: str = r"/mnt/data/GEOSAN/FUNCTIONS/GIRAPH-functions/geosan_funcs/"
data_dir: str = r"/mnt/data/GEOSAN/GEOSAN DB/data/"

# OPEN FILE
sectors = gpd.read_file(os.sep.join(
    [data_dir, "SOUS-SECTEURS STATISIQUES LAUSANNE/Revenus_moyen_median2.shp"]))
sectors = sectors.to_crs(2056)
sectors = sectors[["PKUID", "NUMSECTEUR", "NOMSECTEUR", "geometry"]]

# ADD TO DB
db.import_data('geosan', 'aladoy', sectors, 'lausanne_sectors',
               pk='PKUID', idx_geom=True, ifexists='replace')
