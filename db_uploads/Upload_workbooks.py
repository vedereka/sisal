# -*- coding: utf-8 -*-
"""
Created on Tue Dec 06 15:31:38 2016

@author: Kamolphat Atsawawaranunt

Tested on Python 2.7.15+ and Python 3.6.8

process:
    1. connect to database
    2. import data from xlsx
    3. check whether site exists on database
    3.a. if exist grab site_id
    3.b. if not exist import site into database, grab assigned site_id and proceed without checking
    4. place site_id on entity sheet/table
    5. check whether entity exists on database
    5.a. if exist grab entity_id
    5.a.1. if site/entity exists, gives warning and allow input from database manager before proceeding
    'entity exists on database, please check that the samples had not already been inputted into the database"
    'press y to proceed with input of sample data, if not, press any key to exit'
    5.b. if not exist import entity into database and grab assigned entity_id
    6. place entity_id on sample sheet/table
    7. import sample sheet
    8. move xlsx file into a folder (i.e. a folder called 'import complete')
    9. move onto next xlsx file
    
    

"""

#==============================================================================
# import the required modules
#==============================================================================
#import MySQLdb # Not compatible with Python 3
import mysql.connector
import sys, os, shutil
import numpy as np
import pandas as pd
# need to import module for import of xlsx file

input_file = sys.argv[1]
mysql_username = sys.argv[2] # "root"
mysql_password = sys.argv[3] # "password"
mysql_host = sys.argv[4] # "localhost"
mysql_dbname = sys.argv[5] # "sisalv2

if len(sys.argv) < 6:
    sys.exit('Five argument (path to workbook) is required')
elif len(sys.argv) > 6:
    sys.exit('Too many arguments supplied, only five arguments are accepted: path_to_workbook mysql_username mysql_password mysql_host mysql_dbname')

# Define table inputs
def tb_input(input_table, db_table, AI_ID = False):
    query = ("SHOW COLUMNS FROM %s;" %(db_table))
    cursor.execute(query)
    field_names = [j[0] for j in cursor.fetchall()]
    # create list of all columns from sample
    # sample_entry_field_names = list(field_names)
    field_names = list(set(field_names).intersection(list(input_table.columns.values)))
    if AI_ID is not False:
        field_names.remove(AI_ID)
    f_name = ", ".join(field_names)
    tb_subset = input_table[field_names]
    if tb_subset.shape[0] > 0:
        y = tb_subset.values.tolist()
        ls_ls = []
        for i in y:
            ls = [str(j) for j in i]
            ls_ls.append(ls) 
        str_ls = str(ls_ls)
        str_ls = str_ls.replace('\\t', " ")
        str_ls = str_ls.replace('], [', '), (')
        str_ls = str_ls.replace('[[', '(')
        str_ls = str_ls.replace(']]', ')')
        str_ls = str_ls.replace("'nan'", 'NULL')
        query = ("""INSERT INTO %s (%s) VALUES %s;"""
                 %(db_table, f_name, str_ls))
        #print(query)
        cursor.execute(query)

def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

#==============================================================================
# connect to MySQL SISAL database
#==============================================================================
cnx = mysql.connector.connect(user=mysql_username, 
                      passwd=mysql_password, 
                      host=mysql_host,
                      db=mysql_dbname,use_unicode=True, charset="utf8")
cnx.autocommit = False

cursor = cnx.cursor(buffered = True)
cursor.autocommit = False
# read in excel file
# Warning counter, used to count the number of warnings. If no warnings, file is automatically moved to "Checked" folder
warning_ctr = 0
# Read in Workbook
try:
    xl = pd.ExcelFile(input_file)
    sht_nm = xl.sheet_names
except:
    print('Cannot read in excel file')
    warning_ctr += 1
# create a list of spreadsheet namse containing "Sample data" 
# This is because some workbooks may contain more than one spreadsheet for sample data
sample_ls = [k for k in sht_nm if 'Sample data' in k]
# Read in spreadsheets from the workbook
# needs to skip first row
# column title starts at row number 2/ index = 1
try:
    site_tb = xl.parse(sheet_name = 'Site metadata', skiprows = 1).dropna(how = 'all')
