#geocoding_utils.py

#FUNCTION TO REMOVE ACCENTS ON STRING
def strip_accents(text):
    import unicodedata

    try:
        text = unicode(text, 'utf-8')
    except NameError: # unicode is a default on python 3
        pass
    text = unicodedata.normalize('NFD', text)\
           .encode('ascii', 'ignore')\
           .decode("utf-8")
    return str(text)


#FUNCTION TO EXTRACT THE STREET NUMBER / STREET NAME FROM AN ADDRESS
    #The algorithm splits with Regex the address field when the first digit appears.
    #Thus, Chemin de Montelly 1 -> ['Chemin de Montelly','1'] and Avenue de Morges 9b -> ['Avenue de Morges','9b']
    #Addresses that are not in the standard format (e.g. 24, grande rue) will not be catched however, but the proportion is small
    #If there is no digit (e.g. EMS de l'Ours) or if the address is not in a standard format (see above), the split will return only one element (i.e. the entire address)
    #In this case, the algorithm will return a NaN value.
    #On the other hand, the algorithnm will return the 2nd part of the split (i.e. street number)
def split_address(x):

    import numpy as np
    import re

    try:

        #Address in the form: 20 avenue longchamps
        if x[0].isdigit():

            split=re.split("(\d+).*?\s+(.+)",x)
            split_len=len(split)

            #With this pattern, the first and last element of the list are empty, that's why the index are shifted
            deinr=split[1]
            strname=' '.join(split[2:split_len-1])

        #Address in the form: Avenue longchamps 20
        else:
            split=re.split("(?<=[a-zA-Z-zÀ-ÿ])\\s*(?=[0-9])",x)
            split_len=len(split)

            if split_len==1:
                deinr=np.nan
                strname=x
            else:
                deinr=split[split_len-1]
                strname=' '.join(split[0:split_len-1])

    except:

        deinr=np.nan
        strname=x

    return deinr,strname



#FUNCTION TO PREPARE REGBL FOR GEOCODING
def regbl_wrangling(regbl_dat):

    #Remove missing addresses
    print('Number of missing addresses: ',regbl_dat[regbl_dat.strname.isna()].shape[0],'(',round(regbl_dat[regbl_dat.strname.isna()].shape[0]*100/regbl_dat.shape[0],2),'%)')
    regbl_dat=regbl_dat[~regbl_dat.strname.isna()]
    print('Missing addresses were removed from the dataset.')

    #Remove accents
    regbl_dat['strname']=regbl_dat.strname.map(strip_accents)
    regbl_dat['gdename']=regbl_dat.gdename.map(strip_accents)

    #Convert street and municipality into upper case
    regbl_dat['strname']=regbl_dat.strname.map(str.upper)
    regbl_dat['gdename']=regbl_dat.gdename.map(str.upper)

    #Select only essential columns
    regbl_dat=regbl_dat[['egid','strname','deinr','dplz4','gdename','gkode','gkodn']]
    return regbl_dat


#Function to return centroids of the npa
def npa_centroid(ville,cp):

    import pandas as pd

    #Import NPA
    npa=pd.read_csv(r'Vaccination mobile @ DGS/data/NPA 2021/PLZO_CSV_LV95.csv', delimiter=';',encoding='iso-8859-1')
    #Remove accents in municipalities
    npa['Ortschaftsname']=npa.Ortschaftsname.map(strip_accents)
    #Convert municipalities to upper case
    npa['Ortschaftsname']=npa.Ortschaftsname.map(str.upper)

    try: #match with name + PLZ
        e=npa[(npa.Ortschaftsname==ville) & (npa.PLZ==cp)].E.values[0]
        n=npa[(npa.Ortschaftsname==ville) & (npa.PLZ==cp)].N.values[0]
    except: #take the first PLZ of the list (reason: no match with the name)
        e=npa[npa.PLZ==cp].E.values[0]
        n=npa[npa.PLZ==cp].N.values[0]
    return e,n


