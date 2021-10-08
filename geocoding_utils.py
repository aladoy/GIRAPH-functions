# geocoding_utils.py

# FUNCTION TO REMOVE ACCENTS ON STRING
def strip_accents(text):
    import unicodedata

    try:
        text = unicode(text, 'utf-8')
    except NameError:  # unicode is a default on python 3
        pass

    text = unicodedata.normalize('NFD', text).encode('ascii',
                                                     'ignore').decode("utf-8")

    return str(text)


# FUNCTION TO EXTRACT THE STREET NUMBER / STREET NAME FROM AN ADDRESS

def split_address(x):
    '''
    The algorithm splits with Regex the address field when the first digit
    appears. Thus, Chemin de Montelly 1 -> ['Chemin de Montelly','1'] and
    Avenue de Morges 9b -> ['Avenue de Morges','9b']. Addresses that are not in
    the standard format (e.g. 24, grande rue) will not be catched however, but
    the proportion is small. If there is no digit (e.g. EMS de l'Ours) or if
    the address is not in a standard format (see above), the split will return
    only one element (i.e. the entire address). In this case, the algorithm
    will return a NaN value. On the other hand, the algorithnm will return the
    2nd part of the split (i.e. street number).
    '''

    import numpy as np
    import re

    try:
        # Remove comma in addresses
        x = x.replace(',', '')

        # Address in the form: 20 avenue longchamps
        if x[0].isdigit():

            split = re.split("(\d+).*?\s+(.+)", x)
            split_len = len(split)

            # With this pattern, the first and last element of the list are
            # empty, that's why the index are shifted
            deinr = split[1]
            strname = ' '.join(split[2:split_len-1])

        # Address in the form: Avenue longchamps 20
        else:
            split = re.split("(?<=[a-zA-Z-zÀ-ÿ])\\s*(?=[0-9])", x)
            split_len = len(split)

            if split_len == 1:
                deinr = np.nan
                strname = x
            else:
                deinr = split[split_len-1]
                strname = ' '.join(split[0:split_len-1])

    except Exception:

        deinr = np.nan
        strname = x

    return deinr, strname


# FUNCTION TO PREPARE REGBL FOR GEOCODING

def regbl_wrangling(regbl_dat):

    # Remove missing addresses
    print('Number of missing addresses: ',
          regbl_dat[regbl_dat.strname.isna()].shape[0], '(',
          round(regbl_dat[
              regbl_dat.strname.isna()].shape[0]*100/regbl_dat.shape[0], 2),
          '%)')
    regbl_dat = regbl_dat[~regbl_dat.strname.isna()]
    print('Missing addresses were removed from the dataset.')

    # Remove accents
    regbl_dat['strname'] = regbl_dat.strname.map(strip_accents)
    regbl_dat['gdename'] = regbl_dat.gdename.map(strip_accents)

    # Convert street and municipality into upper case
    regbl_dat['strname'] = regbl_dat.strname.map(str.upper)
    regbl_dat['gdename'] = regbl_dat.gdename.map(str.upper)

    # Select only essential columns
    regbl_dat = regbl_dat[['egid', 'strname', 'deinr', 'dplz4', 'gdename',
                           'gkode', 'gkodn']]

    return regbl_dat


# FUNCTION TO RETURN CENTROIDS OF THE NPA

def npa_centroid(ville, cp, npa):

    import numpy as np

    # Remove accents in municipalities
    npa['Ortschaftsname'] = npa.Ortschaftsname.map(strip_accents)
    # Convert municipalities to upper case
    npa['Ortschaftsname'] = npa.Ortschaftsname.map(str.upper)

    try:  # match with name + PLZ
        e = npa[(npa.Ortschaftsname == ville) & (npa.PLZ == cp)].E.values[0]
        n = npa[(npa.Ortschaftsname == ville) & (npa.PLZ == cp)].N.values[0]

    except Exception:
        if cp in npa.PLZ.values:  # take first PLZ on the list (no match with name)
            e = npa[npa.PLZ == cp].E.values[0]
            n = npa[npa.PLZ == cp].N.values[0]
        else:
            e = np.nan
            n = np.nan

    return e, n


