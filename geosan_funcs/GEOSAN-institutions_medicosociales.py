#LIBRARIES
#Basic
import pandas as pd
import os
import subprocess
import sys
import numpy as np
#Spatial
import geopandas as gpd
from geoalchemy2 import Geometry, WKTElement
from shapely import wkt
from shapely.geometry import Point
import shapely.speedups

# Import functions from GIRAPH-functions repository
sys.path.append(r'/mnt/data/GEOSAN/FUNCTIONS/GIRAPH-functions/')
try:
    import geocoding_utils as g
    import db_utils as db
except FileNotFoundError:
    print("Wrong file or file path")

#############
#IMPORT DATA#
#############

path=r"/mnt/data/GEOSAN/GEOSAN DB/data/INSTITUTIONS MEDICO-SOCIALES 2020/"

#URGENCES
urgences=gpd.read_file(path+"MN95_SSP_TPR_URGENCE.shp")
urgences.dtypes
urgences=urgences[['GROUPE','VOIE','NUMERO','NPA','LOCALITE','geometry']]
urgences.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','geometry']
urgences['NOTE']=np.nan
urgences['TYPE']='URGENCE'

#PERMANENCES DENTAIRES
dentaire=gpd.read_file(path+"MN95_SSP_TPR_PERM_DENTAIRE.shp")
dentaire.dtypes
dentaire=dentaire[['GROUPE','VOIE','NUMERO','NPA','LOCALITE','geometry']]
dentaire.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','geometry']
dentaire['NOTE']=np.nan
dentaire['TYPE']='PERMANENCE DENTAIRE'

#SOINS AIGUS (CLINIQUES, HOPITAUX, HOPITAUX PSYCHIATRIQUES)
soinsaigus=gpd.read_file(path+"MN95_SSP_TPR_SOINS_AIGUS.shp")
soinsaigus.dtypes
soinsaigus=soinsaigus[['NOM','VOIE','NUMERO','NPA','LOCALITE','TYPE','geometry']]
soinsaigus.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','NOTE','geometry']
soinsaigus['TYPE']='SOINS AIGUS'

#CENTRES MÉDICO-SOCIAUX
cms=gpd.read_file(path+"MN95_SSP_TPR_CMS.shp")
cms.dtypes
cms=cms[['NOM','VOIE','NUMERO','NPA','LOCALITE','EXPLOITANT','geometry']]
cms.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','NOTE','geometry']
cms['TYPE']='CMS'

#ORGANISATIONS PRIVÉES DE SOINS À DOMICILE
osad=gpd.read_file(path+"MN95_SSP_TPR_OSAD.shp")
osad.dtypes
osad=osad[['NOM','VOIE','NUMERO','NPA','LOCALITE','geometry']]
osad.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','geometry']
osad['NOTE']=np.nan
osad['TYPE']='OSAD'

#HOMES NON MÉDICALISÉS
hnm=gpd.read_file(path+"MN95_SSP_TPR_HNM.shp")
hnm.dtypes
hnm=hnm[['NOM','VOIE','NUMERO','NPA','LOCALITE','EXPLOITANT','geometry']]
hnm.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','NOTE','geometry']
hnm['TYPE']='HNM'

#PHARMACIES
pharmacies=gpd.read_file(path+"MN95_SSP_TPR_PHARMACIE.shp")
pharmacies.dtypes
pharmacies=pharmacies[['NOM','VOIE','NUMERO','NPA','LOCALITE','EXPLOITANT','geometry']]
pharmacies.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','NOTE','geometry']
pharmacies['TYPE']='PHARMACIE'

#ESPACES DE PRÉVENTION
prevention=gpd.read_file(path+"MN95_SSP_TPR_ESPACE_PREVENTION.shp")
prevention.dtypes
prevention=prevention[['NOM','VOIE','NUMERO','NPA','LOCALITE','geometry']]
prevention.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','geometry']
prevention['NOTE']=np.nan
prevention['TYPE']='ESPACE PREVENTION'

#BUREAUX D'INFORMATION ET D'ORIENTATION
brios=gpd.read_file(path+"MN95_SSP_TPR_BRIOS.shp")
brios.dtypes
brios=brios[['NOM','VOIE','NUMERO','NPA','LOCALITE','geometry']]
brios.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','geometry']
brios['NOTE']=np.nan
brios['TYPE']='BRIOS'

#CENTRES MÉMOIRE
memoire=gpd.read_file(path+"MN95_SSP_TPR_CENTRE_MEMOIRE.shp")
memoire.dtypes
memoire=memoire[['NOM','VOIE','NUMERO','NPA','LOCALITE','geometry']]
memoire.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','geometry']
memoire['NOTE']=np.nan
memoire['TYPE']='CENTRE MEMOIRE'