except:
    print('Cannot read in Site metadata spreadsheet, likely no spreadsheet called "Site metadata"')
    warning_ctr += 1
try:
    entity_tb = xl.parse(sheet_name = 'Entity metadata', skiprows = 1).dropna(how = 'all')
except:
    print('Cannot read in Enitity metadata spreadsheet, likely no spreadsheet called "Entity metadata"')
    warning_ctr += 1
try:
    ref_tb = xl.parse(sheet_name = 'References', skiprows = 1).dropna(how = 'all')
except:
    print('Cannot read in References spreadsheet, likely no spreadsheet called "References"')
    warning_ctr += 1
try:
    dating_tb = xl.parse(sheet_name = 'Dating information', skiprows = 1).dropna(how = 'all')
except:
    print('Cannot read in Dating information spreadsheet, likely no spreadsheet called "Dating information"')
    warning_ctr += 1
# if only one spreadsheet for sample data, read in normally
# or else append the spreadsheets one after the other
# problem is error catching will not be able to pin point rows
if len(sample_ls) == 1:
    try:
        sample_tb = xl.parse(sheet_name = 'Sample data', skiprows = 1).dropna(how = 'all')
    except:
        print('Cannot read in sample data spreadsheet, likley no spreadsheet called "Sample data"')
        warning_ctr += 1
elif len(sample_ls) == 0:
    print('Sample data spreadsheet does not exist')
    warning_ctr += 1
else:
    print('More than one sample data spreadsheet exist. Spreadsheets will be appended')
    sample_tb = pd.DataFrame()
    for i in sample_ls:
        sp_tb = xl.parse(sheet_name = i, skiprows = 1).dropna(how = 'all')
        sample_tb = sample_tb.append(sp_tb, ignore_index = True)
try:
    dating_lamina_tb = xl.parse(sheet_name = 'Lamina age vs depth', skiprows = 1).dropna(how = 'all')
except:
    print('Cannot read in Lamina age vs depth spreadsheet, likely no spreadsheet called "Lamina age vs depth"')
    warning_ctr += 1
    
# Convert all the modern_reference to string
sample_tb.modern_reference = sample_tb.modern_reference.replace(np.nan, '', regex = True)
dating_lamina_tb.modern_reference = dating_lamina_tb.modern_reference.replace(np.nan, '', regex = True)
dating_tb.modern_reference = dating_tb.modern_reference.replace(np.nan, '', regex = True)

if warning_ctr < 1:
    print('Correct interp_age to BP(1950)')
    try:
        sample_tb.loc[sample_tb['modern_reference'] == 'b2k','interp_age'] = sample_tb.loc[sample_tb['modern_reference'] == 'b2k','interp_age'] - 50
        sample_tb.loc[sample_tb['modern_reference'] == 'CE/BCE','interp_age'] = 1950 - sample_tb.loc[sample_tb['modern_reference'] == 'CE/BCE','interp_age']
        sample_tb.loc[sample_tb['modern_reference'] == 'b2k','modern_reference'] = 'BP (1950)'
        sample_tb.loc[sample_tb['modern_reference'] == 'CE/BCE','modern_reference'] = 'BP (1950)'
        if sample_tb.loc[sample_tb['modern_reference'] == 'Year of chemistry',:].shape[0] > 0:
            for i in set(entity_tb['entity_name']):
                print(i)
                if sample_tb.loc[(sample_tb['entity_name'] == i) & (sample_tb['modern_reference'] == 'Year of chemistry'),:].shape[0] > 0:
                    chem_year = sorted(set(dating_tb.loc[(dating_tb['entity_name'] == i) & (dating_tb['modern_reference'] == 'Year of chemistry'), 'chem_year']))[-1]
                    sample_tb.loc[(sample_tb['modern_reference'] == 'Year of chemistry') & (sample_tb['entity_name'] == i),'interp_age'] = sample_tb.loc[(sample_tb['modern_reference'] == 'Year of chemistry') & (sample_tb['entity_name'] == i),'interp_age'] - (chem_year - 1950)
                    sample_tb.loc[(sample_tb['modern_reference'] == 'Year of chemistry') & (sample_tb['entity_name'] == i),'modern_reference'] = 'BP (1950)'
                else:
                    print('entity %d does not have year of chemistry as modern reference')
    except:
        print('Error with correcting for interp_age to BP(1950)')
        warning_ctr += 1
        raise