def find_matches(row, list_addr, on='building', use_npa=True, fuzzy_rue=True,
                 closest_num=False, fuzzy_level=0.9):
    '''
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
    '''

    import re
    import difflib

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
                1, fuzzy_level)[0]
        except IndexError:
            try:
                list_addr['strname_notypo'] = list_addr.strname.map(
                    remove_typo_addr)
                row_streetname = difflib.get_close_matches(
                    remove_typo_addr(row.strname),
                    list_addr[addr_locality == row_locality].strname_notypo,
                    1, fuzzy_level)[0]
                row_streetname = list_addr.loc[
                    list_addr.strname_notypo == row_streetname,
                    'strname'].iloc[0]
            except IndexError:
                e, n, egid = None, None, None
                return e, n, egid
    else:
        row_streetname = row.strname

    if closest_num is True:
        list_no = list_addr[
            (list_addr.strname == row_streetname)
            & (addr_locality == row_locality)
            & (~list_addr.deinr.isna())].deinr
        try:
            list_no = list_no.map(lambda x: float(re.findall('\d+', x)[0]))
            closest = str(int(min(list_no, key=lambda x: abs(
                x-float(re.findall('\d+', row.deinr)[0])))))
        except IndexError:  # if list of deinr ony contains letters
            closest = list_no.values[0]

    if on == 'street':
        matches = list_addr[(list_addr.strname == row_streetname)
                            & (addr_locality == row_locality)
                            ].sort_values('deinr')
        if closest_num is True:
            matches = list_addr[(list_addr.strname == row_streetname)
                                & (list_addr.deinr == closest)
                                & (addr_locality == row_locality)
                                ].sort_values('deinr')

            if matches.empty:
                matches = list_addr[(list_addr.strname == row_streetname)
                                    & (list_addr.deinr.str.contains(
                                        '^'+closest+'[a-zA-Z]', regex=True))
                                    & (addr_locality == row_locality)
                                    ].sort_values('deinr')

    elif on == 'building':
        matches = list_addr[(list_addr.strname == row_streetname)
                            & (list_addr.deinr == row.deinr)
                            & (addr_locality == row_locality)]

    try:
        matching_addr = matches.iloc[0]
        e = matching_addr.gkode
        n = matching_addr.gkodn
        egid = matching_addr.egid
    except IndexError:
        e, n, egid = None, None, None

    return e, n, egid


