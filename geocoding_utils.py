# geocoding_utils.py

import unicodedata
import numpy as np
import re
import difflib
import pandas as pd
import math
import requests
import time
import psycopg2 as ps

# FUNCTION TO REMOVE ACCENTS ON STRING


def strip_accents(text):

    try:
        text = unicode(text, "utf-8")
    except NameError:  # unicode is a default on python 3
        pass

    text = unicodedata.normalize("NFD", text).encode(
        "ascii", "ignore").decode("utf-8")

    return str(text)


# FUNCTION TO EXTRACT THE STREET NUMBER / STREET NAME FROM AN ADDRESS


def split_address(x):
    """
    The algorithm splits with Regex the address field when the first digit
    appears. Thus, Chemin de Montelly 1 -> ['Chemin de Montelly','1'] and
    Avenue de Morges 9b -> ['Avenue de Morges','9b']. Addresses that are not in
    the standard format (e.g. 24, grande rue) will not be catched however, but
    the proportion is small. If there is no digit (e.g. EMS de l'Ours) or if
    the address is not in a standard format (see above), the split will return
    only one element (i.e. the entire address). In this case, the algorithm
    will return a NaN value. On the other hand, the algorithnm will return the
    2nd part of the split (i.e. street number).
    """

    try:
        # Remove comma in addresses
        x = x.replace(",", "")

        # Address in the form: 20 avenue longchamps
        if x[0].isdigit():

            split = re.split("(\d+).*?\s+(.+)", x)
            split_len = len(split)

            # With this pattern, the first and last element of the list are
            # empty, that's why the index are shifted
            deinr = split[1]
            strname = " ".join(split[2: split_len - 1])

        # Address in the form: Avenue longchamps 20
        else:
            split = re.split("(?<=[a-zA-Z-zÀ-ÿ])\\s*(?=[0-9])", x)
            split_len = len(split)

            if split_len == 1:
                deinr = np.nan
                strname = x
            else:
                deinr = split[split_len - 1]
                strname = " ".join(split[0: split_len - 1])

    except Exception:

        deinr = np.nan
        strname = x

    return deinr, strname


# FUNCTION TO PREPARE REGBL FOR GEOCODING


def regbl_wrangling(regbl_dat):

    # Remove missing addresses
    print(
        "Number of RegBL NaN addresses: ",
        regbl_dat[regbl_dat.strname.isna()].shape[0],
        "(",
        round(
            regbl_dat[regbl_dat.strname.isna()].shape[0] * 100 /
            regbl_dat.shape[0], 2
        ),
        "%)",
    )
    regbl_dat = regbl_dat[~regbl_dat.strname.isna()]
    print("Missing addresses were removed from the dataset.")

    # Remove accents
    regbl_dat["strname"] = regbl_dat.strname.map(strip_accents)
    regbl_dat["gdename"] = regbl_dat.gdename.map(strip_accents)

    # Convert street and municipality into upper case
    regbl_dat["strname"] = regbl_dat.strname.map(str.upper)
    regbl_dat["gdename"] = regbl_dat.gdename.map(str.upper)

    # Select only essential columns
    regbl_dat = regbl_dat[
        ["egid", "strname", "deinr", "dplz4", "gdename", "gkode", "gkodn"]
    ]

    return regbl_dat


# FUNCTION TO RETURN CENTROIDS OF THE NPA


def npa_centroid(ville, cp, npa):

    # Remove accents in municipalities
    npa["Ortschaftsname"] = npa.Ortschaftsname.map(strip_accents)
    # Convert municipalities to upper case
    npa["Ortschaftsname"] = npa.Ortschaftsname.map(str.upper)

    try:  # match with name + PLZ
        e = npa[(npa.Ortschaftsname == ville) & (npa.PLZ == cp)].E.values[0]
        n = npa[(npa.Ortschaftsname == ville) & (npa.PLZ == cp)].N.values[0]

    except Exception:
        # take first PLZ on the list (no match with name)
        if cp in npa.PLZ.values:
            e = npa[npa.PLZ == cp].E.values[0]
            n = npa[npa.PLZ == cp].N.values[0]
        else:
            e = np.nan
            n = np.nan

    return e, n


