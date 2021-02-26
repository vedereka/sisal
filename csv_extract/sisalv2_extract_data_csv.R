# Script to upload and query the sisal database from csv files
# 
# This script creates two functions:
#   1- read.sisal.csv: loads csv sisalv2 files and creates a "sisal object"
#   2- sisal.time.series: extracts time-series for a time period and region (with references)
# 
# Tested with sisalv2
# 
# References:
# 
# dataset: Comas-Bru et al., 2020a; https://doi.org/10.17864/1947.256
# data paper: Comas-Bru et al., 2020b; https://doi.org/10.5194/essd-12-2579-2020
# 
# Created by Laia Comas-Bru
# Date: February 2021
# 
# 
library (tidyverse)
# 
#### function to load csv files ####
read.sisal.csv <- function(file_path, # file path to sisal csv files
                           prefix = '' # prefix to sisal csv files; no prefix vor v1b and v2 files
){
  
  # read in files
  composite_link_entity <- read.csv(file.path(file_path, paste(prefix, 'composite_link_entity.csv', sep = '')), header = T,stringsAsFactors = F)
  d13C <- read.csv(file.path(file_path,paste(prefix, 'd13C.csv',sep='')),header = T, stringsAsFactors = F)
  d13C <- rename(d13C, iso_std_d13C = iso_std )
  d18O <- read.csv(file.path(file_path,paste(prefix, 'd18O.csv', sep ='')),header = T, stringsAsFactors = F)
  d18O <- rename(d18O, iso_std_d18O = iso_std)
  dating_lamina <- read.csv(file.path(file_path,paste(prefix, 'dating_lamina.csv', sep = '')), header = T, stringsAsFactors = F) %>% 
    mutate_at(vars(depth_lam, lam_thickness, lam_age_uncert_pos, lam_age_uncert_neg), as.numeric)
  dating <- read.csv(file.path(file_path,paste(prefix, 'dating.csv',sep = '')), header = T, stringsAsFactors = F) %>%
    mutate_at(vars(depth_dating, dating_thickness,min_weight, max_weight, uncorr_age, uncorr_age_uncert_pos, uncorr_age_uncert_neg, starts_with('X'), corr_age), as.numeric)
  entity_link_reference <- read.csv(file.path(file_path,paste(prefix, 'entity_link_reference.csv', sep = '')), header =T, stringsAsFactors = F)
  entity <- read.csv(file.path(file_path,paste(prefix, 'entity.csv', sep = '')), header = T, stringsAsFactors = F) %>% mutate_at(vars(cover_thickness, distance_entrance), as.numeric)
  gap <- read.csv(file.path(file_path,paste(prefix, 'gap.csv', sep = '')), header = T, stringsAsFactors = F)
  hiatus <- read.csv(file.path(file_path,paste(prefix, 'hiatus.csv', sep ='')), header = T, stringsAsFactors = F)
  notes <- read.csv(file.path(file_path,paste(prefix, 'notes.csv', sep = '')), header = T, stringsAsFactors = F)
  original_chronology <- read.csv(file.path(file_path,paste(prefix, 'original_chronology.csv', sep = '')), header = T, stringsAsFactors = F) %>% mutate_at(vars(interp_age_uncert_pos, interp_age_uncert_neg), as.numeric)
  reference <- read.csv(file.path(file_path,paste(prefix, 'reference.csv', sep = '')), header = T, stringsAsFactors = F)
  sample <- read.csv(file.path(file_path,paste(prefix, 'sample.csv', sep = '')), header = T, stringsAsFactors = F) %>% mutate_at(vars(sample_thickness, depth_sample), as.numeric)
  sisal_chronology <- read.csv(file.path(file_path,paste(prefix, 'sisal_chronology.csv', sep = '')), header = T, stringsAsFactors = F) %>% mutate_at(vars(everything()), as.numeric)
  site <- read.csv(file.path(file_path,paste(prefix, 'site.csv', sep = '')), header = T, stringsAsFactors = F) %>% mutate_at(vars(elevation), as.numeric)
  
  # correct for depth_ref 'from base'
  entity_from_base <- entity %>% filter(depth_ref == 'from base') %>% distinct(entity_id)
  sample_from_base <- sample %>% filter(entity_id %in% entity_from_base$entity_id) %>% select(entity_id,depth_sample) %>% group_by(entity_id) %>% summarise(max = max(depth_sample))
  
  dating_from_base <- full_join(dating, sample_from_base, by = 'entity_id') %>% group_by(entity_id) %>% 
    mutate(depth_conv = if_else(entity_id %in% entity_from_base$entity_id, max-depth_dating, NA_real_)) %>% 
    mutate(depth_dating = if_else(!is.na(depth_conv), depth_conv, depth_dating)) %>%
    select(-depth_conv) %>% arrange(., depth_dating, .by_group = T)
  
  sampling_from_base <- full_join(sample, sample_from_base, by = 'entity_id') %>% group_by(entity_id) %>% 
    mutate(depth_conv = if_else(entity_id %in% entity_from_base$entity_id, max-depth_sample, NA_real_)) %>% 
    mutate(depth_sample = if_else(!is.na(depth_conv), depth_conv, depth_sample)) %>%
    select(-depth_conv) %>% arrange(., depth_sample, .by_group = T)
  
  # create sisal object
  d <- list()
  d$composite_link_entity <- composite_link_entity
  d$d13C <- d13C
  d$d18O <- d18O
  d$dating_lamina <- dating_lamina
  d$dating <- dating_from_base
  d$entity_link_reference <- entity_link_reference
  d$entity <- entity
  d$gap <- gap
  d$hiatus <- hiatus
  d$notes <- notes
  d$original_chronology <- original_chronology
  d$reference <- reference
  d$sample <- sampling_from_base
  d$sisal_chronology <- sisal_chronology
  d$site <- site
  
  return(d)
}

