# FUNCTION TO SAVE FILES


def save_gdf(path, file_name, gdf, driver="GPKG", layer=None, del_exist=True):

    import os

    file_src = os.sep.join([path, file_name])

    if (del_exist) & (os.path.exists(file_src)):
        os.remove(file_src)
    
    try:
        gdf.to_file(file_src, driver=driver, layer=layer) 
        print("Sucess")
        print("File saved ", file_src)
    except Exception:
        print("Error while saving data on disk")


def find_nearest_reli(row, reli_centroids, radius=None):
    """
    This function retrieves the nearest neighbor (Point) from a given Point.
    To speed-up the process, the user can restrict the set of destination
    points to a given neighborhood (radius around the point of origin).
    Outputs: nearest RELI index (NaN for isolated point)
    """
    from shapely.ops import nearest_points
    import numpy as np

    if radius is not None:
        neighborhood = reli_centroids.loc[
            reli_centroids.intersects(row.geometry.buffer(radius))
        ]

        # if no RELI can be found around the given radius (isolated point)
        if neighborhood.empty:
            nearest_reli = np.nan
        else:
            nearest_reli = reli_centroids.loc[
                reli_centroids.geometry
                == nearest_points(row.geometry, neighborhood.geometry.unary_union)[1],
                "reli",
            ].values[0]

    else:
        nearest_reli = reli_centroids.loc[
            reli_centroids.geometry
            == nearest_points(row.geometry, reli_centroids.geometry.unary_union)[1],
            "reli",
        ].values[0]

    return nearest_reli


def convert_3D_to_2D(gdf):
    import geopandas as gpd
    from shapely import wkb

    _drop_z = lambda geom: wkb.loads(wkb.dumps(geom, output_dimension=2))
    gdf.geometry = gdf.geometry.transform(_drop_z)

    return gdf