def get_coords(row, regbl, npa, level):

    # print(row["index"])

    addr = regbl.copy()

    if not (row.npa in list(addr.dplz4.unique())):
        # If unknown NPA (e.g. 1014 -> administration), use locality name
        # instead of NPA for all code
        addr.dplz4 = addr.gdename
        row.npa = row.ville

    if pd.isnull(row.strname):
        # If no streetname, geocode at NPA centroid
        e, n = npa_centroid(row.ville, row.npa, npa)
        egid = np.nan
        if math.isnan(e) | math.isnan(n):
            note_geocoding = "To remove from the dataset"
            c = "CASE 1"
        else:
            note_geocoding = "Geocoded at NPA centroid. No street address."
            c = "CASE 2"

    elif pd.isnull(row.deinr):
        # If no street number, geocode at street (exact match or fuzzy match)
        # and geocode at NPA centroid if no correspondance
        try:
            # print('CASE 3')
            e, n, egid = search_regbl(
                row,
                addr,
                on="street",
                use_npa=True,
                fuzzy_rue=False,
                closest_num=False,
                fuzzy_level=level,
            )
            if egid is None:
                e, n, egid = search_regbl(
                    row,
                    addr,
                    on="street",
                    use_npa=False,
                    fuzzy_rue=False,
                    closest_num=False,
                    fuzzy_level=level,
                )
            egid > 0
            note_geocoding = "Geocoded at street."
            c = "CASE 3"

        except TypeError:
            try:
                # print('CASE 4')
                e, n, egid = search_regbl(
                    row,
                    addr,
                    on="street",
                    use_npa=True,
                    fuzzy_rue=True,
                    closest_num=False,
                    fuzzy_level=level,
                )
                if egid is None:
                    e, n, egid = search_regbl(
                        row,
                        addr,
                        on="street",
                        use_npa=False,
                        fuzzy_rue=True,
                        closest_num=False,
                        fuzzy_level=level,
                    )
                egid > 0
                note_geocoding = "Geocoded at street. Fuzzy matching."
                c = "CASE 4"

            except TypeError:
                # print('CASE 5')
                e, n = npa_centroid(row.ville, row.npa, npa)
                egid = np.nan
                if math.isnan(e) | math.isnan(n):
                    note_geocoding = "To remove from the dataset"
                else:
                    note_geocoding = "Geocoded at NPA centroid. No street number."
                c = "CASE 5"
    else:
        # If we have all informations (street number & street name), geocode
        # at building (perfect match or fuzzy match), ang at closest building
        # in the same street if no correspondance. If you can't find any
        # matching street, geocode at NPA centroid.
        try:
            # print('CASE 6')
            e, n, egid = search_regbl(
                row,
                addr,
                on="building",
                use_npa=True,
                fuzzy_rue=False,
                closest_num=False,
                fuzzy_level=level,
            )
            if egid is None:
                e, n, egid = search_regbl(
                    row,
                    addr,
                    on="building",
                    use_npa=False,
                    fuzzy_rue=False,
                    closest_num=False,
                    fuzzy_level=level,
                )
            egid > 0
            note_geocoding = "Geocoded at building."
            c = "CASE 6"

        except TypeError:
            try:
                # print('CASE 7')
                e, n, egid, label = search_geoadmin(
                    str(row.deinr)
                    + " "
                    + remove_typo_addr(row.strname)
                    + " "
                    + str(row.npa)
                )
                c = "CASE 7"
                note_geocoding = "Geocoded at building. Fuzzy API."

                if label == "No match found":
                    # print('CASE 8')
                    e, n, egid = search_regbl(
                        row,
                        addr,
                        on="building",
                        use_npa=True,
                        fuzzy_rue=True,
                        closest_num=False,
                        fuzzy_level=level,
                    )
                    if egid is None:
                        e, n, egid = search_regbl(
                            row,
                            addr,
                            on="building",
                            use_npa=False,
                            fuzzy_rue=True,
                            closest_num=False,
                            fuzzy_level=level,
                        )
                    note_geocoding = "Geocoded at building. Fuzzy matching."
                    c = "CASE 8"
                egid > 0

            except TypeError:
                try:
                    # print('CASE 9')
                    e, n, egid = search_regbl(
                        row,
                        addr,
                        on="street",
                        use_npa=True,
                        fuzzy_rue=False,
                        closest_num=True,
                        fuzzy_level=level,
                    )
                    if egid is None:
                        e, n, egid = search_regbl(
                            row,
                            addr,
                            on="street",
                            use_npa=False,
                            fuzzy_rue=False,
                            closest_num=True,
                            fuzzy_level=level,
                        )
                    egid > 0
                    c = "CASE 9"
                    note_geocoding = "Geocoded at street. Closest building."

                except (ValueError, TypeError):
                    try:
                        # print('CASE 10')
                        e, n, egid = search_regbl(
                            row,
                            addr,
                            on="street",
                            use_npa=True,
                            fuzzy_rue=True,
                            closest_num=True,
                            fuzzy_level=level,
                        )
                        if egid is None:
                            e, n, egid = search_regbl(
                                row,
                                addr,
                                on="street",
                                use_npa=False,
                                fuzzy_rue=True,
                                closest_num=True,
                                fuzzy_level=level,
                            )
                        egid > 0
                        c = "CASE 10"
                        note_geocoding = "Geocoded at street. Fuzzy matching."

                    except (ValueError, TypeError):
                        if row.ville == row.npa:
                            # print('CASE 11')
                            e, n, egid = None, None, None
                            note_geocoding = "To remove from the dataset"
                            c = "CASE 11"
                        else:
                            # print('CASE 12')
                            e, n = npa_centroid(row.ville, row.npa, npa)
                            egid = None
                            if math.isnan(e) | math.isnan(n):
                                note_geocoding = "To remove from the dataset"
                            else:
                                note_geocoding = "Geocoded at NPA centroid."
                                c = "CASE 12"

    return e, n, egid, note_geocoding, c