else:
    print('Warnings have been issued during reading of the workbooks')
    exit()

if warning_ctr < 1:
    print('Correct lam_age to BP(1950)')
    if dating_lamina_tb.shape[0] > 0:
        try:
            dating_lamina_tb.loc[dating_lamina_tb['modern_reference'] == 'b2k','lam_age'] = dating_lamina_tb.loc[dating_lamina_tb['modern_reference'] == 'b2k','lam_age'] - 50
            dating_lamina_tb.loc[dating_lamina_tb['modern_reference'] == 'CE/BCE','lam_age'] = 1950 - dating_lamina_tb.loc[dating_lamina_tb['modern_reference'] == 'CE/BCE','lam_age']
            dating_lamina_tb.loc[dating_lamina_tb['modern_reference'] == 'b2k','modern_reference'] = 'BP (1950)'
            dating_lamina_tb.loc[dating_lamina_tb['modern_reference'] == 'CE/BCE','modern_reference'] = 'BP (1950)'
            if dating_lamina_tb.loc[dating_lamina_tb['modern_reference'] == 'Year of chemistry',:].shape[0] > 0:
                for i in set(entity_tb['entity_name']):
                    print(i)
                    if dating_lamina_tb.loc[(dating_lamina_tb['entity_name'] == i) & (dating_lamina_tb['modern_reference'] == 'Year of chemistry'),:].shape[0] > 0:
                        chem_year = sorted(set(dating_tb.loc[(dating_tb['entity_name'] == i) & (dating_tb['modern_reference'] == 'Year of chemistry'), 'chem_year']))[-1]
                        dating_lamina_tb.loc[(dating_lamina_tb['modern_reference'] == 'Year of chemistry') & (dating_lamina_tb['entity_name'] == i),'lam_age'] = dating_lamina_tb.loc[(dating_lamina_tb['modern_reference'] == 'Year of chemistry') & (dating_lamina_tb['entity_name'] == i),'lam_age'] - (chem_year - 1950)
                        dating_lamina_tb.loc[(dating_lamina_tb['modern_reference'] == 'Year of chemistry') & (dating_lamina_tb['entity_name'] == i),'modern_reference'] = 'BP (1950)'
                    else:
                        print('entity %d does not have year of chemistry as modern reference')
        except:
            print('Error with correcting for lam_age to BP(1950)')
            warning_ctr += 1
            raise
else:
    print('Warnings have been issued during reading of the workbooks')
    exit()    

if warning_ctr < 1:
    print('Correct corr_age to BP(1950)')
    try:
        dating_tb.loc[dating_tb['modern_reference'] == 'b2k','corr_age'] = dating_tb.loc[dating_tb['modern_reference'] == 'b2k','corr_age'] - 50
        dating_tb.loc[dating_tb['modern_reference'] == 'CE/BCE','corr_age'] = 1950 - dating_tb.loc[dating_tb['modern_reference'] == 'CE/BCE','corr_age']
        dating_tb.loc[dating_tb['modern_reference'] == 'Year of chemistry','corr_age'] = dating_tb.loc[dating_tb['modern_reference'] == 'Year of chemistry','corr_age'] - (dating_tb.loc[dating_tb['modern_reference'] == 'Year of chemistry','chem_year'] - 1950)
        dating_tb.loc[dating_tb['modern_reference'] == 'b2k','modern_reference'] = 'BP (1950)'
        dating_tb.loc[dating_tb['modern_reference'] == 'CE/BCE','modern_reference'] = 'BP (1950)'
        dating_tb.loc[dating_tb['modern_reference'] == 'Year of chemistry','modern_reference'] = 'BP (1950)'
    except:
        print('Error with correcting for corr_age to BP(1950)')
        warning_ctr += 1
        raise
else:
    print('Warnings have been issued during correction of interp_age and lam_age')
    
