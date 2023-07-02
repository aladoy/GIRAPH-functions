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


def main():

    # DIRECTORIES
    geosan_db_dir: str = r"/mnt/data/GEOSAN/GEOSAN DB/data"

    # IMPORT DATA
    # Cantons
    cantons = gpd.read_file(
        os.sep.join(
            [
                geosan_db_dir,
                "SWISS TLM REGIO/2022/swissTLMRegio_Boundaries_LV95/swissTLMRegio_KANTONSGEBIET_LV95.shp",
            ]
        )
    )
    cantons.crs = 2056
    # Remove Z-dimension
    cantons = u.convert_3D_to_2D(cantons)
    # Import to GEOSAN DB
    db.import_data("geosan", "aladoy", cantons, "cantons", "uuid", idx_geom=True)

    # Districts
    districts = gpd.read_file(
        os.sep.join(
            [
                geosan_db_dir,
                "SWISS TLM REGIO/2022/swissTLMRegio_Boundaries_LV95/swissTLMRegio_BEZIRKSGEBIET_LV95.shp",
            ]
        )
    )
    districts.crs = 2056
    districts = u.convert_3D_to_2D(districts)
    db.import_data("geosan", "aladoy", districts, "districts", "uuid", idx_geom=True)

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
    db.import_data("geosan", "aladoy", centroid, "reli_centroid", "reli", idx_geom=True)

    ha_polygon = gpd.read_file(
        os.sep.join([geosan_db_dir, "STATPOP/2021/statpop.gpkg"]),
        driver="GPKG",
        layer="statpop_polygon",
    )
    ha_polygon = ha_polygon[["RELI", "E_KOORD", "N_KOORD", "B21BTOT", "geometry"]]
    db.import_data(
        "geosan", "aladoy", ha_polygon, "reli_polygon", "reli", idx_geom=True
    )

    # MICROREGIONS
    mreg = gpd.read_file(
        os.sep.join(
            [
                geosan_db_dir,
                "MICROGIS/MICROREGIONS 2017/JOOSTSPECIAL_NB_2017.shp",
            ]
        ),
        driver="ESRI Shapefile",
    )
    mreg_dat = pd.read_csv(
        os.sep.join(
            [geosan_db_dir, "MICROGIS/MICROREGIONS 2017/JOOSTSPECIAL_NB_2017.csv"]
        ),
        engine="python",
    )
    mreg = pd.merge(mreg, mreg_dat, on="NBID", how="inner")
    db.import_data(
        "geosan", "aladoy", mreg, "microgis_microreg", "NBID", ifexists="replace"
    )

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

    # STATPOP (2021)
    statpop = pd.read_csv(
        os.sep.join([geosan_db_dir, "STATPOP/2021/STATPOP2021.csv"]), sep=";"
    )
    db.import_data(
        "geosan", "aladoy", statpop, "statpop2021", "RELI", ifexists="replace"
    )

    # REGBL (2021)
    vd_addr = pd.read_csv(os.sep.join([geosan_db_dir, "REGBL/2021/VD.csv"]), sep=";")
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
    db.import_data("geosan", "aladoy", vd_addr, "regbl2021", "egid,edid", idx_geom=True)

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
        os.sep.join([geosan_db_dir, "PLAYGROUNDS VD/Jan 23/playgrounds_VD_2056.gpkg"])
    )
    playgrounds.reset_index(drop=False, inplace=True)
    db.import_data(
        "geosan", "aladoy", playgrounds, "playgrounds", "index", ifexists="replace"
    )

    # PUBLIC TRANSPORT (ARE, 2022)
    pub_transport = gpd.read_file(
        os.sep.join([geosan_db_dir, "PUBLIC TRANSPORT/2022/OeV_Gueteklassen_ARE.gpkg"]),
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

    # LAKES (SWISSTOPO, 2022)
    lakes = gpd.read_file(
        os.sep.join(
            [
                geosan_db_dir,
                "SWISS TLM REGIO/2022/swissTLMRegio_Product_LV95/Hydrography/swissTLMRegio_Lake.shp",
            ]
        )
    )
    lakes.crs = 2056
    db.import_data("geosan", "aladoy", lakes, "lakes", "objectid", idx_geom=True)

    # ROADS (SWISSTOPO, 2022)
    roads = gpd.read_file(
        os.sep.join(
            [
                geosan_db_dir,
                "SWISS TLM REGIO/2022/swissTLMRegio_Product_LV95/Transportation/swissTLMRegio_Road.shp",
            ]
        )
    )
    roads.crs = 2056
    db.import_data("geosan", "aladoy", roads, "roads", "objectid", idx_geom=True)

    # BUILDINGS (SWISSTOPO, 2022)
    build = gpd.read_file(
        os.sep.join(
            [
                geosan_db_dir,
                "SWISS TLM REGIO/2022/swissTLMRegio_Product_LV95/Buildings/swissTLMRegio_Building.shp",
            ]
        )
    )
    build.crs = 2056
    db.import_data("geosan", "aladoy", build, "buildings", "objectid", idx_geom=True)


if __name__ == "__main__":
    main()