def search_regbl(
    row,
    list_addr,
    on="building",
    use_npa=True,
    fuzzy_rue=True,
    closest_num=False,
    fuzzy_level=0.9,
):
    """
    This function find any given match in a list of addresses (from RegBL)
    based on a street name and street number.

    Inputs:
    row = a row containing at least the given fields: strname (street name),
    deinr (street number), npa (postal code), ville (municipality)
    list_addr = a dataframe with official addresses containing at least the
    given fields: egid (building ID), strname (street name), deinr (street
    number), dplz4 (postal code), gdename (municipality), gkode (x-coordinate),
    gkodn (y-coordinate).
    on =  the attribute takes either the value "building" if we want to find
    exact matching building, or "street" if we want to geocode at street level
    (closest building or first building on the street).
    use_npa = should we use match list of addresses on postal code (use_npa
    =True) or municipality name (use_npa=False)?
    fuzzy_rue = are we giving the exact street name to the algorithm
    (fuzzy_rue=False) or should the algorithm searches for the closest street
    name in the list of addesses (fuzzy_rue=True)?
    fuzzy_level = fuzzy match cutoff if fuzzy_rue=True. Possibilities that do
    not score at least that similar to row's streetname are ignored.
    closest_num = if on="street", are we giving the exact street number
    (closest_num=False) to the algorithm or should the algorithm searches for
    the closest street number (for a specific address) in list_addr?

    Outputs:
    e = x-coordinate for the matching adress (or None if no correspondance)
    n = y-coordinate for the matching adress (or None if no correspondance)
    egid = building ID
    """

    if use_npa is True:
        row_locality = row.npa
        addr_locality = list_addr.dplz4
    else:
        row_locality = row.ville
        addr_locality = list_addr.gdename

    if fuzzy_rue is True:
        try:
            row_streetname = difflib.get_close_matches(
                row.strname,
                list_addr[addr_locality == row_locality].strname,
                1,
                fuzzy_level,
            )[0]
        except IndexError:
            try:
                list_addr["strname_notypo"] = list_addr.strname.map(
                    remove_typo_addr)
                row_streetname = difflib.get_close_matches(
                    remove_typo_addr(row.strname),
                    list_addr[addr_locality == row_locality].strname_notypo,
                    1,
                    fuzzy_level,
                )[0]
                row_streetname = list_addr.loc[
                    list_addr.strname_notypo == row_streetname, "strname"
                ].iloc[0]
            except IndexError:
                e, n, egid = None, None, None
                return e, n, egid
    else:
        row_streetname = row.strname

    if closest_num is True:
        list_no = list_addr[
            (list_addr.strname == row_streetname)
            & (addr_locality == row_locality)
            & (~list_addr.deinr.isna())
        ].deinr
        try:
            list_no = list_no.map(lambda x: float(re.findall("\d+", x)[0]))
            closest = str(
                int(
                    min(
                        list_no,
                        key=lambda x: abs(
                            x - float(re.findall("\d+", row.deinr)[0])),
                    )
                )
            )
        except IndexError:  # if list of deinr ony contains letters
            closest = list_no.values[0]

    if on == "street":
        matches = list_addr[
            (list_addr.strname == row_streetname) & (
                addr_locality == row_locality)
        ].sort_values("deinr")
        if closest_num is True:
            matches = list_addr[
                (list_addr.strname == row_streetname)
                & (list_addr.deinr == closest)
                & (addr_locality == row_locality)
            ].sort_values("deinr")

            if matches.empty:
                matches = list_addr[
                    (list_addr.strname == row_streetname)
                    & (
                        list_addr.deinr.str.contains(
                            "^" + closest + "[a-zA-Z]", regex=True
                        )
                    )
                    & (addr_locality == row_locality)
                ].sort_values("deinr")

    elif on == "building":
        matches = list_addr[
            (list_addr.strname == row_streetname)
            & (list_addr.deinr == row.deinr)
            & (addr_locality == row_locality)
        ]

    try:
        matching_addr = matches.iloc[0]
        e = matching_addr.gkode
        n = matching_addr.gkodn
        egid = matching_addr.egid
    except IndexError:
        e, n, egid = None, None, None

    return e, n, egid


