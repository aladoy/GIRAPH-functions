#!/bin/sh

DATABASE='geosan'
USERNAME='aladoy'
HOSTNAME='localhost'

psql -h $HOSTNAME -U $USERNAME $DATABASE << EOF

DROP MATERIALIZED VIEW IF EXISTS vd_canton;

CREATE MATERIALIZED VIEW vd_canton
AS
SELECT * FROM cantons WHERE name='Vaud';


DROP MATERIALIZED VIEW IF EXISTS vd_mun;

CREATE MATERIALIZED VIEW vd_mun
AS
SELECT * FROM municipalities WHERE kantonsnum='CH22270000';


DROP MATERIALIZED VIEW IF EXISTS vd_reli_point;

CREATE MATERIALIZED VIEW vd_reli_point
AS
SELECT r.* FROM reli_point r, cantons c WHERE c.name='Vaud' AND st_intersects(r.geometry, c.geometry);


DROP MATERIALIZED VIEW IF EXISTS vd_reli_centroid;

CREATE MATERIALIZED VIEW vd_reli_centroid
AS
SELECT r.* FROM reli_centroid r, vd_reli_point v WHERE v.reli=r.reli;


DROP MATERIALIZED VIEW IF EXISTS vd_reli_polygon;

CREATE MATERIALIZED VIEW vd_reli_polygon
AS
SELECT r.* FROM reli_polygon r, vd_reli_point v WHERE v.reli=r.reli;


DROP MATERIALIZED VIEW IF EXISTS lausanne_region_mun;

CREATE MATERIALIZED VIEW lausanne_region_mun
AS
SELECT * FROM municipalities WHERE name IN ('Belmont-sur-Lausanne', 'Lutry', 'Jorat-Mézières', 'Montpreveyres', 'Paudex', 'Pully', 'Bottens', 'Bretigny-sur-Morrens', 'Cheseaux-sur-Lausanne', 'Cugy (VD)', 'Froideville', 'Jouxtens-Mézery', 'Lausanne', 'Epalinges', 'Le Mont-sur-Lausanne', 'Morrens (VD)', 'Prilly', 'Romanel-sur-Lausanne', 'Bussigny', 'Chavannes-près-Renens', 'Crissier', 'Ecublens (VD)', 'Prilly', 'Renens (VD)', 'Saint-Sulpice (VD)', 'Villars-Sainte-Croix', 'Savigny', 'Servion')
AND icc='CH';


DROP MATERIALIZED VIEW IF EXISTS vd_mgis_ha;

CREATE MATERIALIZED VIEW vd_mgis_ha
AS
SELECT * FROM microgis_ha WHERE kt_21=22;


DROP MATERIALIZED VIEW IF EXISTS vd_mgis_mun;

CREATE MATERIALIZED VIEW vd_mgis_mun
AS
SELECT * FROM microgis_mun where ktacro='VD'


EOF