#AGENCES D'ASSURANCES SOCIALES
aas=gpd.read_file(path+"MN95_SSP_TPR_AAS.shp")
aas.dtypes
aas=aas[['NOM','VOIE','NUMERO','NPA','LOCALITE','geometry']]
aas.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','geometry']
aas['NOTE']=np.nan
aas['TYPE']='AAS'

#CENTRES SOCIAUX RÉGIONAUX
csr=gpd.read_file(path+"MN95_SSP_TPR_CSR.shp")
csr.dtypes
csr=csr[['NOM','VOIE','NUMERO','NPA','LOCALITE','geometry']]
csr.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','geometry']
csr['NOTE']=np.nan
csr['TYPE']='CSR'

#STRUCTURES D'ACCOMPAGNEMENT MÉDICO-SOCIALES
sams=gpd.read_file(path+"MN95_SSP_TPR_SAMS.shp")
sams.dtypes
sams['NOTE']=sams['TYPE']+','+sams['EXPLOITANT']
sams=sams[['NOM','VOIE','NUMERO','NPA','LOCALITE','NOTE','geometry']]
sams.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','NOTE','geometry']
sams['TYPE']='SAMS'

#SITES D'AMBULANCES
ambulance=gpd.read_file(path+"MN95_SSP_TPR_AMBULANCE.shp")
ambulance.dtypes
ambulance=ambulance[['NOM','VOIE','NUMERO','NPA','LOCALITE','TYPE','geometry']]
ambulance.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','NOTE','geometry']
ambulance['TYPE']='AMBULANCE'

#ÉTABLISSEMENTS PSYCHO-SOCIAUX MÉDICALISÉS
epsm=gpd.read_file(path+"MN95_SSP_TPR_EPSM.shp")
epsm.dtypes
epsm=epsm[['NOM','RUE','NUMERO','NPA','LOCALITE','EXPLOITANT','geometry']]
epsm.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','NOTE','geometry']
epsm['TYPE']='EPSM'

#ÉTABLISSEMENTS SOCIO-ÉDUCATIFS
ese=gpd.read_file(path+"MN95_SSP_TPR_ESE.shp")
ese.dtypes
ese=ese[['NOM','VOIE','NUMERO','NPA','LOCALITE','EXPLOITANT','geometry']]
ese.columns=['NOM','RUE','NUMERO','NPA','LOCALITE','NOTE','geometry']
ese['TYPE']='ESE'

#Concatenate dataframes
institutions = pd.concat([urgences, dentaire, soinsaigus, cms, osad, hnm, pharmacies, prevention, brios, memoire, aas, csr, sams, ambulance, epsm, ese], axis=0)
institutions.reset_index(inplace=True, drop=True)


################
#DATA WRANGLING#
################

#Convert NPA to integer
institutions['NPA']=institutions.NPA.map(int)

#Convert all in upper case + remove accents
institutions['NOM']=institutions.NOM.map(g.strip_accents).map(str.upper)
institutions['RUE']=institutions.RUE.map(g.strip_accents).map(str.upper)
institutions['LOCALITE']=institutions.LOCALITE.map(g.strip_accents).map(str.upper)
institutions.loc[~institutions.NOTE.isna(),'NOTE']=institutions.loc[~institutions.NOTE.isna(),'NOTE'].map(g.strip_accents).map(str.upper)

#Drop index
institutions.reset_index(drop=False,inplace=True)


##################
#ADD TO GEOSAN DB#
##################

db.import_data('geosan','aladoy',institutions,'institutions_medicosociales','index',idx_geom=True)


####################
#FILL WITH NEW DATA#
####################

