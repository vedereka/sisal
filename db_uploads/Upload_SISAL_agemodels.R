# This file contains functions which can be used up upload and update SISAL age models in
# the SISAL database
#
# It is to be sourced into another R file
# See Example_upload_SISAL_agemodels.R on how this is done
# 
# Created in September 2019 by K.Atsawawaranunt and modified by Laia Comas-Bru
# Last modified: February 2021

input_sisal_chronology_depth <- function(cnx, 
                                   entity_id, 
                                   agemodeltype, 
                                   tb, 
                                   tb_depth_col, 
                                   tb_age_col, 
                                   tb_age_uncert_pos_col, 
                                   tb_age_uncert_neg_col, 
                                   outputcsv,
                                   execution = F){
  # Function: input_sisal_chronology
  #
  # This function inputs SISAL age models into the SISAL database.
  #
  # Prerequisite libraries:
  #   RMariaDB
  #
  # Inputs:
  #   cnx = connection (Formal class MariaDBConnection)
  #   entity_id = entity_id (numeric)
  #   agemodeltype = age model type (character). This must correspond
  #     to the prefix of the column names in the sisal chronology table.
  #     E.g. "Bchron" if the columns in sisal_chronology is "Bchron_age" etc.
  #   tb = dataframe containing the sisal chronology
  #   tb_depth_col = name of column with the depths data (character)
  #   tb_age_col = name of column with age data (character)
  #   tb_age_uncert_pos_col = name of column with age_uncert_pos data (character)
  #   tb_age_uncert_neg_col = name of column with age_uncert_neg data (character)
  #   outputcsv = path to outputfile for sisal chronology dates with sample_id attached to depths  (character)
  #   execution = whether or not to execute the queries or just to output the xlsx file (True or False, default to False) (boolean)
  # 
  # Return:
  #   Nothing. Updates the database accordingly.
  require(RMariaDB)
  require(openxlsx)
  agecol <- paste(agemodeltype, '_age', sep = '')
  agecoluncertneg <- paste(agemodeltype, '_age_uncert_neg', sep = '')
  agecoluncertpos <- paste(agemodeltype, '_age_uncert_pos', sep = '')
  tb$depth_sample <- tb[[tb_depth_col]]
  tb[[agecol]] <- tb[[tb_age_col]]
  tb[[agecoluncertpos]] <- tb[[tb_age_uncert_pos_col]]
  tb[[agecoluncertneg]] <- tb[[tb_age_uncert_neg_col]]
  tb <- tb[c(agecol, agecoluncertneg, agecoluncertpos, 'depth_sample')]
  if (any(is.na(tb[[tb_depth_col]]))){
    stop(paste('There is data missing in', tb_depth_col, '. This is not allowed.'))
  } else  if (any(is.na(tb[[agecol]]))){
    stop(paste('There is data missing in', agecol, '. As of present, this is not allowed.'))
  } else  if (any(is.na(tb[[agecoluncertpos]]))){
    stop(paste('There is data missing in', agecoluncertpos, '. As of present, this is not allowed.'))
  } else  if (any(is.na(tb[[agecoluncertneg]]))){
    stop(paste('There is data missing in', agecoluncertneg, '. As of present, this is not allowed.'))
  }
  
  # 3. Query the sisal database for the particular entity
  query <- paste("SELECT * FROM sample WHERE entity_id = ", entity_id, ';', sep = '')
  dt <- dbGetQuery(cnx, query)
  
  # check that there are no repeated depths
  if (length(dt$depth_sample[duplicated(dt$depth_sample)]) > 0){
    print(paste('Entity_id =', entity_id,': there are repeated depths in database'))
    next
  }
  
  # check that there all depths in age model output exists in database
  if (length(setdiff(tb$depth_sample, dt$depth_sample)) > 0){
    print(paste('Entity_id =', entity_id,': there are depths in age model output that does not exist in database. These are:', paste(setdiff(tb$depth_sample, dt$depth_sample), collapse = ', ')))
    next
  }
  
  dt <- dt[c('sample_id', 'depth_sample')]
  
  tb <- merge(tb, dt)
  write.csv(tb, outputcsv)
  # dbBegin(cnx)
  if (execution == T) {
    tb$depth_sample <- NULL
    # query sisal_chronology for the same isotope sample_id
    query <- paste("SELECT * FROM sisal_chronology WHERE sample_id IN (", paste(tb$sample_id, collapse = ', '), ');', sep = '')
    dt1 <- dbGetQuery(cnx, query)
    # if sample_id exist in sisal_chronology, we have to use the UPDATE statement instead of dbWriteTable
    if (dim(dt1)[1] > 0){
      # subset for the part with sample_id which already exists in the database
      updatetb <- tb[tb$sample_id %in% dt1$sample_id,] # this will have more than one row to begin with
      col2update <- colnames(updatetb)[!(colnames(updatetb) %in% 'sample_id')] # expecting 3 columns 
      for (j in 1:dim(updatetb)[1]){
        col1 <- col2update[1]
        col2 <- col2update[2]
        col3 <- col2update[3]
        query <- paste("UPDATE sisal_chronology SET ", col1, ' = ', updatetb[[col1]][j], ', ', col2, ' = ', updatetb[[col2]][j], ', ', col3, ' = ', updatetb[[col3]][j], ' WHERE sample_id = ', updatetb[['sample_id']][j], ';', sep = '')
        dbExecute(cnx, query)
      }
      appendtb <- tb[!(tb$sample_id %in% dt1$sample_id),]
      if (dim(appendtb)[1] > 0){
        dbWriteTable(row.names = F, cnx, "sisal_chronology", appendtb, append = T)
      }
    } else {
      dbWriteTable(row.names = F, cnx, "sisal_chronology", tb, append = T)
    }
  }
  # dbCommit(cnx)
}

