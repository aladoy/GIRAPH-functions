#!/bin/sh

DATABASE='geosan'
USERNAME='aladoy'
HOSTNAME='localhost'

psql -h $HOSTNAME -U $USERNAME $DATABASE << EOF

CREATE MATERIALIZED VIEW vd_canton
AS
SELECT * FROM cantons WHERE name='Vaud';


CREATE MATERIALIZED VIEW IF NOT EXISTS vd_mun
AS
SELECT * FROM municipalities WHERE canton_num=22;


CREATE MATERIALIZED VIEW IF NOT EXISTS vd_reli_point
AS
SELECT r.* FROM reli_point r, cantons c WHERE c.name='Vaud' AND st_intersects(r.geometry, c.geometry);


CREATE MATERIALIZED VIEW IF NOT EXISTS vd_reli_centroid
AS
SELECT r.* FROM reli_centroid r, vd_reli_point v WHERE v.reli=r.reli;


CREATE MATERIALIZED VIEW IF NOT EXISTS vd_reli_polygon
AS
SELECT r.* FROM reli_polygon r, vd_reli_point v WHERE v.reli=r.reli;


CREATE MATERIALIZED VIEW IF NOT EXISTS palm_municipalities
AS
SELECT * FROM municipalities WHERE name IN ('Belmont-sur-Lausanne', 'Lutry', 'Paudex', 'Pully', 'Boussens', 'Bretigny-sur-Morrens', 'Cheseaux-sur-Lausanne', 'Cugy', 'Froideville', 'Jouxtens-Mézery', 'Lausanne', 'Epalinges', 'Le Mont-sur-Lausanne', 'Morrens', 'Prilly', 'Romanel-sur-Lausanne', 'Sullens', 'Bussigny', 'Chavannes-près-Renens', 'Crissier', 'Ecublens', 'Prilly', 'Renens (VD)', 'St-Sulpice', 'Villars-Ste-Croix');


CREATE MATERIALIZED VIEW IF NOT EXISTS vd_mgis_ha
AS
SELECT * FROM microgis_ha WHERE kt_21=22;


CREATE MATERIALIZED VIEW IF NOT EXISTS vd_mgis_mun
AS
SELECT * FROM microgis_mun where ktacro='VD'


EOF

