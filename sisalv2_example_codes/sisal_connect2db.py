# -*- coding: utf-8 -*-
"""
Created on Thu Jan 25 14:20:07 2018

@author: akamolphat

Make sure to download and install the python connector first (make sure it's the right python version as well)
https://dev.mysql.com/downloads/connector/python/
This can also be found in the MySQL Installer (which you may already have on your computer when installing MySQL)

This is an example file for just connection between the database and python
This code just query the database and write this to an excel file

"""
# ************************************************************************ #
#                                                                          #
#              EXAMPLE CODES FOR LINKING MySQL to Python                   #
#                                                                          #
# This file is provided as part of the documentation for SISAL version 2  #
#    									   #
# Codes only tested with Python 2.7                                        # 
#                                                                          #

# IMPORT MODULES REQUIRED #################################################
# NOTE that these modules must be installed first 
import MySQLdb
import pandas as pd

# 1. CONNECT TO THE DATEBASE ##############################################
# This assumes that the database has been imported under the name 'sisalv1'
# and is on the local computer (host = 'localhost'), the password as 'password'
# and the user is 'root'
cnx = MySQLdb.connect(user='root', 
                      passwd='password', 
                      host='localhost',
                      db='sisalv2',use_unicode=True, charset="utf8")

cursor = cnx.cursor()

# 2. QUERY THE DATABASE  ##################################################
# ORIGINAL STYLE
# IF YOU ARE READING INTO A TABLE, SEE NEXT POINT #########################
query = ("""SELECT site.*, count(*) as entity_count FROM site LEFT JOIN entity USING (site_id) GROUP BY (site_id);""")
cursor.execute(query)
tb_data = cursor.fetchall() # This reads the table into a tuple (pretty much a list of list) but does not read the header
tb_colnames = [i[0] for i in cursor.description] # reads in column names and convert to a list
# CONVERT TO A PANDAS DATAFRAME #
tb = pd.DataFrame.from_records(data = list(tb_data), columns = tb_colnames)

# Query the database into pandas table ####################################
# MUCH EASIER TO DEAL WITH
tb = pd.read_sql(("""SELECT site.*, count(*) as entity_count FROM site LEFT JOIN entity USING (site_id) GROUP BY (site_id);"""), cnx)

# 2.a. Extract the information needed for age modelling ###################
# This is only done entity_id = 1 as an example
# dating information table (with hiatuses)
dating_tb = pd.read_sql("""SELECT * FROM dating WHERE entity_id = 1;""", cnx) 
# sample depth/isotope table (with hiatuses)
sample_tb = pd.read_sql("""SELECT * FROM sample LEFT JOIN hiatus USING (sample_id) LEFT JOIN d13C USING (sample_id) LEFT JOIN d18O USING (sample_id) WHERE entity_id = 1""", cnx)


# WRITE TABLEs INTO EXCEL #################################################
writer = pd.ExcelWriter('Age_model_entity_1.xlsx')
dating_tb.to_excel(writer,'dating information table', index = False)
sample_tb.to_excel(writer,'sample table', index = False)
writer.save()

# 2.b. Extract citations and DOI for each entity in the database ###########
# execute to change the max concat length for this particular session
cursor.execute('SET SESSION group_concat_max_len = 100000;')
tot_ref = pd.read_sql(("""select entity.entity_id, site.site_name as "Site name", 
site.elevation as "Elevation", 
site.latitude as "Latitude", 
site.longitude as "Longitude", 
entity.entity_name as "Entity name", 
group_concat(reference.citation ORDER BY reference.citation SEPARATOR ' ; ') as "Citations", 
group_concat(reference.citation ORDER BY reference.citation SEPARATOR ' ; ') as "Refs", 
group_concat(reference.publication_DOI ORDER BY reference.citation SEPARATOR ' ; ') as "publication DOI"  from site JOIN entity USING(site_id) 
JOIN entity_link_reference USING(entity_id) JOIN reference USING(ref_id) GROUP BY entity_id;"""), cnx)

# 2.c. Extract sites with entity counts ####################################
tot_site = pd.read_sql("SELECT site.*, count(*) as entity_count FROM site LEFT JOIN entity USING (site_id) WHERE entity_status = 'current' GROUP BY (site_id);", cnx)

# 2.d. Extract entities from an area and report their age range ############
# 35 < latitude < 90, and -20 < longitude < 40
tot_entity = pd.read_sql("SELECT site.site_name, latitude, longitude, entity.*, MAX(interp_age) as max_interp_age, MIN(interp_age) as min_interp_age FROM site LEFT JOIN entity USING (site_id) LEFT JOIN sample USING (entity_id) LEFT JOIN original_chronology USING (sample_id) WHERE latitude > 35 AND latitude < 90 AND longitude > -20 and longitude < 40 GROUP BY entity_id, site_name, latitude, longitude;", cnx)

# 2.e. Extract entities from a certain age range ###########################
# Extract entities with data from the Holocene period (< 12000 BP(1950))
Holocene_entity = pd.read_sql("SELECT site.site_name, latitude, longitude, entity.* FROM site LEFT JOIN entity USING (site_id) LEFT JOIN sample USING (entity_id) LEFT JOIN original_chronology USING (sample_id) WHERE interp_age < 12000 GROUP BY entity_id, site_name, latitude, longitude;", cnx)

# No plots were demonstrated here as python was not used to generate any figures
# This could be done using other modules such as matplotlib, etc.

# close connection to the MySQL database ##################################
cnx.close()