def get_coords(row, regbl, npa, level):

    import pandas as pd
    import numpy as np
    import math

    # print(row['index'])

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
            note_geocoding = 'To remove from the dataset'
            c = 'CASE 1'
        else:
            note_geocoding = 'Geocoded at NPA centroid. No street address.'
            c = 'CASE 2'

    elif pd.isnull(row.deinr):
        # If no street number, geocode at street (exact match or fuzzy match)
        # and geocode at NPA centroid if no correspondance
        try:
            # print('CASE 3')
            e, n, egid = find_matches(
                row, addr, on='street', use_npa=True,
                fuzzy_rue=False, closest_num=False, fuzzy_level=level)
            if egid is None:
                e, n, egid = find_matches(
                    row, addr, on='street', use_npa=False, fuzzy_rue=False,
                    closest_num=False, fuzzy_level=level)
            egid > 0
            note_geocoding = 'Geocoded at street.'
            c = 'CASE 3'

        except TypeError:
            try:
                # print('CASE 4')
                e, n, egid = find_matches(
                    row, addr, on='street', use_npa=True, fuzzy_rue=True,
                    closest_num=False, fuzzy_level=level)
                if egid is None:
                    e, n, egid = find_matches(
                        row, addr, on='street', use_npa=False, fuzzy_rue=True,
                        closest_num=False, fuzzy_level=level)
                egid > 0
                note_geocoding = 'Geocoded at street. Fuzzy matching.'
                c = 'CASE 4'

            except TypeError:
                # print('CASE 5')
                e, n = npa_centroid(row.ville, row.npa, npa)
                egid = np.nan
                if math.isnan(e) | math.isnan(n):
                    note_geocoding = 'To remove from the dataset'
                else:
                    note_geocoding = ('Geocoded at NPA centroid. '
                                      'No street number.')
                c = 'CASE 5'
    else:
        # If we have all informations (street number & street name), geocode
        # at building (perfect match or fuzzy match), ang at closest building
        # in the same street if no correspondance. If you can't find any
        # matching street, geocode at NPA centroid.
        try:
            # print('CASE 6')
            e, n, egid = find_matches(
                row, addr, on='building', use_npa=True, fuzzy_rue=False,
                closest_num=False, fuzzy_level=level)
            if egid is None:
                e, n, egid = find_matches(
                    row, addr, on='building', use_npa=False, fuzzy_rue=False,
                    closest_num=False, fuzzy_level=level)
            egid > 0
            note_geocoding = 'Geocoded at building.'
            c = 'CASE 6'

        except TypeError:
            try:
                # print('CASE 7')
                e, n, egid, label = search_addr_api(
                    str(row.deinr) + ' ' + remove_typo_addr(row.strname)
                    + ' ' + str(row.npa))
                c = 'CASE 7'
                note_geocoding = 'Geocoded at building. Fuzzy API.'

                if label == 'No match found':
                    # print('CASE 8')
                    e, n, egid = find_matches(
                        row, addr, on='building', use_npa=True, fuzzy_rue=True,
                        closest_num=False, fuzzy_level=level)
                    if egid is None:
                        e, n, egid = find_matches(
                            row, addr, on='building', use_npa=False,
                            fuzzy_rue=True, closest_num=False,
                            fuzzy_level=level)
                    note_geocoding = 'Geocoded at building. Fuzzy matching.'
                    c = 'CASE 8'
                egid > 0

            except TypeError:
                try:
                    # print('CASE 9')
                    e, n, egid = find_matches(
                        row, addr, on='street', use_npa=True, fuzzy_rue=False,
                        closest_num=True, fuzzy_level=level)
                    if egid is None:
                        e, n, egid = find_matches(
                            row, addr, on='street', use_npa=False,
                            fuzzy_rue=False, closest_num=True,
                            fuzzy_level=level)
                    egid > 0
                    c = 'CASE 9'
                    note_geocoding = 'Geocoded at street. Closest building.'

                except (ValueError, TypeError):
                    try:
                        # print('CASE 10')
                        e, n, egid = find_matches(
                            row, addr, on='street', use_npa=True,
                            fuzzy_rue=True, closest_num=True,
                            fuzzy_level=level)
                        if egid is None:
                            e, n, egid = find_matches(
                                row, addr, on='street', use_npa=False,
                                fuzzy_rue=True, closest_num=True,
                                fuzzy_level=level)
                        egid > 0
                        c = 'CASE 10'
                        note_geocoding = 'Geocoded at street. Fuzzy matching.'

                    except (ValueError, TypeError):
                        if row.ville == row.npa:
                            # print('CASE 11')
                            e, n, egid = None, None, None
                            note_geocoding = 'To remove from the dataset'
                            c = 'CASE 11'
                        else:
                            # print('CASE 12')
                            e, n = npa_centroid(row.ville, row.npa, npa)
                            egid = None
                            if math.isnan(e) | math.isnan(n):
                                note_geocoding = 'To remove from the dataset'
                            else:
                                note_geocoding = 'Geocoded at NPA centroid.'
                                c = 'CASE 12'

    return e, n, egid, note_geocoding, c


