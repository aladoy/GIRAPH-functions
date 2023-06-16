#!/bin/sh

DATABASE='geosan'
USERNAME='aladoy'
HOSTNAME='localhost'

psql -h $HOSTNAME -U $USERNAME $DATABASE << EOF

DROP MATERIALIZED VIEW IF EXISTS vd_canton CASCADE;
DROP MATERIALIZED VIEW IF EXISTS vd_mun CASCADE;
DROP MATERIALIZED VIEW IF EXISTS vd_reli_point CASCADE;
DROP MATERIALIZED VIEW IF EXISTS vd_reli_centroid CASCADE;
DROP MATERIALIZED VIEW IF EXISTS vd_reli_polygon CASCADE;
DROP MATERIALIZED VIEW IF EXISTS vd_lakes CASCADE;
DROP MATERIALIZED VIEW IF EXISTS vd_roads CASCADE;
DROP MATERIALIZED VIEW IF EXISTS vd_buildings CASCADE;
DROP MATERIALIZED VIEW IF EXISTS lausanne_region_mun CASCADE;
DROP MATERIALIZED VIEW IF EXISTS vd_mgis_ha CASCADE;
DROP MATERIALIZED VIEW IF EXISTS vd_mgis_mun CASCADE;
DROP MATERIALIZED VIEW IF EXISTS lausanne_reli_polygon CASCADE;


CREATE MATERIALIZED VIEW vd_mun
AS
SELECT * FROM municipalities WHERE kantonsnum='CH22000000' AND name NOT LIKE 'Lac %';


CREATE MATERIALIZED VIEW vd_canton
AS
SELECT ST_Union(geometry) as geometry FROM vd_mun WHERE name NOT LIKE 'Lac %';


CREATE MATERIALIZED VIEW vd_reli_point
AS
SELECT r.* FROM reli_point r, cantons c WHERE c.name='Vaud' AND st_intersects(r.geometry, c.geometry);


CREATE MATERIALIZED VIEW vd_reli_centroid
AS
SELECT r.* FROM reli_centroid r, vd_reli_point v WHERE v.reli=r.reli;


CREATE MATERIALIZED VIEW vd_reli_polygon
AS
SELECT r.* FROM reli_polygon r, vd_reli_point v WHERE v.reli=r.reli;


CREATE MATERIALIZED VIEW vd_lakes
AS
SELECT * FROM lakes WHERE ST_INTERSECTS(geometry, SELECT ST_UNION(geometry) as geometry FROM cantons WHERE name='Vaud');


CREATE MATERIALIZED VIEW vd_roads
AS
SELECT r.objectid, r.edgelevel, r.objval, ST_INTERSECTION(r.geometry, c.geometry) as geometry FROM roads r, vd_canton c;


CREATE MATERIALIZED VIEW vd_buildings
AS
SELECT * FROM buildings WHERE ST_INTERSECTS(geometry, (SELECT ST_UNION(geometry) as geometry FROM cantons WHERE name='Vaud'));


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

