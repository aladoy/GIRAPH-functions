#!/bin/sh

DATABASE='geosan'
USERNAME='aladoy'
HOSTNAME='localhost'

psql -h $HOSTNAME -U $USERNAME $DATABASE << EOF

DROP MATERIALIZED VIEW IF EXISTS vd_canton;
DROP MATERIALIZED VIEW IF EXISTS vd_mun;
DROP MATERIALIZED VIEW IF EXISTS vd_reli_point;
DROP MATERIALIZED VIEW IF EXISTS vd_reli_centroid;
DROP MATERIALIZED VIEW IF EXISTS vd_reli_polygon;
DROP MATERIALIZED VIEW IF EXISTS lausanne_region_mun;
DROP MATERIALIZED VIEW IF EXISTS vd_mgis_ha;
DROP MATERIALIZED VIEW IF EXISTS vd_mgis_mun;
DROP MATERIALIZED VIEW IF EXISTS lausanne_reli_polygon;


CREATE MATERIALIZED VIEW vd_canton
AS
SELECT * FROM cantons WHERE name='Vaud';


CREATE MATERIALIZED VIEW vd_mun
AS
SELECT * FROM municipalities WHERE kantonsnum='CH22000000';


CREATE MATERIALIZED VIEW vd_reli_point
AS
SELECT r.* FROM reli_point r, cantons c WHERE c.name='Vaud' AND st_intersects(r.geometry, c.geometry);


CREATE MATERIALIZED VIEW vd_reli_centroid
AS
SELECT r.* FROM reli_centroid r, vd_reli_point v WHERE v.reli=r.reli;


CREATE MATERIALIZED VIEW vd_reli_polygon
AS
SELECT r.* FROM reli_polygon r, vd_reli_point v WHERE v.reli=r.reli;


CREATE MATERIALIZED VIEW lausanne_region_mun
AS
SELECT * FROM municipalities WHERE name IN ('Belmont-sur-Lausanne', 'Lutry', 'Jorat-Mézières', 'Montpreveyres', 'Paudex', 'Pully', 'Bottens', 'Bretigny-sur-Morrens', 'Cheseaux-sur-Lausanne', 'Cugy (VD)', 'Froideville', 'Jouxtens-Mézery', 'Lausanne', 'Epalinges', 'Le Mont-sur-Lausanne', 'Morrens (VD)', 'Prilly', 'Romanel-sur-Lausanne', 'Bussigny', 'Chavannes-près-Renens', 'Crissier', 'Ecublens (VD)', 'Prilly', 'Renens (VD)', 'Saint-Sulpice (VD)', 'Villars-Sainte-Croix', 'Savigny', 'Servion')
AND icc='CH';


CREATE MATERIALIZED VIEW vd_mgis_ha
AS
SELECT * FROM microgis_ha WHERE kt_21=22;


CREATE MATERIALIZED VIEW vd_mgis_mun
AS
SELECT * FROM microgis_mun where ktacro='VD';


CREATE MATERIALIZED VIEW lausanne_reli_polygon
AS
SELECT r.reli, r.geometry FROM vd_reli_polygon r, 
(SELECT ST_Union(geometry) as geometry FROM lausanne_sectors) laus 
WHERE ST_Intersects(r.geometry, laus.geometry);


EOF