#
#
# # FUNCTION GEOCODING
#
# def get_coords_old(row, regbl, npa, fuzzy_level):
#
#     import re
#     import difflib
#     import pandas as pd
#     import numpy as np
#     import math
#
#     #print(row['index'])
#
#     addr = regbl.copy()
#
#     if not (row.npa in list(addr.dplz4.unique())):
#         addr.dplz4 = addr.gdename
#         row.npa = row.ville
#
#     if pd.isnull(row.strname):
#         e, n = npa_centroid(row.ville, row.npa, npa)
#         egid = np.nan
#         if math.isnan(e) | math.isnan(n):
#             note_geocoding = 'To remove from the dataset'
#             c = 'CASE 1'
#         else:
#             note_geocoding = 'Geocoded at NPA centroid. No street address.'
#             c = 'CASE 2'
#
#     elif pd.isnull(row.deinr):
#         try:
#             matches = addr[(addr.strname == row.strname)
#                            & (addr.dplz4 == row.npa)
#                            ].sort_values('deinr').iloc[0]
#             e, n, egid = matches.gkode, matches.gkodn, matches.egid
#             note_geocoding = 'Geocoded at street.'
#             c = 'CASE 3'
#
#         except IndexError:
#             try:
#                 fuzzy_rue = difflib.get_close_matches(
#                     row.strname,
#                     addr[addr.dplz4 == row.npa].strname,
#                     1, fuzzy_level)[0]
#                 matches = addr[(addr.strname == fuzzy_rue)
#                                & (addr.dplz4 == row.npa)
#                                ].sort_values('deinr').iloc[0]
#                 e, n, egid = matches.gkode, matches.gkodn, matches.egid
#                 note_geocoding = 'Geocoded at street. Fuzzy matching.'
#                 c = 'CASE 4'
#
#             except IndexError:
#                 e, n = npa_centroid(row.ville, row.npa, npa)
#                 egid = np.nan
#                 if math.isnan(e) | math.isnan(n):
#                     note_geocoding = 'To remove from the dataset'
#                     c = 'CASE 5'
#                 else:
#                     note_geocoding = ('Geocoded at NPA centroid. '
#                                       'No street number.')
#                     c = 'CASE 6'
#     else:
#         try:
#             matches = addr[(addr.strname == row.strname)
#                            & (addr.deinr == row.deinr)
#                            & (addr.dplz4 == row.npa)].iloc[0]
#             e, n, egid = matches.gkode, matches.gkodn, matches.egid
#             note_geocoding = 'Geocoded at building.'
#             c = 'CASE 7'
#
#         except IndexError:
#             try:
#                 e, n, egid, label = search_addr_api(
#                     str(row.deinr) + ' ' + remove_typo_addr(row.strname)
#                     + ' ' + str(row.npa))
#                 c = 'CASE 8'
#
#                 if label == 'No match found':
#                     fuzzy_rue = difflib.get_close_matches(
#                         row.strname,
#                         addr[addr.dplz4 == row.npa].strname,
#                         1, fuzzy_level)[0]
#
#                     matches = addr[(addr.strname == fuzzy_rue)
#                                    & (addr.deinr == row.deinr)
#                                    & (addr.dplz4 == row.npa)].iloc[0]
#                     e, n, egid = matches.gkode, matches.gkodn, matches.egid
#                     c = 'CASE 9'
#
#                 note_geocoding = 'Geocoded at building. Fuzzy matching.'
#
#             except IndexError:
#                 try:
#
#                     list_no = addr[
#                         (addr.strname == row.strname)
#                         & (addr.dplz4 == row.npa)
#                         & (~addr.deinr.isna())].deinr.map(
#                              lambda x: float(re.findall('\d+', x)[0]))
#
#                     closest_no = str(min(list_no,
#                                          key=lambda x: abs(x-float(re.findall(
#                                              '\d+', row.deinr)[0]))))
#
#                     if addr[(addr.strname == row.strname)
#                             & (addr.deinr == closest_no)
#                             & (addr.dplz4 == row.npa)].empty:
#                         matches = addr[
#                             (addr.strname == row.strname)
#                             & (addr.deinr.str.contains(
#                                 '^' + closest_no + '[a-zA-Z]', regex=True))
#                             & (addr.dplz4 == row.npa)
#                             ].sort_values('deinr').iloc[0]
#                         c = 'CASE 10'
#
#                     else:
#                         matches = addr[(addr.strname == row.strname)
#                                        & (addr.deinr == closest_no)
#                                        & (addr.dplz4 == row.npa)
#                                        ].sort_values('deinr').iloc[0]
#                         c = 'CASE 11'
#
#                     e, n, egid = matches.gkode, matches.gkodn, matches.egid
#                     note_geocoding = 'Geocoded at street.'
#
#                 except (IndexError, ValueError):
#                     try:
#                         fuzzy_rue = difflib.get_close_matches(
#                             row.strname,
#                             addr[addr.dplz4 == row.npa].strname,
#                             1, fuzzy_level)[0]
#
#                         list_no = addr[
#                             (addr.strname == fuzzy_rue)
#                             & (addr.dplz4 == row.npa)
#                             & (~addr.deinr.isna())].deinr.map(
#                                 lambda x: int(re.findall('\d+', x)[0]))
#
#                         closest_no = str(
#                             min(list_no, key=lambda x:
#                                 abs(x-float(re.findall('\d+', row.deinr)[0]))))
#
#                         if addr[(addr.strname == fuzzy_rue)
#                                 & (addr.deinr == closest_no)
#                                 & (addr.dplz4 == row.npa)].empty:
#
#                             matches = addr[
#                                 (addr.strname == fuzzy_rue)
#                                 & (addr.deinr.str.contains(
#                                     '^'+closest_no+'[a-zA-Z]', regex=True))
#                                 & (addr.dplz4 == row.npa)
#                                 ].sort_values('deinr').iloc[0]
#                             c = 'CASE 12'
#
#                         else:
#                             matches = addr[(addr.strname == fuzzy_rue)
#                                            & (addr.deinr == closest_no)
#                                            & (addr.dplz4 == row.npa)
#                                            ].sort_values('deinr').iloc[0]
#                             c = 'CASE 13'
#
#                         e, n, egid = matches.gkode, matches.gkodn, matches.egid
#                         note_geocoding = 'Geocoded at street. Fuzzy matching.'
#
#                     except IndexError:
#
#                         if row.ville == row.npa:
#                             e, n, egid = np.nan
#                             note_geocoding = 'To remove from the dataset'
#                             c = 'CASE 14'
#
#                         else:
#                             e, n = npa_centroid(row.ville, row.npa, npa)
#                             egid = np.nan
#                             if math.isnan(e) | math.isnan(n):
#                                 note_geocoding = 'To remove from the dataset'
#                             else:
#                                 note_geocoding = 'Geocoded at NPA centroid.'
#                             c = 'CASE 15'
#
#     return e, n, egid, note_geocoding, c