def get_coords(row,regbl):

    import re
    import difflib
    import pandas as pd
    import numpy as np

    addr=regbl.copy()

    if (row.npa in list(addr.dplz4.unique()))==False:
        addr.dplz4=addr.gdename
        row.npa=row.ville

    if pd.isnull(row.strname):
        e,n=npa_centroid(row.ville,row.npa)
        note_geocoding='Geocoded at NPA centroid. No street address.'

    elif pd.isnull(row.deinr):
        try:
            e=addr[(addr.strname==row.strname) & (addr.dplz4==row.npa)].gkode.values[0]
            n=addr[(addr.strname==row.strname) & (addr.dplz4==row.npa)].gkodn.values[0]
            note_geocoding='Geocoded at street.'
        except:
            try:
                fuzzy_rue=difflib.get_close_matches(row.strname, addr[addr.dplz4==row.npa].strname,1,0.5)[0]
                #print(fuzzy_rue)
                e=addr[(addr.strname==fuzzy_rue) & (addr.dplz4==row.npa)].gkode.values[0]
                n=addr[(addr.strname==fuzzy_rue) & (addr.dplz4==row.npa)].gkodn.values[0]
                note_geocoding='Geocoded at street. Fuzzy matching.'
            except:
                e,n=npa_centroid(row.ville,row.npa)
                note_geocoding='Geocoded at NPA centroid. No street number.'
    else:
        try:
            e=addr[(addr.strname==row.strname) & (addr.deinr==row.deinr) & (addr.dplz4==row.npa)].gkode.values[0]
            n=addr[(addr.strname==row.strname) & (addr.deinr==row.deinr) & (addr.dplz4==row.npa)].gkodn.values[0]
            note_geocoding='Geocoded at building.'
        except:
            try:
                fuzzy_rue=difflib.get_close_matches(row.strname, addr[addr.dplz4==row.npa].strname,1,0.5)[0]
                e=addr[(addr.strname==fuzzy_rue) & (addr.deinr==row.deinr) & (addr.dplz4==row.npa)].gkode.values[0]
                n=addr[(addr.strname==fuzzy_rue) & (addr.deinr==row.deinr) & (addr.dplz4==row.npa)].gkodn.values[0]
                note_geocoding='Geocoded at building. Fuzzy matching.'
            except:
                try:
                    list_no=addr[(addr.strname==row.strname) & (addr.dplz4==row.npa) & (~addr.deinr.isna())].deinr.map(lambda x: int(re.findall('\d+',x)[0]))
                    closest_no=str(min(list_no, key=lambda x:abs(x-int(re.findall('\d+', row.deinr)[0]))))

                    if addr[(addr.strname==row.strname) & (addr.deinr==closest_no) & (addr.dplz4==row.npa)].empty:
                        e=addr[(addr.strname==row.strname) & (addr.deinr.str.contains('^'+closest_no+'[a-zA-Z]',regex=True)) & (addr.dplz4==row.npa)].gkode.values[0]
                        n=addr[(addr.strname==row.strname) & (addr.deinr.str.contains('^'+closest_no+'[a-zA-Z]',regex=True)) & (addr.dplz4==row.npa)].gkodn.values[0]
                    else:
                        e=addr[(addr.strname==row.strname) & (addr.deinr==closest_no) & (addr.dplz4==row.npa)].gkode.values[0]
                        n=addr[(addr.strname==row.strname) & (addr.deinr==closest_no) & (addr.dplz4==row.npa)].gkodn.values[0]
                    note_geocoding='Geocoded at street.'

                except:
                    try:
                        fuzzy_rue=difflib.get_close_matches(row.strname, addr[addr.dplz4==row.npa].strname,1,0.5)[0]
                        list_no=addr[(addr.strname==fuzzy_rue) & (addr.dplz4==row.npa) & (~addr.deinr.isna())].deinr.map(lambda x: int(re.findall('\d+',x)[0]))
                        closest_no=str(min(list_no, key=lambda x:abs(x-int(re.findall('\d+', row.deinr)[0]))))

                        if addr[(addr.strname==fuzzy_rue) & (addr.deinr==closest_no) & (addr.dplz4==row.npa)].empty:
                            e=addr[(addr.strname==fuzzy_rue) & (addr.deinr.str.contains('^'+closest_no+'[a-zA-Z]',regex=True)) & (addr.dplz4==row.npa)].gkode.values[0]
                            n=addr[(addr.strname==fuzzy_rue) & (addr.deinr.str.contains('^'+closest_no+'[a-zA-Z]',regex=True)) & (addr.dplz4==row.npa)].gkodn.values[0]
                        else:
                            e=addr[(addr.strname==fuzzy_rue) & (addr.deinr==closest_no) & (addr.dplz4==row.npa)].gkode.values[0]
                            n=addr[(addr.strname==fuzzy_rue) & (addr.deinr==closest_no) & (addr.dplz4==row.npa)].gkodn.values[0]
                        note_geocoding='Geocoded at street. Fuzzy matching.'

                    except:

                        if row.ville==row.npa:
                            e=np.nan
                            n=np.nan
                            note_geocoding='To remove from the dataset'

                        else:
                            e,n=npa_centroid(row.ville,row.npa)
                            note_geocoding='Geocoded at NPA centroid.'

    return e,n,note_geocoding


def find_egid(row,addr):

    import re
    import difflib
    import pandas as pd
    import numpy as np

    try:
        egid=addr[(addr.strname==row.strname) & (addr.deinr==row.deinr) & (addr.dplz4==row.npa)].egid.values[0]
        note='Direct match.'
    except:
        try:
            fuzzy_rue=difflib.get_close_matches(row.strname, addr[addr.dplz4==row.npa].strname,1,0.5)[0]
            #print(fuzzy_rue)
            egid=addr[(addr.strname==fuzzy_rue) & (addr.deinr==row.deinr) & (addr.dplz4==row.npa)].egid.values[0]
            note='Fuzzy matching.'
        except:
            egid=np.nan
            note='No match found.'

    return egid, note
