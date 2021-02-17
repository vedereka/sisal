# Script to obtain number of records per period
# Created by Carla Roescher in November 2019
# Last modified by Laia Comas-Bru in February 2021
# Source: SISALv2 database csv flat files (Comas-Bru et al. https://doi.org/10.17864/1947.256)

library(tidyverse)

# functions for quality check
SISAL.quality.check <- function(s, # sisal object
                                T_0, # start of time period
                                T_1, # end of time period
                                N_iso, # number of isotopes desired in time period
                                N_date, # number of dating points desired in time period
                                range, # plus/minus variation on T_0 and T_1
                                e_status = 1 #entity_status; if e_status == 1: no filter; e_status == 2: filter for entity_status != 'superseded'; 
                                                                    #e_status == 3: filter for !(entity_status &in& c('superseded', 'current partially modified'))
                                ){
  
  
  
  if(e_status == 1) {
    eID <- s$entity %>% distinct(entity_id)
  } else if(e_status == 2) {
    eID <- s$entity %>% filter(entity_status != 'superseded') %>% distinct(entity_id)
  } else if(e_status == 3) {
    eID <- s$entity %>% filter(entity_status == 'current') %>% distinct(entity_id)
  }
  
  # merge original and v2 sisal chronology to substitute for missing original chronologies
  linear <- s$sisal_chronology %>% filter(!is.na(linear_age)) %>% select(sample_id, linear_age, linear_age_uncert_pos, linear_age_uncert_neg)  %>% 
    rename(interp_age=linear_age, interp_age_uncert_pos = linear_age_uncert_pos, interp_age_uncert_neg = linear_age_uncert_neg ) %>%
    mutate(age_model_type = 'sisal: linear')
  linear_reg <- s$sisal_chronology %>% filter(!is.na(linear_regress_age)) %>% select(sample_id, linear_regress_age, linear_regress_age_uncert_pos, linear_regress_age_uncert_neg)  %>% 
    rename(interp_age=linear_regress_age, interp_age_uncert_pos = linear_regress_age_uncert_pos, interp_age_uncert_neg = linear_regress_age_uncert_neg ) %>%
    mutate(age_model_type = 'sisal: linear_regress')
  bchron <- s$sisal_chronology %>% filter(!is.na(Bchron_age)) %>% select(sample_id, Bchron_age, Bchron_age_uncert_pos, Bchron_age_uncert_neg) %>% 
    rename(interp_age=Bchron_age, interp_age_uncert_pos = Bchron_age_uncert_pos, interp_age_uncert_neg = Bchron_age_uncert_neg ) %>%
    mutate(age_model_type = 'sisal: Bchron')
  bacon <- s$sisal_chronology %>% filter(!is.na(Bacon_age)) %>% select(sample_id, Bacon_age, Bacon_age_uncert_pos, Bacon_age_uncert_neg) %>% 
    rename(interp_age=Bacon_age, interp_age_uncert_pos = Bacon_age_uncert_pos, interp_age_uncert_neg = Bacon_age_uncert_neg) %>% 
    mutate(age_model_type = 'sisal: Bacon')
  COPRA <- s$sisal_chronology %>% filter(!is.na(COPRA_age)) %>% select(sample_id, COPRA_age, COPRA_age_uncert_pos, COPRA_age_uncert_neg) %>% 
    rename(interp_age=COPRA_age, interp_age_uncert_pos = COPRA_age_uncert_pos, interp_age_uncert_neg = COPRA_age_uncert_neg ) %>%
    mutate(age_model_type = 'sisal: COPRA')
  
  original <- bind_rows(s$original_chronology, linear, linear_reg, bchron, COPRA) %>% left_join(s$sample, ., by = 'sample_id') %>% select(entity_id, sample_id, interp_age, interp_age_uncert_pos, interp_age_uncert_neg, age_model_type) #%>%
  
  # filter first and last interp_age in the desired time period
  t_0 <- original %>% filter(interp_age >= T_0 + range & interp_age <= T_1 - range) %>% group_by(entity_id) %>% slice(.,1) %>% ungroup()
  t_1 <- original %>% filter(interp_age >= T_0 + range & interp_age <= T_1 - range) %>% group_by(entity_id) %>% slice(., n()) %>% ungroup()
  
  # filter interp_ages that are younger and older than desired period to check if record covers the whole time period
  t_check_0 <- original %>% filter(interp_age < T_0 + range) %>% group_by(entity_id) %>% slice(., n()) %>% ungroup()
  t_check_1 <- original %>% filter(interp_age > T_1 - range) %>% group_by(entity_id) %>% slice(., 1) %>% ungroup() %>% filter(entity_id %in% t_check_0$entity_id)
  t_check <- t_check_1 %>% filter(entity_id %in% t_0$entity_id) %>% left_join(., t_check_0, by = 'entity_id') %>%
    mutate(cov_iso = if_else(entity_id %in% t_check_1$entity_id, T, F)) # check if whole period is covered by the record
  
  # count number of isotope measurements in time period
  n <- orig_tb %>% filter(interp_age >= T_0 + range & interp_age <= T_1 - range) %>% group_by(entity_id) %>% count() %>% ungroup()
  
  # filter first and last dating point in the desired time period
  d_0 <- dating %>% filter(date_used == 'yes' & entity_id %in% eID$entity_id & date_type != 'Event; hiatus') %>%  filter(corr_age >= T_0 + range & corr_age <= T_1 - range) %>% group_by(entity_id) %>% slice(.,1) %>% ungroup()
  d_1 <- dating %>% filter(date_used == 'yes' & entity_id %in% eID$entity_id & date_type != 'Event; hiatus') %>%  filter(corr_age >= T_0 + range & corr_age <= T_1 - range) %>% group_by(entity_id) %>% slice(.,n()) %>% ungroup() 
  
  # filter dating points that are younger and older than desired period to check if record covers the whole time period
  d_check_0 <- dating %>% filter(date_used == 'yes' & entity_id %in% eID$entity_id & date_type != 'Event; hiatus') %>%  filter(corr_age < T_0 + range) %>% group_by(entity_id) %>% slice(., n()) %>% ungroup()
  d_check_1 <- dating %>% filter(date_used == 'yes' & entity_id %in% eID$entity_id & date_type != 'Event; hiatus') %>%  filter(corr_age > T_1 - range) %>% group_by(entity_id) %>% slice(., 1) %>% ungroup() %>% filter(entity_id %in% d_check_0$entity_id)
  d_check <- d_check_1 %>% filter(entity_id %in% d_0$entity_id) %>% left_join(., d_check_0, by = 'entity_id') %>%
    mutate(cov_date = if_else(entity_id %in% d_check_1$entity_id, T, F)) # check if whole period is covered by the record
  
  # count number of dating points in time period
  N <- dating %>% filter(date_used == 'yes' & entity_id %in% eID$entity_id) %>%  filter(corr_age >= T_0 + range & corr_age <= T_1 - range) %>% group_by(entity_id) %>% count() %>% ungroup()
  
  # merge isotope information
  return_iso <- t_0 %>% distinct(entity_id) %>% mutate(
    age_model = t_0$age_model_type,
    t_0 = t_0$interp_age,
    t_1 = t_1$interp_age,
    n_iso = n$n,
    min_iso = if_else(t_1 - t_0 > (1/3)*(T_1-T_0), T, F), # check that minimum time period (1/3) is covered 
    n_iso_min = if_else(n_iso < N_iso, F, T)) %>% # check if isotope resolution is met
    full_join(., t_check %>% select(entity_id, cov_iso), by = 'entity_id') 
  
  #merge dating information
  return_date <- d_0 %>% distinct(entity_id) %>% mutate(
    d_0 = d_0$corr_age,
    d_1 = d_1$corr_age,
    n_date = N$n,
    min_date = if_else(d_1 - d_0 < (1/3)*(T_1-T_0), F, T), # check that minimum time period is covered; here: 1/3 of the dsired time period
    n_date_min = if_else(n_date < N_date, F, T)) %>% # chacke that dating resolution is met
    full_join(., d_check %>% select(entity_id, cov_date), by = 'entity_id')
  
  quality.check <- full_join(return_iso, return_date, by = 'entity_id') # merge isotope and dating information
  
  return(quality.check)
}

