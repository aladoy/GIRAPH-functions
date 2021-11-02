#LIBRARIES
#Basic
import pandas as pd
import os
import subprocess
import sys
#Database
import getpass
from sqlalchemy import create_engine
import psycopg2 as ps
#Spatial
import geopandas as gpd
from geoalchemy2 import Geometry, WKTElement
from shapely import wkt
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
import shapely.speedups
#User defined function
sys.path.append(r'./FUNCTIONS/')
import geocoding_utils as g

#CONNECT TO DB
pw=getpass.getpass() #Ask for user password
engine=create_engine("postgresql+psycopg2://aladoy:{}@localhost/geosan".format(pw)) #Create SQLAlchemy engine
conn=ps.connect("dbname='geosan' user='aladoy' host='localhost' password='{}'".format(pw)) #Create a connection object
cursor=conn.cursor() #Create a cursor object

#FUNCTION TO IMPORT DATA (SPATIAL OR NO) INTO GEOSAN DB
def import_data(dat, name, pk, idx_geom=False):
    print(dat.shape)
    dat.columns=map(str.lower,dat.columns) #convert columns to lower case

    if isinstance(dat, gpd.GeoDataFrame):
        print('Geometry Type :' + dat.geometry.geom_type.unique()[0])
        print('CRS :' + str(dat.crs))
        dat.to_postgis(name, engine,if_exists='replace') #Add to postgis
    else:
        dat.to_sql(name, engine,if_exists='replace') #Add to postgres

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM {}".format(name))
    print("Number of rows in the table :", cursor.fetchone())
    cursor.execute("SELECT COUNT(*) FROM information_schema.columns where table_name='{}'".format(name))
    print("Number of columns in the table :", cursor.fetchall())
    if pk!='NULL':
        cursor.execute("ALTER TABLE {} ADD PRIMARY KEY({});".format(name,pk)) #Add PK
        conn.commit()
    if idx_geom==True:
        cursor.execute("CREATE INDEX idx_geom_{} ON {} USING GIST(geometry);".format(name, name)) #Add geometry index
        conn.commit()
    print('TABLE ', name, ' WAS SUCESSFULLY IMPORTED')

#IMPORT DATA
#VD state
canton=gpd.read_file(r"./GEOSAN DB/data/SWISS BOUNDARIES 2021/swissBOUNDARIES2D_1_3_TLM_KANTONSGEBIET.shp")
canton.crs
#Rename columns with appropriate names (lowercase)
canton.columns=['uuid','date_modif','date_creat','data_yr_creat','data_mth_creat','data_yr_verif','data_mth_verif','modif','source','data_yr_upd','data_mth_upd','admin_level','quality','country_code','num','lake_area','area','part','name','nb_hab','geometry']
#Keep only canton of Vaud
canton=canton[canton.name=='Vaud']
import_data(canton,'canton','uuid',False)


#VD districts
districts=gpd.read_file(r"./GEOSAN DB/data/SWISS BOUNDARIES 2021/swissBOUNDARIES2D_1_3_TLM_BEZIRKSGEBIET.shp")
districts.crs
#Rename columns with appropriate names (lowercase)
districts.columns=['uuid','date_modif','date_creat','data_yr_creat','data_mth_creat','data_yr_verif','data_mth_verif','modif','source','data_yr_upd','data_mth_upd','admin_level','district_num','lake_area','quality','area','part','name','canton_num','country_code','nb_hab','geometry']
#Keep only VD features
districts=districts[districts.canton_num==22]
import_data(districts,'districts','uuid',True)


#VD municipalities
municipalities=gpd.read_file(r"./GEOSAN DB/data/SWISS BOUNDARIES 2021/swissBOUNDARIES2D_1_3_TLM_HOHEITSGEBIET.shp")
municipalities.crs
#Rename columns with appropriate names (lowercase)
municipalities.columns=['uuid','date_modif','date_creat','data_yr_creat','data_mth_creat','data_yr_verif','data_mth_verif','modif','source','data_yr_upd','data_mth_upd','admin_level','district_num','lake_area','quality','name','canton_num','country_code','nb_hab','num','part','area','area_code','geometry']
#Keep only VD features
municipalities=municipalities[municipalities.canton_num==22]
import_data(municipalities,'municipalities','uuid',True)

#VD npa
npa=gpd.read_file(r"./GEOSAN DB/data/MICROGIS NPA 2019/SF_COMPACT_LC_2019.shp")
npa.crs
npa=npa.to_crs({'init': 'epsg:2056'}) #Convert CRS from epsg:21781 to epsg:2056
#Keep only VD features
npa=npa[npa.KT=='VD']
import_data(npa,'npa','lcid',True)

#VD microregions
microregions=gpd.read_file(r"./GEOSAN DB/data/MICROREGIONS 2017/JOOSTSPECIAL_NB_2017.shp")
microregions.crs
import_data(microregions,'microregions','nbid',True)

