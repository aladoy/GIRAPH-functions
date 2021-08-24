#db_utils.py

#CONNECT TO DB
def connect_db(db,user):

    import getpass
    from sqlalchemy import create_engine
    import psycopg2 as ps

    try:
        pw=getpass.getpass() #Ask for user password
        engine=create_engine("postgresql+psycopg2://{}:{}@localhost/{}".format(user,pw,db)) #Create SQLAlchemy engine
        conn=ps.connect("dbname='{}' user='{}' host='localhost' password='{}'".format(db,user,pw)) #Create a connection object
        cursor=conn.cursor() #Create a cursor object
        print('Sucessfully connected to '+db.upper()+' DB')
    except:
        print('Error while connecting to DB')

    return engine, conn, cursor



#FUNCTION TO IMPORT DATA (SPATIAL OR NO) INTO DB
def import_data(db, user, dat, name, pk, schema=None, idx_geom=False):

    from sqlalchemy import create_engine
    import psycopg2 as ps
    import geopandas as gpd

    engine, conn, cursor=connect_db(db,user)

    print(dat.shape)
    dat.columns=map(str.lower,dat.columns) #convert columns to lower case

    if isinstance(dat, gpd.GeoDataFrame):
        print('Geometry Type :' + dat.geometry.geom_type.unique()[0])
        print('CRS :' + str(dat.crs))
        dat.to_postgis(name, engine, schema=schema, if_exists='replace') #Add to postgis

    else:
        dat.to_sql(name, engine, schema=schema, if_exists='replace',index=False) #Add to postgres

    conn.commit()

    if schema==None:
        table_name=name
    else:
        table_name=schema+'.'+name

    cursor.execute("SELECT COUNT(*) FROM {}".format(table_name))
    print("Number of rows in the table :", cursor.fetchone())
    cursor.execute("SELECT COUNT(*) FROM information_schema.columns where table_name='{}'".format(table_name))
    print("Number of columns in the table :", cursor.fetchall())
    if pk!='NULL':
        cursor.execute("ALTER TABLE {} ADD PRIMARY KEY({});".format(table_name,pk)) #Add PK
        conn.commit()
        print('!!PAY ATTENTION, DATA ARE REORDERED ACCORDING TO PRIMARY KEY!!')
    if idx_geom==True:
        cursor.execute("CREATE INDEX idx_geom_{} ON {} USING GIST(geometry);".format(name, table_name)) #Add geometry index
        conn.commit()
    print('TABLE ', name, ' WAS SUCESSFULLY IMPORTED')

    conn.close()
