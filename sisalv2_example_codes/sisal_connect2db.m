%%  script to extract SISALv2 data
% By Laia Comas-Bru and Sahar Amirnezhad-Mozhdehi 
% Version 1.0, Created Aug 2018, Last modified 13/02/2020, 
% Created using MATLAB R2019a
% ========================================================================
% Introduction:
% This script extracts example data from the SISAL database previously
% logged into mySQL.
% ========================================================================
%% Instructions and naming conventions
 
% WHAT NEEDS TO BE ENTERED/MODIFIED:
% % #1) path and name of MySQL-Java connector
% % #2) path of the working directory, where this script is located
% % #3) name of database, username, password and any other parameters that
% % are modified in MySQL 
% % #4) SISAL database version: this is the version of the SISAL database 
% % that you are using and querying from

% ========================================================================
% Notes:
% * This script requires MATLAB Database Toolbox.
%  
% * You need to install MySQL and import the SISAL database in MySQL to
% run this script properly. See instructions in the repository of the
% University of Reading, where the database is lodged: https://researchdata.reading.ac.uk/189/
%  
% A very short troubleshooting advice if you are new to MySQL Queries
% from MATLAB:
% If the code does not extract data from database check these first:
% #1 the path and name and version of MySQL connector is correct
% (mysql-connector-java-X.Y.ZT-bin.jar')
% #2 name of database and login and password from the MySQL
% software are correct:
% #3 pay attention to the error message:
% for example if you see the following  message displayed after
% MATLAB tries to access the database "Access denied for user
% 'root'@'localhost' (using password: NO)" it means you have to
% insert the MySQL password in the  '' in the line: conn =
% database('sisalv2', 'root', '', .....

%% ================EXTRACTING DATA FROM DATABASE===================
%% connecting to the sisalv2 database
fclose all; clear; close all;  diary logfile_SISAL_3.txt; warning('off','all');
javapath0=input('Please insert the path and name of the java connector file \n','s');%this will differ depending on the connector you're using 
% javapath0='C:\Program Files\MATLAB\R2019a\java\jarext\mysql-connector-java-5.1.47-bin.jar';%uncomment and change if preferred
javaaddpath(javapath0);
addpath (genpath('C:\Users\Documents\MATLAB\SISAL_MATLAB'))%adjust as appropriate
setdbprefs('DataReturnFormat', 'table');
setdbprefs('NullNumberRead', 'NaN');
setdbprefs('NullStringRead', 'NaN');
conn = database('SISALv2', 'root', 'password', 'Vendor', 'MYSQL', 'Server', 'localhost', 'PortNumber', 3306);
display(conn.Message);% if the output is  [] it means MATLAB is properluy connected to MySQL

%% extracting dating, isotope, hiatus, notes, entity and site data  from sisalv2 database
% get dating data
curs = exec(conn, ['SELECT dating_id, entity_id, depth_dating, dating_thickness, corr_age, corr_age_uncert_pos, corr_age_uncert_neg, date_type, date_used FROM 	dating ']);
curs = fetch(curs);
raw_dating = curs.Data;
close(curs);

% get isotope data
curs = exec(conn, ['SELECT sample.entity_id, sample.sample_id, sample.depth_sample, sample.mineralogy, sample.arag_corr, site.site_name, site.latitude, site.longitude,  entity.entity_name,  d18O.d18O_measurement , hiatus.hiatus, original_chronology.interp_age, original_chronology.interp_age_uncert_pos, original_chronology.interp_age_uncert_neg, site.elevation  , d18O.d18O_precision , d13C.d13C_measurement , d13C.d13C_precision ,entity.entity_status FROM site LEFT JOIN entity USING(site_id) LEFT JOIN sample USING(entity_id) LEFT JOIN original_chronology USING(sample_id) LEFT JOIN hiatus USING(sample_id) LEFT JOIN d18O USING(sample_id) LEFT JOIN d13C USING(sample_id)']);
curs = fetch(curs);
raw_isotope = curs.Data;
close(curs);
clear curs;

%gets entities and sites
curs = exec(conn, ['SELECT 	site.site_name'...
    ' ,	entity.entity_name'...
    ' ,	entity.entity_id'...
    ' ,	entity.speleothem_type'...
    ' ,	entity.depth_ref'...
    ' ,	site.latitude'...
    ' ,	site.longitude'...
    ' , site.elevation'...
    ' ,	entity.entity_status'...
    ' FROM entity '...
    ' JOIN site '...
    ' USING (site_id)']);

curs = fetch(curs);
raw_entities = curs.Data;
close(curs);
clear curs

curs = exec(conn, ['SELECT sample.entity_id, sample.sample_id, sample.depth_sample, sample.mineralogy, sample.arag_corr, site.site_name, site.latitude, site.longitude,  entity.entity_name,  d18O.d18O_measurement , hiatus.hiatus, original_chronology.interp_age, original_chronology.interp_age_uncert_pos, original_chronology.interp_age_uncert_neg, site.elevation  , d18O.d18O_precision , entity.entity_status FROM site LEFT JOIN entity USING(site_id) LEFT JOIN sample USING(entity_id) LEFT JOIN original_chronology USING(sample_id) LEFT JOIN hiatus USING(sample_id) LEFT JOIN d18O USING(sample_id)']);
curs = fetch(curs);
raw_d180_inc_superceded = curs.Data;
close(curs);
clear curs;

curs = exec(conn, ['SELECT site.site_name, site.site_id, notes.site_id, notes.notes FROM site JOIN  notes USING (site_id)']);
curs = fetch(curs);
raw_notes= curs.Data;
close(curs);
clear curs;