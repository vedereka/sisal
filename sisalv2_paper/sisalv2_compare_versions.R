# Script to compare the metadata in two subsequent versions of the SISAL database
# Created by Laia Comas Bru in November 2019
# Last modified by Laia Comas Bru in February 2021

rm(list=ls()) 


library(tidyverse)
library(compare)
library(RMariaDB) 
library(arsenal)
library(lessR)

# the output is going to be saved at the relevant folder depending on the chosen dbnameL
# ./sisalv2_paper/output/v1_v1b/
# ./sisalv2_paper/output/v1b_v2/
  
#### Connect to SISAL and create log file to save prints ####
con1 = dbConnect(MariaDB(), user='root', 
                password='password', 
                dbname='sisalv1b', #chose appropriate dbname as saved in MySQL
                # dbname='sisalv1', 
                host='localhost')

con2 = dbConnect(MariaDB(), user='root', 
                password='password', 
                dbname='sisalv2', 
                # dbname='sisalv1b', 
                host='localhost')

if (con1@db=='sisalv1_pub' & con2@db=='sisalv1b' ) {
  sink(paste(getwd(),"/sisalv2_paper/output/v1_v1b/Comparison_v1_v1b.txt", sep=""),split=TRUE,append = TRUE) # divert all text outputs to a file
  paste('Comparison between v1_pub and v1b', sep = '')
  
} else if (con1@db=='sisalv1b' & con2@db=='sisalv2' ) {
  sink(paste(getwd(),"/sisalv2_paper/output/v1b_v2/Comparison_v1b_v2.txt", sep=""),split=TRUE,append = TRUE) # divert all text outputs to a file
  paste('Output/v1b_v2/Comparison between v1b and v2', sep = '')
}

options(max.print=100000000)

# function to supressing automatic output from cat()
# use it as: y <- quiet(FUNCTION)
quiet <- function(x) { 
  sink(tempfile()) 
  on.exit(sink()) 
  invisible(force(x)) 
} 

paste("===============================================================")

#### SITE TABLE ####
paste("SITE TABLE")

site1 <- dbGetQuery(con1, "SELECT * FROM site")
site2 <- dbGetQuery(con2, "SELECT * FROM site")

cmp <- comparedf(site1, site2, by = "site_id", tol.vars = "case") 

# save all differences identified
if (con1@db=='sisalv1_pub') {
  write.csv(diffs(cmp, by.var = TRUE),'sisalv2_paper/output/v1_v1b/site.csv') 
} else if (con1@db=='sisalv1b') {
  write.csv(diffs(cmp, by.var = TRUE),'sisalv2_paper/output/v1b_v2/site.csv')
}

paste("Sites added to new version: ", dim(site2)[1]-dim(site1)[1], collapse=" ")

rm(cmp)

##### HOW MANY SITES HAD EXTRA ENTITIES UPLOADED ####

