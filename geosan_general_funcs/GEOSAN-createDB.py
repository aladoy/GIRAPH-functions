#LIBRARIES
#Basic
import pandas as pd
import os
import subprocess
#Database
import getpass
from sqlalchemy import create_engine
import psycopg2 as ps

#CREATE DB
#establishing the connection
pw=getpass.getpass()
conn = ps.connect(database="postgres", user='postgres', password=pw, host='127.0.0.1', port= '5432')
conn.autocommit = True
#Creating a cursor object using the cursor() method
cursor = conn.cursor()
try:
  cursor.execute('CREATE database geosan')
  cursor.execute('GRANT ALL PRIVILEGES ON DATABASE geosan TO aladoy')
except:
  print("Database already exists")
#Closing the connection
conn.close()

#CONNECT TO DB
pw=getpass.getpass() #Ask for user password
engine=create_engine("postgresql+psycopg2://aladoy:{}@localhost/geosan".format(pw)) #Create SQLAlchemy engine
conn=ps.connect("dbname='geosan' user='aladoy' host='localhost' password='{}'".format(pw)) #Create a connection object
cursor=conn.cursor() #Create a cursor object
try:
    cursor.execute('CREATE EXTENSION postgis;') #Add postgis extension to make the db spatial
    conn.commit()
except:
    print("Postgis is already included")
#Close the connection
conn.close()
