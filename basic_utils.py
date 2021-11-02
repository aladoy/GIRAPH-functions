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
