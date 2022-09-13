# LIBRARIES
# Basic
import pandas as pd
import os
import sys

# Spatial
import geopandas as gpd


# CONNECT TO GEOSAN DB
sys.path.append(r"/mnt/data/GEOSAN/FUNCTIONS/GIRAPH-functions/")
try:
    import db_utils as db
    import basic_utils as u
except FileNotFoundError:
    print("Wrong file or file path")
engine, conn, cursor = db.connect_db("geosan", "aladoy")

# DIRECTORIES
geosan_db_dir: str = (r"/mnt/data/GEOSAN/GEOSAN DB/data")

# IMPORT DATA
# Cantons
cantons = gpd.read_file(
    os.sep.join(
        [
            geosan_db_dir,
            "SWISS BOUNDARIES/June 2022/swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET.shp",
        ]
    )
)
cantons = cantons.to_crs(2056)
# Rename columns with appropriate names (lowercase)
cantons.columns = [
    "uuid",
    "date_modif",
    "date_creat",
    "data_yr_creat",
    "data_mth_creat",
    "data_yr_verif",
    "data_mth_verif",
    "modif",
    "source",
    "data_yr_upd",
    "data_mth_upd",
    "admin_level",
    "quality",
    "country_code",
    "num",
    "lake_area",
    "area",
    "part",
    "name",
    "nb_hab",
    "geometry",
]
# Remove Z-dimension
cantons = u.convert_3D_to_2D(cantons)
# Import to GEOSAN DB
db.import_data("geosan", "aladoy", cantons, "cantons", "uuid", idx_geom=True)


# Districts
districts = gpd.read_file(
    os.sep.join(
        [
            geosan_db_dir,
            "SWISS BOUNDARIES/June 2022/swissBOUNDARIES3D_1_3_TLM_BEZIRKSGEBIET.shp",
        ]
    )
)
districts = districts.to_crs(2056)
districts.columns = [
    "uuid",
    "date_modif",
    "date_creat",
    "data_yr_creat",
    "data_mth_creat",
    "data_yr_verif",
    "data_mth_verif",
    "modif",
    "source",
    "data_yr_upd",
    "data_mth_upd",
    "admin_level",
    "district_num",
    "lake_area",
    "quality",
    "area",
    "part",
    "name",
    "canton_num",
    "country_code",
    "nb_hab",
    "geometry",
]
districts = u.convert_3D_to_2D(districts)
db.import_data("geosan", "aladoy", districts, "districts", "uuid", idx_geom=True)

# Municipalities
municipalities = gpd.read_file(
    os.sep.join(
        [
            geosan_db_dir,
            "SWISS BOUNDARIES/June 2022/swissBOUNDARIES3D_1_3_TLM_HOHEITSGEBIET.shp",
        ]
    )
)
municipalities = municipalities.to_crs(2056)
municipalities.columns = [
    "uuid",
    "date_modif",
    "date_creat",
    "data_yr_creat",
    "data_mth_creat",
    "data_yr_verif",
    "data_mth_verif",
    "modif",
    "source",
    "data_yr_upd",
    "data_mth_upd",
    "admin_level",
    "district_num",
    "lake_area",
    "quality",
    "name",
    "canton_num",
    "country_code",
    "nb_hab",
    "num",
    "part",
    "area",
    "area_code",
    "geometry",
]
municipalities = u.convert_3D_to_2D(municipalities)
db.import_data(
    "geosan", "aladoy", municipalities, "municipalities", "uuid", idx_geom=True
)

# HECTOMETRIC GRID
reli = gpd.read_file(
    os.sep.join([geosan_db_dir, "STATPOP/2021/statpopVD.gpkg"]),
    driver="GPKG",
    layer="statpopVD_reli",
)
reli = reli[["RELI", "E_KOORD", "N_KOORD", "B21BTOT", "geometry"]]
db.import_data("geosan", "aladoy", reli, "vd_reli_point", "reli", idx_geom=True)
centroid = gpd.read_file(
    os.sep.join([geosan_db_dir, "STATPOP/2021/statpopVD.gpkg"]),
    driver="GPKG",
    layer="statpopVD_centroid",
)
centroid = centroid[["RELI", "E_KOORD", "N_KOORD", "B21BTOT", "geometry"]]
db.import_data("geosan", "aladoy", centroid, "vd_reli_centroid", "reli", idx_geom=True)

ha_polygon = gpd.read_file(
    os.sep.join([geosan_db_dir, "STATPOP/2021/statpopVD.gpkg"]),
    driver="GPKG",
    layer="statpopVD_polygon",
)
ha_polygon = ha_polygon[["RELI", "E_KOORD", "N_KOORD", "B21BTOT", "geometry"]]
db.import_data("geosan", "aladoy", ha_polygon, "vd_reli_polygon", "reli", idx_geom=True)