def search_geoadmin(searchText):

    time.sleep(0.1)
    request = (
        "https://api3.geo.admin.ch/rest/services/api/SearchServer?"
        "layer=ch.bfs.gebaeude_wohnungs_register"
        "&searchText=" + searchText + "&type=locations"
        "&origins=address,zipcode"
        "&sr=2056"
    )
    response = requests.get(request)

    try:
        res = response.json()["results"][0]
        e = res["attrs"]["y"]
        n = res["attrs"]["x"]
        egid = int(res["attrs"]["featureId"].split("_")[0])
        label = res["attrs"]["label"]

    except IndexError:
        if response.status_code == 200:
            e, n, egid = None, None, None
            label = "No match found"
        else:
            e, n, egid = None, None, None
            label = "Error code" + str(response.status_code)

    return e, n, egid, label


def remove_typo_addr(strname):

    stopwords = ["CHEMIN", "RUE", "AVENUE",
                 "ROUTE", "RUELLE", "CH.", "AV.", "RTE"]
    querywords = strname.split()
    resultwords = [word for word in querywords if word not in stopwords]
    result = " ".join(resultwords)

    return result


def retrieve_egid_info(row, vd_addr):
    """
    Function to retrieve strname / deinr for a given egid. First, the
    algorithm try to retrieve the information from RegBL (GEOSAN DB) and if it fails
    (no corresponding egid), the egid info is retrieved from GeoAdmin API
    (new address).
    """


    try:
        res = vd_addr.loc[vd_addr.egid==row.egid]
        strname = res.strname
        deinr = res.deinr

        if not deinr:
            strname_deinr = strname
        else:
            strname_deinr = strname + " " + deinr

    except IndexError:

        time.sleep(0.1)
        request = (
            "https://api3.geo.admin.ch/rest/services/api/MapServer/"
            "find?layer=ch.bfs.gebaeude_wohnungs_register&"
            "searchText=" + str(int(row.egid)) + "&searchField=egid"
            "&returnGeometry=false"
        )
        response = requests.get(request)

        try:
            res = response.json()["results"][0]
            strname_deinr = res["attributes"]["strname_deinr"][0]

        except Exception:
            raise Exception("Sorry, egid not found")

    return strname_deinr


def remove_subset(
    dataset, subset_to_remove, subset_label, initial_size, df_for_stats=None
):
    """
    This function removes a specific subset (=subset_to_remove) from the
    dataset. It also displays the number, and the percentage rounded to two
    decimal places, of the affected rows. The "subset_label" argument allows
    you to specify a label that will be used when printing (e.g. 'tests without
    address'). If the rows in the "dataset" do not represent individuals but
    distinct addresses, you can use the "df_for_stats" argument to calculate
    statistics on the number of individuals instead of the number of addresses.
    The function returns a copy of the original dataset, from which
    we have removed the rows present in the subset.
    """

    if df_for_stats is None:
        nb = subset_to_remove.shape[0]
        perc = round((nb * 100) / dataset.shape[0], 2)
    else:
        indivs = subset_to_remove.merge(
            df_for_stats, on="init_addr", how="inner")
        nb = indivs.shape[0]
        perc = round((nb * 100) / initial_size, 2)

    print("Number of ", subset_label, ": ", nb, " (", perc, "%)")

    try:
        dataset.drop(subset_to_remove.index, axis=0, inplace=True)
        print("Rows were removed from the dataset")
        print()
    except Exception:
        raise Exception("Subset could not be removed from the dataset.")

    return dataset


def find_egid(row, addr):

    try:
        egid = addr[
            (addr.strname == row.strname)
            & (addr.deinr == row.deinr)
            & (addr.dplz4 == row.npa)
        ].egid.values[0]
        note = "Direct match."
    except Exception:
        try:
            fuzzy_rue = difflib.get_close_matches(
                row.strname, addr[addr.dplz4 == row.npa].strname, 1, 0.5
            )[0]
            # print(fuzzy_rue)
            egid = addr[
                (addr.strname == fuzzy_rue)
                & (addr.deinr == row.deinr)
                & (addr.dplz4 == row.npa)
            ].egid.values[0]
            note = "Fuzzy matching."
        except Exception:
            egid = np.nan
            note = "No match found."

    return egid, note