read.SISAL.files <- function(file_path, # file path to sisal csv files
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
  d$composit_link_entity <- composite_link_entity
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


# define variables
file_path <- '.../SISAL Data/sisalv2'
prefix <- ''

# load sisal v2
sisalv2 <- read.SISAL.files(file_path, prefix) # read in data

## SISAL numbers 
#There are XX records that cover the entire last2k with an average resolution of XX.
qc2k <- SISAL.quality.check(sisalv2, -68, 2000, 41, 1, 100) %>% filter(min_iso) %>% mutate(sol = n_iso/(t_1-t_0)*100)
qc2k_1 <- qc2k %>% filter(cov_iso) # filter for total time period cover
qc2k_2 <- qc2k %>% filter(n_date >= 1) # filter for dating resolution
mean(qc2k$sol) # calculate average isotope resolution

#There are XX records that cover some part of the Holocene (last 11.6 kyrs) with XX of these covering the whole period with at least one measurement every 500-yr period.
qcHolocene <- SISAL.quality.check(sisalv2, -68, 11600, 23, 3, 300) %>% filter(min_iso & n_iso_min)
qcHolocene_1 <- qcHolocene %>% filter(cov_iso) # filter for total time period cover
qcHolocene_2 <- qcHolocene %>% filter(n_date >= 3) # filter for dating resolution

#There are XX entities during the deglaciation period (21,000 to 11,600 yrs) with xx records coveringthe whole period with at least one measurement every 500-yr time period.
qcDeGl <- SISAL.quality.check(sisalv2, 11600, 21000, 19, 3, 300) %>% filter(min_iso & n_iso_min)
qcDeGl_1 <- qcDeGl %>% filter(cov_iso) # filter for total time period cover
qcDeGl_2 <- qcDeGl %>% filter(n_date >= 3) # filter for dating resolution

#There are XX speleothem records covering the Last Interglacial (130-115 kyrs) with XX available at every 1000-yr time-slice.
qcIntGl <- SISAL.quality.check(sisalv2, 115000, 130000, 0, 4, 1000) %>% filter(min_iso) %>% mutate(sol = n_iso/(t_1-t_0)*1000)
qcIntGl_1 <- qcIntGl %>% filter(cov_iso) # filter for total time period cover
qcIntgl_2 <- qcIntGl %>% filter(n_date >= 4) # filter for dating resolution
mean(qcIntGl$sol) # calculate average isotope resolution