def remove_typo_addr(strname):

    stopwords = ['CHEMIN', 'RUE', 'AVENUE', 'ROUTE', 'RUELLE', 'CH.',
                 'AV.', 'RTE']
    querywords = strname.split()
    resultwords = [word for word in querywords if word not in stopwords]
    result = ' '.join(resultwords)

    return result


def search_addr_api(searchText):

    import requests
    import time

    time.sleep(0.1)
    request = ("https://api3.geo.admin.ch/rest/services/api/SearchServer?"
               "layer=ch.bfs.gebaeude_wohnungs_register"
               "&searchText=" + searchText +
               "&type=locations"
               "&origins=address,zipcode"
               "&sr=2056")
    response = requests.get(request)

    try:
        res = response.json()['results'][0]
        e = res['attrs']['y']
        n = res['attrs']['x']
        egid = int(res['attrs']['featureId'].split('_')[0])
        label = res['attrs']['label']

    except IndexError:
        if response.status_code == 200:
            e, n, egid = None, None, None
            label = 'No match found'
        else:
            e, n, egid = None, None, None
            label = 'Error code' + str(response.status_code)

    return e, n, egid, label


def find_institutions(row, institutions):
    import difflib

    try:
        res = institutions.loc[
            (institutions.nom == row.strname)
            & (institutions.npa == row.npa), 'nom'].values[0]
        note = 'Good match'

    except Exception:
        try:
            res = difflib.get_close_matches(
                row.strname,
                institutions[institutions.npa == row.npa].nom, 1, 0.5)[0]
            note = 'Fuzzy match npa'

        except Exception:
            try:
                list_instit = institutions[institutions.localite == row.ville]
                list_instit['full_info'] = list_instit.nom + list_instit.note
                res_full = difflib.get_close_matches(
                    row.strname,
                    list_instit.full_info,
                    1, 0.5)[0]
                res = list_instit.loc[list_instit.full_info == res_full,
                                      'nom'].values[0]
                note = 'Fuzzy match npa bis'

            except Exception:
                try:
                    res = difflib.get_close_matches(
                        row.strname,
                        institutions[institutions.localite == row.ville].nom,
                        1, 0.6)[0]
                    note = 'Fuzzy match loc'

                except Exception:
                    res = 'NAN'
                    note = 'No match'

    return res, note


