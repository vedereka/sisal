# ************************************************************************ #
#                                                                          #
#    SCRIPT TO EXTRACT CSV FILES IN R FROM THE DB LOADED IN MySQL          #
#                                                                          #
# This file is provided as part of the documentation for SISAL version 2   #
#                                                                          #
# Prerequisite package:                                                   #
#     - RMariaDB                                                             #
#                                                                          #
# Please note that there may be some authentication issues when using      #
# MySQL 8.0, especially when trying to connect from R/Python. This may be  #
# due to the change in the default authentication plugin from              #
# mysql_native_password to caching_sha2_password. One way round this is to #
# run the following MySQL query in MySQL Workbench:
#   - ALTER USER 'username’@‘localhost’ IDENTIFIED WITH mysql_native_password BY ‘password’;
#   - 'username' refers to the username of the user (usually 'root')
#   - 'password' refers to the password.
#

# Install library if not installed -------------------------------------####

if (!('RMariaDB' %in% installed.packages())){
  install.packages('RMariaDB')
}

# IMPORT LIBRARY -------------------------------------------------------####
library(RMariaDB) 

# 1. Connect to Database -----------------------------------------------####
# This assumes that the database has been imported under the name 'sisalv2'
# and is on the local computer (host = 'localhost'), the password as 'password'
# and the user is 'root'
mydb = dbConnect(MySQL(), user='root', 
                 password='password', 
                 dbname='sisalv2', 
                 host='localhost')

# 2. Extract data and save each table as a csv --------------------------####

# List tables in the database 
tab_ls <- dbListTables(mydb)

for (tab in tab_ls){
  
  tb <- dbGetQuery(mydb, paste ('SELECT * FROM ',tab,';',sep="")) 
  write.csv(tb,paste(tab,".csv",sep=""),na="NA",row.names=F,fileEncoding = "UTF-8")
  
}

