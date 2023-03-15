# db_utils.py

import getpass
from sqlalchemy import create_engine
import psycopg2 as ps
import geopandas as gpd
import geoalchemy2


# CONNECT TO DB
def connect_db(db, user):

    try:
        pw = getpass.getpass()  # Ask for user password
        engine = create_engine(
            "postgresql+psycopg2://{}:{}@localhost/{}".format(user, pw, db)
        )  # Create SQLAlchemy engine
        conn = ps.connect(
            "dbname='{}' user='{}' host='localhost' password='{}'".format(db, user, pw)
        )  # Create a connection object
        cursor = conn.cursor()  # Create a cursor object
        print("Sucessfully connected to " + db.upper() + " DB")
    except:
        print("Error while connecting to DB")

    return engine, conn, cursor


# FUNCTION TO IMPORT DATA (SPATIAL OR NO) INTO DB
def import_data(
    db, user, dat, name, pk, schema="public", idx_geom=False, ifexists="replace"
):

    engine, conn, cursor = connect_db(db, user)

    # drop table cascade if "replace" option
    if ifexists == "replace":

        try:

            cursor.execute(
                "select table_name from information_schema.tables where table_name = '{}' UNION select matviewname from pg_matviews where matviewname = '{}';".format(
                    name, name
                )
            )
            cursor.fetchone()[0]

            cursor.execute("DROP TABLE {}.{} CASCADE;".format(schema, name))
            print("DROP TABLE")
            conn.commit()

        except TypeError:

            pass

    print(dat.shape)
    dat.columns = map(str.lower, dat.columns)  # convert columns to lower case

    if isinstance(dat, gpd.GeoDataFrame):
        print("Geometry Type :" + dat.geometry.geom_type.unique()[0])
        print("CRS :" + str(dat.crs))
        dat.to_postgis(
            name, engine, schema=schema, if_exists=ifexists
        )  # Add to postgis

    else:
        dat.to_sql(
            name, engine, schema=schema, if_exists=ifexists, index=False
        )  # Add to postgres

    conn.commit()

    if schema == None:
        table_name = name
    else:
        table_name = schema + "." + name

    cursor.execute("SELECT COUNT(*) FROM {}".format(table_name))
    print("Number of rows in the table :", cursor.fetchone())
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.columns where table_name='{}'".format(
            table_name
        )
    )
    print("Number of columns in the table :", cursor.fetchall())
    if pk != "NULL":
        cursor.execute(
            "ALTER TABLE {} ADD PRIMARY KEY({});".format(table_name, pk)
        )  # Add PK
        conn.commit()
        print("!!PAY ATTENTION, DATA ARE REORDERED ACCORDING TO PRIMARY KEY!!")
    if idx_geom == True:
        cursor.execute(
            "CREATE INDEX idx_geom_{} ON {} USING GIST(geometry);".format(
                name, table_name
            )
        )  # Add geometry index
        conn.commit()
    print("TABLE ", name, " WAS SUCESSFULLY IMPORTED")

    conn.close()


def insert_attribute(db, user, table_name, attr_name, attr_type, pk, data):

    """
    db: database name
    user: username
    table_name: name of the table to modify
    attr_name: name of the attribute to add
    attr_type: type of the attribute to add (integer, text, etc.)
    pk: primary key
    data: dataframe having at least two attributes (one with the attriute to add, one with the primary key)
    """

    engine, conn, cursor = connect_db(db, user)

    try:
        cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {attr_name};")
        conn.commit()
    except:
        conn.rollback()

    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {attr_name} {attr_type};")
    conn.commit()

    for i, value in enumerate(data[attr_name]):

        val = data.loc[i, pk]

        cursor.execute(
            f"UPDATE {table_name} SET {attr_name} = '{value}' WHERE {pk} = {val}"
        )

    conn.commit()

    cursor.execute(f"SELECT * FROM {table_name} WHERE {attr_name} IS NULL")
    print(
        "Check that everything was correctly inserted into DB: "
        + str(len(cursor.fetchall()) == 0)
    )

    conn.close()