# FIND IF ADDRESSES CORRESPONDS TO INSTITUTIONS
def check_if_institution(row, institutions):
    import difflib
    import numpy as np

    try:
        nom_institution = institutions.loc[
            (institutions.rue == row.strname)
            & (institutions.numero == row.deinr)
            & (institutions.npa == row.npa), 'nom'].values[0]
    except Exception:
        try:
            fuzzy_rue = difflib.get_close_matches(
                row.strname,
                institutions[institutions.npa == row.npa].rue,
                1, 0.8)[0]
            nom_institution = institutions.loc[
                (institutions.rue == fuzzy_rue)
                & (institutions.numero == row.deinr)
                & (institutions.npa == row.npa), 'nom'].values[0]
        except Exception:
            try:
                fuzzy_rue = difflib.get_close_matches(
                    row.strname,
                    institutions[institutions.localite == row.ville].rue,
                    1, 0.8)[0]
                nom_institution = institutions.loc[
                    (institutions.rue == fuzzy_rue)
                    & (institutions.numero == row.deinr)
                    & (institutions.localite == row.ville), 'nom'].values[0]
            except Exception:
                nom_institution = np.nan

    return nom_institution


def geocode_institution(row, cursor):
    '''Function to retrieve coordinates from the table institutions_medicosociales
    (GEOSAN DB)'''
    try:
        cursor.execute(("SELECT ST_X(geometry), ST_Y(geometry), npa, localite "
                        "FROM institutions_medicosociales WHERE nom='{}'")
                       .format(row.institution_nom.replace("'", "''")))
        res = cursor.fetchall()
    except Exception:
        raise Exception("Sorry, institution must be into the database")

    if len(res) == 1:
        gkode = res[0][0]
        gkodn = res[0][1]

    elif len(res) > 1:

        try:
            item = [i for i in res if i[2] == row.npa]
            gkode = item[0][0]
            gkodn = item[0][1]
        except Exception:
            item = [i for i in res if i[3] == row.ville]
            gkode = item[0][0]
            gkodn = item[0][1]

    else:
        raise Exception("An error occured")

    return gkode, gkodn


def remove_subset(dataset, subset_to_remove, subset_label, initial_size,
                  df_for_stats=None):
    '''
    This function removes a specific subset (=subset_to_remove) from the
    dataset. It also displays the number, and the percentage rounded to two
    decimal places, of the affected rows. The "subset_label" argument allows
    you to specify a label that will be used when printing (e.g. 'tests without
    address'). If the rows in the "dataset" do not represent individuals but
    distinct addresses, you can use the "df_for_stats" argument to calculate
    statistics on the number of individuals instead of the number of addresses.
    The function returns a copy of the original dataset, from which
    we have removed the rows present in the subset.
    '''

    if df_for_stats is None:
        nb = subset_to_remove.shape[0]
        perc = round((nb*100)/dataset.shape[0], 2)
    else:
        indivs = subset_to_remove.merge(df_for_stats,
                                        on=['rue', 'npa', 'ville'],
                                        how='inner')
        nb = indivs.shape[0]
        perc = round((nb*100)/initial_size, 2)

    print('Number of ', subset_label, ': ', nb, ' (', perc, '%)')

    try:
        dataset.drop(subset_to_remove.index, axis=0, inplace=True)
        print('Rows were removed from the dataset')
        print()
    except Exception:
        raise Exception('Subset could not be removed from the dataset.')

    return dataset


def find_egid(row, addr):

    import difflib
    import numpy as np

    try:
        egid = addr[
            (addr.strname == row.strname)
            & (addr.deinr == row.deinr)
            & (addr.dplz4 == row.npa)].egid.values[0]
        note = 'Direct match.'
    except Exception:
        try:
            fuzzy_rue = difflib.get_close_matches(
                row.strname, addr[addr.dplz4 == row.npa].strname, 1, 0.5)[0]
            # print(fuzzy_rue)
            egid = addr[
                (addr.strname == fuzzy_rue)
                & (addr.deinr == row.deinr)
                & (addr.dplz4 == row.npa)].egid.values[0]
            note = 'Fuzzy matching.'
        except Exception:
            egid = np.nan
            note = 'No match found.'

    return egid, note
