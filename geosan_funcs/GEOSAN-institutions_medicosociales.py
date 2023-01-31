# LIBRARIES
# Basic
import pandas as pd
import os
import subprocess
import sys
import numpy as np

# Spatial
import geopandas as gpd
from geoalchemy2 import Geometry, WKTElement
from shapely import wkt
from shapely.geometry import Point
import shapely.speedups

# Import functions from GIRAPH-functions repository
sys.path.append(r"/mnt/data/GEOSAN/FUNCTIONS/GIRAPH-functions/")
try:
    import geocoding_utils as g
    import db_utils as db
except FileNotFoundError:
    print("Wrong file or file path")


def main():

    #############
    # IMPORT DATA#
    #############

    path = r"/mnt/data/GEOSAN/GEOSAN DB/data/INSTITUTIONS MEDICO-SOCIALES VD/2022/"

    # URGENCES
    urgences = gpd.read_file(path + "MN95_SSP_TPR_URGENCE.shp")
    urgences.dtypes
    urgences.rename(
        columns={"SERVICE": "NOTE", "GROUPE": "NOM", "VOIE": "RUE"}, inplace=True
    )
    urgences["EXPLOITANT"] = np.nan
    urgences["TYPE"] = "URGENCE"
    urgences = extract_attributes(urgences)

    # PERMANENCES DENTAIRES
    dentaire = gpd.read_file(path + "MN95_SSP_TPR_PERM_DENTAIRE.shp")
    dentaire.dtypes
    dentaire.rename(
        columns={"SERVICE": "NOTE", "GROUPE": "NOM", "VOIE": "RUE"}, inplace=True
    )
    dentaire["EXPLOITANT"] = np.nan
    dentaire["TYPE"] = "PERMANENCE DENTAIRE"
    dentaire = extract_attributes(dentaire)

    # SOINS AIGUS (CLINIQUES, HOPITAUX, HOPITAUX PSYCHIATRIQUES)
    soinsaigus = gpd.read_file(path + "MN95_SSP_TPR_SOINS_AIGUS.shp")
    soinsaigus.dtypes
    soinsaigus.rename(columns={"TYPE": "NOTE", "VOIE": "RUE"}, inplace=True)
    soinsaigus["EXPLOITANT"] = np.nan
    soinsaigus["TYPE"] = "SOINS AIGUS"
    soinsaigus = extract_attributes(soinsaigus)

    # CENTRES MÉDICO-SOCIAUX
    cms = gpd.read_file(path + "MN95_SSP_TPR_CMS.shp")
    cms.dtypes
    cms.rename(columns={"VOIE": "RUE"}, inplace=True)
    cms["TYPE"] = "CMS"
    cms["NOTE"] = np.nan
    cms = extract_attributes(cms)

    # ORGANISATIONS PRIVÉES DE SOINS À DOMICILE
    osad = gpd.read_file(path + "MN95_SSP_TPR_OSAD.shp")
    osad.dtypes
    osad.rename(columns={"VOIE": "RUE"}, inplace=True)
    osad["NOTE"] = np.nan
    osad["EXPLOITANT"] = np.nan
    osad["TYPE"] = "OSAD"
    osad = extract_attributes(osad)

    # HOMES NON MÉDICALISÉS
    hnm = gpd.read_file(path + "MN95_SSP_TPR_HNM.shp")
    hnm.dtypes
    hnm.rename(columns={"VOIE": "RUE", "MISSION": "NOTE"}, inplace=True)
    hnm["NOTE"] = np.nan
    hnm["TYPE"] = "HNM"
    hnm = extract_attributes(hnm)

    # PHARMACIES
    pharmacies = gpd.read_file(path + "MN95_SSP_TPR_PHARMACIE.shp")
    pharmacies.dtypes
    pharmacies.rename(columns={"VOIE": "RUE"}, inplace=True)
    pharmacies["NOTE"] = np.nan
    pharmacies["TYPE"] = "PHARMACIE"
    pharmacies = extract_attributes(pharmacies)

    # ESPACES DE PRÉVENTION
    prevention = gpd.read_file(path + "MN95_SSP_TPR_ESPACE_PREVENTION.shp")
    prevention.dtypes
    prevention.rename(columns={"VOIE": "RUE"}, inplace=True)
    prevention["EXPLOITANT"] = np.nan
    prevention["NOTE"] = np.nan
    prevention["TYPE"] = "ESPACE PREVENTION"
    prevention = extract_attributes(prevention)

    # BUREAUX D'INFORMATION ET D'ORIENTATION
    brios = gpd.read_file(path + "MN95_SSP_TPR_BRIOS.shp")
    brios.dtypes
    brios.rename(columns={"VOIE": "RUE"}, inplace=True)
    brios["EXPLOITANT"] = np.nan
    brios["NOTE"] = np.nan
    brios["TYPE"] = "BRIOS"
    brios = extract_attributes(brios)

    # CENTRES MÉMOIRE
    memoire = gpd.read_file(path + "MN95_SSP_TPR_CENTRE_MEMOIRE.shp")
    memoire.dtypes
    memoire.rename(columns={"VOIE": "RUE"}, inplace=True)
    memoire["EXPLOITANT"] = np.nan
    memoire["NOTE"] = np.nan
    memoire["TYPE"] = "CENTRE MEMOIRE"
    memoire = extract_attributes(memoire)

    # AGENCES D'ASSURANCES SOCIALES
    aas = gpd.read_file(path + "MN95_SSP_TPR_AAS.shp")
    aas.dtypes
    aas.rename(columns={"VOIE": "RUE"}, inplace=True)
    aas["EXPLOITANT"] = np.nan
    aas["NOTE"] = np.nan
    aas["TYPE"] = "AAS"
    aas = extract_attributes(aas)

    # CENTRES SOCIAUX RÉGIONAUX
    csr = gpd.read_file(path + "MN95_SSP_TPR_CSR.shp")
    csr.dtypes
    csr.rename(columns={"VOIE": "RUE"}, inplace=True)
    csr["EXPLOITANT"] = np.nan
    csr["NOTE"] = np.nan
    csr["TYPE"] = "CSR"
    csr = extract_attributes(csr)

    # STRUCTURES D'ACCOMPAGNEMENT MÉDICO-SOCIALES
    sams = gpd.read_file(path + "MN95_SSP_TPR_SAMS.shp")
    sams.dtypes
    sams.rename(columns={"VOIE": "RUE"}, inplace=True)
    sams["NOTE"] = sams["CATEGORIE"] + " (" + sams["TYPE"] + ")"
    sams["TYPE"] = "SAMS"
    sams = extract_attributes(sams)

    # SITES D'AMBULANCES
    ambulance = gpd.read_file(path + "MN95_SSP_TPR_AMBULANCE.shp")
    ambulance.dtypes
    ambulance.rename(columns={"VOIE": "RUE", "TYPE": "NOTE"}, inplace=True)
    ambulance["EXPLOITANT"] = np.nan
    ambulance["TYPE"] = "AMBULANCE"
    ambulance["URL"] = np.nan
    ambulance = extract_attributes(ambulance)

    # ÉTABLISSEMENTS PSYCHO-SOCIAUX MÉDICALISÉS
    epsm = gpd.read_file(path + "MN95_SSP_TPR_EPSM.shp")
    epsm.dtypes
    epsm.rename(columns={"VOIE": "RUE"}, inplace=True)
    epsm["NOTE"] = "Capacité: " + epsm["CAPACITE"].astype(int).apply(str)
    epsm["TYPE"] = "EPSM"
    epsm = extract_attributes(epsm)

    # ÉTABLISSEMENTS SOCIO-ÉDUCATIFS
    ese = gpd.read_file(path + "MN95_SSP_TPR_ESE.shp")
    ese.dtypes
    ese.rename(columns={"VOIE": "RUE"}, inplace=True)
    ese["NOTE"] = "Capacité: " + ese["CAPACITE"].astype(int).apply(str)
    ese["TYPE"] = "ESE"
    ese = extract_attributes(ese)


    # ÉTABLISSEMENTS MEDICAUX-SOCIAUX
    ems = gpd.read_file(path + "MN95_SSP_TPR_EMS.shp")
    ems.dtypes
    ems.rename(columns={"VOIE": "RUE", "MISSION": "NOTE"}, inplace=True)
    ems["EXPLOITANT"] = np.nan
    ems["TYPE"] = "EMS"
    ems = extract_attributes(ems)

    # Concatenate dataframes
    institutions = pd.concat(
        [
            urgences,
            dentaire,
            soinsaigus,
            cms,
            ems,
            osad,
            hnm,
            pharmacies,
            prevention,
            brios,
            memoire,
            aas,
            csr,
            sams,
            ambulance,
            epsm,
            ese,
        ],
        axis=0,
    )
    institutions.reset_index(inplace=True, drop=True)

    ################
    # DATA WRANGLING#
    ################

    # Convert NPA to integer
    institutions["NPA"] = institutions.NPA.map(int)

    # Convert all in upper case + remove accents
    institutions["NOM"] = institutions.NOM.map(g.strip_accents).map(str.upper)
    institutions["RUE"] = institutions.RUE.map(g.strip_accents).map(str.upper)
    institutions["LOCALITE"] = institutions.LOCALITE.map(g.strip_accents).map(str.upper)
    institutions.loc[~institutions.NOTE.isna(), "NOTE"] = (
        institutions.loc[~institutions.NOTE.isna(), "NOTE"]
        .map(g.strip_accents)
        .map(str.upper)
    )
    institutions.loc[~institutions.EXPLOITANT.isna(), "EXPLOITANT"] = (
        institutions.loc[~institutions.EXPLOITANT.isna(), "EXPLOITANT"]
        .map(g.strip_accents)
        .map(str.upper)
    )

    # Drop index
    institutions.reset_index(drop=False, inplace=True)

    ##################
    # ADD TO GEOSAN DB#
    ##################

    db.import_data(
        "geosan",
        "aladoy",
        institutions,
        "institutions_medicosociales",
        "index",
        idx_geom=True,
    )



def extract_attributes(df):

    df = df[
        [
            "NOM",
            "TYPE",
            "EXPLOITANT",
            "RUE",
            "NUMERO",
            "NPA",
            "LOCALITE",
            "URL",
            "NOTE",
            "geometry",
        ]
    ]

    return df


if __name__ == "__main__":
    main()