# Check for repeated sites
# Enter site into database if no repeats were found
# If database has more than one site with the same site_name
# longitude and latitude, inform user
Site_exists = False
if warning_ctr < 1:
    print('Perform import of sites into database')
    query = ("""ALTER TABLE %s auto_increment = 1;""" %('site'))
    cursor.execute(query)
    try:
        for i in site_tb.index:
            query = (""" SELECT site_id FROM site where site_name = "%s" and latitude = %.4f and longitude = %.4f""" %(site_tb['site_name'][i], site_tb['latitude'][i], site_tb['longitude'][i]))
            cursor.execute(query)
            x = cursor.rowcount
            if int(x) == 1:
                print("Site already exists, Site data will not be imported")
                last_site_id = int(cursor.fetchone()[0])
                Site_exists = True
                print("Site id = %d" %last_site_id)
            elif int(x) > 1:
                print("More than one site exists with the same site_name, latitude and longitude, please check database for possible repeated entries")
                warning_ctr += 1
            else:
                print("Import new site into database")
                query = ("""INSERT INTO site (site_name, latitude, longitude, elevation, geology, rock_age, monitoring) VALUES ("%s", %.4f, %.4f, %.2f, '%s', '%s', '%s');""" 
                %(site_tb['site_name'][i],
                  site_tb['latitude'][i],
                  site_tb['longitude'][i],
                  site_tb['elevation'][i],
                  site_tb['geology'][i],
                  site_tb['rock_age'][i],
                  site_tb['monitoring'][i]))
                query = query.replace('nan,', 'NULL,')
                query = query.replace("'nan'", 'NULL')
                cursor.execute(query)
                last_site_id=cursor.lastrowid
    except mysql.connector.Error as err:
        print('Error with site import')
        warning_ctr += 1
        cnx.rollback()
        print("Error {}'".format(err))
        raise
else:
    print('Warnings have been issued during reading of the workbooks. No imports will be performed')
    cnx.rollback()
    exit()
#==============================================================================
# cnx.commit()
#==============================================================================

# Check for repeated entity
# Enter entity into database if no repeats were found
# If database has more than one entity with the same entity_name
# cover_thickness, distance_entrance, Speleothem type
# inform user
Entity_exists = False
entity_tb['site_id'] = last_site_id
if warning_ctr < 1:
    print('Perform import of entities into database')
    query = ("""ALTER TABLE %s auto_increment = 1;""" %('entity'))
    cursor.execute(query)
    try:
        for i in entity_tb.index:
            query = (""" SELECT * FROM entity where entity_name = '%s' AND site_id = %d""" %(entity_tb['entity_name'][i], last_site_id))
            cursor.execute(query)
            x = cursor.rowcount
            field_names = [j[0] for j in cursor.description]
            field_names = list(set(field_names).intersection(list(entity_tb.columns.values)))
            #field_names.remove('entity_id')
            f_name = ", ".join(field_names)
            if int(x) == 1:
                print("Entity already exists")
                Entity_exists = True
            elif int(x) > 1:
                print("More than one entity exists with the same entity_name, please check database for possible repeated entries")
                warning_ctr += 1
            else:
                print("Import new entity into database")
                ent_subset = entity_tb.loc[(entity_tb.index == i), :]
                #tb_input(ent_subset, 'entity', 'entity_id')
