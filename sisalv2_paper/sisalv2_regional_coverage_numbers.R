# Author: Laia Comas-Bru
# date: November 2019 (last edit Feb 2021)
# script to produce table 6 from SISALv2 database paper (Comas-Bru et al., submitted, ESSD)
# output: how many entities from the list of identified records have been uploaded to each version of the database for each region. 
# Input: List of identified records (downloaded from Google Drive > SISAL documents > master list of records and saved as csv file in the wd)


rm(list=ls()) 


library(tidyverse)
library(compare)
library(RMariaDB) 
library(arsenal)
library(lessR)


#### connect to database versions (as loaded in mySQL - see instructions in UoR repository) #### 

con1 = dbConnect(MariaDB(), user='root', 
                 password='password', 
                 dbname='sisalv1_pub', 
                 host='localhost')

con2 = dbConnect(MariaDB(), user='root', 
                 password='password', 
                 dbname='sisalv1b', 
                 host='localhost')

con3 = dbConnect(MariaDB(), user='root', 
                 password='password', 
                 dbname='sisalv2', 
                 host='localhost')


#### Define functions & prepare sink file #### 

# function to supressing automatic output from cat()
# use it as: y <- quiet(FUNCTION)
quiet <- function(x) { 
  sink(tempfile()) 
  on.exit(sink()) 
  invisible(force(x)) 
} 


unlink("sisalv2_paper/output/coverage.txt")
sink("sisalv2_paper/output/coverage.txt",split=TRUE,append = TRUE) # divert all text outputs to a file
paste('SISAL Entity/sites regional coverage', sep = '')

#### Extract data from SISAL database v1, v1b and v2 ####

cov1 <- dbGetQuery(con1, "SELECT site.site_id, site.site_name, entity.entity_id, entity.entity_name, entity.entity_status, site.latitude, site.longitude
FROM entity LEFT JOIN site USING (site_id);")
cov2 <- dbGetQuery(con2, "SELECT site.site_id, site.site_name, entity.entity_id, entity.entity_name, entity.entity_status, site.latitude, site.longitude
FROM entity LEFT JOIN site USING (site_id);")
cov3 <- dbGetQuery(con3, "SELECT site.site_id, site.site_name, entity.entity_id, entity.entity_name, entity.entity_status, site.latitude, site.longitude
FROM entity LEFT JOIN site USING (site_id);")

#### Load list of identified records (master list in SISAL's google drive) ####
# file structure: entity_id, cave_name, latitude, longitude 

ident_sites <- read.csv(paste(getwd(),"/sisalv2_paper/sisal_list_identified_sites.csv",sep=""), header = TRUE, stringsAsFactors = FALSE)
quiet(transform(ident_sites, latitude = as.numeric(latitude)))
quiet(transform(ident_sites, longitude = as.numeric(longitude)))
exc = !names(ident_sites) %in% c("entity_id","cave","db_status")
ident_sites[,exc] = round(ident_sites[,exc], digits = 4)

#### Define regions and extract distinct number of entity_ids #### 

#### Oceania (-60° < Lat < 0°; 90° < Lon < 180°) ####
lat_min=-60; lat_max=0
lon_min=90; lon_max=180

cov1sel <- cov1 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov2sel <- cov2 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov3sel <- cov3 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
id <- ident_sites %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))

paste("---------------------------------------")
paste("Oceania ident: ",length(unique(id$cave)),"/",length(unique(id$entity_id)), collapse =" ")
paste("Oceania v1_pub: ",length(unique(cov1sel$site_id)),"/",length(unique(cov1sel$entity_id)), collapse =" ")
paste("Oceania v1b: ",length(unique(cov2sel$site_id)),"/",length(unique(cov2sel$entity_id)), collapse =" ")
paste("Oceania v2: ",length(unique(cov3sel$site_id)),"/",length(unique(cov3sel$entity_id)), collapse =" ")

####  Asia (0° < Lat < 60°; 60° < Lon < 130°) #### 
lat_min=0; lat_max=60
lon_min=60; lon_max=130

cov1sel <- cov1 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov2sel <- cov2 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov3sel <- cov3 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
id <- ident_sites %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))

paste("---------------------------------------")
paste("Asia ident: ",length(unique(id$cave)),"/",length(unique(id$entity_id)), collapse =" ")
paste("Asia v1_pub: ",length(unique(cov1sel$site_id)),"/",length(unique(cov1sel$entity_id)), collapse =" ")
paste("Asia v1b: ",length(unique(cov2sel$site_id)),"/",length(unique(cov2sel$entity_id)), collapse =" ")
paste("Asia v2: ",length(unique(cov3sel$site_id)),"/",length(unique(cov3sel$entity_id)), collapse =" ")

#### Middle East (7.6° < Lat < 50°; 26° < Lon < 59°) #### 
lat_min=7.6; lat_max=50
lon_min=26; lon_max=59

cov1sel <- cov1 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov2sel <- cov2 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov3sel <- cov3 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
id <- ident_sites %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))