new_institutions=[
['P.A. FOYER EVAM','(UI)','EVAM',2118472],
['P.A. FOYER EVAM','(UI)','EVAM',280100842],
['P.A. FOYER EVAM','(UI)','EVAM',781202],
['P.A. FOYER EVAM','(UI)','EVAM',849048],
['P.A. FOYER EVAM','(UI)','EVAM',837277],
['P.A. FOYER EVAM','(UI)','EVAM',781417],
['P.A. FOYER EVAM','(UI)','EVAM',886938],
['P.A. FOYER EVAM','(UI)','EVAM',2118704],
['P.A. FOYER EVAM','(UI)','EVAM',887659],
['P.A. FOYER EVAM','(UI)','EVAM',851754],
['P.A. FOYER EVAM','(UI)','EVAM',3162384],
['P.A. FOYER EVAM','(UI)','EVAM',9031306],
['P.A. FOYER EVAM','(UI)','EVAM',845507],
['SCTP','(UI)','SCTP',2119195],
['SCTP','(UI)','SCTP',840334],
['SCTP','(UI)','SCTP',400001368],
['EMS BOIS-GENTIL','(UI)','SAMS',280073909],
['FOYER BOIS-GENTIL','(UI)','EPSM',887728],
['RESIDENCE LES NOVALLES','(UI)','SAMS',786932],
['RESIDENCE LES TREMIERES','(UI)','SAMS',887683],
['EMS LA ROZAVERE','(UI)','SAMS',887656],
["EMS L'ORIEL",'(UI)','SAMS',787749],
["EMS MEILLERIE",'(UI)','SAMS',887678],
["LES PALMIERS / LE PARASOL",'(UI)','SAMS',280058094],
["EMS CLAIR-SOLEIL",'(UI)','SAMS',3163177],
["EMS LE HOME / LES PINS - SITE LE HOME",'(UI)','SAMS',786573],
["EMS LE HOME / LES PINS - SITE LES PINS",'(UI)','SAMS',887641],
["LES OLIVIERS",'(UI) SITE PONTAISE','EPSM',887719],
["LES BERGES DU LEMAN","(UI)","EPSM",841211],
["ASSOCIATION SAINTE FAMILLE","(UI)","ESE",280091714],
["FOYER DE COUR","(UI) FONDATION LA RAMBARDE","ESE",886377],
["AEME MONTELLY","(UI) FONDATION JEUNESSE ET FAMILLES","ESE",887789],
["LA ROSE DES VENTS","(UI) FONDATION DEO GRATIAS","ESE",880405],
["EMS LA FONTANELLE","(UI)","SAMS",841142],
["EMS PRE-FLEURI","(UI)","SAMS",280091860],
["LA CIGALE","(UI)","ESE",881092],
["SERIX","(UI)","ESE",822030],
["RÉSIDENCE O TALENT","(UI)","SAMS",280098514],
["FONDATION LOUIS BOISSONNET","(UI)","SAMS",887636],
["EMS LE PAVILLON","(UI)","SAMS",1770293],
["RIVE-NEUVE","(UI) FONDATION RIVE-NEUVE","SAMS",280074885],
["FONDATION LES CHATEAUX","(UI)","SAMS",868276],
["FOND-VERT","(UI)","SAMS",828560],
["FONDATION SILO","(UI)","SAMS",796203],
["RESIDENCE LA GOTTAZ","(UI) TERTIANUM","SAMS",9020584],
["L'EAUDINE","(UI) TERTIANUM","SAMS",9031062],
["JOLI AUTOMNE","(UI) TERTIANUM","SAMS",796593],
["BEL-HORIZON","(UI) TERTIANUM","SAMS",3163360],
["LE PACIFIC","(UI) TERTIANUM","SAMS",280054181],
["EMS LES JARDINS DU LEMAN","(UI) GHOL","SAMS",280078440],
["EMS LES ARCADES","(UI) GROUPE ODYSSE","SAMS",791784],
["EMS ODYSSE","(UI) GROUPE ODYSSE","SAMS",791785],
["EMS CHANTEMERLE","(UI) GROUPE ODYSSE","SAMS",887648],
["PRE DE LA TOUR","(UI) FONDATION PRE PARISET","SAMS",3102002],
["EMS HAUTE COMBE","(UI) FONDATION PRE PARISET","SAMS",786574],
["EPSM LES TILLEULS","(UI) GROUPE ALTAGE","EPSM",805580],
["EMS LES JARDINS DE LA PLAINE","(UI) GROUPE ALTAGE","SAMS",846442],
["EMS PARC DE VALENCY",'(UI) GROUPE ALTAGE','SAMS',887765],
["EMS LA CHOCOLATIERE",'(UI) GROUPE ALTAGE','SAMS',9020439],
["EMS L'ESCAPADE",'(UI) GROUPE ALTAGE','SAMS',9019388],
["EPSM LA SYLVABELLE",'(UI) GROUPE ALTAGE','SAMS',817886],
["PENSION LA TRAVERSE",'(UI) GROUPE ALTAGE','SAMS',870774],
["LES PRES",'(UI) GROUPE ALTAGE','SAMS',280079834],
["L'ECHAPPEE",'(UI) GROUPE ALTAGE','SAMS',884186],
["EMS COTTIER-BOYS",'(UI)','SAMS',864922],
["EMS LES LYS",'(UI) FONDATION PRIMEROCHE','SAMS',3101929],
["EMS LE GRAND PRE",'(UI) FONDATION PRIMEROCHE','SAMS',280077179],
["EMS LA ROSIERE-SOERENSEN",'(UI) SITE DE SOERENSEN','SAMS',859380],
["EMS LA ROSIERE-SOERENSEN",'(UI) SITE DE LA ROSIERE','SAMS',859384],
["EMS LES BOVERESSES",'(UI)','SAMS',881192],
["RESIDENCE LE BYRON",'(UI)','SAMS',856933],
["LES HIRONDELLES",'(UI) FONDATION CLAIRE MAGNIN','SAMS',835192],
["DOMAINE DE LA GRACIEUSE",'(UI)','SAMS',797828],
["RESIDENCE NOVA VITA",'(UI)','SAMS',9031051],
["EMS CHATEAU DE LA RIVE",'(UI)','SAMS',791786],
["EMS LES LAURELLES",'(UI)','SAMS',836606],
["EMS LE PETIT BOIS",'(UI)','SAMS',808637],
["RESIDENCE CLOS BERCHER",'(UI)','SAMS',867049],
["LES PERGOLAS",'(UI) FONDATION CLAIRE MAGNIN','SAMS',788512],
["EMS MONTCHOISI",'(UI) GROUPE SAPHIR','SAMS',280102380],
["EMS LA VENOGE",'(UI)','SAMS',865353],
["EMS SILO",'(UI)','SAMS',280127822],
["EMS LA CLEF DES CHAMPS",'(UI)','SAMS',829086],
["EMS LE CHENE",'(UI)','SAMS',280100852],
["FONDATION ABS / LE PASSAGE",'(UI)','CAT',882327],
["EMS LA VERNIE",'(UI) FONDATION PRIMEROSE','SAMS',280060899],
["EMS JOLI-BOIS",'(UI) FONDATION PRIMEROSE','SAMS',837269],
["EMS L'ARBRE DE VIE",'(UI)','SAMS',280096261],
["LA FEUILLERE",'(UI) FONDATION LA FEUILLERE','ESE',782678],
["FOYER DE CHAILLY",'(UI) FONDATION LA POMMERAIE','ESE',887651],
["FOYER LA POMMERAIE",'(UI) FONDATION LA POMMERAIE','ESE',797635],
["EMS BEAU-SITE",'(UI) FONDATION BEAU-SITE','SAMS',835553],
["EMS MONTBRILLANT",'(UI) FONDATION BEAU-SITE','SAMS',835632],
["FOYER VALVERT",'(UI) FONDATION LA RAMBARDE','ESE',786576],
["FOYER CARREFOUR-ECHALLENS",'(UI) FONDATION LA RAMBARDE','ESE',887761],
["FOYER DE MEILLERIE",'(UI) FONDATION LA RAMBARDE','ESE',2119116],
["FOYER APAC",'(UI) FONDATION LA RAMBARDE','ESE',300000781],
["EMS LE FLON",'(UI) FONDATION DU RELAIS','SAMS',821722],
["EMS BURIER",'(UI) FONDATION MAISON DE RETRAITE DE BURIER','SAMS',280001703],
["EMS PRAZ-SECHAUD I",'(UI) HOME-AGE SA','SAMS',881229]
]

