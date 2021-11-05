# FUNCTION TO SAVE FILES

def save_gdf(path, file_name, gdf, driver):

    import os

    file_src = os.sep.join([path, file_name])

    try:
        if os.path.exists(file_src):
            os.remove(file_src)
        gdf.to_file(file_src, driver=driver)
        print('Sucess')
        print('File saved ', file_src)

    except Exception:
        print('Error while saving data on disk')


def find_nearest_reli(row, reli_centroids, radius=None):
    '''
    This function retrieves the nearest neighbor (Point) from a given Point.
    To speed-up the process, the user can restrict the set of destination
    points to a given neighborhood (radius around the point of origin).
    Outputs: nearest RELI index
    '''
    from shapely.ops import nearest_points

    if radius is not None:
        neighborhood = reli_centroids.loc[
            reli_centroids.intersects(row.geometry.buffer(radius))]
        nearest_geom = nearest_points(
            row.geometry, neighborhood.geometry.unary_union)[1]  # [0] origin
    else:
        nearest_geom = nearest_points(
            row.geometry, reli_centroids.geometry.unary_union)[1]  # [0] origin

    # retrieve corresponding reli
    nearest_reli = reli_centroids.loc[reli_centroids.geometry == nearest_geom]

    return nearest_reli