paste("---------------------------------------")
paste("Middle East ident: ",length(unique(id$cave)),"/",length(unique(id$entity_id)), collapse =" ")
paste("Middle East v1_pub: ",length(unique(cov1sel$site_id)),"/",length(unique(cov1sel$entity_id)), collapse =" ")
paste("Middle East v1b: ",length(unique(cov2sel$site_id)),"/",length(unique(cov2sel$entity_id)), collapse =" ")
paste("Middle East v2: ",length(unique(cov3sel$site_id)),"/",length(unique(cov3sel$entity_id)), collapse =" ")

####  Africa (-45° < Lat < 36.1°; -30° < Lon < 60°; with records in the Middle East region removed) #### 
lat_min=-45; lat_max=36.1
lon_min=-30; lon_max=60

cov1sel <- cov1 %>% filter(between(latitude,lat_min,lat_max) & between (longitude,lon_min,lon_max), !between(latitude,7.6,50) & between (longitude,26,59))
cov2sel <- cov2 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max), !between(latitude,7.6,50) & between (longitude,26,59))
cov3sel <- cov3 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max), !between(latitude,7.6,50) & between (longitude,26,59))
id <- ident_sites %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max), !between(latitude,7.6,50) & between (longitude,26,59))

paste("---------------------------------------")
paste("Africa ident: ",length(unique(id$cave)),"/",length(unique(id$entity_id)), collapse =" ")
paste("Africa v1_pub: ",length(unique(cov1sel$site_id)),"/",length(unique(cov1sel$entity_id)), collapse =" ")
paste("Africa v1b: ",length(unique(cov2sel$site_id)),"/",length(unique(cov2sel$entity_id)), collapse =" ")
paste("Africa v2: ",length(unique(cov3sel$site_id)),"/",length(unique(cov3sel$entity_id)), collapse =" ")

#### Europe (36.7° < Lat < 75°; -30° < Lon < 30°; plus Gibraltar and Siberian sites) #### 
lat_min=36.7; lat_max=75
lon_min=-30; lon_max=30

cov1sel <- cov1 %>% filter(xor(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max), xor(site_id == 137, site_id == 89)))
cov2sel <- cov2 %>% filter(xor(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max), xor(site_id == 137, site_id == 89)))
cov3sel <- cov3 %>% filter(xor(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max), xor(site_id == 137, site_id == 89)))
id <- ident_sites %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))

paste("---------------------------------------")
paste("Europe ident: ",length(unique(id$cave))+2,"/",length(unique(id$entity_id))+4, collapse =" ") #tweacking numbers because of sites outside of defined rectangle (Gibraltar and RUssia)
paste("Europe v1_pub: ",length(unique(cov1sel$site_id)),"/",length(unique(cov1sel$entity_id)), collapse =" ")
paste("Europe v1b: ",length(unique(cov2sel$site_id)),"/",length(unique(cov2sel$entity_id)), collapse =" ")
paste("Europe v2: ",length(unique(cov3sel$site_id)),"/",length(unique(cov3sel$entity_id)), collapse =" ")

#### South America (-60° < Lat < 8°; -150° < Lon < -30°) #### 
lat_min=-60; lat_max=8
lon_min=-150; lon_max=-30

cov1sel <- cov1 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov2sel <- cov2 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov3sel <- cov3 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
id <- ident_sites %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))

paste("---------------------------------------")
paste("SAm ident: ",length(unique(id$cave)),"/",length(unique(id$entity_id)), collapse =" ")
paste("SAm v1_pub: ",length(unique(cov1sel$site_id)),"/",length(unique(cov1sel$entity_id)), collapse =" ")
paste("SAm v1b: ",length(unique(cov2sel$site_id)),"/",length(unique(cov2sel$entity_id)), collapse =" ")
paste("SAm v2: ",length(unique(cov3sel$site_id)),"/",length(unique(cov3sel$entity_id)), collapse =" ")

#### North and Central America (8.1° < Lat < 60°; -150° < Lon < -50°) #### 
lat_min=8.1; lat_max=60
lon_min=-150; lon_max=-50

cov1sel <- cov1 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov2sel <- cov2 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov3sel <- cov3 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
cov3sel <- cov3 %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))
id <- ident_sites %>% filter(between(latitude, lat_min, lat_max) & between (longitude,lon_min,lon_max))

paste("---------------------------------------")
paste("NCAm ident: ",length(unique(id$cave)),"/",length(unique(id$entity_id)), collapse =" ")
paste("NCAm v1_pub: ",length(unique(cov1sel$site_id)),"/",length(unique(cov1sel$entity_id)), collapse =" ")
paste("NCAm v1b: ",length(unique(cov2sel$site_id)),"/",length(unique(cov2sel$entity_id)), collapse =" ")
paste("NCAm v2: ",length(unique(cov3sel$site_id)),"/",length(unique(cov3sel$entity_id)), collapse =" ")

#### Disconnect from db ####
dbDisconnect(con1)
dbDisconnect(con2)
dbDisconnect(con3)

rm(con1,con2,con3)
sink()
file.show("sisalv2_paper/output/coverage.txt")
