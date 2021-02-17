# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 14:30:18 2017

@author: A

Codes check the workbooks and inform the database manager of the checks
13 September 2019 (A)
    - Renamed file from wb_checkv12.py to wb_check.py to allow more smooth tracking of file history. The version name is to only be attached to the version distributed to people. Git does not track the history of files very well when the names are changed.
    - Dating table, calib_used column: added options 'unknown' and 'other'
    - Dating table, depth_dating must be 0 if Event; actively growing and depth_ref = from top. Cannot have more than one Event; actively growing.
    - Entity table, entity_status_notes column converted to string at the very start. Only convert if it is not 'O' type (i.e. character)
    - Converted to Python 3. Tested and is compatible with both Python 2.7.15+ and Python 3.6.8.
    - 
    
13 March 2019 (A)
    - Corrected checking issues when modern_reference == 'Year of chemistry'

20 November 2018 (A) 5:11pm
	- hashed off the line that converts citations and site_name to string. This cannot be done properly as there are special characters in citations and will cause error.
	
20 November 2018 (A)
	- renamed file to v12 along with the printout that detects the version (column names of version 11 and 12 are identical)
	- force set the site_name and entity_name(s) to string (also the refernences table)
	
19 November 2018
	- Laia edited some of the printouts:
	
16 November 2018
    - If site table contains more than or less than one site, print warning and script terminates. (used to just print warning)
    - If entity table is empty, print warning and terminates
    - check for repeated entity_name, print warning and terminates
    - check that sample data is available for every entity
    - check that dating data is available for every non-composite entity (there is already a check that there should be no dating table when the entity is a composite
    - check that only entity name and 'gaps' column is filled in the sample table when gaps = 'G' 
    - check that drip_type must be 'not applicable' when entity is a composite. 
    - check that drip_type is not 'not applicable' when entity is not a composite.
    - alter script so that if it is missing an age model, the checks that ann_lam_check must be not applicable if the speleothem is non-laminated. 
    - checks that entity_status_info cannot be 'not applicable' when one_and_only = 'no'
    - fix bug so entity_status_notes must be filled in when one_and_only = 'no'
    - fix bug in check_hiatusgaps_columns function. previously had error with detecting columns that must be filled in but are not.
    - fixed bugs when enumerate (data_DOI_URL, citation, publication_DOI, entity_status_notes). s.lower was missing the brackets at the end (now s.lower()). These were used to check that the fields are not written as 'unknown', 'not applicable', 'na', etc.
    - 'not available' included in the drop down list for drip_type
    - alter script to create sample_tb_rm_hiatus_agemodel if sample_tb is empty. This is to prevent errors when it gets called in the future (issue if workbook has dating information on individual records of composite but no samples and has records)
    - data_DOI_URL can only start with ‘http’, ‘10.’, or ‘ftp’.
    - publication_DOI can only start with ‘http’, ‘10.’ or = ‘unpublished’
    - added checks with regards to mineralogy and arag_corr in composites as well.
    - fix bugs (stop printing out warning about modern_reference should be missing when there is no age model when modern_reference is already missing)
22 October 2018
    - Print out warnings to inform user that if depths are missing, you can still add a dummy depth and remove them as we still want the workbooks. 

18-19 October 2018
    - check_hiatusgaps_columns altered. Old function will only sometimes work if all hiatuses entered were wrong (i.e. entity_name, depth_sample and hiatus all missing)
    - Annotate codes into sections as in documents
    - rearranged the order of some codes to have a 'decision tree' order of warning prints to prevent several occurences of multiple warnings of the same issue
    - If 'Checked' folder is missing, print out that it is likely missing rather than giving an error
    - Make checks with regards to short records (< 100mm) informative
    - Make checks with regards to elevation informative (there could be missing elevation)
    - Stop warnings with regards to chained assignment (pandas; to prevent confusion)
    - If the codes cannot read in the file, or read in the sheets, this terminates before performign other checks
    - Added checks so that if Event; end of laminations are modern and depth_dating == 0 (depth_ref = 'from top') or depth_dating is from the very top (depth_ref = 'from base'), it raises an informative warning.

17 October 2018
    - added check for data_DOI_URL being the same as publication_DOI. This is not allowed. 
    - check that no hiatuses occured at the same depth_dating as dates (Dating information table)

16 October 2018
    - change 'sheetname' argument in xl.parse to 'sheet_name'
    - remove checks for whether the age and depths are in order in the dating information table
    - annotate every function
    - rearrange the checks so that the check for age inversions in Sample data is to be performed only when there are no repeated depth_sample and interp_age, and no wrong depth_ref.
    - rearrange the checks so that the check for possible hiatuses when there are no repeated depth_sample and interp_age, and no wrong depth_ref.
    - rearrange the checks so that the crosschecking of the modern_reference = 'Year of Chemistry' in the Sample data table is performed only after it has passed the checks for the any mistakes in dating table first (for non-composites) with regards to the chem_year (non-numeric and non-finite chem_year).
    - allow interp_age_uncert_neg, interp_age_uncert_pos to be missing, but there is an 'Informative' warning to flag this.
    - check sample_thickness values to be positive only when present.
    - Added 'Informative' in front of warnings which do not count to the final warning counts

18 September 2018 - file date removed from file name. File now called 'wb_checkv11.py'
14 September 2018 - correct false warning of inverted ages in dating table when modern reference is CE/BCE. Problem identified by Istvan
14 September 2018 - fix problem with checking code when a row is empty. Problem identified by Istvan
12 September 2018 - first uploaded onto dropbox for regional coordinators

"""

# =============================================================================
# Section 1. Import prerequisite modules
# =============================================================================
import pandas as pd
import numpy as np
import shutil, os, sys
from numbers import Number
import xlrd # needs to be added to read excel files. usually installed along with pandas 
# turn off pandas chained assignment warning
pd.options.mode.chained_assignment = None

# =============================================================================
# Section 2. Read in the workbook
# =============================================================================
#input_file = 'test_input_files/test_entity_status_notes_number.xlsx'
input_file = sys.argv[1]
# Try to read in the workbook
try:
    xl = pd.ExcelFile(input_file)
    sht_nm = xl.sheet_names
except:
    # If fails to read in workbook, exit the script
    sys.exit('Cannot read in excel file. input_file name may be supplied incorrectly.')

# List of spreadsheet names containing "Sample data"
# This is to check for cases where workbooks contain more than one Sample data
# spreadsheet.
sample_ls = [k for k in sht_nm if 'Sample data' in k]
# -----------------------------------------------------------------------------
# Read in spreadsheets from the workbook
# -----------------------------------------------------------------------------
# Skip first row (description row)
# column title starts at row number 2/ index = 1
try:
    site_tb = xl.parse(sheet_name = 'Site metadata', skiprows = 1).dropna(how = 'all')
except:
    sys.exit('Cannot read in Site metadata spreadsheet, likely no spreadsheet called "Site metadata"')
try:
    entity_tb = xl.parse(sheet_name = 'Entity metadata', skiprows = 1).dropna(how = 'all')
except:
    sys.exit('Cannot read in Enitity metadata spreadsheet, likely no spreadsheet called "Entity metadata"')
try:
    ref_tb = xl.parse(sheet_name = 'References', skiprows = 1).dropna(how = 'all')
except:
    sys.exit('Cannot read in References spreadsheet, likely no spreadsheet called "References"')
try:
    dating_tb = xl.parse(sheet_name = 'Dating information', skiprows = 1).dropna(how = 'all')
except:
    sys.exit('Cannot read in Dating information spreadsheet, likely no spreadsheet called "Dating information"')
try:
    dating_lamina_tb = xl.parse(sheet_name = 'Lamina age vs depth', skiprows = 1).dropna(how = 'all')
except:
    sys.exit('Cannot read in Lamina age vs depth spreadsheet, likely no spreadsheet called "Lamina age vs depth"')

# Read in sample spreadsheet
if len(sample_ls) == 1:
    try:
        sample_tb = xl.parse(sheet_name = 'Sample data', skiprows = 1).dropna(how = 'all')
    except:
        sys.exit('Cannot read in Sample data spreadsheet, likely no spreadsheet called "Sample data"')
elif len(sample_ls) == 0:
    sys.exit('Sample data spreadsheet does not exist, likely no spreadsheet called "Sample data"')
else:
    sys.exit('More than one Sample data spreadsheet exist. This is not allowed')

# =============================================================================
# Section 3. Check workbook is the right version
# =============================================================================
site_col = set(['site_name', 'latitude', 'longitude', 'elevation', 'geology', 'rock_age', 'monitoring']) - set(site_tb.columns)
entity_col = set(['entity_name', 'one_and_only', 'entity_status_info', 'entity_status_notes', 'depth_ref', 'cover_thickness', 'distance_entrance', 'speleothem_type', 'drip_type', 'd13C', 'd18O', 'd18O_water_equilibrium', 'trace_elements', 'organics', 'fluid_inclusions', 'mineralogy_petrology_fabric', 'clumped_isotopes', 'noble_gas_temperatures', 'C14', 'ODL', 'Mg_Ca', 'contact', 'data_DOI_URL']) - set(entity_tb.columns)
ref_col = set(['entity_name', 'citation', 'publication_DOI']) - set(ref_tb.columns)
date_col = set(['entity_name','date_type','depth_dating','dating_thickness','lab_num','material_dated','min_weight','max_weight','uncorr_age','uncorr_age_uncert_pos','uncorr_age_uncert_neg','14C_correction','calib_used','date_used','238U_content','238U_uncertainty','232Th_content','232Th_uncertainty','230Th_content','230Th_uncertainty','230Th_232Th_ratio','230Th_232Th_ratio_uncertainty','230Th_238U_activity','230Th_238U_activity_uncertainty','234U_238U_activity','234U_238U_activity_uncertainty','decay_constant','ini_230Th_232Th_ratio','ini_230Th_232Th_ratio_uncertainty','corr_age','corr_age_uncert_pos','corr_age_uncert_neg','modern_reference','chem_year']) - set(dating_tb.columns)
lam_col = set(['entity_name', 'depth_lam', 'lam_thickness', 'lam_age', 'lam_age_uncert_pos', 'lam_age_uncert_neg', 'modern_reference']) - set(dating_lamina_tb.columns)
sample_col = set(['entity_name', 'depth_sample', 'hiatus', 'gap', 'mineralogy', 'arag_corr', 'interp_age', 'interp_age_uncert_pos', 'interp_age_uncert_neg', 'age_model_type', 'modern_reference', 'ann_lam_check', 'dep_rate_check', 'sample_thickness', 'd13C_measurement', 'd13C_precision', 'd18O_measurement', 'd18O_precision', 'iso_std']) - set(sample_tb.columns)
if len(site_col) + len(entity_col) + len(ref_col) + len(date_col) + len(lam_col) + len(sample_col) > 0:
    if len(site_col) > 0:
        print('Site metadata table is missing column: %s' %str(list(site_col)))
    if len(entity_col) > 0:
        print('Entity metadata table is missing column: %s' %str(list(entity_col)))
    if len(ref_col) > 0:
        print('Entity metadata table is missing column: %s' %str(list(ref_col)))
    if len(date_col) > 0:
        print('Entity metadata table is missing column: %s' %str(list(date_col)))
    if len(lam_col) > 0:
        print('Entity metadata table is missing column: %s' %str(list(lam_col)))
    if len(sample_col) > 0:
        print('Entity metadata table is missing column: %s' %str(list(sample_col)))
    sys.exit('This workbook is likely not version 12. The checks cannot be performed.')

# =============================================================================
# Section 4. Define prerequisite functions
# =============================================================================

def count_values(table, value):
    """Count the number of occurences of a particular value in a table
    
    Args:
        table: A pandas dataframe object. Table with the data.
        value: string, the value to count 
    
    Returns:
        integer, count of occurences of value specified in 'value'
    
    Raises:
        None
    """
    ctr = 0
    for i in table.index:
        ctr += len(np.flatnonzero(table.loc[i,:] == value))
    return(ctr)

def check_possible_hiatuses(table, depthcol, agecol, hiatuscol, depth_ref, entity_name = '', modrefcol = 'modern_reference', na_rm = False):
    """Check for possible missing hiatuses
    
    Args:
        table: A pandas dataframe object. Table with the sample data.
        depthcol: string, name of the depth column
        agecol: string, name of the age column
        hiatuscol: string, name of the hiatus column
        depth_ref: string, depth reference ('from top' or 'from base')
        entity_name: string, name of entity (to be printed in warnings)
        modrefcol: string, name of modern reference column 
        na_rm: boolean, whether or not to remove rows with missing ages. (default to False)
    
    Returns:
        integer, either 0 or 1
    
    Raises:
        None
        
    NOTES:
        This function only works with the sample table and therefore there is no table_name argument
    """
    if na_rm == True:
        table = table.loc[pd.notnull(table[agecol]),:]
    else:
        pass
    table_nohiat = table.loc[table[hiatuscol] == '', :] # np.nan has been replaced with ''
    table_nohiat.loc[table_nohiat[modrefcol] == 'CE/BCE',agecol] = 1950 - table_nohiat.loc[table_nohiat[modrefcol] == 'CE/BCE',agecol]
    if table_nohiat[depthcol].isnull().values.any() == True:
        print('Sample data tab: Entity %s has samples (not identified as hiatuses) that are missing depths. Checks for possible hiatuses cannot be performed. Warning is issued' %entity_name)
        return(1)
    if depth_ref == 'from top':
        table_nohiat = table_nohiat.sort_values(by = [depthcol], ascending = True)
    elif depth_ref == 'from base':
        table_nohiat = table_nohiat.sort_values(by = [depthcol], ascending = False)
    else:
        print('Entity metadata tab: The depth_ref chosen is not "from top" or "from base"')
        return(1)
    agediff = np.diff(table_nohiat[agecol])
    avg_agediff = np.mean(agediff)
    diff_idx = np.flatnonzero(np.diff(table_nohiat[agecol]) >= avg_agediff*5)
    if len(diff_idx) > 0:
        table_nohiat = table_nohiat.reset_index(drop = True)
        depth1 = table_nohiat[depthcol][diff_idx]
        depth2 = table_nohiat[depthcol][diff_idx + 1]
        paired_depths = np.column_stack((depth1, depth2))
        hiatus_depth = table.loc[pd.notnull(table[hiatuscol]),depthcol]
        paired_depths_no = False
        if len(hiatus_depth) != 0:
            idx = []
            for j in range(0, paired_depths.shape[0]):
                l = paired_depths[j]
                ctr = 0
                for k in hiatus_depth:
                    if (l[0] > k >l[1])|(l[1] > k >l[0]):
                        ctr += 1
                    else:
                        pass
                if ctr < 1:
                    idx.append(j)
            if len(idx) > 0:
                paired_depths = paired_depths[idx]
            else:
                paired_depths_no = True
        if (paired_depths.shape[0] > 0) & (paired_depths_no == False):
            for j in range(0, paired_depths.shape[0]):
                if j == 0:
                    depths = str(list(paired_depths[j])).replace(',', ' and')
                else:
                    more_depths = str(list(paired_depths[j])).replace(',', ' and')
                    depths = '%s and %s' %(depths, more_depths)
            if entity_name != '':
                entity_name = 'Entity %s; ' %entity_name
            print('Informative: Sample data tab: %s There is a possible unaccounted hiatus between the following paired %s: %s ' %(entity_name, depthcol, depths))
            return(0) # THIS IS CURRENTLY INFORMATIVE
        else:
            return(0)
    else:
        return(0)

def check_ages_and_depths_in_order(table, depthcol, agecol, depth_ref, table_name, entity_name = '', na_rm = False):
    """Check that ages and depths are in order

    Args:
        table: A pandas dataframe object. Table with the data.
        depthcol: string, name of the depth column
        agecol: string, name of the age column
        depth_ref: string, depth reference ('from top' or 'from base')
        table_name: string, name of table (to be printed in warnings)
        entity_name: string, name of entity (to be printed in warnings)
        na_rm: boolean, whether or not to remove rows with missing ages. (default to False)
        
    Returns:
        integer, either 0 or 1

    Raises:
        None
    """
    if na_rm == True:
        table = table.loc[pd.notnull(table[agecol]),:]
    else:
        pass
    if depth_ref == 'from top':
        table = table.sort_values(by = [depthcol], ascending = True)
    elif depth_ref == 'from base':
        table = table.sort_values(by = [depthcol], ascending = False)
    else:
        print('Entity metadata tab: The depth_ref chosen is not "from top" or "from base"')
        return(1)
    diff_idx = np.flatnonzero(np.diff(table[agecol]) <= 0)
    table = table.reset_index(drop = True)
    if entity_name != '':
        entity_name = 'Entity %s;' %entity_name
    if (len(diff_idx) + 1) == table.shape[0]:
        print('%s tab: %s depth_ref is likely wrong (all ages are inverted)' %(table_name, entity_name))
        return(1)
    elif len(diff_idx) > 0:
        depth1 = table[depthcol][diff_idx]
        depth2 = table[depthcol][diff_idx + 1]
        paired_depths = np.column_stack((depth1, depth2))
        for j in range(0, paired_depths.shape[0]):
            if j == 0:
                depths = str(list(paired_depths[j])).replace(',', ' and')
            else:
                more_depths = str(list(paired_depths[j])).replace(',', ' and')
                depths = '%s and %s' %(depths, more_depths)
        print('%s tab: %s There is %s inversion at the following paired %s: %s ' %(table_name, entity_name, agecol, depthcol, depths))
        return(1)
    else:
        return(0)

def check_values2list(table, col_name, table_name, dropdownlist, na_rm = False):
    """Check that values are from a list

    Args:
        table: A pandas dataframe object. Table with the data.
        col_name: string. Name of column to check
        table_name: string. Name of table (to be printed in warnings).
        dropdownlist: list of string. List for the column to be checked against
        na_rm: boolean. whether or not to accept NA

    Returns:
        integer, either 0 or 1

    Raises:
        None
    """
    if na_rm == True:
        table = table.loc[pd.notnull(table[col_name]),:]
    else:
        pass
    list_append = []
    for i in table.index:
        subset = table.loc[i,col_name]
        if subset not in dropdownlist:
            list_append.append((i+3))
    if len(list_append) > 0:
        print('%s tab: %s; %d row(s) contains values not in the dropdown lists. row: %s' %(table_name, col_name, len(list_append), str(list_append).replace('[', '').replace(']', '')))
        return(1)
    else:
        return(0)

def check_no_values(table, table_name, col_name, col_dtype_str_set = False):
    """Check that there are no missing values in a column.

    Args:
        table: A pandas dataframe object. Table with the data.
        table_name: string. Name of table (to be printed in warnings).
        col_name: string. Name of column to check
        col_dtype_str_set: boolean. True if np.nan has been replaced with ''

    Returns:
        integer, either 0 or 1

    Raises:
        None
    """
    idx = []
    if (col_dtype_str_set == False):
        idx = table.loc[pd.isnull(table[col_name]),:].index + 3
    elif (col_dtype_str_set == True):
        idx = table.loc[table[col_name] == ''].index + 3
    if len(idx) > 0:
        print('%s tab: %s; %d row(s) is missing. row: %s' %(table_name, col_name, len(idx), str(list(idx)).replace('[', '').replace(']', '')))
        return(1)
    else:
        return(0)

def check_independent_dependent_col(table, table_name, independent_column, dependent_column):
    """Check that if there are values in one column, that a dependent column must also have values
    
    Args:
        table: A pandas dataframe object. Table with the data.
        table_name: string. Name of table (to be printed in warnings).
        independent_column: string. Name of the independent column
        dependent_column: string. Name of the dependent column

    Returns:
        integer, either 0 or 1
        
    Raises:
        None
    """
    sub_tb = table.loc[pd.isnull(table[independent_column]) & pd.notnull(table[dependent_column]),:]
    # +3 because values starts on row number 3
    number_of_rows = sub_tb.shape[0]
    ctr = False
    if number_of_rows > 0:
        Row_numbers = str([i for i in (sub_tb.index + 3)]).replace('[','').replace(']', '')
        print('%s tab: %d row(s) have %s but no %s. See row(s) %s' %(table_name, number_of_rows, dependent_column, independent_column, Row_numbers))
        ctr = True
    if ctr == False:
        return(0)
    else:
        return(1)

def check_Isotope_Checks(table, independent_column, dependent_column1, dependent_column2):
    sub_tb = table.loc[pd.notnull(table[independent_column]) & (pd.isnull(table[dependent_column1]) & pd.isnull(table[dependent_column2])),:]
    # +3 because values starts on row number 3
    number_of_rows = len(sub_tb.index)
    if number_of_rows > 0:
        print('Sample table tab: There is at least one row with isotope standard and no d13C or d18O measurement. Ensure that only isotope measurements have iso_std info. %d rows. See row(s): %s' %(number_of_rows, str(list(sub_tb.index + 3)).replace(']','').replace('[', '')) )
        return(1)
    else:
        return(0)

# Check that entity names in table exists in the Entity metadata spreadsheet
def check_entity_names(entity_tb, table, tablename):
    """Check that entity_name in table exists in the Entity metadata spreadsheet

    Args:
        entity_tb, A pandas dataframe object. Table with Entity metadata
        table: A pandas dataframe object. Table with the data.
        table_name: string. Name of table (to be printed in warnings).
        
    Returns:
        integer, either 0 or 1

    Raises:
        None
    """
    entity_name_list = []
    for i in np.unique(table['entity_name']):
        if i not in list(entity_tb['entity_name']):
            entity_name_list.append(str(i))
    if len(entity_name_list) > 0:
        print('Entity metadata tab: Entity %s is missing from the list (we have found it in the %s spreadsheet)' %(str(entity_name_list).replace('[', '').replace(']', ''),tablename))
        return(1)
    else:
        return(0)

# Check that column are only numbers
def check_numbers(table, tablename, column):
    """Check for non-numeric numbers in a column

    Args:
        table: A pandas dataframe object. Table with the data.
        table_name: string. Name of table (to be printed in warnings).
        col_name: string. Name of column
        
    Returns:
        integer, either 0 or 1

    Raises:
        None
    """
    warning = False
    store_ls = []
    for i in table.index:
        obj = table.loc[i, column]
        if isinstance(obj, Number):
            pass
        else:
            warning = True
            store_ls.append(i)
    if warning == True:
        store_ls_len = len(store_ls)
        store_ls = str([i+3 for i in store_ls]).replace('[', '').replace(']', '')
        print('%s tab: %s; %d row(s) is not a number. row: %s' %(tablename, column, store_ls_len, store_ls))
        return(1)
    else:
        return(0)

# check that there is only one record for each depth
def check_no_repeated_records(table, tablename, entity_name, column):
    """Check that there are no repeated values in the database (to the nearest 6 d.p.)
    
    Args:
        table: A pandas dataframe object. Table with the data.
        tablename: string. Name of table (to be printed in warnings).
        entity_name: string. Name of entity
        column: string. Name of column
        
    Returns:
        integer, either 0 or 1

    Raises:
        None
    """
    table = table.loc[pd.to_numeric(table[column], errors = 'coerce').notnull(),:]
    col_val = list(table[column].round(6)) # round to 6 dp first to prevent rounding issues
    if len(col_val) == len(set(col_val)):
        return(0)
    else:
        ls = list(sorted(set([x for x in col_val if col_val.count(x) > 1])))
        rep = str(ls)[1:-1]
        col_number = []
        for i in ls:
            col_number.append(list(table[table[column].round(6).isin([i])].index + 3))
        print('%s tab: Entity %s; The following %s occured more than once: %s Row: %s' %(tablename, entity_name, column, rep, str(col_number)[1:-1]))
        return(1)

# Check that column are only numbers
def check_positivenumbers(table, tablename, column, na_rm = False):
    """Check if numbers positive

    Args:
        table: A pandas dataframe object. Table with the data.
        tablename: string. Name of table (to be printed in warnings).
        column: string. Name of column
        na_rm: boolean. whether or not to accept NA
        
    Returns:
        integer, either 0 or 1

    Raises:
        None
    """
    ctr = 0
    store_ls = []
    if na_rm == True:
        table = table.loc[pd.notnull(table[column]),:]
    else:
        pass
    for i in table.index:
        obj = table.loc[i, column]
        if pd.isnull(obj) | (obj < 0):
            ctr+=1
            store_ls.append(i)
        else:
            pass
    if ctr > 0:
        store_ls_len = len(store_ls)
        store_ls = str([i+3 for i in store_ls]).replace('[', '').replace(']', '')
        print('%s tab: %s; %d row(s) is not a positive number (or not a number). row: %s' %(tablename, column, store_ls_len, store_ls))
        return(1)
    else:
        return(0)
                               
# Check that if Modern_reference = year of chemistry that Year_done exist in dating information 
def check_yearofchemistry_crosstable(sample_tb, dating_tb):
    """Cross check for chem_year when there is a year of chemistry. If both 
    tables are dating table, then it is allowed to have more than one chem_year
    as long as they are numeric. If they are used to cross check sample_tb and 
    dating_tb, there must be only one chem_year. This is actually allowed but 
    due to it's complications, it is flagged and authors are suggested to use 
    convert the ages to a standard age before submitting to SISAL if possible

    Args:
        sample_tb: A pandas dataframe object. Table of interest (sample_tb, dating_lamina_tb, or dating_tb)
        dating_tb: A pandas dataframe object. Table with the chem_year information (dating_tb)
        
    Returns:
        integer, either 0 or number of warnings (maximum 1 warning per entity)

    Raises:
        None
    """
    sample_tb_subset = sample_tb.loc[sample_tb['modern_reference'] == 'Year of chemistry',:] #EDIT
    if sample_tb_subset.shape[0] > 0:
        warning_count = 0
        for i in np.unique(sample_tb_subset['entity_name']):
            dating_tb_sample_tb = False
            if sample_tb is dating_tb:
                dating_tb_sample_tb = True
                # if referencing the same table (in case of using dating table), check references also for the dates which were not used in the original model
                unique_list = np.unique(dating_tb.loc[(dating_tb['entity_name'] == i) & (dating_tb['modern_reference'] == 'Year of chemistry'), 'chem_year'])
            else:
                # if referencing a different table (i.e. sample table to dating table), only refer to dates which were used in the original model
                unique_list = np.unique(dating_tb.loc[(dating_tb['entity_name'] == i) & (dating_tb['modern_reference'] == 'Year of chemistry') & (dating_tb['date_used'] != 'no'), 'chem_year'])
            notnumber = False
            for k in unique_list:
                if isinstance(k, Number):
                    if np.isfinite(k):
                        notnumber = False
                    else:
                        notnumber = True
                        break
                else:
                    notnumber = True
                    break
            if (notnumber == True):
                if (dating_tb_sample_tb == True):
                    print('Dating information tab: Entity %s has chem_year which is not a finite number (or missing) where modern_reference is Year of chemistry.' %(i))
                    warning_count += 1
                else:
                    if (unique_list.shape[0] == 0):
                        warning_count += 1
                        print('Dating information tab: Entity %s is missing chem_year where modern_reference is Year of chemistry.' %(i))
                    elif (unique_list.shape[0] == 1):
                        warning_count += 1
                        print('Dating information tab: Entity %s has chem_year which is not a finite number (or missing) where modern_reference is Year of chemistry.' %(i))
                    else:
                        if (np.isfinite(unique_list).any()):
                            print('Dating information tab: date_used = "yes"; Entity %s has more than one chem_year, not all of which are a finite number (or missing). This may also be flagged in other checks' %(i))
                            warning_count += 1
                        else:
                            warning_count += 1
                            print('Dating information tab: Entity %s has more than one chem_year, all of which are not a finite number (or missing) where modern_reference is Year of chemistry.' %(i))
            else:
                if (dating_tb_sample_tb == True):
                    if (unique_list.shape[0] >= 1):
                        pass
                    else:
                        print('Dating information tab: Entity %s is missing chem_year where modern_reference is Year of chemistry.' %(i))
                        warning_count += 1
                else:
                    if (unique_list.shape[0] == 1):
                        pass
                    elif (unique_list.shape[0] < 1):
                        print('Dating information tab: Entity %s is missing chem_year in Dating Information spreadsheet (where date_used = "yes"). If chem_year exists in the workbook, it is likely that date_used = "no". Best practice is to convert all dates to the same modern reference manually' %(i))
                        warning_count += 1
                    else:
                        print('Informative: Dating information tab: Entity %s has more than one chem_year. The youngest chem_year will be used when converting the database to BP(1950). Please check whether this is correct.' %(i))
#                        warning_count += 1
        return(warning_count)
    else:
        return(0)

        
def check_notminmax_age(table, age, uncert1, uncert2, table_name, entity_name = '', na_rm = False):
    """Check if a set of values are not min/max ages in a column (age is inbetween or equal to the uncertaintites)
    
    Args:
        table: A pandas dataframe object. Table with the data.
        age: string. Name of (age) column
        uncert1: string. Name of (age) positive uncertainty column
        uncert2. string. Name of (age) negative uncertainty column
        table_name: string. Name of table (to be printed in warnings).
        entity_name: string. Name of entity
        na_rm: boolean. whether or not to accept missing uncertainties
        
    Returns:
        integer, either 0 or 1

    Raises:
        None
    """
    if na_rm == True:
        table = table.loc[pd.notnull(table[uncert1]),:] # only uncert1 is required as there are other checks for the coexistence of both uncert1 and uncert2
    else:
        pass
    list_append = list(table.index[((table[age] <= table[uncert1]) & (table[age] >= table[uncert2])) | ((table[age] <= table[uncert2]) & (table[age] >= table[uncert1]))] + 3)
    if (len(list_append) > 1):
        if entity_name != '':
            entity_name = 'Entity %s;' %entity_name
        print('%s tab; %s It looks like %s and %s have been entered as ranges (min/max) instead of uncertainties. %d row(s). row: %s' %(table_name, entity_name, uncert1, uncert2, len(list_append), str(list_append).replace('[', '').replace(']', '')))
        return(1)
    else:
        return(0)
        
        
def check_numbers_in_range(table, tablename, column, minval, maxval, na_rm = False):
    """Check if numbers are in range in a column (assuming they are all numeric)

    Args:
        table: A pandas dataframe object. Table with the data.
        tablename: string. Name of table (to be printed in warnings).
        column: string. Name of column
        minval: numeric. minium value for the column
        maxval: numeric. maximum value for the column
        na_rm: boolean. whether or not to accept NA
        
    Returns:
        integer, either 0 or 1

    Raises:
        None
    """
    if na_rm == True:
        table = table.loc[pd.notnull(table[column]),:]
    else:
        pass
    warning = False
    store_ls = []
    for i in table.index:
        obj = table.loc[i, column]
        if ((obj <= maxval) & (obj >= minval)):
            pass
        else:
            warning = True
            store_ls.append(i)
    if warning == True:
        store_ls_len = len(store_ls)
        store_ls = str([i+3 for i in store_ls]).replace('[', '').replace(']', '')
        print('%s table: %s; %d row(s) is not within the valid range (>=%.2f and <=%.2f) (or not a number). row: %s' %(tablename, column, store_ls_len, minval, maxval, store_ls))
        return(1)
    else:
        return(0)
        
def check_hiatusgaps_columns(table, table_name, diagnosiscolumn, hiatusorgap, must_filled_columns, maybe_filled_columns = []):
    """Check that when a row is a hiatus, the other columns are filled in properly (i.e. some columns must be filled in while othesr must not)#
        
    Args:
        table: A pandas dataframe object. Table with the data.
        tablename: string. Name of table (to be printed in warnings).
        diagnosiscolumn: string. Name of hiatus or gap column (i.e. hiatus in sample table, or date_type in dating information table)
        hiatusorgap: string. Value which indicates that the row is a hiatus or gap (or other events)
        must_filled_columns: list. Columns which are to be filled in when the row is a hiatus or gap
        maybe_filled_columns: list. Columns which may be filled in when th row is a hiatus or gap
        
    Returns:
        integer, either 0 or 1

    Raises:
        None
    """
    if hiatusorgap in list(table[diagnosiscolumn]):
        subset_tb = table.loc[(table[diagnosiscolumn] == hiatusorgap),:]
        subset_tb = subset_tb.replace('', np.nan, regex=True)
        hiatus_check = pd.isnull(subset_tb)
        if hiatus_check.shape[0] > 0:
            store_idx = np.array([])
            store_idx2 = np.array([])
            colname_empty = []
            colname_mustfill = []
            for i in hiatus_check.columns:
#                print(i)
                temp_tb = hiatus_check.loc[hiatus_check[i] == True,i]
                temp_tb2 = hiatus_check.loc[hiatus_check[i] == False,i]
                if i in must_filled_columns:
                    if len(temp_tb.index) > 0:
                        store_idx = np.append(store_idx, temp_tb.index)
                        colname_mustfill.append(str(i))
                elif i in maybe_filled_columns:
                    pass
                else:
                    if len(temp_tb2.index) > 0:
                        store_idx2 = np.append(store_idx2, temp_tb2.index)
                        colname_empty.append(str(i))
            if hiatusorgap == 'H':
                hiatusorgap = 'hiatuses'
            elif hiatusorgap == 'G':
                hiatusorgap = 'gaps'
            warning = 0
            if len(store_idx) > 0:
                warning += 1
                store_idx = list(set(store_idx.astype('int') + 3))
                store_idx.sort()
                print('%s tab: For %s, %s should be filled in but is empty. see row: %s' %(table_name, hiatusorgap, str(colname_mustfill).replace('[', '').replace(']', ''), str(store_idx).replace('[', '').replace(']', '')))
            if len(store_idx2) > 0:
                warning += 1
                store_idx2 = list(set(store_idx2.astype('int') + 3))
                store_idx2.sort()
                if len(maybe_filled_columns) > 0:
                    print('%s tab: For %s, There are columns which must be empty but are filled in. row: %s. see column(s): %s' %(table_name, hiatusorgap, str(store_idx2).replace('[', '').replace(']', ''), str(colname_empty).replace('[', '').replace(']', '')))
                else:
                    print('%s tab: For %s, Only %s should be filled in. Other columns must be empty. see row: %s' %(table_name, hiatusorgap, str(must_filled_columns).replace('[', '').replace(']', ''), str(store_idx2).replace('[', '').replace(']', '')))
            if warning > 0:
                return(warning)
            else:
                return(0)
        else:
            #print('There is no "%s" in this table' %(hiatusorgap))
            return(0)
    else:
        return(0)

# =============================================================================
# Section 5. Set columns data types
# =============================================================================
# set all np.nan to '' in columns which are non-numeric
sample_tb.entity_name = sample_tb.entity_name.replace(np.nan, '', regex = True)
sample_tb.modern_reference = sample_tb.modern_reference.replace(np.nan, '', regex = True)
sample_tb.hiatus = sample_tb.hiatus.replace(np.nan, '', regex = True)
sample_tb.gap = sample_tb.gap.replace(np.nan, '', regex = True)
sample_tb.mineralogy = sample_tb.mineralogy.replace(np.nan, '', regex = True)
sample_tb.arag_corr = sample_tb.arag_corr.replace(np.nan, '', regex = True)
sample_tb.ann_lam_check = sample_tb.ann_lam_check.replace(np.nan, '', regex = True)
sample_tb.dep_rate_check = sample_tb.dep_rate_check.replace(np.nan, '', regex = True)
entity_tb.data_DOI_URL = entity_tb.data_DOI_URL.replace(np.nan, '', regex = True)
entity_tb.entity_name = entity_tb.entity_name.replace(np.nan, '', regex = True)
entity_tb.entity_status_notes = entity_tb.entity_status_notes.replace(np.nan, '', regex = True)
ref_tb.entity_name = ref_tb.entity_name.replace(np.nan, '', regex = True)
ref_tb.citation = ref_tb.citation.replace(np.nan, '', regex = True)
ref_tb.publication_DOI = ref_tb.publication_DOI.replace(np.nan, '', regex = True)
dating_tb.entity_name = dating_tb.entity_name.replace(np.nan, '', regex = True)
dating_tb.date_used = dating_tb.date_used.replace(np.nan, '', regex = True)
dating_tb.date_type = dating_tb.date_type.replace(np.nan, '', regex = True)
dating_tb.calib_used = dating_tb.calib_used.replace(np.nan, '', regex = True)
# convert all site and entity names to string
# site_tb.site_name = site_tb.site_name.astype('str')
if entity_tb.entity_name.dtype != 'O':
    entity_tb.entity_name = entity_tb.entity_name.astype('str')
if entity_tb.entity_status_notes.dtype != 'O':
    entity_tb.entity_status_notes = entity_tb.entity_status_notes.astype('str')
if dating_tb.entity_name.dtype != 'O':
    dating_tb.entity_name = dating_tb.entity_name.astype('str')
if dating_lamina_tb.entity_name.dtype != 'O':
    dating_lamina_tb.entity_name = dating_lamina_tb.entity_name.astype('str')
if sample_tb.entity_name.dtype != 'O':
    sample_tb.entity_name = sample_tb.entity_name.astype('str')
if ref_tb.entity_name.dtype != 'O':
    ref_tb.entity_name = ref_tb.entity_name.astype('str')
# convert everything in reference table to string
# ref_tb.citation = ref_tb.citation.astype('str') # This cannot be converted to string as citation often contains some special characters.
if ref_tb.publication_DOI.dtype != 'O':
    ref_tb.publication_DOI = ref_tb.publication_DOI.astype('str')

# =============================================================================
# Section 6. Count number of unknowns
# =============================================================================
# count number of unknowns in each table and print this at the end
site_unkwn = count_values(site_tb, 'unknown')
entity_unkwn = count_values(entity_tb, 'unknown')
dating_unkwn = count_values(dating_tb, 'unknown')
sample_unkwn = count_values(sample_tb, 'unknown')
total_unkwn = site_unkwn + entity_unkwn + dating_unkwn + sample_unkwn
entity_count = len(pd.unique(entity_tb['entity_name']))

# =============================================================================
# 
# # Section 7. Start content checking
# 
# =============================================================================
# Initiate warning counter
warning_ctr = 0

# _____________________________________________________________________________
#
# Section 7.i. Check for all entities/sites
# _____________________________________________________________________________
# create yes, No, unknown list
y_n_nk_list = ['yes', 'no', 'unknown']

# -----------------------------------------------------------------------------
# Section 7.i.a. Site spreadsheet 
# -----------------------------------------------------------------------------
# Check that the site table has one and only one record
if len(site_tb.index) != 1:
    sys.exit('Site metadata table is either empty or has more than one site. Only one site per workbook is allowed.')
else:
    lat = site_tb.loc[0, 'latitude']
    lon = site_tb.loc[0, 'longitude']
    # Check that latitude, longitude and elevation are numbers
    loc_warning = False
    if check_numbers(site_tb, 'Site metadata', 'latitude') == 0:
        if check_numbers_in_range(site_tb, 'Site metadata', 'latitude', -90, 90) == 1:
            warning_ctr += 1
            loc_warning = True
    else:
        warning_ctr += 1
        loc_warning = True
    if check_numbers(site_tb, 'Site metadata', 'longitude') == 0:
        if check_numbers_in_range(site_tb, 'Site metadata', 'longitude', -180, 180) == 1:
            warning_ctr += 1
            loc_warning = True
    else:
        warning_ctr += 1
        loc_warning = True
    if loc_warning == True:
        print('Site metadata tab: The coordinates for this site are definitely wrong, please check')
    else:
        print('Informative: Site metadata tab: This site is at Lat: %f deg and Lon: %f deg. Ensure that these have been properly converted to decimal degrees and are correct' %(lat, lon))
    site_name = site_tb.loc[0, 'site_name'] 
    if check_no_values(site_tb, 'Site metadata', 'site_name') == 0:
        if site_name.startswith(' ') | site_name.endswith(' '):
            warning_ctr += 1
            print('Site metadata tab: The site_name either starts or ends with a space. Please remove the extra space')
    else:
        warning_ctr += 1
    # Check that entity name is being filled in the entity metadata spreadsheet
#    if check_no_values(site_tb, 'Site metadata', 'elevation') == 1:
    if len(site_tb.loc[pd.isnull(site_tb['elevation']), 'elevation'].index) > 0:
#        warning_ctr += 1
        print('Informative: Site metadata: elevation is missing. Please check and make sure that elevation is truly missing.')
    else:
        warning_ctr += check_numbers(site_tb, 'Site metadata', 'elevation')
    # Check that if geology is filled in, and if so, that they are from a dropdown list
    if check_no_values(site_tb, 'Site metadata', 'geology') == 0:
        warning_ctr += check_values2list(site_tb, 'geology', 'Site metadata', ['limestone', 'dolomite', 'gypsum', 'magmatic', 'marble', 'granite', 'mixed', 'unknown', 'other'])
    else:
        warning_ctr += 1
    if check_no_values(site_tb, 'Site metadata', 'rock_age') == 0:
        warning_ctr += check_values2list(site_tb, 'rock_age', 'Site metadata', ['Holocene', 'Pleistocene', 'Pliocene', 'Miocene', 'Oligocene', 'Eocene', 'Palaeocene', 'Cretaceous', 'Jurassic', 'Triassic', 'Permian', 'Carboniferous', 'Devonian', 'Silurian', 'Ordovician', 'Cambrian', 'Precambrian', 'unknown'])
    else:
        warning_ctr += 1
    if check_no_values(site_tb, 'Site metadata', 'monitoring') == 0:
        warning_ctr += check_values2list(site_tb, 'monitoring', 'Site metadata', y_n_nk_list)
    else:
        warning_ctr += 1


# -----------------------------------------------------------------------------
# Section 7.i.b. Entity spreadsheet
# -----------------------------------------------------------------------------
if len(entity_tb.index) == 0:
    sys.exit('Entity_metadata tab: There are no entities in this workbook. The checks will terminate here.') 
if check_no_values(entity_tb, 'Entity metadata', 'entity_name') == 0:
    for i in set(entity_tb['entity_name']):
        if i.startswith(' ') | i.endswith(' '):
            warning_ctr += 1
            print('Entity metadata tab: The entity_name %s either starts or ends with a space. Please remove the extra space' %i)
    ent_ls = list(entity_tb['entity_name'])
    rep_ent = list(sorted(set([x for x in ent_ls if ent_ls.count(x) > 1]))) 
    if len(rep_ent) > 0:
        warning_ctr += 1
        sys.exit('Entity metadata tab: There are repeated entity_name(s): %s. The checking script cannot continue and will terminate here.' %str(list(rep_ent)).replace('[', '').replace(']', ''))
else:
    warning_ctr += 1
if check_no_values(entity_tb, 'Entity metadata', 'speleothem_type') == 0: 
    warning_ctr += check_values2list(entity_tb, 'speleothem_type', 'Entity metadata', ['composite', 'stalagmite', 'stalactite', 'flowstone', 'other', 'unknown'])
else:
    warning_ctr += 1
if check_no_values(entity_tb, 'Entity metadata', 'depth_ref') == 0:
    warning_ctr += check_values2list(entity_tb, 'depth_ref', 'Entity metadata', ['from top', 'from base', 'not applicable'])
else:
    warning_ctr += 1
# Check that the values are from within the list
warning_ctr += check_values2list(entity_tb, 'drip_type', 'Entity metadata', ['seepage flow', 'seasonal drip', 'fast flow', 'mixture', 'unknown', 'not applicable'])
Entity_y_n_nk = ['d13C', 'd18O', 'd18O_water_equilibrium', 'trace_elements', 'organics', 'fluid_inclusions', 'mineralogy_petrology_fabric', 'clumped_isotopes', 'noble_gas_temperatures', 'C14', 'ODL', 'Mg_Ca']
for i in Entity_y_n_nk:
    if check_no_values(entity_tb, 'Entity metadata', i) == 0:
        warning_ctr += check_values2list(entity_tb, i, 'Entity metadata', y_n_nk_list)
    else:
        warning_ctr += 1
# Check that contact names are filled in properly

for i in entity_tb.index:
    contact = entity_tb['contact'][i]
    if pd.isnull(contact):
        print('Entity metadata tab: Contact_name in row %d is empty. Name and surname(s) are required' %(i + 3))
        warning_ctr += 1
        continue
    elif isinstance(contact, Number):
        print('Entity metadata tab: Contact_name in row %d is numeric instead of text. Name and surname(s) are required' %(i + 3))
        warning_ctr += 1
        continue
    elif ' ' not in contact:
        print('Entity metadata tab: Contact_name in row %d is only one word. Name and surname(s) are required' %(i + 3))
        warning_ctr += 1
        continue
    elif contact.isspace() | contact.startswith(' ') | contact.endswith(' '):
        print('Entity metadata tab: Contact_name in row %d is just spaces or starts and ends with spaces. Name and surname(s) are required' %(i + 3))
        warning_ctr += 1
        continue
    else:
        words = contact.split(' ')
        countr = 0
        # if name is two word long and one is initial, this is not accepted
        # if this is a three worded name, one initial is accepted
        if len(words) > 2:
            threshold = 1
        else:
            threshold = 0
        for j in words:
            # Check for names with one letter length. Likely initials
            if len(j) < 2:
                countr += 1
            # Check for initials with full stop at the end of their names
            elif j.endswith('.'):
                countr += 1
        if countr > threshold:
            print('Entity metadata tab: Contact_name in row %d seems to not fulfill the criteria of a full name. Name and surname(s) are required' %(i + 3))
            warning_ctr += 1

# Check one and only
if check_no_values(entity_tb, 'Entity metadata', 'one_and_only') == 0:
    if check_values2list(entity_tb, 'one_and_only', 'Entity metadata', ['yes', 'no']) == 0:
        if check_no_values(entity_tb, 'Entity metadata', 'entity_status_info') == 0:
            if check_values2list(entity_tb, 'entity_status_info', 'Entity metadata', ['completely supersedes', 'completely superseded by', 'partially supersedes', 'partially superseded by', 'not applicable']) == 0:
                one_and_only_entity = entity_tb.loc[(entity_tb['one_and_only'] == 'yes') & (entity_tb['entity_status_info'] != 'not applicable'),:]
                if one_and_only_entity.shape[0] > 0:
                    warning_ctr += 1
                    print('Entity metadata tab: if one_and_only = "yes", entity_status_info must be "not applicable". See row %s' %(str([i+3 for i in one_and_only_entity.index]).replace('[', '').replace(']', '')))
                one_and_only_entity = entity_tb.loc[(entity_tb['one_and_only'] == 'yes') & (entity_tb['entity_status_notes'] != ''),:]
                if one_and_only_entity.shape[0] > 0:
                    warning_ctr += 1
                    print('Entity metadata tab: if one_and_only = "yes", entity_status_notes must be empty. See row %s' %(str([i+3 for i in one_and_only_entity.index]).replace('[', '').replace(']', '')))
                not_one_and_only_ent = entity_tb.loc[(entity_tb['one_and_only'] == 'no'),:]
                # Note that check_no_values was not used here as the checks are already 
                # taken into account when creating the indices. '' already replaces
                # np.nan and we do not allow '' anyways
                indices = [i for i, s in enumerate(not_one_and_only_ent['entity_status_info']) if (any(x == s.lower() for x in ['not applicable']))]
                not_one_and_only_ent = not_one_and_only_ent.iloc[indices,:]
                if not_one_and_only_ent.shape[0] > 0:
                    warning_ctr += 1
                    print('Entity metadata tab: if one_and_only = "no", entity_status_info cannot be "not applicable". row number: %s' %(str([i+3 for i in not_one_and_only_ent.index]).replace('[', '').replace(']', ''))) 
                indices = [i for i, s in enumerate(not_one_and_only_ent['entity_status_notes']) if (any(x == s.lower() for x in ['unknown', 'unknwn', '', ' ', 'n/a', 'na', 'not applicable', 'not known', 'notknown', 'unkwn'])) | s.isspace()]
                not_one_and_only_ent = not_one_and_only_ent.iloc[indices,:]
                if not_one_and_only_ent.shape[0] > 0:
                    warning_ctr += 1
                    print('Entity metadata tab: if one_and_only = "no", entity_status_notes cannot be empty, "NA", "unknown", "not known" (and their respective variants, see notes in SISAL_wb_checks GD document if required). row number: %s' %(str([i+3 for i in not_one_and_only_ent.index]).replace('[', '').replace(']', '')))

            else:
                warning_ctr += 1
        else:
            warning_ctr += 1
    else:
        warning_ctr += 1
else:
    warning_ctr += 1

# Check that the number columns are filled in properly
warning_ctr += check_numbers(entity_tb, 'Entity metadata', 'cover_thickness')
warning_ctr += check_numbers(entity_tb, 'Entity metadata', 'distance_entrance')
# Check that data_DOI_URL are entered properly. Either empty or an actual URL/DOI
indices = [i for i, s in enumerate(entity_tb['data_DOI_URL']) if (any(x == s.lower() for x in ['unknown', ' ', 'n/a', 'na', 'not known', 'notknown', 'not applicable', 'unkwn'])) | s.startswith(' ') | s.endswith(' ')]
indices = entity_tb.iloc[indices,:].index + 3
if len(indices) > 0:
    warning_ctr += 1
    print('Entity metadata tab: the NOAA/PANGEA URL or DOI of the data in row %s is incorrect. This cannot be "unknown", "N/A", "not known", etc. or have spaces before/after the text. It must either be the URL/DOI or just empty (as is expected in most cases)' %str(list(indices)))
else:
    # Check that data_DOI_URL starts with http, 10. or ftp.
    entity_tb_s = entity_tb.loc[entity_tb['data_DOI_URL'] != '',:]
    indices = [i for i, s in enumerate(entity_tb_s['data_DOI_URL']) if not (s.startswith('10.') | s.startswith('ftp') | s.startswith('http'))]
    indices = entity_tb_s.iloc[indices,:].index + 3
    if len(indices) > 0:
        warning_ctr += 1
        print('Entity metadata tab: the NOAA/PANGEA URL or DOI of the data in row %s is incorrect. The URL or DOI must start with either "10.", "ftp", or "http".' %str(list(indices))) 


# -----------------------------------------------------------------------------
# Section 7.i.c. Sample spreadsheet   
# -----------------------------------------------------------------------------
warning_ctr += check_values2list(sample_tb, 'hiatus', 'Sample data', ['H', ''], na_rm = True)  # added '' as np.nan was replaced by ''
warning_ctr += check_values2list(sample_tb, 'gap', 'Sample data', ['G', ''], na_rm = True)  # added '' as np.nan was replaced by ''
ent_ls = []
for i in entity_tb.index:
    ent_name = entity_tb['entity_name'][i]
    sample_tb_s = sample_tb.loc[sample_tb['entity_name'] == ent_name,:]
    if len(sample_tb_s.index) == 0:
        ent_ls.append(ent_name)
if len(ent_ls) > 0:
    warning_ctr += 1
    print('Sample data tab: Entity %s has no Sample data. This will only be accepted if this entity is part of a composite and its isotope data is to be submitted to SISAL soon. If this is the case (and no other warnings are issued), you can move the file into the Checked folder manually.' %str(ent_ls).replace('[','').replace(']','')) 




# _____________________________________________________________________________
#
# Section 7.ii. Check for composites
# _____________________________________________________________________________
if 'composite' in list(entity_tb['speleothem_type']):
    print('Informative: Notes tab: There is a composite in this workbook. Please list the entity_names/references (or entity_id if already in SISAL) of the records used to construct this composite in the Notes tab.')
ent_ls2 = []
for i in entity_tb.index:
    ent_name = entity_tb['entity_name'][i]
    speleothem_type = entity_tb['speleothem_type'][i]
    drip_type = entity_tb['drip_type'][i]
    dating_tb_s = dating_tb.loc[dating_tb['entity_name'] == ent_name,:]
    if speleothem_type == 'composite':
        print('Entity %s is a composite, checks will be done separatley. Ensure that individual records forming this composite are listed in the Notes tab.' %ent_name)
        if drip_type != 'not applicable':
            warning_ctr += 1
            print('Entity metadata tab: Entity %s is a composite. Drip type must be "not applicable".' %ent_name) 
        dating_tb_composite = dating_tb.loc[dating_tb['entity_name'] == ent_name,:]
        sample_tb_composite = sample_tb.loc[sample_tb['entity_name'] == ent_name,:]
        dating_lamina_tb_composite = dating_lamina_tb.loc[dating_lamina_tb['entity_name'] == ent_name,:]
        dating_tb = dating_tb.loc[dating_tb['entity_name'] != ent_name,:]
        sample_tb = sample_tb.loc[sample_tb['entity_name'] != ent_name,:]
        dating_lamina_tb = dating_lamina_tb.loc[dating_lamina_tb['entity_name'] != ent_name,:]
        # ---------------------------------------------------------------------
        # Section 7.ii.a. Sample spreadsheet
        # ---------------------------------------------------------------------
        warning_ctr += check_no_values(sample_tb_composite, 'Sample data', 'entity_name')
        warning_ctr += check_hiatusgaps_columns(sample_tb_composite, 'Sample data', 'gap', 'G', ['entity_name', 'gap'])
        sample_tb_composite_rm_gap = sample_tb_composite[(sample_tb_composite['gap'] == '')]
        a = check_no_values(sample_tb_composite_rm_gap, 'Sample data', 'modern_reference')  
        b = check_values2list(sample_tb_composite_rm_gap, 'modern_reference', 'Sample data', ['BP (1950)', 'b2k', 'CE/BCE', 'Year of chemistry'])
        warning_ctr += a + b
        if check_no_values(sample_tb_composite_rm_gap, 'Sample data', 'interp_age') == 0:
            if check_numbers(sample_tb_composite_rm_gap, 'Sample data', 'interp_age') == 0:
                if check_independent_dependent_col(sample_tb_composite_rm_gap, 'Sample data', 'interp_age', 'interp_age_uncert_pos') == 0:
                    if check_independent_dependent_col(sample_tb_composite_rm_gap, 'Sample data', 'interp_age', 'interp_age_uncert_neg') == 0:
                        if check_positivenumbers(sample_tb_composite_rm_gap, 'Sample data', 'interp_age_uncert_pos', na_rm = True) == 0:
                            if check_positivenumbers(sample_tb_composite_rm_gap, 'Sample data', 'interp_age_uncert_neg', na_rm = True) == 0:
                                check_notminmax_age(sample_tb_composite_rm_gap, 'interp_age', 'interp_age_uncert_pos', 'interp_age_uncert_neg', 'Sample', ent_name)
                            else:
                                warning_ctr += 1
                        else:
                            warning_ctr += 1
                    else:
                        warning_ctr += 1
                else:
                    warning_ctr += 1
                if a == 0:
                    if b == 0:
                        # convert to CE/BCE to BP(1950) first
                        sample_tb_composite_rm_gap.loc[sample_tb_composite_rm_gap['modern_reference'] == 'CE/BCE', 'interp_age'] = 1950 - sample_tb_composite_rm_gap.loc[sample_tb_composite_rm_gap['modern_reference'] == 'CE/BCE', 'interp_age'] 
                        warning_ctr += check_numbers_in_range(sample_tb_composite_rm_gap, 'Sample table', 'interp_age', -70, np.inf)
                        # Check if Sample data Modern_reference == 'Year of chemistry' that Year_done is filled in for the same entity in the Dating_information 
                        try:
                            warning_ctr += check_yearofchemistry_crosstable(sample_tb_composite_rm_gap.loc[sample_tb_composite_rm_gap['modern_reference'] == 'Year of chemistry',:], dating_tb_composite)
                        except:
                            warning_ctr += 1
                            print('Dating information and Sample data tab (composite entity): There is a problem checking chem_year when modern_reference is "Year of chemistry". Perhaps modern_reference is entirely missing. Please check.')
            else:
                warning_ctr += 1
        else:
            warning_ctr += 1
        warning_ctr += check_numbers(sample_tb_composite_rm_gap, 'Sample data', 'd18O_measurement')
        warning_ctr += check_numbers(sample_tb_composite_rm_gap, 'Sample data', 'd18O_precision')
        warning_ctr += check_numbers(sample_tb_composite_rm_gap, 'Sample data', 'd13C_measurement')
        warning_ctr += check_numbers(sample_tb_composite_rm_gap, 'Sample data', 'd13C_precision')
        
        warning_ctr += check_independent_dependent_col(sample_tb_composite_rm_gap, 'Sample data', independent_column='d18O_measurement', dependent_column='d18O_precision')
        warning_ctr += check_independent_dependent_col(sample_tb_composite_rm_gap, 'Sample data', 'd13C_measurement', 'd13C_precision')
        warning_ctr += check_independent_dependent_col(sample_tb_composite_rm_gap, 'Sample data', 'd18O_precision', 'd18O_measurement')
        warning_ctr += check_independent_dependent_col(sample_tb_composite_rm_gap, 'Sample data', 'd13C_precision', 'd13C_measurement')
        warning_ctr += check_independent_dependent_col(sample_tb_composite_rm_gap, 'Sample data', 'interp_age_uncert_neg', 'interp_age_uncert_pos')
        warning_ctr += check_independent_dependent_col(sample_tb_composite_rm_gap, 'Sample data', 'interp_age_uncert_pos', 'interp_age_uncert_neg')
        warning_ctr += check_independent_dependent_col(sample_tb_composite_rm_gap, 'Sample data', 'iso_std', 'd18O_measurement')
        warning_ctr += check_independent_dependent_col(sample_tb_composite_rm_gap, 'Sample data', 'iso_std', 'd13C_measurement')
        warning_ctr += check_Isotope_Checks(sample_tb_composite_rm_gap, 'iso_std', 'd18O_measurement', 'd13C_measurement')
        warning_ctr += check_values2list(sample_tb_composite_rm_gap, 'hiatus', 'Sample data', ['H', ''], na_rm = True) # added '' as np.nan was replaced by ''
        warning_ctr += check_values2list(sample_tb_composite_rm_gap, 'gap', 'Sample data', ['G', ''], na_rm = True) # added '' as np.nan was replaced by ''
# =============================================================================
#         #
# =============================================================================
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Check on sample table of composites
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if check_no_values(sample_tb_composite_rm_gap, 'Sample metadata', 'mineralogy', col_dtype_str_set = True) == 0:
            a1 = check_values2list(sample_tb_composite_rm_gap, 'mineralogy', 'Sample data', ['calcite', 'secondary calcite', 'aragonite', 'vaterite', 'mixed', 'unknown'])
        else:
            warning_ctr += 1
            a1 = 0
        if check_no_values(sample_tb_composite_rm_gap, 'Sample metadata', 'arag_corr', col_dtype_str_set = True) == 0:
            b1 = check_values2list(sample_tb_composite_rm_gap, 'arag_corr', 'Sample data', ['yes', 'no', 'not applicable', 'unknown'])
        else:
            warning_ctr += 1
            b1 = 0
        warning_ctr += a1 + b1
        if (a1 == 0) & (b1 == 0): # If the sample table excluding gaps have mineralogy and arag_corr
            # Check if mineralogy = 'calcite', 'secondary calcite' or 'vaterite', arag_corr must be 'not applicable'
            sample_calcite = sample_tb_composite_rm_gap.loc[(sample_tb_composite_rm_gap['mineralogy'] == 'calcite') | (sample_tb_composite_rm_gap['mineralogy'] == 'vaterite') | (sample_tb_composite_rm_gap['mineralogy'] == 'secondary calcite'), :]
            row_no = sample_calcite.loc[sample_calcite['arag_corr'] != 'not applicable',:].index
            if len(row_no) > 0:
                row_no = str([i+3 for i in row_no]).replace('[', '').replace(']', '')
                print('Sample data tab: if mineralogy is not "aragonite" or "mixed", arag_corr must be "not applicable". See row(s) %s' %row_no)
                warning_ctr += 1
            else:
                pass # all are 'not applicable'
            
            # Check if mineralogy = 'aragonite' or 'mixed', arag_corr is not 'not applicable'
            sample_calcite = sample_tb_composite_rm_gap.loc[(sample_tb_composite_rm_gap['mineralogy'] == 'aragonite') | (sample_tb_composite_rm_gap['mineralogy'] == 'mixed'), :]
            row_no = sample_calcite.loc[sample_calcite['arag_corr'] == 'not applicable',:].index
            if len(row_no) > 0:
                row_no = str([i+3 for i in row_no]).replace('[', '').replace(']', '')
                print('Sample data tab: if mineralogy = "aragonite" or "mixed", arag_corr must be something different than "not applicable". See row(s) %s' %row_no)
                warning_ctr += 1
            else:
                pass # all are 'not applicable'
            
            # Check if mineralogy = 'unknown' that arag_corr must be 'unknown'
            sample_calcite = sample_tb_composite_rm_gap.loc[(sample_tb_composite_rm_gap['mineralogy'] == 'mixed'), :]
            row_no = sample_calcite.loc[(sample_calcite['arag_corr'] == 'unknown')|(sample_calcite['arag_corr'] == 'yes'),:].index
            if len(row_no) > 0:
                print('Informative: Sample data tab: There are samples with mixed mineralogy where aragonite correction has been performed. Please make sure to give as much detail as possible in the notes section with regards to this.')
            else:
                pass # all are 'not applicable'
            # Check if mineralogy = 'unknown' that arag_corr must be 'unknown'
            sample_calcite = sample_tb_composite_rm_gap.loc[(sample_tb_composite_rm_gap['mineralogy'] == 'unknown'), :]
            row_no = sample_calcite.loc[sample_calcite['arag_corr'] != 'unknown',:].index
            if len(row_no) > 0:
                row_no = str([i+3 for i in row_no]).replace('[', '').replace(']', '')
                print('Sample data tab: if mineralogy = unknown, arag_corr cannot be anything other than "unknown". See row(s) %s' %row_no)
                warning_ctr += 1
            else:
                pass # all are 'not applicable'
#        warning_ctr += check_values2list(sample_tb_composite_rm_gap, 'mineralogy', 'Sample data', ['calcite', 'secondary calcite', 'aragonite', 'vaterite', 'mixed', 'unknown', ''], na_rm = True)  # added '' as np.nan was replaced by ''
# =============================================================================
#         #
# =============================================================================
        warning_ctr += check_values2list(sample_tb_composite_rm_gap, 'arag_corr', 'Sample data', ['yes', 'no', 'not applicable', 'unknown'])
        warning_ctr += check_values2list(sample_tb_composite_rm_gap, 'age_model_type', 'Sample data', ['linear', 'linear between dates', 'polynomial fit', 'polynomial fit omitting outliers', 'Bayesian', 'Bayesian Bacon', 'Bayesian Bchron', 'StalAge', 'StalAge and other', 'Clam', 'COPRA', 'OxCal', 'combination of methods', 'unknown', 'other'])
        if check_no_values(sample_tb_composite_rm_gap, 'Sample data', 'ann_lam_check', col_dtype_str_set = True) == 0:
            warning_ctr += check_values2list(sample_tb_composite_rm_gap, 'ann_lam_check', 'Sample data', ['14C peak', '14C slope', 'U/Th cycle', 'trace element cycle', 'assumed', 'unknown', 'not applicable', 'other'])
        else:
            warning_ctr += 1
        if check_no_values(sample_tb_composite_rm_gap, 'Sample data', 'dep_rate_check', col_dtype_str_set = True) == 0:
            warning_ctr += check_values2list(sample_tb_composite_rm_gap, 'dep_rate_check', 'Sample data', ['yes', 'no', 'assumed', 'unknown', 'not applicable'])
        else:
            warning_ctr += 1
        warning_ctr += check_values2list(sample_tb_composite_rm_gap, 'iso_std', 'Sample data', ['PDB', 'Vienna-PDB'])
        # ---------------------------------------------------------------------
        # Section 7.ii.b. Dating spreadsheet
        # ---------------------------------------------------------------------
        if len(dating_tb_composite.index) > 0:
            warning_ctr += 1
            print('Dating information tab: Something has been entered in the dating spreadsheet for the composite entity %s. This should be left empty for composites.' %ent_name)
        # ---------------------------------------------------------------------
        # Section 7.ii.c. Lamina age vs depth spreadsheet
        # ---------------------------------------------------------------------
        if len(dating_lamina_tb_composite.index) > 0:
            warning_ctr += 1
            print('Lamina age vs depth tab: Something has been entered in the lamina age vs depth spreadsheet for the composite entity %s, This should be left empty for composites.' %ent_name)
    else:
        if drip_type == 'not applicable':
            warning_ctr += 1
            print('Entity metadata tab: Entity %s is not a composite and drip type cannot be "not applicable".' %ent_name) 
        if len(dating_tb_s.index) == 0:
            ent_ls2.append(ent_name)
        pass

if len(ent_ls2) > 0:
    warning_ctr += 1
    print('Sample data tab: Entity %s is not a composite and has no Dating information data. This will only be accepted in very special cases. If this is the only warning (and dating info is really not retrievable) move the workbook to the Checked folder manually.' %str(ent_ls2).replace('[','').replace(']','')) 


# _____________________________________________________________________________
#
# Section 7.iii. Check for non-composites
# _____________________________________________________________________________

# -----------------------------------------------------------------------------
# Section 7.iii.a. Site spreadsheet 
# -----------------------------------------------------------------------------
# NONE, all checks for sites are performed irrespect of the entity

# -----------------------------------------------------------------------------
# Section 7.iii.b. Entity spreadsheet
# -----------------------------------------------------------------------------
# NONE, all checks for entities are performed above.

# -----------------------------------------------------------------------------
# Section 7.iii.c. Sample spreadsheet
# -----------------------------------------------------------------------------

if len(sample_tb.index) > 0:
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.1. Check on sample table (full) 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    warning_ctr += check_no_values(sample_tb, 'Sample data', 'entity_name')
    # Check that depth_sample is in mm not cm or m
    for i in set(sample_tb['entity_name']):
        if max(sample_tb.loc[sample_tb['entity_name'] == i,'depth_sample']) - min(sample_tb.loc[sample_tb['entity_name'] == i,'depth_sample']) <= 100:
#            warning_ctr += 1
            print('Informative: Sample data tab: The total length of Entity %s is less than 100mm. This is either a very small speleothem or the depths are in cm.' %i)
    # Check depth_sample values
    pass_depthsample_checks = False
    if check_no_values(sample_tb, 'Sample data', 'depth_sample') == 0:
        pass_depthsample_checks = True
        if check_numbers(sample_tb, 'Sample data', 'depth_sample') == 0:
            warning_ctr += check_positivenumbers(sample_tb, 'Sample data', 'depth_sample')
        else:
            warning_ctr += 1
    else:
        warning_ctr += 1

    warning_ctr += check_hiatusgaps_columns(sample_tb, 'Sample data', 'hiatus', 'H', ['entity_name', 'depth_sample', 'hiatus'])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.2. Check on sample table (excluding hiatuses) 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    sample_tb_rm_hiatus = sample_tb.loc[sample_tb['hiatus'] != 'H']
    if check_no_values(sample_tb_rm_hiatus, 'Sample metadata', 'mineralogy', col_dtype_str_set = True) == 0:
        a1 = check_values2list(sample_tb_rm_hiatus, 'mineralogy', 'Sample data', ['calcite', 'secondary calcite', 'aragonite', 'vaterite', 'mixed', 'unknown'])
    else:
        warning_ctr += 1
        a1 = 0
    if check_no_values(sample_tb_rm_hiatus, 'Sample metadata', 'arag_corr', col_dtype_str_set = True) == 0:
        b1 = check_values2list(sample_tb_rm_hiatus, 'arag_corr', 'Sample data', ['yes', 'no', 'not applicable', 'unknown'])
    else:
        warning_ctr += 1
        b1 = 0
    warning_ctr += a1 + b1
    if (a1 == 0) & (b1 == 0): # If the sample table excluding hiatuses have mineralogy and arag_corr
        # Check if mineralogy = 'calcite', 'secondary calcite' or 'vaterite', arag_corr must be 'not applicable'
        sample_calcite = sample_tb_rm_hiatus.loc[(sample_tb_rm_hiatus['mineralogy'] == 'calcite') | (sample_tb_rm_hiatus['mineralogy'] == 'vaterite') | (sample_tb_rm_hiatus['mineralogy'] == 'secondary calcite'), :]
        row_no = sample_calcite.loc[sample_calcite['arag_corr'] != 'not applicable',:].index
        if len(row_no) > 0:
            row_no = str([i+3 for i in row_no]).replace('[', '').replace(']', '')
            print('Sample data tab: if mineralogy is not "aragonite" or "mixed", arag_corr must be "not applicable". See row(s) %s' %row_no)
            warning_ctr += 1
        else:
            pass # all are 'not applicable'
        
        # Check if mineralogy = 'aragonite' or 'mixed', arag_corr is not 'not applicable'
        sample_calcite = sample_tb_rm_hiatus.loc[(sample_tb_rm_hiatus['mineralogy'] == 'aragonite') | (sample_tb_rm_hiatus['mineralogy'] == 'mixed'), :]
        row_no = sample_calcite.loc[sample_calcite['arag_corr'] == 'not applicable',:].index
        if len(row_no) > 0:
            row_no = str([i+3 for i in row_no]).replace('[', '').replace(']', '')
            print('Sample data tab: if mineralogy = "aragonite" or "mixed", arag_corr must be something different than "not applicable". See row(s) %s' %row_no)
            warning_ctr += 1
        else:
            pass # all are 'not applicable'
        
        # Check if mineralogy = 'unknown' that arag_corr must be 'unknown'
        sample_calcite = sample_tb_rm_hiatus.loc[(sample_tb_rm_hiatus['mineralogy'] == 'mixed'), :]
        row_no = sample_calcite.loc[(sample_calcite['arag_corr'] == 'unknown')|(sample_calcite['arag_corr'] == 'yes'),:].index
        if len(row_no) > 0:
            print('Informative: Sample data tab: There are samples with mixed mineralogy where aragonite correction has been performed. Please make sure to give as much detail as possible in the notes section with regards to this.')
        else:
            pass # all are 'not applicable'
        # Check if mineralogy = 'unknown' that arag_corr must be 'unknown'
        sample_calcite = sample_tb_rm_hiatus.loc[(sample_tb_rm_hiatus['mineralogy'] == 'unknown'), :]
        row_no = sample_calcite.loc[sample_calcite['arag_corr'] != 'unknown',:].index
        if len(row_no) > 0:
            row_no = str([i+3 for i in row_no]).replace('[', '').replace(']', '')
            print('Sample data tab: if mineralogy = unknown, arag_corr cannot be anything other than "unknown". See row(s) %s' %row_no)
            warning_ctr += 1
        else:
            pass # all are 'not applicable'
    # Check that the numbers columns are filled in properly
    samplecolumnnameslist = ['d18O_measurement', 'd13C_measurement']
    for i in samplecolumnnameslist:
        warning_ctr += check_numbers(sample_tb_rm_hiatus, 'Sample data', i)
    # Check for positive numbers
    samplecolumnnameslist2 = ['interp_age_uncert_pos', 'interp_age_uncert_neg', 'sample_thickness', 'd18O_precision',
                             'd13C_precision']
    for i in samplecolumnnameslist2:
        if check_numbers(sample_tb_rm_hiatus, 'Sample data', i) == 0:
            warning_ctr += check_positivenumbers(sample_tb_rm_hiatus, 'Sample data', i, na_rm = True)
        else:
            warning_ctr += 1
    # Check for precision/measurements co-existing
    warning_ctr += check_independent_dependent_col(sample_tb_rm_hiatus, 'Sample data', independent_column='d18O_measurement', dependent_column='d18O_precision')
    warning_ctr += check_independent_dependent_col(sample_tb_rm_hiatus, 'Sample data', 'd13C_measurement', 'd13C_precision')
    warning_ctr += check_independent_dependent_col(sample_tb_rm_hiatus, 'Sample data', 'd18O_precision', 'd18O_measurement')
    warning_ctr += check_independent_dependent_col(sample_tb_rm_hiatus, 'Sample data', 'd13C_precision', 'd13C_measurement')
    warning_ctr += check_independent_dependent_col(sample_tb_rm_hiatus, 'Sample data', 'interp_age_uncert_neg', 'interp_age_uncert_pos')
    warning_ctr += check_independent_dependent_col(sample_tb_rm_hiatus, 'Sample data', 'interp_age_uncert_pos', 'interp_age_uncert_neg')
    warning_ctr += check_independent_dependent_col(sample_tb_rm_hiatus, 'Sample data', 'iso_std', 'd18O_measurement')
    warning_ctr += check_independent_dependent_col(sample_tb_rm_hiatus, 'Sample data', 'iso_std', 'd13C_measurement')
    warning_ctr += check_Isotope_Checks(sample_tb_rm_hiatus, 'iso_std', 'd18O_measurement', 'd13C_measurement')
    warning_ctr += check_values2list(sample_tb_rm_hiatus, 'iso_std', 'Sample data', ['PDB', 'Vienna-PDB'])
    # Check that there are no 'gaps' in the normal entities
    if sample_tb_rm_hiatus.loc[sample_tb_rm_hiatus['gap'] == 'G',:].shape[0] > 0:
        print('Sample data tab: A gap column is filled in with non-composite entities. Check if this should be a hiatus instead.')
        warning_ctr += 1
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.3. Check on sample table (entities with no age model)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    sample_tb_no_agemodel = sample_tb.copy()
    sample_tb_rm_hiatus_agemodel = sample_tb_rm_hiatus.copy()
    for i in set(sample_tb_rm_hiatus['entity_name']):
        sample_tb_rm_hiatus_ent = sample_tb_rm_hiatus.loc[sample_tb_rm_hiatus['entity_name'] == i, :]
        if all(pd.isnull(sample_tb_rm_hiatus_ent['interp_age'])):
            # Excludes entities with no age models from future checks ---------
            sample_tb_no_agemodel = sample_tb_no_agemodel.loc[sample_tb_no_agemodel['entity_name'] != i, :]
            sample_tb_rm_hiatus_agemodel = sample_tb_rm_hiatus_agemodel.loc[sample_tb_rm_hiatus_agemodel['entity_name'] != i, :]
            # Check for repeated depths when there is no age model
            warning_ctr += check_no_repeated_records(sample_tb.loc[sample_tb['entity_name'] == i, :], 'Sample data', i, 'depth_sample')
            warning_ctr += 1
            print('Sample data tab: Entity %s is likely missing an age model. This is not allowed except for some VERY special cases. No more checks will be done for this entity. Please add a dummy age-depth model to make sure that all other checks can be performed. IMPORTANT: Do not forget to delete the dummy age-depth model from the workbook once it has passed all checks!' %i)
            if all(pd.notnull(sample_tb_rm_hiatus_ent['interp_age_uncert_pos'])):
                print('Sample data tab: If entity %s has no age model, interp_age_uncert_pos should be empty.' %i)
            if all(pd.notnull(sample_tb_rm_hiatus_ent['interp_age_uncert_neg'])):
                print('Sample data tab: If entity %s has no age model, interp_age_uncert_neg should be empty' %i)
            if all(pd.notnull(sample_tb_rm_hiatus_ent['age_model_type'])):
                print('Sample data tab: Entity %s is likely missing an age model (i.e. no interp_ages). If this is correct, age_model_type should be empty.' %i)
            if all(sample_tb_rm_hiatus_ent['modern_reference'] != ''):
                print('Sample data tab: Entity %s is likely missing an age model (i.e. no interp_ages). If this is correct, modern_reference should be empty.' %i)
            if all(sample_tb_rm_hiatus_ent['ann_lam_check'] != ''):
                print('Sample data tab: Entity %s is likely missing an age model (i.e. no interp_ages). If this is correct, ann_lam_check should be empty.' %i)            
            if all(sample_tb_rm_hiatus_ent['dep_rate_check'] != ''):
                print('Sample data tab: Entity %s is likely missing an age model (i.e. no interp_ages). If this is correct, dep_rate_check should be empty.' %i)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.4. Check on sample table (excluding hiatuses and entities with no agemodel)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if check_no_values(sample_tb_rm_hiatus_agemodel, 'Sample data', 'modern_reference') == 0:
        check_modref = check_values2list(sample_tb_rm_hiatus_agemodel, 'modern_reference', 'Sample data', ['BP (1950)', 'b2k', 'CE/BCE', 'Year of chemistry'])
    else:
        warning_ctr += 1
        check_modref = 0
    warning_ctr += check_modref
    check_interp_age = False
    if check_no_values(sample_tb_rm_hiatus_agemodel, 'Sample data', 'interp_age') == 0:
        if check_numbers(sample_tb_rm_hiatus_agemodel, 'Sample data', 'interp_age') == 0:
            if check_independent_dependent_col(sample_tb_rm_hiatus_agemodel, 'Sample data', 'interp_age', 'interp_age_uncert_pos') == 0:
                if check_independent_dependent_col(sample_tb_rm_hiatus_agemodel, 'Sample data', 'interp_age', 'interp_age_uncert_neg') == 0:
                    check_interp_age = True
                else:
                    warning_ctr += 1
            else:
                warning_ctr += 1
        else:
            warning_ctr += 1
    else:
        warning_ctr += 1                     
    if check_modref == 0:
        if check_interp_age:
            # if modern_reference is CE/BCE, the ages must be converted to BP(1950) before performing checks
            sample_tb_rm_hiatus_agemodel.loc[sample_tb_rm_hiatus_agemodel['modern_reference'] == 'CE/BCE','interp_age'] = 1950 - sample_tb_rm_hiatus_agemodel.loc[sample_tb_rm_hiatus_agemodel['modern_reference'] == 'CE/BCE','interp_age'] 
            warning_ctr += check_numbers_in_range(sample_tb_rm_hiatus_agemodel.loc[sample_tb_rm_hiatus_agemodel['hiatus'] != 'H',:], 'Sample table', 'interp_age', -70, np.inf)
    
    # Check that values are from lists
    warning_ctr += check_values2list(sample_tb_rm_hiatus_agemodel, 'age_model_type', 'Sample data', ['linear', 'linear between dates', 'polynomial fit', 'polynomial fit omitting outliers', 'Bayesian', 'Bayesian Bacon', 'Bayesian Bchron', 'StalAge', 'StalAge and other', 'Clam', 'COPRA', 'OxCal', 'combination of methods', 'unknown', 'other'])
    if check_no_values(sample_tb_rm_hiatus_agemodel, 'Sample data', 'ann_lam_check', col_dtype_str_set = True) == 0:
        warning_ctr += check_values2list(sample_tb_rm_hiatus_agemodel, 'ann_lam_check', 'Sample data', ['14C peak', '14C slope', 'U/Th cycle', 'trace element cycle', 'assumed', 'unknown', 'not applicable', 'other'])
    else:
        warning_ctr += 1
    if check_no_values(sample_tb_rm_hiatus_agemodel, 'Sample data', 'dep_rate_check', col_dtype_str_set = True) == 0:
        warning_ctr += check_values2list(sample_tb_rm_hiatus_agemodel, 'dep_rate_check', 'Sample data', ['yes', 'no', 'assumed', 'unknown', 'not applicable'])
    else:
        warning_ctr += 1
    # Check if Sample data Modern_reference == 'Year of chemistry' that Year_done is filled in for the same entity in the Dating_information 
    sample_tb_subset = sample_tb_rm_hiatus_agemodel.loc[(sample_tb_rm_hiatus_agemodel['modern_reference'] == 'Year of chemistry') & (sample_tb_rm_hiatus_agemodel['hiatus'] != 'H'),:] #EDIT
    try:
        warning_ctr += check_yearofchemistry_crosstable(sample_tb_subset, dating_tb)
    except:
        warning_ctr += 1
        print('Dating information and Sample data tab: There is a problem checking chem_year when modern_reference is "Year of chemistry". Perhaps modern_reference is entirely missing. Please check.')
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.5. Check on sample table (excluding entities with no agemodel, including hiatuses)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for i in set(sample_tb_no_agemodel['entity_name']):
        sample_tb_subset = sample_tb_no_agemodel.loc[sample_tb['entity_name'] == i,:]
        warning_ctr += check_notminmax_age(sample_tb_subset, 'interp_age', 'interp_age_uncert_pos', 'interp_age_uncert_neg', 'Sample', i)
        depth_ref = entity_tb.loc[entity_tb['entity_name'] == i,'depth_ref'].values[0]
        a = check_no_repeated_records(sample_tb_subset, 'Sample data', i, 'depth_sample')
        b = check_no_repeated_records(sample_tb_subset, 'Sample data', i, 'interp_age')
        warning_ctr += a + b
        sample_tb_subset_rm_hiatus = sample_tb_subset.loc[(sample_tb_subset['hiatus'] != 'H'),:]
        # if modern_reference is CE/BCE, the ages must be converted to BP(1950) before performing checks
        sample_tb_subset_rm_hiatus.loc[sample_tb_subset_rm_hiatus['modern_reference'] == 'CE/BCE','interp_age'] = 1950 - sample_tb_subset_rm_hiatus.loc[sample_tb_subset_rm_hiatus['modern_reference'] == 'CE/BCE','interp_age'] 
        if a == 0:
            if b == 0:
                further_check = True
                if depth_ref == 'from top':
                    sample_tb_subset_rm_hiatus = sample_tb_subset_rm_hiatus.loc[pd.to_numeric(sample_tb_subset_rm_hiatus['depth_sample'], errors = 'coerce').notnull(),:].sort_values(by = ['depth_sample'], ascending = True)
                elif depth_ref == 'from base':
                    sample_tb_subset_rm_hiatus = sample_tb_subset_rm_hiatus.loc[pd.to_numeric(sample_tb_subset_rm_hiatus['depth_sample'], errors = 'coerce').notnull(),:].sort_values(by = ['depth_sample'], ascending = False)
                else:
                    further_check = False
                if further_check == True:
                    if (np.mean(np.diff(sample_tb_subset_rm_hiatus['interp_age'])) <= 0):
                        print("Sample data tab: Entity %s. depth_ref likely wrong. The oldest speleothem sample cannot be the one at the top! Further checks cannot be completed until this is fixed." %i)
                        warning_ctr += 1
                    else:
                        warning_ctr += check_ages_and_depths_in_order(sample_tb_subset_rm_hiatus, 'depth_sample', 'interp_age', depth_ref, 'Sample data', i)
                        warning_ctr += check_possible_hiatuses(sample_tb_subset, 'depth_sample', 'interp_age', 'hiatus', depth_ref, i)
        if any(pd.isnull(sample_tb_subset_rm_hiatus['interp_age_uncert_neg'])):
            print('Informative: Sample data tab: Entity %s; Excluding hiatuses, there are missing interp_age uncertainties. This is possible but please make sure that you have tried your best to obtain this information' %i)
else:
    # If sample table is empty, then create a copy of sample_tb_rm_hiatus_agemodel
    # as it is being called later on
    sample_tb_rm_hiatus_agemodel = sample_tb.copy()
# -----------------------------------------------------------------------------
# Section 7.iii.d. Dating spreadsheet
# -----------------------------------------------------------------------------
if len(dating_tb.index) > 0:
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.1. Check on dating table (full) 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Check date_type exists and from dropdown list
    pass_datetype_warning = False
    if check_no_values(dating_tb, 'Dating information', 'date_type', True) == 0:
        warning_ctr += check_values2list(dating_tb, 'date_type', 'Dating information', ['C14', 'MC-ICP-MS U/Th', 'ICP-MS U/Th Other', 'Alpha U/Th', 'TIMS', 'U/Th unspecified', 'Cross-dating', 'Multiple methods', 'Event; hiatus', 'Event; gap (composite record)', 'Event; actively forming', 'Event; start of laminations', 'Event; end of laminations', 'unknown', 'other'])
        pass_datetype_warning = True
    else:
        warning_ctr += 1
    # Check date_used exists and from dropdown list
    pass_dateused_warning = False
    if check_no_values(dating_tb, 'Dating information', 'date_used', True) == 0:
        warning_ctr += check_values2list(dating_tb, 'date_used', 'Dating information', y_n_nk_list)
        pass_dateused_warning = True
    else:
        warning_ctr += 1
    # Check for entity_name
    pass_depthdating_warning = False
    if check_no_values(dating_tb, 'Dating information', 'depth_dating') == 0:
        pass_depthdating_warning = True
        # Check that depth_dating is a number and is a positive number
        if check_numbers(dating_tb, 'Dating information', 'depth_dating') == 0:
            warning_ctr += check_positivenumbers(dating_tb, 'Dating information', 'depth_dating')
        else:
            warning_ctr += 1
    else:
        warning_ctr += 1
    # Check for entity_name
    pass_entityname_warning = False
    if check_no_values(dating_tb, 'Dating information', 'entity_name', True) == 0:
        pass_entityname_warning = True
    else:
        warning_ctr += 1
    if pass_datetype_warning:
        if pass_dateused_warning:
            if pass_entityname_warning:
                if pass_depthdating_warning:
                    # Check that the rows with 'Event; hiatus' or 'Event; gap', etc. are filled in properly
                    warning_ctr += check_hiatusgaps_columns(dating_tb, 'Dating information', 'date_type', 'Event; hiatus', ['entity_name', 'depth_dating', 'date_used', 'date_type'])
                    warning_ctr += check_hiatusgaps_columns(dating_tb, 'Dating information', 'date_type', 'Event; actively forming', ['entity_name', 'depth_dating', 'date_used', 'date_type', 'corr_age', 'corr_age_uncert_pos', 'corr_age_uncert_neg', 'modern_reference'], ['chem_year'])
                    warning_ctr += check_hiatusgaps_columns(dating_tb, 'Dating information', 'date_type', 'Event; start of laminations', ['entity_name', 'depth_dating', 'date_used', 'date_type', 'corr_age', 'corr_age_uncert_pos', 'corr_age_uncert_neg', 'modern_reference'], ['chem_year'])
                    warning_ctr += check_hiatusgaps_columns(dating_tb, 'Dating information', 'date_type', 'Event; end of laminations', ['entity_name', 'depth_dating', 'date_used', 'date_type', 'corr_age', 'corr_age_uncert_pos', 'corr_age_uncert_neg', 'modern_reference'], ['chem_year'])
                    warning_ctr += check_hiatusgaps_columns(dating_tb, 'Dating information', 'date_type', 'other', ['entity_name', 'depth_dating', 'date_used', 'date_type', 'corr_age', 'modern_reference'], ['dating_thickness', 'material_dated', 'min_weight', 'max_weight', 'corr_age_uncert_neg', 'corr_age_uncert_pos', 'lab_num'])

    # Check that min_weight and max_weight coexists and min_weight cannot be greater than max_weight
    if check_independent_dependent_col(dating_tb, 'Dating information', 'min_weight', 'max_weight') == 0:
        if check_independent_dependent_col(dating_tb, 'Dating information', 'max_weight', 'min_weight') == 0:
            dating_idx_weight = dating_tb.loc[dating_tb.min_weight > dating_tb.max_weight,:].index
            if len(dating_idx_weight) > 0:
                warning_ctr += 1
                print('Dating information tab: min_weight is greater than max_weight at row %s' %(str(list(dating_idx_weight))))
        else:
            warning_ctr += 1
    else:
        warning_ctr += 1
    # Check that uncorr_age are numeric (np.nan is considered a number)
    warning_ctr += check_numbers(dating_tb, 'Dating information', 'uncorr_age')
    warning_ctr += check_numbers(dating_tb, 'Dating information', 'corr_age')
    # Check for positive numbers
    datingcolumnnameslist2 = ['dating_thickness', 'min_weight','max_weight', '14C_correction',
                  'uncorr_age_uncert_pos', 'uncorr_age_uncert_neg', '238U_content','238U_uncertainty',
                  '232Th_content', '232Th_uncertainty', '230Th_content', '230Th_uncertainty',
                  '230Th_232Th_ratio','230Th_232Th_ratio_uncertainty', '230Th_238U_activity', '230Th_238U_activity_uncertainty',
                  '234U_238U_activity', '234U_238U_activity_uncertainty', 'ini_230Th_232Th_ratio',	'ini_230Th_232Th_ratio_uncertainty', 
                  'corr_age_uncert_pos', 'corr_age_uncert_neg','chem_year']
    for j in datingcolumnnameslist2:
        if check_numbers(dating_tb, 'Dating information', j) == 0:
            warning_ctr += check_positivenumbers(dating_tb, 'Dating information', j, na_rm = True)
        else:
            warning_ctr += 1
    # Check that measurements are being filled in properly
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', 'uncorr_age', 'uncorr_age_uncert_pos')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', 'uncorr_age', 'uncorr_age_uncert_neg')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', '234U_238U_activity', '234U_238U_activity_uncertainty')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', 'ini_230Th_232Th_ratio', 'ini_230Th_232Th_ratio_uncertainty')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', '238U_content', '238U_uncertainty')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', '232Th_content', '232Th_uncertainty')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', '230Th_content', '230Th_uncertainty')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', '230Th_232Th_ratio', '230Th_232Th_ratio_uncertainty')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', '230Th_238U_activity', '230Th_238U_activity_uncertainty')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', 'corr_age', 'corr_age_uncert_pos')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', 'corr_age', 'corr_age_uncert_neg')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', 'corr_age_uncert_pos', 'corr_age_uncert_neg')
    warning_ctr += check_independent_dependent_col(dating_tb, 'Dating information', 'corr_age_uncert_neg', 'corr_age_uncert_pos')
    # check if there are modern_reference when there are corr_age
    if check_independent_dependent_col(dating_tb, 'Dating information', 'modern_reference', 'corr_age') == 0:
        # check if modern_reference is from dropdown list. na_rm = True as it can be empty if there are no corr_age
        warning_ctr += check_values2list(dating_tb, 'modern_reference', 'Dating information', ['BP (1950)', 'b2k', 'CE/BCE', 'Year of chemistry'], na_rm = True)
    try:
        # Check if Dating information/Lamina age vs depth Modern_reference == 'Year of chemistry' that Year_done is filled in 
        warning_ctr += check_yearofchemistry_crosstable(dating_tb, dating_tb)
    except:
        warning_ctr += 1
        print('Dating information tab: There is a problem checking chem_year when modern_reference is "Year of chemistry". Perhaps modern_reference is entirely missing. Please check.')
    # Check if values are from list
    warning_ctr += check_values2list(dating_tb, 'calib_used', 'Dating information', ['INTCAL13 NH', 'INTCAL13 SH', 'INTCAL13 marine', 'INTCAL09', 'INTCAL09 marine', 'INTCAL04 NH', 'INTCAL04 SH', 'INTCAL98', 'FAIRBANKS09', 'not calibrated', 'other', 'unknown', ''], na_rm = True)  # added '' as np.nan was replaced by ''
    # Check that for each entity that corr_age_uncert_pos and neg are not min and max ages
    for i in set(dating_tb['entity_name']):
        warning_ctr += check_notminmax_age(dating_tb.loc[dating_tb['entity_name'] == i,:], 'corr_age', 'corr_age_uncert_pos', 'corr_age_uncert_neg', 'Dating', i)
        warning_ctr += check_notminmax_age(dating_tb.loc[dating_tb['entity_name'] == i,:], 'uncorr_age', 'uncorr_age_uncert_pos', 'uncorr_age_uncert_neg', 'Dating', i)
    # Check that corr_age is in range
    # if modern_reference is CE/BCE, the ages must be converted to BP(1950) before performing checks
    dating_tb.loc[dating_tb['modern_reference'] == 'CE/BCE','corr_age'] = 1950 - dating_tb.loc[dating_tb['modern_reference'] == 'CE/BCE','corr_age'] 
    dating_tb.loc[dating_tb['modern_reference'] == 'CE/BCE','modern_reference'] = 'BP(1950)'
    warning_ctr += check_numbers_in_range(dating_tb.loc[(dating_tb['date_type'] != 'Event; hiatus') & ((dating_tb['date_used'] == 'yes') | (dating_tb['date_used'] == 'unknown')),:], 'Dating information table', 'corr_age', -70, np.inf)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.2. Check on dating table (excluding date_type LIKE ‘Event; %’)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    events_list = ['Event; gap (composite record)', 'Event; hiatus', 'Event; actively forming', 'Event; start of laminations', 'Event; end of laminations']
    ctr = 0
    for p in events_list:
        ctr += 1
        if ctr == 1:
            dating_tb_subset_no_events = dating_tb.loc[(dating_tb['date_type'] != p), :]
        else:
            dating_tb_subset_no_events = dating_tb_subset_no_events.loc[(dating_tb_subset_no_events['date_type'] != p), :]
    if dating_tb_subset_no_events.shape[0] > 0:
        warning_ctr += check_values2list(dating_tb_subset_no_events, 'material_dated', 'Dating information', ['calcite', 'aragonite', 'organic', 'other', 'unknown'])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.3. Check on dating table (excluding where date_used = 'no' and date_type = 'Event; hiatus') 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    dating_tb_useinagemodel = dating_tb.loc[(dating_tb['date_used'] != 'no') & (dating_tb['date_type'] != 'Event; hiatus')& (dating_tb['date_type'] != 'Event; gap (composite record'),:]
    if len(dating_tb_useinagemodel.index) > 0:
        for k in ['corr_age', 'corr_age_uncert_pos', 'corr_age_uncert_neg', 'modern_reference']:
            sub_tb = dating_tb_useinagemodel.loc[pd.isnull(dating_tb_useinagemodel[k]),:]
            number_of_rows = len(sub_tb.index)
            if number_of_rows > 0:
                Row_numbers = str(list(sub_tb.index + 3)).replace('[','').replace(']', '')
                print('Dating information tab: %s is not filled in when date_used = "yes" or "unknown". %d row(s). row: %s' %(k, number_of_rows, Row_numbers))
                warning_ctr += 1
    for i in set(dating_tb['entity_name']):
        dating_tb_hiatus = dating_tb_useinagemodel.loc[(dating_tb_useinagemodel['entity_name'] == i),:]
        if len(dating_tb_hiatus.index) == 0:
            warning_ctr += 1
            print('Dating information tab: Entity %s has no dating info other than hiatuses and/or not used dates. This is not allowed except for very special cases where the entity is missing an age model.' %(i))
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.4. Check integrity of dating table based on date_used
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    dating_c14 = dating_tb.loc[(dating_tb['date_type'] == 'C14'), :]
    # Where date_used == 'C14'
    if dating_c14.shape[0] > 0:
        warning_ctr += check_values2list(dating_c14, 'calib_used', 'Dating information', ['INTCAL13 NH', 'INTCAL13 SH', 'INTCAL13 marine', 'INTCAL09', 'INTCAL09 marine', 'INTCAL04 NH', 'INTCAL04 SH', 'INTCAL98', 'FAIRBANKS09', 'not calibrated', 'other', 'unknown'])
    else:
        pass # there are no C14 dates in this workbook
    # Where date_used != 'C14'
    dating_notc14 = dating_tb.loc[(dating_tb['date_type'] != 'C14'), :]
    if dating_notc14.shape[0] > 0:
        tb_empty = dating_notc14.loc[dating_notc14['calib_used'] != '',:]
        tb_notempty = dating_notc14.loc[pd.notnull(dating_notc14['14C_correction']),:]
        if tb_empty.shape[0] > 0:
            row_no = str([i+3 for i in tb_empty.index]).replace('[', '').replace(']', '')
            warning_ctr += 1
            print('Dating information tab: calib_used must be empty when date_type is not C14. See row(s) %s' %row_no)
        if tb_notempty.shape[0] > 0:
            row_no = str([i+3 for i in tb_notempty.index]).replace('[', '').replace(']', '')
            warning_ctr += 1
            print('Dating information tab: 14C_correction must be empty when date_type is not C14. See row(s) %s' %row_no)
    else:
        pass # There are only C14 dates
    # Where date_used is of U/Th type (has U/Th in it or 'TIMS')
    # Create an set of indices (faster)
    indices = [i for i, s in enumerate(dating_tb['date_type']) if (('U/Th' in s) | (s == 'TIMS'))]
    dating_uth = dating_tb.iloc[indices,:]
    if dating_uth.shape[0] > 0:
    #    warning_ctr += check_no_values(dating_uth, 'Dating information', 'decay_constant')
        tb_empty = dating_uth.loc[pd.isnull(dating_uth['decay_constant']),:]
        if len(tb_empty.index) > 0:
            row_no = str([i+3 for i in tb_empty.index]).replace('[', '').replace(']', '')
            warning_ctr += 1
            print('Dating information tab: decay_constant must be filled in when date_type is of U/Th type. See row(s) %s' %row_no)
        else:
            warning_ctr += check_values2list(dating_uth, 'decay_constant', 'Dating information', ['Cheng et al. 2000', 'Cheng et al. 2013', 'Edwards et al. 1987', 'Ivanovich & Harmon 1992', 'other', 'unknown'])
    else:
        pass
    # Where date_used is of U/Th type (does not have 'U/Th' in it or is not 'TIMS')
    # Create an set of indices (faster)
    indices = [i for i, s in enumerate(dating_tb['date_type']) if (('U/Th' not in s) & (s != 'TIMS'))]
    dating_notuth = dating_tb.iloc[indices,:]
    if dating_notuth.shape[0] > 0:
        tb_empty = dating_notuth.loc[pd.notnull(dating_notuth['decay_constant']),:]
        if tb_empty.shape[0] > 0:
            row_no = str([i+3 for i in tb_empty.index]).replace('[', '').replace(']', '')
            warning_ctr += 1
            print('Dating information tab: decay_constant must be empty when date_type is not of U/Th type. See row(s) %s' %row_no)
    else:
        pass # There are only C14 or event date types
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.5. Check no hiatuses at the same depth as dates
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Dating information table
    # Make sure that for each entity, that no hiatuses have the same depth as dates
    # 1. Loop through each entity in the dating information table
    #   i.  subset the dating information table into two tables; hiatuses, and not 
    #       hiatuses.
    #   ii. check if depth_dating for the table with hiatuses are not duplicated.
    #       If they are not:
    #       a. Loop through each depth_dating for the table with hiatuses
    #           - see if the depth exist in depths of table with no hiatuses
    #
    warning_ctr_bef = warning_ctr
    for i in pd.unique(dating_tb['entity_name']):
        depth_ent_hiat = dating_tb.loc[(dating_tb['entity_name'] == i) & (dating_tb['date_type'] == 'Event; hiatus'), 'depth_dating']
        if len(depth_ent_hiat.index) == 0: # used len(dataframe.index) instead of dataframe.empty as it is faster
            pass
        else:
            depth_ent_nohiat = dating_tb.loc[(dating_tb['entity_name'] == i) & (dating_tb['date_type'] != 'Event; hiatus'), 'depth_dating']
            if len(depth_ent_hiat) != len(set(depth_ent_hiat)):
                depth_ent_ls = []
                for j in set(depth_ent_hiat):
                    if list(depth_ent_hiat).count(j) > 1:
                        depth_ent_ls.append(j)
                depth_ent_ls = str(depth_ent_ls).replace('[', '').replace(']', '')
                print('Dating information tab: Entity %s; There are multiple hiatuses recorded at depth_dating: %s' %(i, depth_ent_ls))
                warning_ctr += 1
            else:
                depth_ent_ls = []
                for k in depth_ent_hiat:
                    if k in list(depth_ent_nohiat):
                        depth_ent_ls.append(k)
                if len(depth_ent_ls) > 0:
                    depth_ent_ls = str(depth_ent_ls).replace('[', '').replace(']', '')
                    print('Dating information tab: Entity %s; A hiatus cannot be at the same depth as a date. See depth_dating: %s' %(i, depth_ent_ls))
                    warning_ctr += 1
    # check if there has been new warnings counted. This will be use to indicate 
    # whether or not to check for hiatuses in sample tables and in the dating table
    warning_ctr_hiat = warning_ctr - warning_ctr_bef 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 7.iii.c.6. Check that if there is an Event; actively forming
    #   that depth_dating = 0, if depth_ref = 'from top'
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for i in pd.unique(dating_tb['entity_name']):
        depth_ref = entity_tb.loc[entity_tb['entity_name'] == i, 'depth_ref'].values[0]
        ent_activ = dating_tb.loc[(dating_tb['entity_name'] == i) & (dating_tb['date_type'] == 'Event; actively forming'), :]
        if len(ent_activ.index) == 0: # used len(dataframe.index) instead of dataframe.empty as it is faster
            pass
        elif len(ent_activ.index) > 1:
            print('Dating information tab: Entity %s; There are more than one actively growing event.' %(i))
            warning_ctr += 1
        else:
            if depth_ref == 'from top':
                if ent_activ.loc[:,'depth_dating'].values[0] != 0:
                    print('Dating information tab: Entity %s; Actively growing event is not at depth_dating = 0 when depth_ref is from top.' %(i))
                    warning_ctr += 1
            corr_age_ent_activ = ent_activ.loc[:,'corr_age'].values[0]
            modref_ent_activ = ent_activ.loc[:,'modern_reference'].values[0]
            if modref_ent_activ in ['b2k', 'BP(1950)', 'Year of chemistry']: # modern_ref = CE/BCE already changed to BP(1950)
                if modref_ent_activ == 'b2k':
                    corr_age_ent_activ = corr_age_ent_activ + 50
                elif modref_ent_activ == 'Year of chemistry':
                    chemyear_ent = ent_activ.loc[:,'chem_year'].values[0]
                    if pd.notnull(chemyear_ent):
                        corr_age_ent_activ = corr_age_ent_activ - (chemyear_ent - 1950)
                    else:
                        pass # chem_year is missing and this would have been flagged elsewhere
                else:
                    pass # the rest should just be BP(1950)
            else:
                pass # modern reference is not b2k, BP(1950) or Year of chemistry and would be flagged elsewhere
            if corr_age_ent_activ > 0:
                warning_ctr += 1
                print('Dating information tab: Entity %s; Actively growing event is not in the modern era (younger than 1950) and this is very unlikely. Please check.' %(i))

                    
# -----------------------------------------------------------------------------
# Section 7.iii.e. Lamina age vs depth spreadsheet
# -----------------------------------------------------------------------------
if dating_lamina_tb.shape[0] > 0:
    warning_ctr += check_no_values(dating_lamina_tb, 'Lamina age vs depth', 'entity_name')
    warning_ctr += check_no_values(dating_lamina_tb, 'Lamina age vs depth', 'depth_lam')
    check_lamage_warning = check_no_values(dating_lamina_tb, 'Lamina age vs depth', 'lam_age')
    warning_ctr += check_lamage_warning
    check_modref_warning_lam = False
    if check_no_values(dating_lamina_tb, 'Lamina age vs depth', 'modern_reference') == 0:
        # Check if values in rows are valid when column has to be from a dropdown box
        if check_values2list(dating_lamina_tb, 'modern_reference', 'Lamina age vs depth', ['BP (1950)', 'b2k', 'CE/BCE', 'Year of chemistry']) == 0:
            check_modref_warning_lam = True
        else:
            warning_ctr += 1
    else:
        warning_ctr += 1
    if check_modref_warning_lam:
        try:
            warning_ctr += check_yearofchemistry_crosstable(dating_lamina_tb, dating_tb)
        except:
            warning_ctr += 1
            print('Lamina age vs depth tab: There is a problem checking chem_year when modern_reference is "Year of chemistry". Perhaps modern_reference is entirely missing. Please check.')
    # Check that the uncertainties coexist and that lam_age exist if they exist
    warning_ctr += check_independent_dependent_col(dating_lamina_tb, 'Lamina age vs depth', 'lam_age_uncert_pos', 'lam_age_uncert_neg')
    warning_ctr += check_independent_dependent_col(dating_lamina_tb, 'Lamina age vs depth', 'lam_age_uncert_neg', 'lam_age_uncert_pos')
    warning_ctr += check_independent_dependent_col(dating_lamina_tb, 'Lamina age vs depth', 'lam_age', 'lam_age_uncert_pos')
    warning_ctr += check_independent_dependent_col(dating_lamina_tb, 'Lamina age vs depth', 'lam_age', 'lam_age_uncert_neg')
    # Check that lam_age_uncert_pos and neg have positive values
    warning_ctr += check_positivenumbers(dating_lamina_tb, 'Lamina age vs depth', 'lam_age_uncert_pos', na_rm = True)
    warning_ctr += check_positivenumbers(dating_lamina_tb, 'Lamina age vs depth', 'lam_age_uncert_neg', na_rm = True)
    for i in set(dating_lamina_tb['entity_name']):
        warning_ctr += check_notminmax_age(dating_lamina_tb.loc[dating_lamina_tb['entity_name'] == i,:], 'lam_age', 'lam_age_uncert_pos', 'lam_age_uncert_neg', 'Lamina age vs depth', i)
    # Make sure lam_age is in valid range
    # convert ages to BP(1950 first)
    if check_lamage_warning == 0:
        if check_modref_warning_lam:
            dating_lamina_tb.loc[dating_lamina_tb['modern_reference'] == 'CE/BCE', 'lam_age'] = 1950 - dating_lamina_tb.loc[dating_lamina_tb['modern_reference'] == 'CE/BCE', 'lam_age'] 
            warning_ctr += check_numbers_in_range(dating_lamina_tb, 'Lamina age vs depth', 'lam_age', -70, np.inf)

# -----------------------------------------------------------------------------
# Section 7.iii.f. Reference spreadsheet
# -----------------------------------------------------------------------------
# Reference table
# Check that if the citation is the same, the DOI must be the same
ref_ctr = len(pd.unique(ref_tb['citation'])) # save to be printed out later
# 1. Make a list of references with more than one count
mylist = set(ref_tb['citation'].value_counts()[ref_tb['citation'].value_counts() > 1].index)
if len(mylist) > 0:
    ctr = 0
    for i in mylist:
        if len(set(ref_tb.loc[ref_tb['citation'] == i, 'publication_DOI'])) > 1:
            rownumber = str(list(ref_tb.loc[ref_tb['citation'] == i, 'publication_DOI'].index + 3)).replace('[', '').replace(']', '')
            ctr += 1 
            try:
                print('References tab: There is more than one DOI associated to %s. Possible drag-down error with the DOI. row:' %(i, rownumber))
            except:
                print('References tab: There is more than one DOI associated to one of the references. This could not be printed due to special characters in the citation. Please identify this manually. Possible drag-down error with the DOI. see row: %s' %(rownumber))
        elif len(set(ref_tb.loc[ref_tb['citation'] == i, 'publication_DOI'])) == 0:
            ctr += 1
            print('Jackpot! You should go buy a lottery ticket but before, please let us know what did you do to get this (theoretically impossible) warning!')
        else:
            pass
    if ctr > 0:
        warning_ctr += 1
else:
    pass # all citations in this workbooks are unique
# Check that if the DOI is the same, the citation must be the same unless the DOI is 'unpublished'
# 1. Make a list of DOI with more than one counts
mylist = set(ref_tb['publication_DOI'].value_counts()[ref_tb['publication_DOI'].value_counts() > 1].index)
if len(mylist) > 0:
    ctr = 0
    for i in mylist:
        if len(set(ref_tb.loc[ref_tb['publication_DOI'] == i, 'citation'])) > 1:
            ctr += 1 
            print('References tab: One same DOI (%s) is linked to multiple citations. If two citations are reported as "unpublished" or if the same DOI is from different chapters of the same book, please move the workbook to the "Checked" folder manually' %i)
        elif len(set(ref_tb.loc[ref_tb['publication_DOI'] == i, 'citation'])) == 0:
            ctr += 1
            print('Jackpot! You should go buy a lottery ticket but before, please let us know what did you do to get this (theoretically impossible) warning!')
        else:
            pass
    if ctr > 0:
        warning_ctr += 1
else:
    pass # all citations in this workbooks are unique

for g in np.unique(ref_tb['entity_name']):
    ref_tb_integrity = ref_tb.loc[ref_tb['entity_name'] == g, :]
    if len(set(ref_tb_integrity['citation'])) < ref_tb_integrity.shape[0]:
        warning_ctr += 1
        print('References tab: There are repeated citation(s) in %s.' %g)
    
indices = [i for i, s in enumerate(ref_tb['publication_DOI']) if (any(x == s.lower() for x in ['unknown', '', ' ', 'n/a', 'na', 'not known', 'notknown', 'not applicable', 'unkwn'])) | s.startswith(' ') | s.endswith(' ')]
indices = ref_tb.iloc[indices,:].index + 3
if len(indices) > 0:
    warning_ctr += 1
    print('References tab: The DOI(s) entered in row %s is incorrect. This must be either a DOI, URL or "unpublished". If it looks OK in the workbook, check for spaces before or after the DOI and re-check.' %str(list(indices)))
else:
    indices = [i for i, s in enumerate(ref_tb['publication_DOI']) if not (s.startswith('http') | s.startswith('10.') | (s == 'unpublished'))]
    indices = ref_tb.iloc[indices,:].index + 3
    if len(indices) > 0:
        warning_ctr += 1
        print('References tab: Incorrect DOI(s) entered in row %s. DOI/URL must either be "unpublished" (e.g. PhDs and unpublished records) or start with "http", "10."' %str(list(indices))) 


indices = [i for i, s in enumerate(ref_tb['citation']) if (any(x == s.lower() for x in ['unknown', '', ' ', 'n/a', 'na', 'not known', 'notknown', 'not applicable', 'unkwn'])) | s.startswith(' ') | s.endswith(' ')]
indices = ref_tb.iloc[indices,:].index + 3
if len(indices) > 0:
    warning_ctr += 1
    print('References tab: The citation(s) in row %s is incorrect. This cannot be empty, "unknown", "N/A", "not known", etc or have spaces before/after the text' %str(list(indices)))

# _____________________________________________________________________________
#
# Section 7.vi. Check across tables (between table integrity)
# _____________________________________________________________________________

# -----------------------------------------------------------------------------
# Section 7.vi.a. Reference spreadsheet
# -----------------------------------------------------------------------------

# Check that if lamina age vs depth table exists that the dating information table contain an 'Event; start of laminations'
if dating_lamina_tb.shape[0] > 0:
    #find the unique entity name
    entity_name_datinglamina_list = np.unique(dating_lamina_tb['entity_name'])
    #for each of the entity name
    for z in entity_name_datinglamina_list:
        #there must be an Event;start of laminations
        dating_tb_subset_startoflam = dating_tb.loc[(dating_tb['entity_name'] == z) & (dating_tb['date_type'] == 'Event; start of laminations'),:]
        if dating_tb_subset_startoflam.shape[0] > 0:
            pass
        else:
            print('Lamina age vs depth tab: There is at least one date in this tab but the dating information table does not contain an "Event; start of laminations".')
            warning_ctr += 1

# Check that if dating information table conatin an 'Event; start of laminations' and whether lamina age vs depth table exists
dating_tb_startoflam = dating_tb.loc[(dating_tb['date_type'] == 'Event; start of laminations'),:]
if dating_tb_startoflam.shape[0] > 0:
    #find the unique entity name
    entity_name_datinglamina_list = np.unique(dating_tb_startoflam['entity_name'])
    #for each of the entity name
    for z in entity_name_datinglamina_list:
        #there must be an lamina age vs depth
        dating_lamina_tb_subset = dating_lamina_tb.loc[(dating_lamina_tb['entity_name'] == z),:]
        if dating_lamina_tb_subset.shape[0] > 0:
            pass
        else:
            print('Dating information tab: There is an "Event; start of laminations" but no data in the lamina age vs depth spreadsheet')
            warning_ctr += 1

# Check if hiatuses depth in sample spreadsheet matches the depths in dating information
if 'H' in list(sample_tb['hiatus']):
    hiatus_sample_subset = sample_tb.loc[(sample_tb['hiatus'] == 'H'),:]
    entity_name_unique = np.unique(hiatus_sample_subset['entity_name'])
    for q in entity_name_unique:
        hiatus_dating_subset = dating_tb.loc[(dating_tb['date_type'] == 'Event; hiatus') & (dating_tb['entity_name'] == q), :]
        hiatus_sample_subset_entity = hiatus_sample_subset.loc[(hiatus_sample_subset['entity_name'] == q), :]
        if len(set(hiatus_dating_subset['depth_dating']).intersection(hiatus_sample_subset_entity['depth_sample'])) == len(hiatus_sample_subset_entity['depth_sample']):
            pass
        else:
            warning_ctr += 1
            hiatus_ls = str(list(set(hiatus_sample_subset_entity['depth_sample']) - set(hiatus_dating_subset['depth_dating'])))
            print('Sample data tab: Entity %s has a hiatus in this tab that does not match that of the dating spreadsheet. See depth_sample %s' %(q, hiatus_ls))
else:
    pass
    #print('No hiatus in this workbook')
if (len(dating_tb.index) > 0) & (len(sample_tb.index) > 0):
    if warning_ctr_hiat == 0:
        # Check if hiatus in dating table occurs in the sample table if they arein the range of the depths of samples
        if 'Event; hiatus' in list(dating_tb['date_type']):
            hiatus_dating_subset = dating_tb.loc[(dating_tb['date_type'] == 'Event; hiatus'),:]
            entity_name_unique = np.unique(hiatus_dating_subset['entity_name'])
            for q in entity_name_unique:
                maxdepth = np.max(sample_tb.loc[(sample_tb['entity_name'] == q), 'depth_sample'])
                mindepth = np.min(sample_tb.loc[(sample_tb['entity_name'] == q), 'depth_sample'])
                hiatus_dating_subset_entity = hiatus_dating_subset.loc[(hiatus_dating_subset['entity_name'] == q) & (hiatus_dating_subset['depth_dating'] >= mindepth) & (hiatus_dating_subset['depth_dating'] <= maxdepth), :]
                if sample_tb['hiatus'].dtype == 'O':
                    hiatus_sample_subset = set(sample_tb.loc[(sample_tb['hiatus'] == 'H') & (sample_tb['entity_name'] == q), 'depth_sample'])
                else:
                    hiatus_sample_subset = set()
                if len(hiatus_sample_subset.intersection(set(hiatus_dating_subset_entity['depth_dating']))) == len(hiatus_dating_subset_entity['depth_dating']):
                    pass
                else:
                    warning_ctr += 1
                    hiatus_ls = str(list(set(hiatus_dating_subset_entity['depth_dating']) - hiatus_sample_subset))
                    print('Dating information tab: Entity %s has a hiatus in this tab that does not match that of the sample data spreadsheet. See depth_dating %s' %(q, hiatus_ls))
        else:
            pass
            #print('No hiatus in this workbook')
    
# Check that there are at least one reference for each entity
for g in np.unique(entity_tb['entity_name']):
    ref_tb_integrity = ref_tb.loc[ref_tb['entity_name'] == g, :]
    if ref_tb_integrity.shape[0] < 1:
        warning_ctr += 1
        print('References tab: Entity %s is missing a reference' %g)
    
# Check that there at least the dating table exist or both dating table and lamina age vs depth table exist  
for e in np.unique(entity_tb.loc[entity_tb['speleothem_type'] != 'composite','entity_name']):
    dating_tb_subset = dating_tb.loc[(dating_tb['entity_name'] == e), :]
    datinglamina_tb_subset = dating_lamina_tb.loc[(dating_lamina_tb['entity_name'] == e), :]
    if (dating_tb_subset.shape[0] > 0):
        pass
    else:
        if datinglamina_tb_subset.shape[0] > 0:
            print('Dating information tab: Entity %s has laminae information but no dating information. date_type = "Event; start of laminations" and "Event; end of laminations" must be entered' %e)
            warning_ctr += 1
        else:
            print('Dating information tab: Entity %s has no dating information' %e)
            warning_ctr += 1
    # If there is Event; end of laminations, there must be Event; start of laminations
    if 'Event; end of laminations' in list(dating_tb_subset['date_type']):
        if 'Event; start of laminations' in list(dating_tb_subset['date_type']):
            pass
        else:
            warning_ctr += 1
            print('Dating information tab: there is date_type = "Event; end of laminations" but no date_type = "Event; start of laminations" for Entity %s. Both must be entered' %e)
    else:
        if 'Event; start of laminations' in list(dating_tb_subset['date_type']):
            warning_ctr += 1
            print('Dating information tab: there is date_type = "Event; start of laminations" but no date_type = "Event; end of laminations" for entity %s. Both must be entered' %e)
    # If there is Event; end of laminations or Event; start of laminations, there shoudl be lamina age vs depth table
    if (any(x in list(dating_tb_subset['date_type']) for x in ['Event; end of laminations', 'Event; start of laminations'])) & (datinglamina_tb_subset.shape[0] == 0):
        warning_ctr += 1
        print('Lamina age vs depth tab: According to the Dating information tab, entity %s is laminated (i.e. date_type = "Event; end of laminations" or "Event; start of laminations" have been entered). However, there is no information on the laminae in the lamina age vs depth table. Have you done your best to find these data?' %e)
    # If there is lamina age vs depth table, there must be 'Event; start of laminations
    if datinglamina_tb_subset.shape[0] > 0:
        if ('Event; start of laminations' in list(dating_tb_subset['date_type'])):
            pass
        else:
            warning_ctr += 1
            print('Dating information tab: Entity %s has laminae data but is missing date_type = "Event; start of laminations" in the dating information spreadsheet' %e)
    # If there is no Event; start of laminations, ann_lam_check for that particular entity must be not applicable
    sample_tb_rm_hiatus_ent = sample_tb_rm_hiatus_agemodel.loc[sample_tb_rm_hiatus_agemodel['entity_name'] == e, :]
    if (any(x in list(dating_tb_subset['date_type']) for x in ['Event; start of laminations', 'Event; end of laminations'])):
        if sample_tb_rm_hiatus_ent.shape[0] > 0:
            if (any(sample_tb_rm_hiatus_ent['ann_lam_check'] == 'not applicable')):
                warning_ctr += 1
                print('Sample data tab: Entity %s is laminated and therefore ann_lam_check cannot not be "not applicable"' %e)
            else:
                pass
        else:
            pass # has lamina but no age model
    else:
        if len(sample_tb_rm_hiatus_ent.index) > 0:
            if (all(sample_tb_rm_hiatus_ent['ann_lam_check'] != 'not applicable')):
                warning_ctr += 1
                print('Sample data tab: ann_lam_check for entity %s must be "not applicable" if this is a non-laminated speleothem (as assumed from the lack of date_type = "Event; start of laminations"/"Event; end of laminations" in the dating information table)' %e)
           
# Check integrity of the lamina dating information
# 1. select just the lamination dates
# 2. for each of these entity that is left:
#   Sort these by depth (or reversed with depth_ref = 'from base')
#   First item (first item from top) must be 'Event; end of laminations' 
#   Last item (first item from bottom) must be 'Event; start of laminations'
#   check that there are no entries where Event; start of laminations has a depth of 0 (if depth_ref = 'from top')
#   check that there are no entries where Event; end of laminations has a depth of 0 (if depth_ref = 'from base')
#   If it pass these four tests and there are more than just two of them:
#       check that there are no consecutive 'Event; start of laminations' (which means that they have to be alternating)

indices = [i for i, s in enumerate(dating_tb['date_type']) if ('laminations' in s)]
dating_tb_lam = dating_tb.iloc[indices, :]
for e in np.unique(dating_tb_lam.loc[:,'entity_name']):
    dating_ent_activelyforming = dating_tb.loc[(dating_tb['entity_name'] == e) & (dating_tb['date_type'] == 'Event; actively forming'), :]
    dating_ent = dating_tb_lam.loc[dating_tb_lam['entity_name'] == e,:]
    depth_ref = entity_tb.loc[entity_tb['entity_name'] == e, 'depth_ref'].values[0]
    further_check = True
    if depth_ref == 'from top':
        dating_ent = dating_ent.sort_values(by = ['depth_dating'], ascending = True)
        if any(dating_ent.loc[dating_ent['date_type'] == 'Event; start of laminations', 'depth_dating'] == 0):
            warning_ctr += 1
            print('Dating information tab: depth_ref = "from top" for Entity %s and therefore date_type = "Event; start of laminations" cannot exist at depth_dating = 0. This should probably be date_type = "Event; end of laminations". Note that "start of laminations" refers to the depth at which laminae started forming (i.e. bottom/oldest part of the section) and NOT to the counting order' %e)
            further_check = False
    elif depth_ref == 'from base':
        dating_ent = dating_ent.sort_values(by = ['depth_dating'], ascending = False)
        if any(dating_ent.loc[dating_ent['date_type'] == 'Event; end of laminations', 'depth_dating'] == 0):
            warning_ctr += 1
            print('Dating information tab: depth_ref = "from base" for Entity %s and therefore date_type = "Event; end of laminations" cannot exist at depth_dating = 0. This should probably be date_type = "Event; start of laminations". Note that "start of laminations" refers to the depth at which laminae started forming (i.e. bottom/oldest part of the section) and NOT to the counting order' %e)
            further_check = False
    else:
        print('Dating information tab: The depth_ref chosen for entity %s is not "from top" or "from base". Cannot perform further checks ' %e)
        warning_ctr += 1
        further_check = False
    if further_check == True:
        if dating_ent['date_type'].iloc[0] != 'Event; end of laminations':
            further_check = False
            warning_ctr += 1
            print('Dating information tab: The youngest date related to laminae for entity %s is not linked to an "Event; end of laminations". This may be missing. Note that "start of laminations" refers to the depth at which laminae started forming (i.e. bottom/oldest part of the section) and NOT to the counting order' %e)
        else:
            if len(dating_ent_activelyforming.index) == 0:
                if depth_ref == 'from top':
                    if dating_ent['depth_dating'].iloc[0] == 0:
                        modref_ent = dating_ent['modern_reference'].iloc[0]
                        corrage_ent = dating_ent['corr_age'].iloc[0]
                        nocheck = False
                        if modref_ent in ['b2k', 'BP(1950)', 'Year of chemistry']:
                            if modref_ent == 'b2k':
                                corrage_ent = corrage_ent + 50
                            elif modref_ent == 'Year of chemistry':
                                chemyear_ent = dating_ent['chem_year'].iloc[0]
                                if pd.notnull(chemyear_ent):
                                    corrage_ent = corrage_ent - (chemyear_ent - 1950)
                                else:
                                    nocheck = True # chem_year is missing and this would have been flagged elsewhere
                            else:
                                pass # the rest should just be BP(1950)
                        else:
                            nocheck = True
                        if nocheck == False:
                            if corrage_ent <= 0:
                                print('Informative: Dating information tab: The youngest "Event; end of laminations" appears like it could also be an "Event; actively forming". Please add this extra date_type if this is the case.')                  
                if depth_ref == 'from base':
                    modref_ent = dating_ent['modern_reference'].iloc[0]
                    corrage_ent = dating_ent['corr_age'].iloc[0]
                    nocheck = False
                    if modref_ent in ['b2k', 'BP(1950)', 'Year of chemistry']:
                        if modref_ent == 'b2k':
                            corrage_ent = corrage_ent + 50
                        elif modref_ent == 'Year of chemistry':
                            chemyear_ent = dating_ent['chem_year']
                            if pd.notnull(chemyear_ent):
                                corrage_ent = corrage_ent - (chemyear_ent - 1950)
                            else:
                                nocheck = True # chem_year is missing and this would have been flagged elsewhere
                        else:
                            pass # the rest should just be BP(1950)
                    else:
                        nocheck = True
                    if nocheck == False:
                        if corrage_ent <= 0:
                            print('Informative: Dating information tab: The youngest "Event; end of laminations" appears like it could also be an "Event; actively forming". Please add this extra date_type if this is the case.')                  
            else:
                pass # no need to check as there is already one 'Event; actively forming'
        if list(dating_ent['date_type'])[-1] != 'Event; start of laminations':
            further_check = False
            warning_ctr += 1
            print('Dating information tab: The oldest date related to laminae for entity %s is not linked to an "Event; start of laminations". This may be missing. Note that "start of laminations" refers to the depth at which laminae started forming (i.e. bottom/oldest part of the section) and NOT to the counting order' %e)
        if further_check == True:
            if dating_ent.shape[0] > 2:
                consec_warning = False
                for i in range(dating_ent.shape[0]):
                    if i == 0:
                        date_type = dating_ent['date_type'].iloc[i]
                    if i > 0:
                        if date_type == dating_ent['date_type'].iloc[i]:
                            consec_warning = True
                        else:
                            date_type = dating_ent['date_type'].iloc[i]
                if consec_warning == True:
                    warning_ctr += 1
                    print('Dating information tab: There are two consecutive "Event; end of laminations" or "Event; start of laminations" when the dating information of entity %s is sorted by depth. The two events should alternate between each other.' %e)
        
        
# Check that entity name in dating information and sample data matches the ones on the entity metadata spreadsheet
# sample table
warning_ctr += check_entity_names(entity_tb, sample_tb, 'Sample data')
# dating information table
warning_ctr += check_entity_names(entity_tb, dating_tb, 'Dating information')
# Lamina age vs depth
warning_ctr += check_entity_names(entity_tb, dating_lamina_tb, 'Lamina age vs depth')
# References
warning_ctr += check_entity_names(entity_tb, ref_tb, 'References')

# -----------------------------------------------------------------------------
# Section 7.vi.b. All entities
# -----------------------------------------------------------------------------
# Check that the last 10 characters in data_DOI_URL and publication_DOI are not
# identical
# 1. Loop through each entity in entity_tb
#   i. Selects for data_DOI_URL
#   ii. If exists, subset the last 10 characters
#       a. subset ref_tb table for references of that particular entity
#           - Loop through each publication_DOI for that entity, only select last 10 characters
#           - if last 10 characters are the same, raise warning for that entity

for i in entity_tb['entity_name']:
    dataDOIURL = entity_tb.loc[entity_tb['entity_name'] == i, 'data_DOI_URL']
    if len(dataDOIURL) == 1:
        dataDOIURL = dataDOIURL.iloc[0] # select for the just data_DOI_URL
        if dataDOIURL == '':
            pass
        else:
            dataDOIURLend = dataDOIURL[-10:]
            pub_DOI_ent = ref_tb.loc[ref_tb['entity_name'] == i, 'publication_DOI']
            for j in pub_DOI_ent:
                pub_DOI_last10 = j[-10:]
                if pub_DOI_last10 == dataDOIURLend:
                    print('Entity metadata tab: data_DOI_URL; Entity %s likely has the same data_DOI_URL as publication_DOI in References tab. The data_DOI_URL refers only to the data (e.g. https://doi.org/10.17864/1947.147 or https://www.ncdc.noaa.gov/paleo-search/study/24070) while the publication_DOI refers to the paper (e.g. https://doi.org/10.5194/essd-10-1687-2018). If no data_DOI_URL is available, please leave empty.' %(i))
                    warning_ctr += 1
                    break
    else:
        warning_ctr += 1

# =============================================================================
# Section 8. Print out the number of unknowns
# =============================================================================

if total_unkwn > 0:
    if site_unkwn == 0:
        site_unkwn_txt = ''
    else:
        site_unkwn_txt = '%d in the site table; ' %site_unkwn
    if entity_unkwn == 0:
        entity_unkwn_txt = ''
    else:
        entity_unkwn_txt = '%d in the entity table; ' %entity_unkwn
    if dating_unkwn == 0:
        dating_unkwn_txt = ''
    else:
        dating_unkwn_txt = '%d in the dating information table; ' %dating_unkwn
    if sample_unkwn == 0:
        sample_unkwn_txt = ''
    else:
        sample_unkwn_txt = '%d in the sample table; ' %sample_unkwn
    print('Informative: There is a total of %d "unknown" in %d entities in this workbook: %s%s%s%s Please ensure that the information is truly inaccessible before choosing "unknown".' %(total_unkwn, entity_count, site_unkwn_txt, entity_unkwn_txt, dating_unkwn_txt, sample_unkwn_txt))
if len(dating_tb.index) > 0:
    if pass_depthdating_warning == False:
        print('If depths in Dating information table really cannot be obtained, please add dummy depths to make sure that other checks can be performed. IMPORTANT: Do not forget to delete the dummy depths from the workbook once it has passed all checks.')
if len(sample_tb.index) > 0:
    if pass_depthsample_checks == False:
        print('If depths in the Sample data table really cannot be obtained, please add dummy depths to make sure that other checks can be performed. IMPORTANT: Do not forget to delete the dummy depths from the workbook once it has passed all checks.')


print('%d warning/s were detected' %warning_ctr)
# =============================================================================
# Section 9. Move files to Checked folder
# =============================================================================
if warning_ctr < 1:
    try:
        shutil.move(input_file, os.path.join('Checked', input_file))
    except IOError:
        print('Checked folder is likely missing. Unable to move file automatically into Checked folder.')
    

