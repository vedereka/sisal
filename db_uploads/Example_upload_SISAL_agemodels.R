# This script is an example of how to use upload_SISAL_agemodels.R to 
# update the SISAL database
# Created by K.Atsawawaranunt and modified by Laia Comas-Bru. Last modified: February 2021
#
# The example input files do not exist here but are described in the comments
#
# Load required libraries ------------------------------------------------#####
library(RMariaDB)
library(openxlsx)
library (dplyr)

# Source the upload_SISAL_agemodels.R
source('upload_SISAL_agemodels.R')

# Example 2: ages with sample_id -----------------------------------------#####
# Connect to SISAL database
mydb = dbConnect(MariaDB(), user='[ADD USERNAME]', 
                 password='[ADD PASSWORD]', 
                 dbname='[ADD DB NAME]', 
                 host='localhost')

# Read in the csv file with the following data
#   sample_id
#   agemodel_age (e.g. COPRA_age) yrs BP (1950)
#   agemodel_age_uncert_pos (e.g. COPRA_age_uncert_pos)
#   agemodel_age_uncert_neg (e.g. COPRA_age_uncert_neg)
#
# All rows must contain data, as missing data is not useful here
# It can be removed before being read into R or done in R, that
# is up the personal choice
#
# load file with SISAL_chronologies and remove NULLs for that AM

#FILE NUM 1
sisal_chrono <- read.csv("[CSV FILENAME]")

#Linear regression
tb_linear_regress <- sisal_chrono %>% filter(sisal_chrono$linear_regress_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'linear_regress', # Prefix of column name
                                tb = tb_bacon, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'linear_regress_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'linear_regress_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'linear_regress_age_uncert_neg')

#Linear
tb_linear <- sisal_chrono %>% filter(sisal_chrono$linear_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'linear', # Prefix of column name
                                tb = tb_bacon, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'linear_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'linear_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'linear_age_uncert_neg')

#COPRA (ideally CopRa), update col name
tb_COPRA <- sisal_chrono %>% filter(sisal_chrono$COPRA_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'COPRA', # Prefix of column name
                                tb = tb_bchron, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'COPRA_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'COPRA_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'COPRA_age_uncert_neg')

#StalAge -> NEED TO CREATE COLS
tb_StalAge <- sisal_chrono %>% filter(sisal_chrono$StalAge_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'StalAge', # Prefix of column name
                                tb = tb_bchron, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'StalAge_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'StalAge_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'StalAge_age_uncert_neg')

#BACON
tb_bacon <- sisal_chrono %>% filter(sisal_chrono$Bacon_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'Bacon', # Prefix of column name
                                tb = tb_bacon, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'Bacon_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'Bacon_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'Bacon_age_uncert_neg')

#BCHRON
tb_bchron <- sisal_chrono %>% filter(sisal_chrono$Bchron_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'Bchron', # Prefix of column name
                                tb = tb_bchron, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'Bchron_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'Bchron_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'Bchron_age_uncert_neg')

#OxCal
tb_OxCal <- sisal_chrono %>% filter(sisal_chrono$OxCal_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'OxCal', # Prefix of column name
                                tb = tb_bchron, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'OxCal_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'OxCal_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'OxCal_age_uncert_neg')

#FILE NUM 2
sisal_chrono <- read.csv("AM_for_v2/sisal_chrono_final.csv")

#Linear regression
tb_linear_regress <- sisal_chrono %>% filter(sisal_chrono$linear_regress_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'linear_regress', # Prefix of column name
                                tb = tb_bacon, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'linear_regress_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'linear_regress_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'linear_regress_age_uncert_neg')

#Linear
tb_linear <- sisal_chrono %>% filter(sisal_chrono$linear_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'linear', # Prefix of column name
                                tb = tb_bacon, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'linear_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'linear_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'linear_age_uncert_neg')

#COPRA (ideally CopRa), update col name
tb_COPRA <- sisal_chrono %>% filter(sisal_chrono$COPRA_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'COPRA', # Prefix of column name
                                tb = tb_bchron, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'COPRA_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'COPRA_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'COPRA_age_uncert_neg')

#StalAge -> NEED TO CREATE COLS
tb_StalAge <- sisal_chrono %>% filter(sisal_chrono$StalAge_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'StalAge', # Prefix of column name
                                tb = tb_bchron, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'StalAge_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'StalAge_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'StalAge_age_uncert_neg')

#BACON
tb_bacon <- sisal_chrono %>% filter(sisal_chrono$Bacon_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'Bacon', # Prefix of column name
                                tb = tb_bacon, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'Bacon_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'Bacon_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'Bacon_age_uncert_neg')

#BCHRON
tb_bchron <- sisal_chrono %>% filter(sisal_chrono$Bchron_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'Bchron', # Prefix of column name
                                tb = tb_bchron, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'Bchron_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'Bchron_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'Bchron_age_uncert_neg')

#OxCal
tb_OxCal <- sisal_chrono %>% filter(sisal_chrono$OxCal_age!="NULL")
# Run the function to input the data into the database
input_sisal_chronology_sampleid(cnx = mydb, 
                                agemodeltype = 'OxCal', # Prefix of column name
                                tb = tb_bchron, # dataframe name
                                tb_sample_id_col = 'sample_id', # name of depth column in dataframe 
                                tb_age_col = 'OxCal_age', # name of age column in dataframe
                                tb_age_uncert_pos_col = 'OxCal_age_uncert_pos', 
                                tb_age_uncert_neg_col = 'OxCal_age_uncert_neg')



# Close connection
dbDisconnect(mydb)



#### STEP 2 #####
# Update date_used_agemodel in dating table ------------------------------#####
# Connect to SISAL database
mydb = dbConnect(MariaDB(), user='[ADD USERNAME]', 
                 password='[ADD PASSWORD]', 
                 dbname='[ADD DB NAME]', 
                 host='localhost')

# Read in the table where date_used_agemodels are to be updated
# The table should have:
#   dating_id
#   date_used_agemodel column filled in (i.e. date_used_COPRA)
tb_dateused <- read.csv('[CSV FILENAME]')
# Run the function
update_date_used_agemodel(cnx = mydb, # connection
                          tb = tb_dateused, # dataframe containing date_used information
                          dating_id_col = 'dating_id', #name of dating_id column in dataframe
                          tbdate_used_col = 'date_used_Bchron', # name of date_used_agemodel column in dataframe
                          dbdate_use_col = 'date_used_Bchron') # name of date_used_agemodel column in database

# close connection
dbDisconnect(mydb)