#                tb_input(ent_subset, 'entity')
                one_and_only = entity_tb['one_and_only'][i]
                if one_and_only == 'yes':
                    print("This is the one and only record of this entity. Entity is uploaded into database with entity_status = current")
                    query = ("""INSERT INTO entity (site_id, entity_name, entity_status, depth_ref, cover_thickness, distance_entrance, speleothem_type, drip_type, d13C, d18O, d18O_water_equilibrium, trace_elements, organics, fluid_inclusions, mineralogy_petrology_fabric, clumped_isotopes, noble_gas_temperatures, C14, ODL, Mg_Ca, contact, data_DOI_URL) VALUES (%d, '%s', '%s', '%s', %f, %f, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');""" 
                             %(last_site_id,
                               entity_tb['entity_name'][i],
                               'current',
                               entity_tb['depth_ref'][i],
                               entity_tb['cover_thickness'][i],
                               entity_tb['distance_entrance'][i],
                               entity_tb['speleothem_type'][i],
                               entity_tb['drip_type'][i],
                               entity_tb['d13C'][i],
                               entity_tb['d18O'][i],
                               entity_tb['d18O_water_equilibrium'][i],
                               entity_tb['trace_elements'][i],
                               entity_tb['organics'][i],
                               entity_tb['fluid_inclusions'][i],
                               entity_tb['mineralogy_petrology_fabric'][i],
                               entity_tb['clumped_isotopes'][i],
                               entity_tb['noble_gas_temperatures'][i],
                               entity_tb['C14'][i],
                               entity_tb['ODL'][i],
                               entity_tb['Mg_Ca'][i],
                               entity_tb['contact'][i],
                               entity_tb['data_DOI_URL'][i]))
                else:
                    print("This is not the one and only record of this entity. Entity is uploaded into database but entity_status is being left blank. This must be dealt with manually.")
                    query = ("""INSERT INTO entity (site_id, entity_name, depth_ref, cover_thickness, distance_entrance, speleothem_type, drip_type, d13C, d18O, d18O_water_equilibrium, trace_elements, organics, fluid_inclusions, mineralogy_petrology_fabric, clumped_isotopes, noble_gas_temperatures, C14, ODL, Mg_Ca, contact, data_DOI_URL) VALUES (%d, '%s', '%s', %f, %f, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');""" 
                             %(last_site_id,
                               entity_tb['entity_name'][i],
                               entity_tb['depth_ref'][i],
                               entity_tb['cover_thickness'][i],
                               entity_tb['distance_entrance'][i],
                               entity_tb['speleothem_type'][i],
                               entity_tb['drip_type'][i],
                               entity_tb['d13C'][i],
                               entity_tb['d18O'][i],
                               entity_tb['d18O_water_equilibrium'][i],
                               entity_tb['trace_elements'][i],
                               entity_tb['organics'][i],
                               entity_tb['fluid_inclusions'][i],
                               entity_tb['mineralogy_petrology_fabric'][i],
                               entity_tb['clumped_isotopes'][i],
                               entity_tb['noble_gas_temperatures'][i],
                               entity_tb['C14'][i],
                               entity_tb['ODL'][i],
                               entity_tb['Mg_Ca'][i],
                               entity_tb['contact'][i],
                               entity_tb['data_DOI_URL'][i]))
                query = query.replace('nan,', 'NULL,')
                query = query.replace("'nan'", 'NULL')
#                print(query)
                cursor.execute(query)
#                extract entity_id
#                check for repeated reference based on either DOI or actual reference
#                if no repeats, import reference into reference table in db 
#                extract ref_id from reference tb in db
#                match entity_id and ref_id in entity_link_reference table
    except mysql.connector.Error as err:
        print('Problems with importing Entity')
        warning_ctr += 1
        cnx.rollback()
        print("Error {}'".format(err))
        # rollback somehow does not remove the query in the previous try statement
        # will perform deletion manually instead
        if Site_exists != True:
            query = ("""DELETE FROM site WHERE site_id=%d;""" %(last_site_id))
            cursor.execute(query)
            cnx.commit()
else:
    print('Warnings have been issued. No imports will be performed')
    cnx.rollback()
    exit()
#==============================================================================
# cnx.commit()
#==============================================================================

# import samples
# this will have to be moved to within the for loop for entity so that 
# the import will only occur when the entity/entities were not repeated

