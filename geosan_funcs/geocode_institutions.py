'''This code contains several functions that are useful while geocoding health data possibly within medicosocial institutions'''


# FIND IF THE ADDRESS IS AN INSTITUTION'S NAME
def find_institutions(row, institutions):

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


# FIND IF ADDRESSES CORRESPONDS TO AN INSTITUTION'S ADDRESS
def check_if_institution(row, institutions):

    try:
        nom_institution = institutions.loc[
            (institutions.rue == row.match_strname)
            & (institutions.numero == row.match_deinr)
            & (institutions.npa == row.npa), 'nom'].values[0]
    except Exception:
        try:
            fuzzy_rue = difflib.get_close_matches(
                row.match_strname,
                institutions[institutions.npa == row.npa].rue,
                1, 0.9)[0]
            nom_institution = institutions.loc[
                (institutions.rue == fuzzy_rue)
                & (institutions.numero == row.match_deinr)
                & (institutions.npa == row.npa), 'nom'].values[0]
        except Exception:
            try:
                fuzzy_rue = difflib.get_close_matches(
                    row.match_strname,
                    institutions[institutions.localite == row.ville].rue,
                    1, 0.9)[0]
                nom_institution = institutions.loc[
                    (institutions.rue == fuzzy_rue)
                    & (institutions.numero == row.match_deinr)
                    & (institutions.localite == row.ville), 'nom'].values[0]
            except Exception:
                nom_institution = np.nan

    return nom_institution


# RETRIEVE COORDINATES FOR A GIVEN INSTITUTION
def geocode_institution(row, cursor):
    '''Function to retrieve coordinates from the table institutions_medicosociales
    (GEOSAN DB)'''
    try:
        cursor.execute(("SELECT ST_X(geometry), ST_Y(geometry),"
                        "npa, localite, rue, numero "
                        "FROM institutions_medicosociales WHERE nom='{}'")
                       .format(row.institution_nom.replace("'", "''")))
        res = cursor.fetchall()
    except Exception:
        raise Exception("Sorry, institution must be into the database")

    if len(res) == 1:
        gkode = res[0][0]
        gkodn = res[0][1]
        strname = res[0][4]
        deinr = res[0][5]

    elif len(res) > 1:

        try:
            item = [i for i in res if i[2] == row.npa]
            gkode = item[0][0]
            gkodn = item[0][1]
            strname = item[0][4]
            deinr = item[0][5]

        except Exception:
            item = [i for i in res if i[3] == row.ville]
            gkode = item[0][0]
            gkodn = item[0][1]
            strname = item[0][4]
            deinr = item[0][5]

    else:
        raise Exception("An error occured")

    if not deinr:
        strname_deinr = strname
    else:
        strname_deinr = strname + " " + deinr

    return gkode, gkodn, strname_deinr
