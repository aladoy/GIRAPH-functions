# FUNCTION TO SAVE FILES

import os
import geopandas as gpd
from shapely import wkb
import numpy as np

def save_gdf(path, file_name, gdf, driver="GPKG", layer=None, del_exist=True):

    file_src = os.sep.join([path, file_name])

    if (del_exist) & (os.path.exists(file_src)):
        os.remove(file_src)
    
    try:
        gdf.to_file(file_src, driver=driver, layer=layer) 
        print("Sucess")
        print("File saved ", file_src)
    except Exception:
        print("Error while saving data on disk")


def find_nearest_reli(row, ha_poly, radius=None):
    """
    This function retrieves the nearest neighbor (Point) from a given Point.
    To speed-up the process, the user can restrict the set of destination
    points to a given neighborhood (radius around the point of origin).
    Outputs: nearest RELI index (NaN for isolated point)
    """
    try:
        nearest_reli = ha_poly[ha_poly.geometry.contains(
            row.geometry)]['reli'].values[0]

    except IndexError:

        try:

            if radius is not None:

                ha_poly = ha_poly.loc[
                    ha_poly.intersects(row.geometry.buffer(radius))
                ]

            ha_poly['distance'] = ha_poly.geometry.distance(row.geometry)
            ha_poly = ha_poly.sort_values(by='distance')
            nearest_reli = ha_poly.iloc[0]['reli']

        except IndexError:
            nearest_reli = np.nan  # no hectares within this distance

    return nearest_reli


def convert_3D_to_2D(gdf):

    _drop_z = lambda geom: wkb.loads(wkb.dumps(geom, output_dimension=2))
    gdf.geometry = gdf.geometry.transform(_drop_z)

    return gdf