# MICROREGIONS

# HA LEVEL
mha_demo = pd.read_csv(
    os.sep.join([geosan_db_dir, "MICROGIS/2021/DEMO/HA_DEMO.csv"]),
    engine="python",
    skipfooter=1,
)
mha_rdemo = pd.read_csv(
    os.sep.join([geosan_db_dir, "MICROGIS/2021/DEMO/HA_DEMO.csv"]),
    engine="python",
    skipfooter=1,
)
mha_income = pd.read_csv(
    os.sep.join([geosan_db_dir, "MICROGIS/2021/INCOME_IQMD/HA_INCOME_IQMD.csv"]),
    engine="python",
    skipfooter=1,
)
mha_soceco = pd.read_csv(
    os.sep.join([geosan_db_dir, "MICROGIS/2021/SOCECO/HA_SOCECO.csv"]),
    engine="python",
    skipfooter=1,
)
mha = mha_demo.drop(["mfd_id", "gde_21", "bz_21", "kt_21"], axis=1).merge(
    mha_income.drop(["mfd_id", "gde_21", "bz_21", "kt_21", "ch_21"], axis=1),
    on=["reli"],
    how="inner",
)
mha = mha.merge(mha_soceco.drop(["mfd_id"], axis=1), on=["reli"], how="inner")
db.import_data("geosan", "aladoy", mha, "microgis_ha", "reli")


# MUNICIPALITY LEVEL
mmun_demo = pd.read_csv(
    os.sep.join([geosan_db_dir, "MICROGIS/2021/DEMO/SF_DEMO_GD_2021.csv"]),
    encoding="iso-8859-1",
)
mmun_demo.columns = mmun_demo.columns.str.replace(" ", "")
mmun_rdemo = pd.read_csv(
    os.sep.join([geosan_db_dir, "MICROGIS/2021/DEMO/SF_DEMORATIO_GD_2021.csv"]),
    encoding="iso-8859-1",
)
mmun_rdemo.columns = mmun_rdemo.columns.str.replace(" ", "")
mmun_income = pd.read_csv(
    os.sep.join(
        [geosan_db_dir, "MICROGIS/2021/INCOME_IQMD/SF_INCOME_TP_IQMD_GD_2021.csv"]
    ),
    encoding="utf-8",
)
mmun_income.columns = mmun_income.columns.str.replace(" ", "")
mmun_soceco = pd.read_csv(
    os.sep.join([geosan_db_dir, "MICROGIS/2021/SOCECO/SF_SOCECO_GD_2021.csv"]),
    encoding="iso-8859-1",
)
mmun_soceco.columns = mmun_soceco.columns.str.replace(" ", "")
mmun_rsoceco = pd.read_csv(
    os.sep.join([geosan_db_dir, "MICROGIS/2021/SOCECO/SF_SOCECORATIO_GD_2021.csv"]),
    encoding="iso-8859-1",
)
mmun_rsoceco.columns = mmun_rsoceco.columns.str.replace(" ", "")
mmun = mmun_demo.merge(
    mmun_rdemo.drop(
        ["GDENAME", "BZNR", "BZNAME", "KTACRO", "KTNAME", "CENTER_X", "CENTER_Y"],
        axis=1,
    ),
    on="GDENR",
    how="inner",
)
mmun = mmun.merge(
    mmun_income.drop(
        ["GDENAME", "BZNR", "BZNAME", "KTACRO", "KTNAME", "CENTER_X", "CENTER_Y"],
        axis=1,
    ),
    on="GDENR",
    how="inner",
)
mmun = mmun.merge(
    mmun_soceco.drop(
        ["GDENAME", "BZNR", "BZNAME", "KTACRO", "KTNAME", "CENTER_X", "CENTER_Y"],
        axis=1,
    ),
    on="GDENR",
    how="inner",
)
mmun = mmun.merge(
    mmun_rsoceco.drop(
        ["GDENAME", "BZNR", "BZNAME", "KTACRO", "KTNAME", "CENTER_X", "CENTER_Y"],
        axis=1,
    ),
    on="GDENR",
    how="inner",
)
db.import_data("geosan", "aladoy", mmun, "microgis_mun", "gdenr")


# # VD npa
# npa = gpd.read_file(r"./GEOSAN DB/data/MICROGIS NPA 2019/SF_COMPACT_LC_2019.shp")
# npa.crs
# npa = npa.to_crs({"init": "epsg:2056"})  # Convert CRS from epsg:21781 to epsg:2056
# # Keep only VD features
# npa = npa[npa.KT == "VD"]
# import_data(npa, "npa", "lcid", True)