query <- paste("SELECT site.site_id, count(distinct(entity.entity_id)) as 'entity_counts'
FROM site LEFT JOIN entity USING (site_id) GROUP BY (site.site_id);")

site_ent_1 <- dbGetQuery(con1, query)
site_ent_2 <- dbGetQuery(con2, query)

cmp <- comparedf(site_ent_1, site_ent_2, by = "site_id", tol.vars = "case")
paste ("Number of sites with extra entities uploaded: ",n.diffs(cmp, by.var = TRUE))

if (con1@db=='sisalv1_pub') {
  write.csv(diffs(cmp),'sisalv2_paper/output/v1_v1b/site_ent.csv')
} else if (con1@db=='sisalv1b') {
  write.csv(diffs(cmp),'sisalv2_paper/output/v1b_v2/site_ent.csv')
}

#what are these sites?
paste(c("Sites with extra entities: ", diffs(cmp, by = site_id)$site_id), collapse=" ")

rm(cmp)

paste("===============================================================")



#### ENTITY TABLE ####
paste("ENTITY TABLE")

ent1 <- dbGetQuery(con1, "SELECT * FROM entity")
ent2 <- dbGetQuery(con2, "SELECT * FROM entity")

cmp <- comparedf(ent1, ent2, by = "entity_id", tol.vars = "case") 

# save all differences identified
if (con1@db=='sisalv1_pub') {
  write.csv(diffs(cmp, by.var = TRUE),'sisalv2_paper/output/v1_v1b/ent.csv') 
} else if (con1@db=='sisalv1b') {
  write.csv(diffs(cmp, by.var = TRUE),'sisalv2_paper/output/v1b_v2/ent.csv')
}


##### HOW MANY ENTITIES HAVE BEEN SUBMITTED TO ALREADY EXISTING SITES? ####
paste("ENTITY METADATA")

e1 <- site_ent_1
e2 <- site_ent_2 %>% filter(site_id %in% e1$site_id) #filter v2 for sites in v1 to compare for differences

#note to self: one entity was removed in v1b, filter again the other way around to avoid mismatch

e1 <- e1 %>% filter(site_id %in% e2$site_id) #filter v2 for sites in v1 to compare for differences
site_diff <- sum(e2$entity_counts-e1$entity_counts)

paste0('Number of entities added to already existing sites: ',site_diff)

##### ENTITY TABLE ####

ent1 <- dbGetQuery(con1, "SELECT * FROM entity")
ent2 <- dbGetQuery(con2, "SELECT * FROM entity")
paste("Entities added to the new db version: ", dim(ent2)[1]-dim(ent1)[1], collapse=" ")

if (con1@db=='sisalv1_pub') {
  write.csv(diffs(cmp, by.var = TRUE),'sisalv2_paper/output/v1_v1b/entity.csv')
} else if (con1@db=='sisalv1b') {
  write.csv(diffs(cmp, by.var = TRUE),'sisalv2_paper/output/v1b_v2/entity.csv')
}

rm(cmp)

paste("===============================================================")

#### HIATUSES ####
paste("HIATUS TABLE")

#note to self: Sample_id has changed for some hiatuses between v1 and v1b: ignore that and sort data frames wrt to depth
# caution! all combinations ent-depth are identified are differences. Check this one manually

# depths
query <- paste ("SELECT entity.entity_id, sample.depth_sample, sample.sample_id
                FROM hiatus LEFT JOIN sample USING (sample_id) LEFT JOIN entity USING (entity_id) ORDER BY (entity.entity_id), (sample.depth_sample);")
hiat1 <- dbGetQuery(con1, query)
hiat2 <- dbGetQuery(con2, query)

hiat1$depth_sample <- round(hiat1$depth_sample, digits = 5)
hiat2$depth_sample <- round(hiat2$depth_sample, digits = 5)

hiat1 <- hiat1
hiat2 <- hiat2 %>% filter(entity_id %in% hiat1$entity_id) #filter v2 for sites in v1 to compare for differences

s= unique(hiat1$entity_id)
hiat_removed=0
hiat_added=0
count=0

for (val in 1:length(s)) {
  d1 <- hiat1 %>% filter(entity_id == s[val]) 
  d2 <- hiat2 %>% filter(entity_id == s[val]) 
  
  if (dim(d1)[1]>dim(d2)[1]){ #hiatus removed
    hiat_removed=hiat_removed+1
  }
  if (dim(d1)[1]<dim(d2)[1]){ #hiatus added
    hiat_added=hiat_added+1
  }
  
  d1$entity_id <- NULL; d2$entity_id <- NULL
  
  cmp <- comparedf(d1, d2)
  d <- diffs(cmp, by.var = TRUE)
  
  
  if(n.diffs(cmp)!=0){
    count=count+1 # this counts entities with some changes in the dating metadata
  }
  d[1] <-NULL
  if(val==1){
    d_ent=d[1:2]
    d_ent$n= ifelse(d_ent$n>0,1,0)  # convert any value to 1 or 0
  }else if (val!=1){
    d$n = ifelse(d$n>0,1,0)  
    d_ent <- quiet(Merge(d_ent[1], d_ent[2]+d[2], by="row.names")) # this counts what changes have been done to any entity
    d_ent [1] <- NULL
  }
}

paste("Entities with hiatuses at altered depths: ", d_ent$n[1] , collapse=" ")
paste("How many entities have had hiatuses removed? ", hiat_removed , collapse=" ")
paste("How many entities have had hiatuses added? ", hiat_added , collapse=" ")

rm(cmp)

paste("===============================================================")

#### LAMINATIONS ####
paste("LAMINATIONS TABLE")

query <- paste ("SELECT * FROM dating_lamina;")

lam1 <- dbGetQuery(con1, query)
lam2 <- dbGetQuery(con2, query)

#filter for overlapping entities
lam2 <- lam2 %>% filter(entity_id %in% lam1$entity_id) #filter v2 for sites in v1 to compare for differences

exc = !names(lam1) %in% c("dating_id, entity_id")
lam1[,exc] = round(lam1[,exc], digits = 3)
lam2[,exc] = round(lam2[,exc], digits = 3)

s= unique(lam1$entity_id)
count=0

for (val in 1:length(s)) {
  d1 <- lam1 %>% filter(entity_id == s[val]) 
  d2 <- lam2 %>% filter(entity_id == s[val]) 
  
  d1$entity_id <- NULL; d2$entity_id <- NULL
  
  cmp <- comparedf(d1, d2)
  d <- diffs(cmp, by.var = TRUE)
  
  d[1] <-NULL
  if(val==1){
    d_ent=d[1:2]
    d_ent$n= ifelse(d_ent$n>0,1,0)  # convert any value to 1 or 0
  }else if (val!=1){
    d$n = ifelse(d$n>0,1,0)  
    d_ent <- quiet(Merge(d_ent[1], d_ent[2]+d[2], by="row.names")) # this counts what changes have been done to any entity
    d_ent [1] <- NULL
  }
}

if (con1@db=='sisalv1_pub') {
  write.csv(d_ent,'sisalv2_paper/output/v1_v1b/lam.csv')
} else if (con1@db=='sisalv1b') {
  write.csv(d_ent,'sisalv2_paper/output/v1b_v2/lam.csv')
}

# swapped start/end of laminations

lamevent1 <- dbGetQuery(con1, "SELECT * FROM dating WHERE date_type LIKE '%Event; s%' OR date_type LIKE '%Event; e%' ;")
lamevent2 <- dbGetQuery(con2, "SELECT * FROM dating WHERE date_type LIKE '%Event; s%' OR date_type LIKE '%Event; e%' ;")
lamevent1 <- lamevent1 [2:4]
lamevent2 <- lamevent2 [2:4]

lamevent2 <- lamevent2 %>% filter(entity_id %in% lamevent1$entity_id) #filter v2 for sites in v1 to compare for differences

s= unique(lamevent1$entity_id)
count=0

for (val in 1:length(s)) {
  d1 <- lamevent1 %>% filter(entity_id == s[val]) 
  d2 <- lamevent2 %>% filter(entity_id == s[val]) 
  
  st = !names(d1) %in% c("dating_id, entity_id")
  
  
  d1$entity_id <- NULL; d2$entity_id <- NULL
  
  cmp <- comparedf(d1, d2)
  d <- diffs(cmp, by.var = TRUE)
  
  d[1] <-NULL
  if(val==1){
    d_ent=d[1:2]
    d_ent$n= ifelse(d_ent$n>0,1,0)  # convert any value to 1 or 0
  }else if (val!=1){
    d$n = ifelse(d$n>0,1,0)  
    d_ent <- quiet(Merge(d_ent[1], d_ent[2]+d[2], by="row.names")) # this counts what changes have been done to any entity
    d_ent [1] <- NULL
  }
}

paste("How many entities have had the depths of Event:start/end laminations changed? ", d_ent$n[2] , collapse=" ")

#swapped events
cmp <- comparedf(lam1, lam2, by = "dating_id", tol.vars = "case")
paste("------")
paste("Number of swapped Event: start/end of lam: ", n.diffs(cmp, vars = "date_type"), collapse=" ")
paste("------")
paste("Number of changes in corr_age of start/end of lam:", n.diffs(cmp, vars = "corr_age"), collapse=" ")
paste("------")
paste("Number of changes in depth of Event: start/end of lam:", n.diffs(cmp, vars = "depth_dating"), collapse=" ")

if (con1@db=='sisalv1_pub') {
  write.csv(d_ent,'sisalv2_paper/output/v1_v1b/lam.csv')
} else if (con1@db=='sisalv1b') {
  write.csv(d_ent,'sisalv2_paper/output/v1b_v2/lam.csv')
}

rm(cmp)

paste("===============================================================")

#### SAMPLES ####
paste("SAMPLE d18O DATA")

query <- paste("SELECT sample.entity_id, sample.depth_sample, d18o.d18O_measurement
FROM sample, d18O WHERE sample.sample_id = d18O.sample_id;")

sam1 <- dbGetQuery(con1, query)
sam2 <- dbGetQuery(con2, query)

#filter for overlapping entities
sam2 <- sam2 %>% filter(entity_id %in% sam1$entity_id) #filter v2 for sites in v1 to compare for differences

# round values just in case
sam1$depth_sample <- round(sam1$depth_sample, digits = 4)
sam2$depth_sample <- round(sam2$depth_sample, digits = 4)
sam1$d18O_measurement <- round(sam1$d18O_measurement, digits = 4)
sam2$d18O_measurement <- round(sam2$d18O_measurement, digits = 4)

# sample table is to big to be compared at once. Divide by entity....

count_length <- 0
count_d18O <- 0
count_d18O_ent <- 0

s= unique(sam1$entity_id)

for (val in 1:length(s)) {
  sam1_sel <- sam1 %>% filter(entity_id == s[val]) 
  sam2_sel <- sam2 %>% filter(entity_id == s[val]) 
  if (length(sam1_sel)!=length(sam2_sel)){ # if length of records is different, we assume that the entire time-series has been modified *no need to comapre it
    count_length<-count_length+1
  }else {
    cmp <- comparedf(sam1_sel, sam2_sel)
    if (n.diffs(cmp,vars = "d18O_measurement")!= 0){
      count_d18O<-count_d18O+n.diffs(cmp,vars = "d18O_measurement") #changes in individual d18O values
      count_d18O_ent =count_d18O_ent +1
    }
  }
}

paste("------")
paste("Number of entities for which the length of the d18O time-series changes:", count_length , collapse=" ")
paste("------")
paste("Number of entities for which some or all sample_depth and/or d18O values changed:", count_d18O_ent , collapse=" ")
paste("------")
paste("Number of samples with modified sample_depth and/or d18O values:", count_d18O , collapse=" ")
paste("------")
rm(cmp)


paste("===============================================================")

#### SAMPLES ####
paste("SAMPLE d13CO DATA")

query <- paste("SELECT sample.entity_id, sample.depth_sample, d13C.d13C_measurement
FROM sample, d13C WHERE sample.sample_id = d13C.sample_id;")

sam1 <- dbGetQuery(con1, query)
sam2 <- dbGetQuery(con2, query)

#filter for overlapping entities
sam2 <- sam2 %>% filter(entity_id %in% sam1$entity_id) #filter v2 for sites in v1 to compare for differences

# round values just in case
sam1$depth_sample <- round(sam1$depth_sample, digits = 4)
sam2$depth_sample <- round(sam2$depth_sample, digits = 4)
sam1$d13C_measurement <- round(sam1$d13C_measurement, digits = 4)
sam2$d13C_measurement <- round(sam2$d13C_measurement, digits = 4)

# sample table is to big to be compared at once. Divide by entity....

count_length <- 0
count_d13C <- 0
count_d13C_ent <- 0

s= unique(sam1$entity_id)

for (val in 1:length(s)) {
  sam1_sel <- sam1 %>% filter(entity_id == s[val])  
  sam2_sel <- sam2 %>% filter(entity_id == s[val])  
  if (length(sam1_sel)!=length(sam2_sel)){ # if length of records is different, we assume that the entire time-series has been modified *no need to comapre it
    count_length<-count_length+1
  }else {
    cmp <- comparedf(sam1_sel, sam2_sel)
    if (n.diffs(cmp,vars = "d13C_measurement")!= 0){
      count_d13C<-count_d13C+n.diffs(cmp,vars = "d13C_measurement") #changes in individual d13C values
      count_d13C_ent =count_d13C_ent +1
    }
  }
}

paste("------")
paste("Number of entities for which the length of the d13C time-series changes:", count_length , collapse=" ")
paste("------")
paste("Number of entities for which some or all sample_depth and/or d13C values changed:", count_d13C_ent , collapse=" ")
paste("------")
paste("Number of samples with modified sample_depth and/or d13C values:", count_d13C , collapse=" ")
paste("------")


#### sample table at once#### 


paste("SAMPLE TABLE")

sample1 <- dbGetQuery(con1, "SELECT * FROM sample ;")
sample2 <- dbGetQuery(con2, "SELECT * FROM sample;")

exc = !names(sample1) %in% c("entity_id","sample_id","mineralogy","arag_corr")
sample1[,exc] = round(sample1[,exc], digits = 4)
sample2[,exc] = round(sample2[,exc], digits = 4)

s= unique(sample1$entity_id)
count=0

for (val in 1:length(s)) {
  d1 <- sample1 %>% filter(entity_id == s[val]) 
  d2 <- sample2 %>% filter(entity_id == s[val]) 
  
  cmp <- comparedf(d1, d2, by = "sample_id", tol.vars = "case")
  d <- diffs(cmp, by.var = TRUE)
  d [1] <- NULL
  
  if(n.diffs(cmp)!=0){
    count=count+1 # this counts entities with some changes in the dating metadata
  }
  
  if(val==1){
    d_ent=d[1:2]
    d_ent$n= ifelse(d_ent$n>0,1,0)  # convert any value to 1 or 0
  }else if (val!=1){
    d$n = ifelse(d$n>0,1,0)  
    d_ent <- quiet(Merge(d_ent[1], d_ent[2]+d[2], by="row.names")) # this counts what changes have been done to any entity
    d_ent [1] <- NULL
  }
}

if (con1@db=='sisalv1_pub') {
  write.csv(d_ent,'sisalv2_paper/output/v1_v1b/sample_ent.csv') #dfile with the # of changes by variable.
} else if (con1@db=='sisalv1b' ) {
  write.csv(d_ent,'sisalv2_paper/output/v1b_v2/sample_ent.csv')
}


paste("===============================================================")

#### original chronology table#### 


paste("ORIGINAL CHRONOLOGY")

chrono1 <- dbGetQuery(con1, "SELECT entity.entity_id, original_chronology.* FROM entity
LEFT JOIN sample USING(entity_id) LEFT JOIN original_chronology USING(sample_id);")

chrono2 <- dbGetQuery(con2, "SELECT entity.entity_id, original_chronology.* FROM entity
LEFT JOIN sample USING(entity_id) LEFT JOIN original_chronology USING(sample_id);")

exc = !names(chrono1) %in% c("sample_id, entity_id","age_model_type","ann_lam_check","dep_rate_check")
chrono1[,exc] = round(chrono1[,exc], digits = 4)
chrono2[,exc] = round(chrono2[,exc], digits = 4)

s= unique(chrono1$entity_id)
count=0

for (val in 1:length(s)) {
  d1 <- chrono1 %>% filter(entity_id == s[val]) 
  d2 <- chrono2 %>% filter(entity_id == s[val]) 
  
  cmp <- comparedf(d1, d2, by = "sample_id", tol.vars = "case")
  d <- diffs(cmp, by.var = TRUE)
  d [1] <- NULL
  
  if(n.diffs(cmp)!=0){
    count=count+1 # this counts entities with some changes in the dating metadata
  }
  
  if(val==1){
    d_ent=d[1:2]
    d_ent$n= ifelse(d_ent$n>0,1,0)  # convert any value to 1 or 0
  }else if (val!=1){
    d$n = ifelse(d$n>0,1,0)  
    d_ent <- quiet(Merge(d_ent[1], d_ent[2]+d[2], by="row.names")) # this counts what changes have been done to any entity
    d_ent [1] <- NULL
  }
}

if (con1@db=='sisalv1_pub') {
  write.csv(d_ent,'sisalv2_paper/output/v1_v1b/chrono_ent.csv') #dfile with the # of changes by variable.
} else if (con1@db=='sisalv1b') {
  write.csv(d_ent,'sisalv2_paper/output/v1b_v2/chrono_ent.csv')
}


paste("===============================================================")

#### DATING TABLE ####

paste("DATING TABLE - 14C dates ")

dating1 <- dbGetQuery(con1, "SELECT * FROM dating WHERE dating.date_type='C14';")
dating2 <- dbGetQuery(con2, "SELECT * FROM dating WHERE dating.date_type='C14';")

#drop U/Th metadata and SISAL_chrono
dat1 <- dating1 %>% select(-1, -3, -(16:30))
dat2 <- dating2 %>% select(-1, -3, -(16:30), -(34:38))

# Instructions to round selected columns:
#d <- data.frame(d1 = rnorm(10, 10), d2 = rnorm(10, 6),d3 = rnorm(10, 2), d4 = rnorm(10, -4))
#exc = !names(d) %in% "d3" # replace d3 by columns not to be rounded
#d[,exc] = round(d[,exc])
#d

exc = !names(dat1) %in% c("entity_id","lab_num","material_dated","calib_used","date_used")
dat1[,exc] = round(dat1[,exc], digits = 1)

s= unique(dat1$entity_id)
count=0

for (val in 1:length(s)) {
  d1 <- dat1 %>% filter(entity_id == s[val]) 
  d2 <- dat2 %>% filter(entity_id == s[val]) 
  cmp <- comparedf(d1, d2, by = "lab_num", tol.vars = "case")
  d <- diffs(cmp, by.var = TRUE) # num of differences per variable for entity s(val)
  d [1] <- NULL
  #d <- d[order(d$var.y),] 
  if(n.diffs(cmp)!=0){
    count=count+1
  }
  if (val==1){
    d_arch=d[1:2]
  } else if(val!=1){
    d_arch <- quiet(Merge(d_arch[1], d_arch[2]+d[2], by="row.names"))
    d_arch [1] <- NULL
    #d_arch <- d_arch[order(d_arch$var.y),] 
  }
}

if (con1@db=='sisalv1_pub' | con2@db=='sisalv1b' ) {
  write.csv(d_arch,'sisalv2_paper/output/v1_v1b/14C.csv') #dfile with the # of changes by variable.
} else if (con1@db=='sisalv1b' | con2@db=='sisalv2' ) {
  write.csv(d_arch,'sisalv2_paper/output/v1b_v2/14C.csv')
}

paste("------")
paste("How many entities had changes in 14C metadata?:", count , collapse=" ")
paste("------")


paste("===============================================================")

#### DATING TABLE ####

paste("DATING TABLE")

dating1 <- dbGetQuery(con1, "SELECT * FROM dating WHERE date_type NOT LIKE '%Event%';")
dating2 <- dbGetQuery(con2, "SELECT * FROM dating WHERE date_type NOT LIKE '%Event%';")

#drop U/Th metadata and SISAL_chrono
dat1 <- dating1 %>% select(1:33)
dat2 <- dating2 %>% select(1:33)

# Instructions to round selected columns:
#d <- data.frame(d1 = rnorm(10, 10), d2 = rnorm(10, 6),d3 = rnorm(10, 2), d4 = rnorm(10, -4))
#exc = !names(d) %in% "d3" # replace d3 by columns not to be rounded
#d[,exc] = round(d[,exc])
#d

exc = !names(dat1) %in% c("dating_id","entity_id","date_type","lab_num","material_dated","calib_used","date_used","decay_constant")
dat1[,exc] = round(dat1[,exc], digits = 4)
dat2[,exc] = round(dat2[,exc], digits = 4)

s= unique(dat1$entity_id)
count=0

for (val in 1:length(s)) {
  d1 <- dat1 %>% filter(entity_id == s[val]) 
  d2 <- dat2 %>% filter(entity_id == s[val]) 
  
  if (is.na(d1$lab_num[1])){ # look for alternative when lab_num is NA!!!
    d1$entity_id <- NULL; d1$entity_id <- NULL
    cmp <- comparedf(d1, d2, by = "corr_age", tol.vars = "case")
  }else {
    d1$entity_id <- NULL; d1$entity_id <- NULL
    cmp <- comparedf(d1, d2, by = "lab_num", tol.vars = "case")
  }
  d <- diffs(cmp, by.var = TRUE)
  d [1] <- NULL

  
  if(n.diffs(cmp)!=0){
    count=count+1 # this counts entities with some changes in the dating metadata
  }
    
  if(val==1){
    d_ent=d[1:2]
    d_ent$n= ifelse(d_ent$n>0,1,0)  # convert any value to 1 or 0
  }else if (val!=1){
    d$n = ifelse(d$n>0,1,0)  
    d_ent <- quiet(Merge(d_ent[1], d_ent[2]+d[2], by="row.names")) # this counts what changes have been done to any entity
    d_ent [1] <- NULL
  }
}


if (con1@db=='sisalv1_pub' | con2@db=='sisalv1b' ) {
  # write.csv(d_arch,'sisalv2_paper/output/v1_v1b/dating_samples.csv') #dfile with the # of changes by variable.
  write.csv(d_ent,'sisalv2_paper/output/v1_v1b/dating_entity.csv') #dfile with the # of changes per entity
} else if (con1@db=='sisalv1b' | con2@db=='sisalv2' ) {
  # write.csv(d_arch,'sisalv2_paper/output/v1b_v2/dating_samples.csv')
  write.csv(d_ent,'sisalv2_paper/output/v1b_v2/dating_entity.csv') #dfile with the # of changes per entity
}

paste("------")
paste("How many entities had changes in dating metadata?:", count , collapse=" ")
paste("------")
paste("See dating_entity for details on what has been changed in how many entities")
# paste("See dating_samples.csv for how many samples in the dating table have been changed")


#### NOTES ####
paste("NOTES TABLE")

note1 <- dbGetQuery(con1, "SELECT * FROM notes")
note2 <- dbGetQuery(con2, "SELECT * FROM notes")

cmp <- comparedf(note1, note2, by = "site_id", tol.vars = "case")
paste("------")
paste("Number of old notes modified:", n.diffs(cmp, vars = "notes"), collapse=" ")
paste("------")
paste("Number of old notes deleted: see overall summary")
paste("------")
paste("Number of new notes added: see overall summary")
paste("------")
paste("See overall summary to check the extent of those modifications (are they typos?)")
paste("------")

if (con1@db=='sisalv1_pub') {
  write.csv(diffs(cmp, by.var = TRUE),'sisalv2_paper/output/v1_v1b/notes.csv')
} else if (con1@db=='sisalv1b') {
  write.csv(diffs(cmp, by.var = TRUE),'sisalv2_paper/output/v1b_v2/notes.csv')
}

#summary(cmp)
rm(cmp)

paste("===============================================================")

# REFERENCES
paste("REFERENCES TABLE")

query <- paste("SELECT entity.entity_id, 
group_concat(reference.citation ORDER BY reference.citation SEPARATOR ' ; ') as 'citation', 
group_concat(reference.publication_DOI ORDER BY reference.citation SEPARATOR ' ; ') as 'publication_DOI' 
FROM site JOIN entity USING (site_id) JOIN entity_link_reference USING (entity_id) JOIN reference USING (ref_id) GROUP BY (entity_id);")

ref1 <- dbGetQuery(con1, query)
ref2 <- dbGetQuery(con2, query)

cmp <- comparedf(ref1, ref2, by = "entity_id", tol.vars = "case")

paste("------")
paste("Number of old citations modified:", n.diffs(cmp, vars = "citation"), collapse=" ")
paste("------")
paste("Number of publication_DOI modified:", n.diffs(cmp, vars = "publication_DOI"), collapse=" ")
paste("------")
paste("See overall summary to check the extent of those modifications (are they typos?)")
paste("------")

if (con1@db=='sisalv1_pub') {
  write.csv(diffs(cmp, by.var = TRUE),'sisalv2_paper/output/v1_v1b/ref.csv')
} else if (con1@db=='sisalv1b') {
  write.csv(diffs(cmp, by.var = TRUE),'sisalv2_paper/output/v1b_v2/ref.csv')
}

#summary(cmp)
rm(cmp)


#### Disconnect from db ####
dbDisconnect(con1)
dbDisconnect(con2)

rm(con1,con2)
sink()
#file.show("all.Rout")



paste("===============================================================")

