# This script builds on a Matlab script created by Sahar Amirnejad and Laia Comas-Bru
# to produce the resolution plot in Lechleitner et al., 2019 (Quaternary).
# It also creates a regional map with number of entities per site (with WOKAM data underneath)
# Example region here is region but the coordinates´range can be adjusted as necessary. 
# This script requires the SISALv2 database in a local sql server (or adjust script to load a csv file with the data)
# WOKAM and coastal shapefiles must be saved in input
# Plots will be saved in "output" as pdf
# Define lat/lon limits for other regions in L58
# Author: Laia Comas-Bru
# Date: May 2020
# 
# Clear plots
graphics.off()
# 
# Clear environment
rm(list = ls())
#
# clear console
cat("\014") #ctrl+L

# SET FOLDERS, FUNCTIONS AND READ SHAPE FILE FOR COASTLINES------------------------------------------------------------------------------

# load contributed packages
if(!require("pacman")) install.packages ("pacman")
options("rgdal_show_exportToProj4_warnings"="none")
pacman::p_load (RMariaDB, RColorBrewer, openxlsx, dplyr, ggplot2, tidyr,data.table, 'plot.matrix', sp,rgdal)

# set folders
plotpath <- (paste(getwd(),"/sisal_regional_map_resolution/output/",sep="")) #figures saved here
datapath <- (paste(getwd(),"/sisal_regional_map_resolution/input/",sep="")) # wokam and coast shapefiles

# function to supress automatic output from cat(). Use it as: y <- quiet(FUNCTION)
quiet <- function(x) { 
  sink(tempfile()) 
  on.exit(sink()) 
  invisible(force(x)) 
} 

# Read in WOKAM shape file for plotting
shapefile_wokam <- quiet(readOGR(dsn=paste(datapath,"wokam/wokam_final_WGS84.shp",sep="")))
shapefile_wokam_df <- fortify(shapefile_wokam)

# Read in coastal shape file for plotting
shapefile <- quiet(readOGR(dsn=paste(datapath,"ne_110m_land/ne_110m_land.shp", sep=""),layer = 'ne_110m_land'))
shapefile_df <- fortify(shapefile)

# prepare shapefiles for plotting map with sites (change continent colour, transparency, line thickness here)
mapWorld <- geom_polygon(data= shapefile, aes(x = long, y = lat, group = group), fill = 'grey87', colour = 'grey', size = 0.05, alpha=0.7)
mapWokam <- geom_polygon(data= shapefile_wokam_df, aes(x = long, y = lat, group = group), fill = 'grey67', size = 0.05, alpha=0.7)

# CONNECT TO SISAL DATABASE (LOCAL SERVER)------------------------------------------------------------------------------
#adjust user/password/dbname as necessary
mydb = dbConnect(MariaDB(), user='root', 
                 password='password', 
                 dbname='sisalv2', 
                 host='localhost')

quiet(dbExecute(mydb, 'SET NAMES UTF8;'))

# DB DATA EXTRACTION ------------------------------------------------------------------------------

# Set region/age limits
latmin <- 20; latmax <- 70
lonmin <- -15; lonmax <- 100
agelim <- 12000;