input_sisal_chronology_sampleid <- function(cnx, 
                                   agemodeltype, 
                                   tb, 
                                   tb_sample_id_col, 
                                   tb_age_col, 
                                   tb_age_uncert_pos_col, 
                                   tb_age_uncert_neg_col){
  # Function: input_sisal_chronology 
  #
  # This function inputs SISAL age models into the SISAL database.
  #
  # Prerequisite libraries:
  #   RMariaDB
  #
  # Inputs:
  #   cnx = connection (Formal class MariaDBConnection)
  #   agemodeltype = age model type (character). This must correspond
  #     to the prefix of the column names in the sisal chronology table.
  #     E.g. "Bchron" if the columns in sisal_chronology is "Bchron_age" etc.
  #   tb = dataframe containing the sisal chronology
  #   tb_sample_id_col = name of column with the sample_id data (character)
  #   tb_age_col = name of column with age data (character)
  #   tb_age_uncert_pos_col = name of column with age_uncert_pos data (character)
  #   tb_age_uncert_neg_col = name of column with age_uncert_neg data (character)
  # 
  # Return:
  #   Nothing. Updates the database accordingly.
  require(RMariaDB)
  require(openxlsx)
  agecol <- paste(agemodeltype, '_age', sep = '')
  agecoluncertneg <- paste(agemodeltype, '_age_uncert_neg', sep = '')
  agecoluncertpos <- paste(agemodeltype, '_age_uncert_pos', sep = '')
  tb$sample_id <- tb[[tb_sample_id_col]]
  tb[[agecol]] <- tb[[tb_age_col]]
  tb[[agecoluncertpos]] <- tb[[tb_age_uncert_pos_col]]
  tb[[agecoluncertneg]] <- tb[[tb_age_uncert_neg_col]]
  tb <- tb[c(agecol, agecoluncertneg, agecoluncertpos, 'sample_id')]
  if (any(is.na(tb[[tb_sample_id_col]]))){
    stop(paste('There is data missing in', tb_sample_id_col, '. This is not allowed.'))
  } else  if (any(is.na(tb[[agecol]]))){
    stop(paste('There is data missing in', agecol, '. As of present, this is not allowed.'))
  } else  if (any(is.na(tb[[agecoluncertpos]]))){
    stop(paste('There is data missing in', agecoluncertpos, '. As of present, this is not allowed.'))
  } else  if (any(is.na(tb[[agecoluncertneg]]))){
    stop(paste('There is data missing in', agecoluncertneg, '. As of present, this is not allowed.'))
  }
  # dbBegin(cnx)
  # tb$depth_sample <- NULL
  # query sisal_chronology for the same isotope sample_id
  query <- paste("SELECT * FROM sisal_chronology WHERE sample_id IN (", paste(tb$sample_id, collapse = ', '), ');', sep = '')
  dt1 <- dbGetQuery(cnx, query)
  # if sample_id exist in sisal_chronology, we have to use the UPDATE statement instead of dbWriteTable
  if (dim(dt1)[1] > 0){
    # subset for the part with sample_id which already exists in the database
    updatetb <- tb[tb$sample_id %in% dt1$sample_id,] # this will have more than one row to begin with
    col2update <- colnames(updatetb)[!(colnames(updatetb) %in% 'sample_id')] # expecting 3 columns 
    for (j in 1:dim(updatetb)[1]){
      col1 <- col2update[1]
      col2 <- col2update[2]
      col3 <- col2update[3]
      query <- paste("UPDATE sisal_chronology SET ", col1, ' = ', updatetb[[col1]][j], ', ', col2, ' = ', updatetb[[col2]][j], ', ', col3, ' = ', updatetb[[col3]][j], ' WHERE sample_id = ', updatetb[['sample_id']][j], ';', sep = '')
      dbExecute(cnx, query)
    }
    appendtb <- tb[!(tb$sample_id %in% dt1$sample_id),]
    if (dim(appendtb)[1] > 0){
      dbWriteTable(row.names = F, cnx, "sisal_chronology", appendtb, append = T)
    }
  } else {
    dbWriteTable(row.names = F, cnx, "sisal_chronology", tb, append = T)
  }

  # dbCommit(cnx)
}

update_date_used_agemodel <- function(cnx, tb, dating_id_col, tbdate_used_col, dbdate_use_col){
  # Function name: update_date_used_agemodel
  #
  # This function updates the date_used_agemodel column in the database according to a table 
  # with dating_id
  #
  # Prerequisite libraries
  #   RMariaDB
  #
  # Input:
  #   cnx = connection (Formal class MariaDBConnection)
  #   tb = dataframe containing the sisal chronology
  #   dating_id_col = name of column with the dating_id data (character) (usually would be 'dating_id')
  #   tbdate_used_col = name of column in the dataframe tb with date_used information for that agemodel type (character) (e.g. 'date_used_Bacon')
  #   dbdate_use_col = name of column in the database with date_used information for that agemodel type (character) (e.g. 'date_used_Bacon')
  #
  # Return:
  #   Nothing, updates the database accordingly
  dbBegin(cnx)
  for (i in seq(1,dim(tb)[1], by = 1)){
    dating_id <- tb[[dating_id_col]][i]
    dateused <- tb[[tbdate_used_col]][i]
    query <- paste("UPDATE dating SET ", dbdate_use_col, " = '", dateused, "' WHERE dating_id = ", dating_id, ";",  sep = '')
    dbSendQuery(cnx, query)
  }
  dbCommit(cnx)
}