# # VD microregions
# microregions = gpd.read_file(
#     r"./GEOSAN DB/data/MICROREGIONS 2017/JOOSTSPECIAL_NB_2017.shp"
# )
# microregions.crs
# import_data(microregions, "microregions", "nbid", True)

# # INHABITED HECTARES (STATPOP)
# # Read Statpop data file (CSV)
# statpop = pd.read_csv(r"./GEOSAN DB/data/STATPOP 2019/STATPOP2019.csv", sep=",")
# statpop.shape
# # Move to RELI centroids
# statpop[["X_KOORD", "Y_KOORD", "E_KOORD", "N_KOORD"]] = statpop[
#     ["X_KOORD", "Y_KOORD", "E_KOORD", "N_KOORD"]
# ].applymap(lambda x: x + 50)
# # Create a geometry column using Shapely
# statpop = statpop.assign(
#     geometry=statpop.apply(lambda row: Point(row.E_KOORD, row.N_KOORD), axis=1)
# )
# # Convert to geodataframe
# statpop = gpd.GeoDataFrame(
#     statpop, geometry=statpop.geometry, crs={"init": "epsg:2056"}
# )
# # Add lat lon
# statpop["lon"] = statpop.to_crs({"init": "epsg:4326"}).geometry.x
# statpop["lat"] = statpop.to_crs({"init": "epsg:4326"}).geometry.y
# shapely.speedups.enable()  # Speed query
# statpop = gpd.overlay(statpop, canton)  # Keep only VD hectares
# statpop.shape
# import_data(statpop, "inhabited_ha_centroid", "reli", True)

# # Create same file with polygons geometry
# cursor.execute(
#     "CREATE TABLE inhabited_ha AS SELECT reli,ST_Expand(geometry,50) AS geometry FROM inhabited_ha_centroid"
# )
# conn.commit()

# # STATPOP INDIVIDUALS (STATPOP NON PROTEGE)
# statpop_indiv = pd.read_csv(
#     r"./GEOSAN DB/data/STATPOP NON PROTEGE 2017/STATPOP_2016_VD.csv", sep=";"
# )
# # Create unique index
# statpop_indiv.reset_index(drop=False, inplace=True)
# # Create a geometry column using Shapely
# statpop_indiv = statpop_indiv.assign(
#     geometry=statpop_indiv.apply(
#         lambda row: Point(row.GEOCOORDE, row.GEOCOORDN), axis=1
#     )
# )
# # Convert to geodataframe
# statpop_indiv = gpd.GeoDataFrame(
#     statpop_indiv, geometry=statpop_indiv.geometry, crs={"init": "epsg:2056"}
# )
# import_data(statpop_indiv, "statpop_indiv", "index", True)

# # PUBLIC TRANSPORTS
# pt = pd.read_csv(
#     r"./GEOSAN DB/data/PUBLIC TRANSPORT OFT 2021/PointExploitation.csv",
#     sep=",",
#     encoding="iso-8859-1",
# )
# pt[pt.duplicated(subset=["Numero"])]  # Check if Numero is unique -> True
# # Create a geometry column using Shapely
# pt = pt.assign(geometry=pt.apply(lambda row: Point(row.E, row.N), axis=1))
# pt = gpd.GeoDataFrame(
#     pt, geometry=pt.geometry, crs={"init": "epsg:2056"}
# )  # Convert to geodataframe
# import_data(pt, "public_transport_stops", "Numero", True)


# # REGBL (2021)
# vd_addr = pd.read_csv(r"GEOSAN DB/data/REGBL 2021/VD.csv", delimiter=";")
# vd_addr.shape
# # Remove accents in object type
# vd_addr["GDENAME"] = vd_addr.GDENAME.map(g.strip_accents)
# vd_addr["STRNAME"] = vd_addr.STRNAME.map(g.strip_accents)
# vd_addr["DPLZNAME"] = vd_addr.DPLZNAME.map(g.strip_accents)
# # Convert object type to upper case
# vd_addr["GDENAME"] = vd_addr.GDENAME.map(str.upper)
# vd_addr["STRNAME"] = vd_addr.STRNAME.map(str.upper)
# vd_addr["DPLZNAME"] = vd_addr.DPLZNAME.map(str.upper)
# # Create a geometry column using Shapely
# vd_addr = vd_addr.assign(
#     geometry=vd_addr.apply(lambda row: Point(row.GKODE, row.GKODN), axis=1)
# )
# vd_addr = gpd.GeoDataFrame(
#     vd_addr, geometry=vd_addr.geometry, crs="EPSG:2056"
# )  # Convert to geodataframe
# import_data(vd_addr, "regbl_2021", "egid,edid", True)

# Close the connection
conn.close()
