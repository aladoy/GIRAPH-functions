# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 10:09:07 2021

@author: gwena
"""

import rasterio
import rasterio.plot
import rasterio.mask
from rasterio.io import MemoryFile
from rasterio.warp import reproject
from rasterio.merge import merge
from rasterstats import zonal_stats

import fiona
import numpy as np
import pandas as pd


def open_raster(band_path):
    # https://geohackweek.github.io/raster/04-workingwithrasters/
    with rasterio.open(band_path) as src:
        profile = src.profile
        # oviews = src.overviews(1) # list of overviews from biggest to smallest
        # oview = oviews[res]  # Use second-highest resolution overview
        # print('Decimation factor= {}'.format(oview))
        band = src.read(1)
    return profile, band

def calc_ndvi(nir,red):
    # https://geohackweek.github.io/raster/04-workingwithrasters/
    '''Calculate NDVI from integer arrays'''
    nir = nir.astype('f4')
    red = red.astype('f4')
    ndvi = (nir - red) / (nir + red)
    return ndvi

def scale_lst(band):
    # https://www.usgs.gov/faqs/how-do-i-use-a-scale-factor-landsat-level-2-science-products?qt-news_science_products=0#qt-news_science_products
    # or in the product user guide
    scaled_lst=np.copy(band)
    with np.nditer(scaled_lst, op_flags=['readwrite']) as image:
        for pixel in image:
            if pixel!=0:
                pixel[...]=0.00341802 * pixel + 149.0 - 273.15
    return scaled_lst

def lst_treatment(band_path,path_data,file_name):
    profile_lst, lst=open_raster(band_path)
    lst=scale_lst(lst)
    with rasterio.open(path_data+"LST\\"+file_name, 'w', **profile_lst) as dst:
        dst.write_band(1, lst)
    return lst

def create_dataset(data, crs, transform):
    # Receives a 2D array, a transform and a crs to create a rasterio dataset
    memfile = MemoryFile()
    dataset = memfile.open(driver='GTiff', height=data.shape[0], width=data.shape[1], count=1, crs=crs, transform=transform, dtype=data.dtype)
    dataset.write(data, 1)
        
    return dataset

def reproj_merge(filepath1, filepath2, resultpath, no_data=None):
    # https://medium.com/analytics-vidhya/python-for-geosciences-raster-merging-clipping-and-reprojection-with-rasterio-9f05f012b88a
    
    ch_crs=rasterio.crs.CRS({"init": "epsg:2056"})

    src1=rasterio.open(filepath1)
    src1_reproj, src1_reproj_trans = reproject(source=rasterio.band(src1, 1),
                                                   dst_crs=ch_crs)
    src1_reproj=create_dataset(src1_reproj[0], ch_crs, src1_reproj_trans)
    
    src2=rasterio.open(filepath2)
    src2_reproj, src2_reproj_trans = reproject(source=rasterio.band(src2, 1),
                                                   dst_crs=ch_crs)
    src2_reproj=create_dataset(src2_reproj[0], ch_crs, src2_reproj_trans)
    
    lst, transf=merge([src1_reproj, src2_reproj],nodata=no_data)
    out_meta = src1_reproj.meta.copy()
    if no_data is None:
        out_meta.update({"driver": "GTiff","height": lst.shape[1],"width": lst.shape[2],"transform": transf,
                          "crs": ch_crs})
    else:
        out_meta.update({"driver": "GTiff","height": lst.shape[1],"width": lst.shape[2],"transform": transf,
                          "crs": ch_crs, "nodata": no_data})
    
    with rasterio.open(resultpath, "w", **out_meta) as dest:
        dest.write(lst)
    
    src1.close()
    src2.close()
    return lst

def clip_raster(rasterpath,vectorpath):
    # https://rasterio.readthedocs.io/en/latest/topics/masking-by-shapefile.html
    with fiona.open(vectorpath, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    with rasterio.open(rasterpath) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)
        out_meta = src.meta
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    return out_image, out_meta

def zonal_statistics(rasterpath,hectares,no_data=None):
    with rasterio.open(rasterpath) as src:
        affine=src.transform
        donnees=src.read(1)
        hectares_donnees=pd.DataFrame(zonal_stats(hectares, donnees, affine=affine, nodata=no_data))
        
    valeurs=pd.concat([hectares[["RELI"]],hectares_donnees],axis=1)
    return valeurs