#INHABITED HECTARES (STATPOP)
#Read Statpop data file (CSV)
statpop=pd.read_csv(r"./GEOSAN DB/data/STATPOP 2019/STATPOP2019.csv",sep=',')
statpop.shape
#Move to RELI centroids
statpop[['X_KOORD','Y_KOORD','E_KOORD','N_KOORD']]=statpop[['X_KOORD','Y_KOORD','E_KOORD','N_KOORD']].applymap(lambda x: x + 50)
#Create a geometry column using Shapely
statpop=statpop.assign(geometry=statpop.apply(lambda row: Point(row.E_KOORD, row.N_KOORD),axis=1))
#Convert to geodataframe
statpop=gpd.GeoDataFrame(statpop, geometry=statpop.geometry, crs={'init': 'epsg:2056'})
#Add lat lon
statpop['lon']=statpop.to_crs({'init': 'epsg:4326'}).geometry.x
statpop['lat']=statpop.to_crs({'init': 'epsg:4326'}).geometry.y
shapely.speedups.enable() #Speed query
statpop=gpd.overlay(statpop,canton) #Keep only VD hectares
statpop.shape
import_data(statpop,'inhabited_ha_centroid','reli',True)

#Create same file with polygons geometry
cursor.execute("CREATE TABLE inhabited_ha AS SELECT reli,ST_Expand(geometry,50) AS geometry FROM inhabited_ha_centroid")
conn.commit()

#STATPOP INDIVIDUALS (STATPOP NON PROTEGE)
statpop_indiv=pd.read_csv(r"./GEOSAN DB/data/STATPOP NON PROTEGE 2017/STATPOP_2016_VD.csv",sep=';')
#Create unique index
statpop_indiv.reset_index(drop=False,inplace=True)
#Create a geometry column using Shapely
statpop_indiv=statpop_indiv.assign(geometry=statpop_indiv.apply(lambda row: Point(row.GEOCOORDE, row.GEOCOORDN),axis=1))
#Convert to geodataframe
statpop_indiv=gpd.GeoDataFrame(statpop_indiv, geometry=statpop_indiv.geometry, crs={'init': 'epsg:2056'})
import_data(statpop_indiv,'statpop_indiv','index',True)

#PUBLIC TRANSPORTS
pt=pd.read_csv(r"./GEOSAN DB/data/PUBLIC TRANSPORT OFT 2021/PointExploitation.csv",sep=',',encoding='iso-8859-1')
pt[pt.duplicated(subset=['Numero'])] #Check if Numero is unique -> True
#Create a geometry column using Shapely
pt=pt.assign(geometry=pt.apply(lambda row: Point(row.E, row.N),axis=1))
pt=gpd.GeoDataFrame(pt, geometry=pt.geometry, crs={'init': 'epsg:2056'}) #Convert to geodataframe
import_data(pt,'public_transport_stops','Numero',True)

#MICROGIS DATA AT THE HECTARE LEVEL
mgis_ha_demo=pd.read_csv(r"./GEOSAN DB/data/MICROGIS HA 2021/DEMO/HA_DEMO.csv",skipfooter=1,engine='python').drop('mfd_id',axis=1) #Demographic data
mgis_ha_demo.shape
mgis_ha_income=pd.read_csv(r"./GEOSAN DB/data/MICROGIS HA 2021/INCOME_IQMD/HA_INCOME_IQMD.csv",skipfooter=1,engine='python').drop('mfd_id',axis=1) #Income data
mgis_ha_income.shape
mgis_ha_soceco=pd.read_csv(r"./GEOSAN DB/data/MICROGIS HA 2021/SOCECO/HA_SOCECO.csv",skipfooter=1,engine='python').drop('mfd_id',axis=1) #Socioeconomic data
mgis_ha_soceco.shape
#Join the three dataframes
mgis_ha=pd.merge(mgis_ha_demo,mgis_ha_income,how='inner',on=['reli'], suffixes=('', '_drop'))
mgis_ha.drop([col for col in mgis_ha.columns if 'drop' in col], axis=1, inplace=True) #Remove duplicated columns
mgis_ha=pd.merge(mgis_ha,mgis_ha_soceco,how='inner',on=['reli'], suffixes=('', '_drop'))
mgis_ha.drop([col for col in mgis_ha.columns if 'drop' in col], axis=1, inplace=True) #Remove duplicated columns
mgis_ha.shape
import_data(mgis_ha,'mgis_ha_2021','reli',False)


#REGBL (2021)
vd_addr=pd.read_csv(r'GEOSAN DB/data/REGBL 2021/VD.csv', delimiter=';')
vd_addr.shape
#Remove accents in object type
vd_addr['GDENAME']=vd_addr.GDENAME.map(g.strip_accents)
vd_addr['STRNAME']=vd_addr.STRNAME.map(g.strip_accents)
vd_addr['DPLZNAME']=vd_addr.DPLZNAME.map(g.strip_accents)
#Convert object type to upper case
vd_addr['GDENAME']=vd_addr.GDENAME.map(str.upper)
vd_addr['STRNAME']=vd_addr.STRNAME.map(str.upper)
vd_addr['DPLZNAME']=vd_addr.DPLZNAME.map(str.upper)
#Create a geometry column using Shapely
vd_addr=vd_addr.assign(geometry=vd_addr.apply(lambda row: Point(row.GKODE, row.GKODN),axis=1))
vd_addr=gpd.GeoDataFrame(vd_addr, geometry=vd_addr.geometry, crs="EPSG:2056") #Convert to geodataframe
import_data(vd_addr,'regbl_2021','egid,edid',True)

#Close the connection
conn.close()