if warning_ctr < 1:
    print('Perform import of samples into database')
    query = ("""ALTER TABLE %s auto_increment = 1;""" %('sample'))
    cursor.execute(query)
    query = ("""ALTER TABLE %s auto_increment = 1;""" %('dating'))
    cursor.execute(query)
    if Site_exists == True & Entity_exists == True:
        importornot = query_yes_no("""
        Site and Entity already exists in Database.
        Would you like to import the sample spreadsheets of this workbook?
        
        Is this workbook an addition to the records of the particular entity/site. If yes, please type 'yes'
        If not, this workbook is then a repeat of previous workbooks - then please type 'no'
        Default = No
        """)
    else:
        importornot = True
    if importornot ==True:
        try:
            ctr = 0
            for i in entity_tb.index:
                # extract entity_name from entity spreadsheet
                ent_name = entity_tb['entity_name'][i]
                # try to extract entity_id from entity table in database, based on site_id and entity_name
                # select all 
                query = (""" SELECT * FROM entity where entity_name = '%s' and site_id = %d""" %(ent_name, last_site_id))
                cursor.execute(query)
                # extract column names from entity
                field_names = [j[0] for j in cursor.description]
                ent_data = cursor.fetchone()
                # extract entity_id
                # ent_id = int(ent_data[field_names == 'entity_id'])
                # FOR SOME REASON the ABOVE INDEX for site_id instead so I will just index this manually for now
                # entity_id is always the 2nd in the list anyways
                ent_id = int(ent_data[1])
                if ctr == 0:
                    first_ent_id = ent_id
                ctr += 1
                print("Entity id = %d" %ent_id)
                # create subset of table based on entity name
                # this is for one insert statement instead of a statement for every row
                sample_tb_subset = sample_tb.loc[(sample_tb['entity_name'] == ent_name), :]
                # replaces entity_id column with actualy entity id (normalisation based on the entity name)
                # sample_tb_subset.loc[:,'entity_id'] = ent_id
                print('import samples')
                if sample_tb_subset.shape[0] > 0:
                    sample_tb_subset.loc[:,'entity_id'] = ent_id
                    tb_input(sample_tb_subset, 'sample')
                    last_sample_insert_id=cursor.lastrowid
                    # extract sample id from sample table in database
                    # InnoDB always ensure sequential auto_incremented ids
                    query = ("""SELECT sample_id FROM sample WHERE sample_id >= %d;""" %last_sample_insert_id)
                    cursor.execute(query)
                    last_inserted_sample_ids = [int(j[0]) for j in cursor.fetchall()]
                    # replace last_inserted_sample_ids into sample_id in sample_tb_subset
                    sample_tb_subset.loc[:, 'sample_id'] = last_inserted_sample_ids
                    # exclude rows with no d18O_measurement
                    sample_d18O_tb_subset = sample_tb_subset.loc[pd.notnull(sample_tb_subset['d18O_measurement']),:]
                    tb_input(sample_d18O_tb_subset, 'd18O')
                    sample_d13C_tb_subset = sample_tb_subset.loc[pd.notnull(sample_tb_subset['d13C_measurement']),:]
                    tb_input(sample_d13C_tb_subset, 'd13C')
                    sample_dating_tb_subset = sample_tb_subset.loc[pd.isnull(sample_tb_subset['hiatus']),:]
                    sample_dating_tb_subset = sample_dating_tb_subset.loc[pd.isnull(sample_dating_tb_subset['gap']),:]                                               
                    print('import original chronology')
                    tb_input(sample_dating_tb_subset, 'original_chronology')
                    # gap and hiatuses
                    sample_gap_tb_subset = sample_tb_subset.loc[pd.notnull(sample_tb_subset['gap']),:]
                    print('import gaps and hiatuses')
                    tb_input(sample_gap_tb_subset, 'gap')
                    sample_hiatus_tb_subset = sample_tb_subset.loc[pd.notnull(sample_tb_subset['hiatus']),:]
                    tb_input(sample_hiatus_tb_subset, 'hiatus')
                dating_tb_subset = dating_tb.loc[(dating_tb['entity_name'] == ent_name)]
                print('import dating table')
                if dating_tb_subset.shape[0] > 0:
                    # replaces entity_id column with actualy entity id (normalisation based on the entity name)
                    dating_tb_subset.loc[:,'entity_id'] = ent_id
#                    tb_input(dating_tb_subset, 'dating', 'dating_info_id')
                    tb_input(dating_tb_subset, 'dating')
                # Lamina age vs depth
                dating_lamina_tb_subset = dating_lamina_tb.loc[(dating_lamina_tb['entity_name'] == ent_name)]
                if dating_lamina_tb_subset.shape[0] > 0:
                    # replaces entity_id column with actualy entity id (normalisation based on the entity name)
                    dating_lamina_tb_subset.loc[:,'entity_id'] = ent_id