# Extract region sites
require(gsubfn) # to include lat/lon/time variables in the query
query <- paste("SELECT site.site_name, site.site_id, site.latitude, site.longitude, site.elevation, count(distinct(entity.entity_id)) as `entity_counts`
from site 
JOIN entity USING (site_id)
JOIN sample USING (entity_id)
JOIN original_chronology USING (sample_id)
JOIN d18O USING (sample_id)",
fn$identity ("WHERE site.latitude > $latmin AND site.latitude < $latmax
AND site.longitude > $lonmin AND site.longitude < $lonmax
AND interp_age < $agelim
GROUP BY site.site_id;"), sep="")

sisal_reg_sites <- dbGetQuery(mydb, query)

## Extract data for each entity ##
query <- paste("
SELECT site.site_id, site.latitude, site.longitude, site.elevation, entity.entity_id, original_chronology.interp_age, sample.mineralogy, sample.arag_corr, d18O.d18O_measurement
FROM site 
JOIN entity USING (site_id)
JOIN sample USING (entity_id)
JOIN original_chronology USING (sample_id)
JOIN d18O USING (sample_id)", 
fn$identity (" WHERE site.latitude > $latmin AND site.latitude < $latmax
AND site.longitude > $lonmin AND site.longitude < $lonmax
AND interp_age < $agelim;"), sep="")

sisal_reg <- dbGetQuery(mydb, query)

# disconnect from db
dbDisconnect(mydb) 
rm(query,mydb)

# number of distinct sites
sit <- length(unique(sisal_reg_sites$site_id))

# number of distinct entitie
ent <- length(unique(sisal_reg$entity_id))

# order entities according to latitude
sisal_reg <- sisal_reg[order(-sisal_reg$latitude, sisal_reg$entity_id, sisal_reg$interp_age),] ## order by latitude.

# PLOT MAP WITH SITES ------------------------------------------------------------------------------

mp <- ggplot() +
  coord_fixed(xlim = c(lonmin-2,lonmax+2), ylim = c(latmin-2,latmax+2), expand = F) +
  theme_bw() +
  xlab('Longitude [deg]') +
  ylab('Latitude [deg]') +
  theme(axis.title.x = element_text(size = rel(0.8))) + #these few lines reduce the size of the labelling
  theme(axis.text.x = element_text(size = rel(0.8))) +
  theme(axis.title.y = element_text(size = rel(0.8))) + 
  theme(axis.text.y = element_text(size = rel(0.8))) +
  theme(legend.position = 'bottom',
        legend.key.width = unit(0.5, 'cm')
  ) + ggtitle(paste('Sites: ',sit,'. Entities: ',ent,sep="")) +
  mapWorld+ # adds coastlines and continent
  mapWokam  # adds wokam (just in one colour, no idea how to add the different colours for the different types of karsts...

p <- mp +  geom_point(data = sisal_reg_sites, aes (x = longitude, y = latitude, color=factor(entity_counts), size=100), #color="black", fill="grey85",
                      alpha = 0.7, size = 3, stroke = 2, show.legend = T, inherit.aes = F) + 
  theme_bw() + # apply bw theme
  scale_shape_manual (values=c(min(sisal_reg_sites[,5]), max(sisal_reg_sites[,5]))) +
  theme(legend.position="bottom", legend.box = "horizontal")+
  labs(color='Number of entities per site')

# cairo_pdf(paste(plotpath,Sys.Date(),'_Map_Sites_Entities.pdf',sep=""), width = 10, height = 6, onefile = T)
# print(p)
ggsave (p, file = paste(plotpath,Sys.Date(),'_Map_Sites_Entities.jpeg',sep=""),width = 10,height = 6)

# TEMPORAL RESOLUTION PLOT------------------------------------------------------------------------------
# plot difference between consecutive samples per entity over Holocene

sisal_reg$diff_age <- rbind(NA, diff(as.matrix(sisal_reg$interp_age))) # age diff between interpolated samples

for (val in 1:(length(sisal_reg[, 1]) - 1)) {
  val1 <- sisal_reg$entity_id[val]
  val2 <- sisal_reg$entity_id[val + 1]
  
  if (val1 != val2) {
    sisal_reg$diff_age[val + 1] <-
      NA # age diff between interpolated samples
  }
}

rm(val,val1, val2)

#get a list of entity names keeping the latitude order!
ent_ls <- unique(sisal_reg[c("latitude", "entity_id")]) %>% 
  mutate (.[order(-latitude),]) %>% dplyr::select (entity_id) %>% as.matrix (.)

# Uncomment one of the two following options:
  # # Option 1: all entities in the same plot
    # start_idx <- 1 #plotting all entities (n=31) at a time, so getting 'starting entities' index in ent_ls for each plot.
    # end_idx <- length(ent_ls)
  # # Option 2: A max of 20 entities per plot (output will create as many panels as necessary to plot them all)
    start_idx <- seq(1,length(ent_ls), 20) #plotting 20 entities at a time, so getting 'starting entities' index in ent_ls for each plot.
    end_idx <- c(start_idx[2:length(start_idx)]-1, length(ent_ls)) ##get the ending index for each plot. the way its formulated here results in the last entity of each plot and the first of the consecutive plot being repetitions.

# remove Na (1st sample of each entity)
out1 <- na.omit(sisal_reg)

for(j in 1:length(start_idx)){ #If "1:1", it creates only 1 plot with all 21 entities. Adjust as necessary for larger n

  subset_ent_ls <-
    ent_ls[start_idx[j]:end_idx[j]] ## subset to # of entities defined above
  
  # get subset of data you want to plot and remove rows with duplicated interp_age once they're rounded to exact years
  
  out2 <-
    out1[out1$entity_id %in% subset_ent_ls, c("entity_id", "diff_age", "interp_age")] %>% 
    mutate (., interp_age = round(.$interp_age)) %>%
    aggregate(diff_age ~ entity_id + interp_age, ., mean, na.rm = TRUE) %>% 
    dplyr::rename (diff_age = V1) 
  
  # # if next line is different than zero it means that there are duplicated rows
  # anyDuplicated(out2[, c("entity_id", "interp_age")])
  
  out2[out2 == "NaN"] <- NA
  
  # reorder entity_id as in subset_ent_ls
  out2 <- left_join(data.frame(entity_id=unique(subset_ent_ls)),out2,by="entity_id") 
    
  # add empty rows for missing exact years
  
  check <-
    reshape(out2,
            idvar = "interp_age",
            timevar = "entity_id",
            direction = "wide") %>% .[order(.$interp_age), ]
  
  comp <- seq(get("interp_age", envir = as.environment(check)) %>% min (.),
              get("interp_age", envir = as.environment(check)) %>% max (.) , by = 1)
  
  which_miss <- comp[!comp %in% get("interp_age", envir = as.environment(check))]
  
  row_samp <- check [1, ] * NA # sample row
  
  check_missing <- do.call("rbind", replicate(length(which_miss), row_samp, simplify = FALSE))
  check_missing[["interp_age"]] <- which_miss
  
  check <- rbind(check, check_missing) %>% .[order(.$interp_age), ]
  check[is.na(check)] <- 0
  
  ## for all the 0 values within an entity (there will be many because all entities are on a single age axis),
  # add the previous age diff value (previous in time) to fill in blanks where there shouldnt be within an entity.
  # this is to obtain a continuous series across the lenght of the record rather than single data points
  
  # 1) index the dframe by 1-nrow(dataframe).
  row.num <- seq(1, nrow(check), 1)
  check <- cbind(row.num, check)
  
  # remove the "age.diff" label.
    for (k in 3:length(check)) {
      ent.name <- colnames(check)[k]
      colnames(check)[k] <- gsub("([a-zA-Z_]|[.])", "", ent.name)
    }
  
  #make a new dataframe, to cbind the updated entities into, alongside age.
  out <- data.frame(check$interp_age) %>% dplyr::rename (interp_age = check.interp_age)

  ## loop through rows, with if else statement that if the row value is 0, assign it the previous rows value.
  
    for (l in 3:length(check)) {
    # from column 3 where the entities begin (excluding interp_age and the index)
    # subset the age and index row with the entity, so that you can identify the index value with the highest age.
    sub <- check[, c(1, 2, l)] 
    # get this for step below
    ent <- colnames(sub)[3] 
    # get index value where entity value is nonzero and age is maximum.
    index.val <- sub[!(sub[ent] == 0),]
    # index.val is now the length of the next loop.
    index.val <- index.val[index.val$interp_age == max(index.val$interp_age), "row.num"] 
    
      for (m in 2:index.val) {
        # starts at two because youre assigning the previous rows value.
        if (sub[m, ent] == 0) {
          sub[m, ent] <- sub[m - 1, ent]
        }
        
      }
    out <- cbind(out, sub[ent]) # this df has all the data that we want to plot
    }
  
  rm(ent)
  
  # plotting. make Interp_age the index - for matrix plotting
  # careful, there shouldn't be any repeatd interp_age! We've removed this problem above when rounding & merging acc to interp_Age
  rownames(out) <- out$interp_age
  out$interp_age <- NULL #can delete est age column and index
  out$row.num <- NULL
  
  ##define new df for matrix plotting that includes spaces between entities (rows of zero separating entities in matrix)
  # uncomment the lines with "#*" at the end to add an empty space between bars so that they don't touch each other
  # if you do this, you'll need to readjust the yticks to on/off so that empty rows are ignored.
  
  space_bt = TRUE # true for spaces between entity' bars (FALSE for no extra spaces)
  
  
  if (space_bt == T) {
    out.f <- out[, 1]
    z <-
      rep(0, nrow(out)) # matrix of zeros with the same horiz size than out. Always leave this one uncommented (for names)
    # add spaces between entities
    for (n in 2:(length(out))) {
      out.f <- cbind(out.f, z)
      out.f <- cbind(out.f, out[, n])
      colnames(out.f)[dim(out.f)[2]] <-
        colnames(out)[n] #to name the column properly.
    }
    out.f <-
      as.data.frame(out.f) #it coerced to a matrix. change back to df
    out.f$blank <-
      z # add the vector of zeroes to the end so theres a space between x axis and first entity.
    
  } else if (space_bt == F)  {
    # without white space in between entities
    z <-
      rep(0, nrow(out)) # matrix of zeros with the same horiz size than out. Always leave this one uncommented (for names)
    out.f <- out
    out.f <-
      as.data.frame(out.f) #it coerced to a matrix. change back to df
  }
  
  colnames(out.f)[1] <- colnames(out)[1] # name of first entity in first column is wrong so fixing it
  rownames(out.f) <- rownames(out) #make the index the ages
  x <- as.matrix(out.f) %>% t(.) # convert to matrix and transpose
  x[x == 0] <- NA
  
  #define output filename
  if (space_bt == T) {
    outputfilename <-
      paste(plotpath,
            Sys.Date(),
            '_Temporal_Resolution_space_',
            j,
            '.pdf',
            sep = "")
    pdf(outputfilename)
  } else if (space_bt == F)  {
    # without white space in between entities
    outputfilename <-
      paste(plotpath,
            Sys.Date(),
            '_Temporal_Resolution_',
            j,
            '.pdf',
            sep = "")
    pdf(outputfilename)
  }
  
  ##adjust margins and move key (NOTE: Key is an extra axis, not a proper legend)
  par(mar = c(4.8,  # pulls down on bottom when you reduce this number
              5, ## increase this number squashes left border to centre
              4.6, ## increasing this number pulls down on top
              3.1))# increase number squashes the right of the plot to the centre
  
  require('plot.matrix')
  plot(
      x,
      border = NA,
      breaks = c(0.001, 1, 5, 10, 20, 40, 50, 100, 200, 500, 1000), ##adjust breaks to individual needs
      col = c(brewer.pal(11, "Paired")),
      na.col = "white",
      digits = 2,
      las = 1,
      cex.axis = 0.7,
      # axis.row = NULL,
      # axis.col = NULL,
      xlab = 'Interp. Age (BP)',
      ylab = "Entity_id (sorted by descending lat)",
      main = "",
      key = list(side = 3, cex.axis = 0.7)
      )

  # set axis (different depending on whether there's space in between entities)
  if (space_bt == T) {
    a <- rev(rownames(x))
    a[which(a == "z")] = NA
    a[which(a == "blank")] = NA
    a <- a[a > 0 & !is.na(a)]
    axis(
      side = 2,
      labels = c(a) ,
      at = seq(2, dim(x)[1] + 1, 2),
      cex.axis = 0.7,
      las = 1
    )
    #axis(side = 1,labels = seq(0, 12000, by = 500),at = seq(0, 12000, by = 500),cex.axis = 0.7,las = 1)
  } else if (space_bt == F) {
    axis(
      side = 2,
      labels = c(rev(rownames(x))),
      at = seq(1, dim(x)[1], 1),
      cex.axis = 0.7,
      las = 1
    )
# axis(side = 1,labels = seq(0, 12000, by = 500),at = seq(0, 12000, by = 500),cex.axis = 0.7,las = 1)
  }
  
  # getOption("max.print" = 50)
  dev.off()

}

graphics.off()