#### function to extract time series data for a region and time period ####
sisal.time.series <- function(s, # sisal object
                              t_i, # start of time period (oldest; yrs BP 1950)
                              t_f, # end of time period (more recent; yrs BP 1950)
                              lat_min, # min latitude
                              lat_max, # max latitude
                              lon_min, # min longitude
                              lon_max, # max longitude
                              e_status #entity_status; if e_status == 1: no filter;
                              # e_status == 2: filter for entity_status != 'superseded'; 
                              # e_status == 3: filter for !(entity_status &in& c('superseded', 'current partially modified'))
){
  
  # merge original and v2 sisal chronology to substitute for missing original chronologies
  linear <- s$sisal_chronology %>% filter(!is.na(lin_interp_age)) %>% select(sample_id, lin_interp_age, lin_interp_age_uncert_pos, lin_interp_age_uncert_neg)  %>% 
    rename(interp_age=lin_interp_age, interp_age_uncert_pos = lin_interp_age_uncert_pos, interp_age_uncert_neg = lin_interp_age_uncert_neg ) %>%
    mutate(age_model_type = 'sisal: linear')
  
  linear_reg <- s$sisal_chronology %>% filter(!is.na(lin_reg_age)) %>% select(sample_id, lin_reg_age, lin_reg_age_uncert_pos, lin_reg_age_uncert_neg)  %>% 
    rename(interp_age=lin_reg_age, interp_age_uncert_pos = lin_reg_age_uncert_pos, interp_age_uncert_neg = lin_reg_age_uncert_neg ) %>%
    mutate(age_model_type = 'sisal: linear_reg')
  
  bchron <- s$sisal_chronology %>% filter(!is.na(Bchron_age)) %>% select(sample_id, Bchron_age, Bchron_age_uncert_pos, Bchron_age_uncert_neg) %>% 
    rename(interp_age=Bchron_age, interp_age_uncert_pos = Bchron_age_uncert_pos, interp_age_uncert_neg = Bchron_age_uncert_neg ) %>%
    mutate(age_model_type = 'sisal: Bchron')
  
  bacon <- s$sisal_chronology %>% filter(!is.na(Bacon_age)) %>% select(sample_id, Bacon_age, Bacon_age_uncert_pos, Bacon_age_uncert_neg) %>% 
    rename(interp_age=Bacon_age, interp_age_uncert_pos = Bacon_age_uncert_pos, interp_age_uncert_neg = Bacon_age_uncert_neg) %>% 
    mutate(age_model_type = 'sisal: Bacon')
  
  COPRA <- s$sisal_chronology %>% filter(!is.na(copRa_age )) %>% select(sample_id, copRa_age, copRa_age_uncert_pos, copRa_age_uncert_neg) %>% 
    rename(interp_age=copRa_age, interp_age_uncert_pos = copRa_age_uncert_pos, interp_age_uncert_neg = copRa_age_uncert_neg ) %>%
    mutate(age_model_type = 'sisal: COPRA')
  
  StalAge <- s$sisal_chronology %>% filter(!is.na(StalAge_age)) %>% select(sample_id, StalAge_age, StalAge_age_uncert_pos, StalAge_age_uncert_neg) %>% 
    rename(interp_age=StalAge_age, interp_age_uncert_pos = StalAge_age_uncert_pos, interp_age_uncert_neg = StalAge_age_uncert_neg ) %>%
    mutate(age_model_type = 'sisal: StalAge')
  
  s$chrono <- bind_rows(s$original_chronology, linear, linear_reg, bchron, bacon, COPRA, StalAge) %>%
    left_join(s$sample, ., by = 'sample_id') %>%
    select(entity_id, sample_id, interp_age, interp_age_uncert_pos, interp_age_uncert_neg, age_model_type)
  
  # not all entities have chrono/iso (composite entities)
  s$entity <- s$entity %>% filter(entity_id %in% s$chrono$entity_id)
  
  # apply regional filter
  sit <- s$site %>% filter (latitude < lat_max & latitude > lat_min & 
                              longitude < lon_max & longitude > lon_min)
  
  # select list of entities
  if(e_status == 1) {
    eID <- s$entity %>% filter(site_id %in% sit$site_id) %>% distinct(entity_id)
  } else if(e_status == 2) {
    eID <- s$entity %>% filter(site_id %in% sit$site_id) %>%
      filter(entity_status != 'superseded') %>% distinct(entity_id)
  } else if(e_status == 3) {
    eID <-s$entity %>% filter(site_id %in% sit$site_id) %>% 
      filter(entity_status == 'current') %>% distinct(entity_id)
  }
  
  # filter chrono for selected entities
  t <- s$chrono %>% filter(entity_id %in% eID$entity_id)
  
  # merge isotope information
  iso <- t %>% left_join(., s$d18O %>% select(sample_id, d18O_measurement, d18O_precision), by = 'sample_id') 
  
  # filter for time period 
  ts <- iso %>% filter(interp_age < t_i & interp_age > t_f)
  
  # add reference info
  ref <- s$reference %>% full_join (., s$entity_link_reference, by ="ref_id") %>% 
    filter (entity_id %in% ts$entity_id) %>%
    left_join(., s$entity %>% select (site_id, entity_id, entity_name), by = 'entity_id') %>% 
    left_join (., sit %>% select (site_id,site_name), by = 'site_id') %>% 
    select (site_id, site_name, entity_id, entity_name, publication_DOI, citation) %>% 
    rename (DOI = publication_DOI)
  
  # create sisal object
  return.data <- list()
  return.data$ref <- ref
  return.data$ts <- ts
  
  return(return.data)
}

#### data extraction ####
# define variables
file_path <- paste(getwd(), '/csv_extract/sisalv2_csv/', sep="")
prefix <- '' # no prefix for v2

# load sisal v2
sisalv2 <- read.sisal.csv(file_path, prefix) # read in data

# extract time series
# SISAL.time.series (sisalobject, oldest time, more recent time, min lat, max lat, min long, max long, entity status)
sisal_data <- sisal.time.series (sisalv2, 2000, 0, -90, 90, -180, 180,1)

# select only original chronologies:
sisal_data_subset <- sisal_data$ts %>% filter(., !grepl("sisal",age_model_type))