#                    tb_input(dating_lamina_tb_subset, 'dating_lamina', 'dating_lamina_id')
                    tb_input(dating_lamina_tb_subset, 'dating_lamina')
        except mysql.connector.Error as err:
            print('Problems with importing sample spreadsheet (include d18O, d13C and original_chronology).')
            warning_ctr += 1
            cnx.rollback()
            print("Error {}'".format(err))
            if Site_exists == False & Entity_exists == False:
                query = ("""DELETE FROM site WHERE site_id=%d;""" %(last_site_id))
                cursor.execute(query)
                cnx.commit()
            elif Site_exists == True & Entity_exists == False:
                query = ("""DELETE FROM entity WHERE entity_id>=%d;""" %(first_ent_id))
                cursor.execute(query)
                cnx.commit()
else:
    print('Warnings have been issued. No imports will be performed')
    cnx.rollback()
    exit()
#==============================================================================
# cnx.commit()
#==============================================================================
if warning_ctr < 1:
    print('Perform import of reference into database')
    query = ("""ALTER TABLE %s auto_increment = 1;""" %('reference'))
    cursor.execute(query)
    if importornot == True:
        try:
            for i in ref_tb.index:
                print(i)
#                wah = str(MySQLdb.escape_string(ref_tb['citation'][i].encode('utf-8'))) #encode this string to utf8 before passing it through the escape_string function
                wah = ref_tb['citation'][i]
#                print(wah)
                pub_DOI = ref_tb['publication_DOI'][i]
                query = ("""SELECT ref_id FROM reference WHERE citation = "%s" AND publication_DOI = "%s"; """ %(wah, pub_DOI)) # uses AND instead of OR because there could be cases of missing DOIs, or same DOI due to typo.
#                print(query)
                cursor.execute(query)
                x = cursor.rowcount
                if int(x) == 1:
                    last_ref_id = int(cursor.fetchone()[0])
                    print("Reference exists; Ref_id = %d" %last_ref_id)
                elif int(x) > 1:
                    print("More than one reference exists with the same citation or the same DOI, CHECK DATABASE")
                    # might have to just keep the process going and use the ref_id from the first one
                else:
                    print("Import new reference into database")
                    query = ("""INSERT INTO reference (citation, publication_DOI) VALUES ("%s","%s")""" %(ref_tb['citation'][i], ref_tb['publication_DOI'][i]))
                    cursor.execute(query)
                    last_ref_id = cursor.lastrowid
                query = ("SELECT entity_id FROM entity where entity_name = '%s' AND site_id = %d" %(ref_tb['entity_name'][i], last_site_id))
                cursor.execute(query)
                entity_id = int(cursor.fetchone()[0])
                # check whether current entity_reference combinations already exists
                query = ("SELECT * FROM entity_link_reference where entity_id = %d AND ref_id = %d;" %(entity_id, last_ref_id))
                cursor.execute(query)
                x = cursor.rowcount
                if int(x) > 0:
                    print("The following entity/reference combinations has already been uploaded in the database, no entry will be uploaded")
                else:
                    query = ("INSERT INTO entity_link_reference (entity_id, ref_id) VALUES (%d, %d);" %(entity_id, last_ref_id))
                    cursor.execute(query)
        except:
            print('Problems with importing reference spreadsheet')
            warning_ctr += 1
            cnx.rollback()
            if Site_exists == False & Entity_exists == False:
                query = ("""DELETE FROM site WHERE site_id=%d;""" %(last_site_id))
                cursor.execute(query)
                cnx.commit()
            elif Site_exists == True & Entity_exists == False:
                query = ("""DELETE FROM entity WHERE entity_id>=%d;""" %(first_ent_id))
                cursor.execute(query)
                cnx.commit()
else:
    print('Warnings have been issued. No imports will be performed')
    cnx.rollback()
    exit()

try:
    if warning_ctr < 1 & importornot == True:
        cnx.commit()
        print(input_file + ' uploaded')
        shutil.move(input_file, os.path.join('Uploaded', input_file))
        print(input_file + ' moved to Uploaded folder')
    else:
        shutil.move(input_file, os.path.join('likely_repeated_records', input_file))
        print(input_file + ' moved to likely repeated folders')
        cnx.rollback()
except:
    cnx.rollback()
cnx.close()