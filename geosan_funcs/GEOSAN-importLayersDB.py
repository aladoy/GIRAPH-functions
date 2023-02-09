# LIBRARIES
# Basic
import fiona
import pandas as pd
import os
import sys

# Spatial
import geopandas as gpd
from shapely.geometry import Point


# CONNECT TO GEOSAN DB
sys.path.append(r"/mnt/data/GEOSAN/FUNCTIONS/GIRAPH-functions/")
try:
    import db_utils as db
    import basic_utils as u
except FileNotFoundError:
    print("Wrong file or file path")
engine, conn, cursor = db.connect_db("geosan", "aladoy")

# DIRECTORIES
geosan_db_dir: str = r"/mnt/data/GEOSAN/GEOSAN DB/data"

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
db.import_data("geosan", "aladoy", districts,
               "districts", "uuid", idx_geom=True)

# Municipalities
# Use SWISS TLM REGIO dataset instead of SWISS BOUNDARIES because lakes are separated from municipalities
municipalities = gpd.read_file(
    os.sep.join(
        [
            geosan_db_dir,
            "SWISS TLM REGIO/2022/swissTLMRegio_Boundaries_LV95/swissTLMRegio_HOHEITSGEBIET_LV95.shp",
        ]
    )
)
municipalities.crs = 2056
municipalities = u.convert_3D_to_2D(municipalities)
db.import_data(
    "geosan", "aladoy", municipalities, "municipalities", "objectid", idx_geom=True
)


# HECTOMETRIC GRID
reli = gpd.read_file(
    os.sep.join([geosan_db_dir, "STATPOP/2021/statpop.gpkg"]),
    driver="GPKG",
    layer="statpop_reli",
)
reli = reli[["RELI", "E_KOORD", "N_KOORD", "B21BTOT", "geometry"]]
db.import_data("geosan", "aladoy", reli, "reli_point", "reli", idx_geom=True)
centroid = gpd.read_file(
    os.sep.join([geosan_db_dir, "STATPOP/2021/statpop.gpkg"]),
    driver="GPKG",
    layer="statpop_centroid",
)
centroid = centroid[["RELI", "E_KOORD", "N_KOORD", "B21BTOT", "geometry"]]
db.import_data("geosan", "aladoy", centroid,
               "reli_centroid", "reli", idx_geom=True)

ha_polygon = gpd.read_file(
    os.sep.join([geosan_db_dir, "STATPOP/2021/statpop.gpkg"]),
    driver="GPKG",
    layer="statpop_polygon",
)
ha_polygon = ha_polygon[["RELI", "E_KOORD", "N_KOORD", "B21BTOT", "geometry"]]
db.import_data("geosan", "aladoy", ha_polygon,
               "reli_polygon", "reli", idx_geom=True)


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
    os.sep.join(
        [geosan_db_dir, "MICROGIS/2021/INCOME_IQMD/HA_INCOME_IQMD.csv"]),
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
    os.sep.join(
        [geosan_db_dir, "MICROGIS/2021/SOCECO/SF_SOCECORATIO_GD_2021.csv"]),
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


# STATPOP (2021)
statpop = pd.read_csv(
    os.sep.join([geosan_db_dir, "STATPOP/2021/STATPOP2021.csv"]), sep=";"
)
db.import_data("geosan", "aladoy", statpop,
               "statpop2021", "RELI", ifexists="replace")


# REGBL (2021)
vd_addr = pd.read_csv(os.sep.join(
    [geosan_db_dir, "REGBL/2021/VD.csv"]), sep=";")
# Remove accents in object type
vd_addr["GDENAME"] = vd_addr.GDENAME.map(g.strip_accents)
vd_addr["STRNAME"] = vd_addr.STRNAME.map(g.strip_accents)
vd_addr["DPLZNAME"] = vd_addr.DPLZNAME.map(g.strip_accents)
# Convert object type to upper case
vd_addr["GDENAME"] = vd_addr.GDENAME.map(str.upper)
vd_addr["STRNAME"] = vd_addr.STRNAME.map(str.upper)
vd_addr["DPLZNAME"] = vd_addr.DPLZNAME.map(str.upper)
# Create a geometry column using Shapely
vd_addr = vd_addr.assign(
    geometry=vd_addr.apply(lambda row: Point(row.gkode, row.gkodn), axis=1)
)
vd_addr = gpd.GeoDataFrame(vd_addr, geometry=vd_addr.geometry, crs="EPSG:2056")
# Convert to geodataframe
db.import_data("geosan", "aladoy", vd_addr,
               "regbl2021", "egid,edid", idx_geom=True)


# DISTANCE TO SERVICES (OFS, 2018)
dist_serv = pd.read_csv(
    os.sep.join(
        [geosan_db_dir, "ACCESSIBILITY TO SERVICES/ag-b-00.03-2018spop-csv.csv"]
    ),
    delimiter=";",
)
db.import_data(
    "geosan", "aladoy", dist_serv, "distance_services", "RELI", ifexists="replace"
)


# PLAYGROUNDS (OSM, 2022)
playgrounds = gpd.read_file(
    os.sep.join(
        [geosan_db_dir, "PLAYGROUNDS VD/Jan 23/playgrounds_VD_2056.gpkg"])
)
playgrounds.reset_index(drop=False, inplace=True)
db.import_data(
    "geosan", "aladoy", playgrounds, "playgrounds", "index", ifexists="replace"
)

# PUBLIC TRANSPORT (ARE, 2022)
pub_transport = gpd.read_file(
    os.sep.join(
        [geosan_db_dir, "PUBLIC TRANSPORT/2022/OeV_Gueteklassen_ARE.gpkg"]),
    layer="OeV_Haltestellen_ARE",
)
db.import_data(
    "geosan",
    "aladoy",
    pub_transport,
    "public_transport_stops",
    "Haltestellen_No",
    ifexists="replace",
)

# Close the connection
conn.close()