#Create dataframe
new_institutions=pd.DataFrame(new_institutions,columns=['nom','note','type','egid'])

#CONNECT TO GEOSAN DB
engine,conn,cursor=db.connect_db('geosan','aladoy')

#Find info (rue, numero, etc.) from regbl
def regbl_info(egid):
    cursor.execute('SELECT strname,deinr,dplz4,gdename,gkode,gkodn FROM regbl_2021 WHERE egid={}'.format(egid))
    res=cursor.fetchone()
    return res[0],res[1],res[2],res[3],res[4],res[5]

new_institutions['rue'],new_institutions['numero'],new_institutions['npa'],new_institutions['localite'],new_institutions['gkode'],new_institutions['gkodn']=zip(*new_institutions.egid.map(regbl_info))

#Convert to geodataframe
new_institutions=new_institutions.assign(geometry=new_institutions.apply(lambda row: Point(row.gkode, row.gkodn),axis=1))
new_institutions=gpd.GeoDataFrame(new_institutions, geometry=new_institutions.geometry, crs="EPSG:2056")

#Find max index in DB
cursor.execute("SELECT max(index) FROM institutions_medicosociales")
max_id=cursor.fetchone()[0]

#Change index in new_institutions
new_institutions['index']=new_institutions.index+max_id+1

#Reorder columns to match other institutions
new_institutions=new_institutions[['index','nom','rue','numero','npa','localite','geometry','note','type']]

#Append to GEOSAN DB
new_institutions.to_postgis('institutions_medicosociales', engine,if_exists='append')

#CLOSE CONNECTION WITH GEOSAN DB
conn.close()
