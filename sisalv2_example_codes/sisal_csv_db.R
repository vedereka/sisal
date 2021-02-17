# ************************************************************************ #
#                                                                          #
#              EXAMPLE CODES FOR Querying the CSV files                    #
#               without having to install MySQL                            #    
#                                                                          #
# This file is provided as part of the documentation for SISAL version 2  #
#                                                                          #
# Prerequisite packages:                                                   #
#     - sqldf                                                              #
#     - ggplot2                                                            #
#     - ggmap                                                              #
#     - maps                                                               #
#     - xlsx                                                               #
#     - plyr                                                               #

# Install library if not installed -------------------------------------####
if (!('sqldf' %in% installed.packages())){
  install.packages('sqldf')
}

if (!('ggplot2' %in% installed.packages())){
  install.packages('ggplot2')
}

if (!('ggmap' %in% installed.packages())){
  install.packages('ggmap')
}

if (!('maps' %in% installed.packages())){
  install.packages('maps')
}

if (!('plyr' %in% installed.packages())){
  install.packages('plyr')
}

if (!('xlsx' %in% installed.packages())){
  install.packages('xlsx')
}

# IMPORT LIBRARY -------------------------------------------------------####
library(sqldf)
# Make sure the sqldf driver is SQLite
# This is essential when there are other sql packages loaded such as RMySQL
options(sqldf.driver = "SQLite") 
# Other packages here are just for plotting
library(ggplot2)
library(ggmap)
library(maps)
# packages for outputing xlsx file
library(xlsx)
# Packages for making figures analogous to figures 1 and 2 in the database paper
library(plyr)

# 1. Read in the CSV files ---------------------------------------------####
# This assumes that all the CSV files are in the working directory
site <- read.csv('site.csv', fileEncoding = 'UTF-8')
notes <- read.csv('notes.csv', fileEncoding = 'UTF-8')
composite_link_entity <- read.csv('composite_link_entity.csv', fileEncoding = 'UTF-8')
entity <- read.csv('entity.csv', fileEncoding = 'UTF-8')
dating <- read.csv('dating.csv', fileEncoding = 'UTF-8')
entity_link_reference <- read.csv('entity_link_reference.csv', fileEncoding = 'UTF-8')
reference <- read.csv('reference.csv', fileEncoding = 'UTF-8')
dating_lamina <- read.csv('dating_lamina.csv', fileEncoding = 'UTF-8')
sample <- read.csv('sample.csv', fileEncoding = 'UTF-8')
gap <- read.csv('gap.csv', fileEncoding = 'UTF-8')
hiatus <- read.csv('hiatus.csv', fileEncoding = 'UTF-8')
original_chronology <- read.csv('original_chronology.csv', fileEncoding = 'UTF-8')
d13C <- read.csv('d13C.csv', fileEncoding = 'UTF-8')
d18O <- read.csv('d18O.csv', fileEncoding = 'UTF-8')
sisal_chronology <- read.csv('sisal_chronology.csv', fileEncoding = 'UTF-8')

# 2. Querying the database ---------------------------------------------####

# Query the database into a table --------------------------------------####
# 2.a. Extract the information needed for age modelling ----------------####
# This is only done entity_id = 1 as an example
# dating information table (with hiatuses)
dating_tb <- sqldf('SELECT * FROM dating WHERE entity_id = 1;') 
# sample depth/isotope table (with hiatuses)
sample_tb <- sqldf('SELECT * FROM sample LEFT JOIN hiatus USING (sample_id) LEFT JOIN d13C USING (sample_id) LEFT JOIN d18O USING (sample_id) WHERE entity_id = 1')
# write to excel file
write.xlsx(dating_tb, 'Age_model_entity_1.xlsx', sheetName = "dating information table", 
           col.names = TRUE, row.names = F, append = F)
write.xlsx(sample_tb, 'Age_model_entity_1.xlsx', sheetName = "sample table", 
           col.names = TRUE, row.names = F, append = T)
# 2.b. Extract citations and DOI for each entity in the database -------####
# Due to being unable to set maximum group_concat length to more characters, 
# the query will return citations list but truncated 
# To retain as much information as possible, you can just group_concat the ref_id
# which would mean that the information will be retained and not truncated
# There are also issues with this maximum number of characters in SQLite queries
# and also when merging dataframes with columns with large number of characters
# This is a limitation, but unless you look at notes or citations, this should not be a problem
# Alternatively, you can query to find the id and look this up in the csv tables themselves
#
# Please note that the queries are not exactly identical here
tot_ref <- sqldf('SELECT entity.entity_id, site.site_name as "Site name", 
                      site.elevation as "Elevation", 
                      site.latitude as "Latitude", 
                      site.longitude as "Longitude", 
                      entity.entity_name as "Entity name", 
                      group_concat(reference.ref_id, " ; ") as "ref_id_lists"
                      from site JOIN entity USING(site_id) 
                      JOIN entity_link_reference USING(entity_id) JOIN reference USING(ref_id) GROUP BY entity_id;')

# 2.c. Extract sites with entity counts --------------------------------####
tot_site <- sqldf("SELECT site.*, count(*) as entity_count FROM site LEFT JOIN entity USING (site_id) WHERE entity_status = 'current' GROUP BY (site_id);")

# 2.d. Extract entities from an area and report their age range --------####
# 35 < latitude < 90, and -20 < longitude < 40
tot_entity <- sqldf("SELECT site.site_name, latitude, longitude, entity.*, MAX(interp_age) as max_interp_age, MIN(interp_age) as min_interp_age FROM site LEFT JOIN entity USING (site_id) LEFT JOIN sample USING (entity_id) LEFT JOIN original_chronology USING (sample_id) WHERE latitude > 35 AND latitude < 90 AND longitude > -20 and longitude < 40 GROUP BY entity_id, site_name, latitude, longitude;")

# 2.e. Extract entities from a certain age range -----------------------####
# Extract entities with data from the Holocene period (< 12000 BP(1950))
Holocene_entity <- sqldf("SELECT site.site_name, latitude, longitude, entity.* FROM site LEFT JOIN entity USING (site_id) LEFT JOIN sample USING (entity_id) LEFT JOIN original_chronology USING (sample_id) WHERE interp_age < 12000 GROUP BY entity_id, site_name, latitude, longitude;")

# make map with entity counts ------------------------------------------#### 
# Note that the queries also count the number of entities per site
# There is only one 'current' entity respective the the entity 
tot_site <- sqldf("SELECT site.*, count(*) as entity_count FROM site LEFT JOIN entity USING (site_id) WHERE entity_status = 'current' GROUP BY (site_id);")

# convert total number of entity per site to factor
tot_site$entity_count <- factor(tot_site$entity_count)

# PLOT MAP #
# This is just an example of a quick plot #
mapWorld <- borders("world", colour="lightgrey", fill="lightgrey", xlim = c(-180, 180), ylim = c(-90, 90)) # create a layer of borders
mp <- ggplot() + mapWorld 
mp <- mp + geom_point(data = tot_site, aes(x=longitude, y=latitude, 
                                           size=entity_count), alpha = 0.8) +
  coord_fixed(xlim = c(-180, 180), ylim = c(-60, 90), expand = T)

# output site map to pdf -----------------------------------------------####
pdf(paste('output.pdf', sep = ''), 11.69, 8.27)
print(mp)
dev.off()

# example of how Figure 1 in Atsawawaranunt et al., 2018 was made -------------------------------------####
db_version <- 'version 2'
tot_site <- sqldf("SELECT site.*, count(*) as entity_count FROM site LEFT JOIN entity USING (site_id) WHERE entity_status = 'current' GROUP BY (site_id);")
tot_d18Osite <- sqldf("SELECT site_id, site_name, latitude, longitude, elevation, entity_id, entity_name FROM site LEFT JOIN entity USING (site_id) JOIN sample USING(entity_id) JOIN d18O USING(sample_id) GROUP BY (entity_id) HAVING COUNT(*) > 0;")
tot_d13Csite <- sqldf("SELECT site_id, site_name, latitude, longitude, elevation, entity_id, entity_name FROM site LEFT JOIN entity USING (site_id) JOIN sample USING(entity_id) JOIN d13C USING(sample_id) GROUP BY (entity_id) HAVING COUNT(*) > 0;")
tot_d18Osite$d18O <- 'yes'
tot_d13Csite$d13C <- 'yes'
tot_site_entity <- join(tot_d18Osite, tot_d13Csite, type = 'full')
# This query generally works but is not entirely based on what is available in the database
#
# There might be cases where the author may put down that d13C is available in the entity table
# but this does not necessarily mean that the author has made d13C available in the sisal database
#
# There are also cases where the author knows that d13C data is available, but only the composite 
# were made available and therefore d13C would be noted down as 'yes' for the individual entity
# but only the composite d13C is made available.
#
# tot_site_entity <- sqldf("SELECT * FROM site JOIN entity USING (site_id);")

subsetfunc <- function(tot_site_entity){
  wah = 0
  if ('yes' %in% tot_site_entity$d18O){
    wah = wah + 1
  }
  if ('yes' %in% tot_site_entity$d13C){
    wah = wah + 2
  }
  if (wah == 0){
    wah = 'None'
  } else if (wah == 1){
    wah = 'd18O only'
  } else if (wah == 2){
    wah = 'd13C only'
  } else if (wah == 3){
    wah = 'd18O and d13C'
  }
  return(wah)
}

wahwah <- ddply(tot_site_entity, .(site_id), subsetfunc)
colnames(wahwah) <- c('site_id', 'isotopic_data')

tot_site <- merge(tot_site, wahwah, by = 'site_id')


tot_site$entity_count <- factor(tot_site$entity_count)


# PLOT FIGURE 1 #
min_lat = -90
max_lat = 90
min_lon = -180
max_lon = 180
d18Oandd13C <- expression(paste(delta^{18}, "O and ", delta^{13}, "C "))
d18Oonly <- expression(paste(delta^{18}, "O", " only"))
d13Conly <- expression(paste(delta^{13}, "C", " only"))
# Actual Figure 1 was plotted with a shape file but this is very similar
mapWorld <- borders("world", colour="lightgrey", fill="lightgrey", xlim = c(min_lon, max_lon), ylim = c(min_lat, max_lat)) # create a layer of borders
mp <- ggplot() + mapWorld 
#Now Layer the points on top
mp <- mp + geom_point(data = tot_site, aes(x=longitude, y=latitude, 
                                           shape = isotopic_data), 
                      alpha = 0.8) +
  scale_y_continuous(breaks = seq(-60, 90, by = 30), 
                     labels = paste(seq(-60, 90, by = 30), '°', sep = ''),
                     expand = c(0, 0)) +
  scale_x_continuous(breaks = seq(-180, 180, by = 30), 
                     labels = paste(seq(-180, 180, by = 30), '°', sep = ''),
                     expand = c(0, 0)) +
  coord_fixed(xlim = c(min_lon, max_lon), ylim = c(-60, max_lat), expand = T) +
  scale_shape_manual(name = 'Isotopic data available',
                     values = c(16,
                                4),
                     labels = c(d18Oandd13C, d18Oonly)) +
  ggtitle(paste('  ', db_version, sep = '')) +
  theme_bw() +
  theme(legend.justification = c(0.015, 0.04), 
        legend.position = c(0.015,0.04), 
        legend.text=element_text(size=16),
        legend.title=element_text(size=16, face = 'bold'),
        legend.text.align = 0,
        legend.background = element_rect(color = "black", size = 0.01, linetype = "solid"),
        axis.text=element_text(colour = 'black', size=16),
        axis.line = element_line(colour = 'black'),
        axis.title = element_blank(),
        axis.text.x = element_text(margin = margin(3, unit = "pt")),
        plot.title = element_text(margin = margin(b = -25, unit = "pt"), size = 20),
        plot.margin = unit(c(0,20,0,5), 'pt'),
        panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank())
mp
pdf(paste('Figure1.pdf', sep = ''), 11.69, 8.27)
print(mp)
dev.off()

# example of how Figure 2 in Atsawawaranunt et al., 2018 was made -------------------------------------####
# Define some functions
#**************************************************************************#
# Function name: subset_tbbinsize
# Function: put entity counts into binsizes and return a dataframe
# Input: 1. input_tb: Dataframe containing the following columns:
#                       a. Age_corrected2reference (numeric)
#                       b. entity_id 
#        2. min_age: minimum age (numeric)
#        3. max_age: maximum age (numeric)
#        4. bin_size: bin size (numeric)
# Return: A dataframe with number of samples within each bin
#
#**************************************************************************#
subset_tbbinsize <- function(input_tb, min_age, max_age, bin_size){
  maxval_ls <- list()
  entityidvals_ls <- list()
  minval_ls <- list()
  midval_ls <- list()
  for (j in seq(min_age, max_age, bin_size)[-1]){ # remove one value out
    maxval = j
    minval = j - bin_size
    midval = j - bin_size/2
    input_tb_subset <- subset(input_tb, 
                              (Age_corrected2reference >= minval & 
                                 Age_corrected2reference < maxval))
    entityidvals <- unique(input_tb_subset$entity_id)
    n <- length(entityidvals)
    maxvals <- rep(maxval, n)
    minvals <- rep(minval, n)
    midvals <- rep(midval, n)
    maxval_ls <- append(maxval_ls, maxvals)
    minval_ls <- append(minval_ls, minvals)
    midval_ls <- append(midval_ls, midvals)
    entityidvals_ls <- append(entityidvals_ls, entityidvals)
  }
  
  dt_bins <- data.frame(min_age = unlist(minval_ls),
                        max_age = unlist(maxval_ls),
                        mid_age = unlist(midval_ls),
                        entity_id = unlist(entityidvals_ls))
  return(dt_bins)
}

#**************************************************************************#
# Multiple plot function
#
# This function is copied from the following link:
# http://www.cookbook-r.com/Graphs/Multiple_graphs_on_one_page_(ggplot2)/
#
# ggplot objects can be passed in ..., or to plotlist (as a list of ggplot objects)
# - cols:   Number of columns in layout
# - layout: A matrix specifying the layout. If present, 'cols' is ignored.
#
# If the layout is something like matrix(c(1,2,3,3), nrow=2, byrow=TRUE),
# then plot 1 will go in the upper left, 2 will go in the upper right, and
# 3 will go all the way across the bottom.
#
#**************************************************************************#
multiplot <- function(..., plotlist=NULL, file, cols=1, layout=NULL) {
  library(grid)
  
  # Make a list from the ... arguments and plotlist
  plots <- c(list(...), plotlist)
  
  numPlots = length(plots)
  
  # If layout is NULL, then use 'cols' to determine layout
  if (is.null(layout)) {
    # Make the panel
    # ncol: Number of columns of plots
    # nrow: Number of rows needed, calculated from # of cols
    layout <- matrix(seq(1, cols * ceiling(numPlots/cols)),
                     ncol = cols, nrow = ceiling(numPlots/cols))
  }
  
  if (numPlots==1) {
    print(plots[[1]])
    
  } else {
    # Set up the page
    grid.newpage()
    pushViewport(viewport(layout = grid.layout(nrow(layout), ncol(layout))))
    
    # Make each plot, in the correct location
    for (i in 1:numPlots) {
      # Get the i,j matrix positions of the regions that contain this subplot
      matchidx <- as.data.frame(which(layout == i, arr.ind = TRUE))
      
      print(plots[[i]], vp = viewport(layout.pos.row = matchidx$row,
                                      layout.pos.col = matchidx$col))
    }
  }
}

# Query the database
# Note that I only use JOIN statement here instead of LEFT JOIN on purpose to neglect samples which are hiatuses
full_sample_tb <- sqldf("SELECT site.*, entity.entity_name, sample.*, original_chronology.* FROM site JOIN entity USING(site_id) JOIN sample USING(entity_id) JOIN original_chronology USING(sample_id);")
full_sample_tb$Age_corrected2reference <- full_sample_tb$interp_age

# Make histogram for the past approximately 2000 years
min_age = -200 # min_age in years BP(1950)
max_age = 2000 # man_age in years BP(1950)
bin_size = 10 # bin size in years

# subset and count the number of samples in each bin
dt_bins <- subset_tbbinsize(full_sample_tb, min_age, max_age, bin_size)

# plot using ggplot
pa <- ggplot(dt_bins, aes(x = mid_age)) +
  geom_histogram(binwidth = bin_size, boundary = min_age, fill = 'grey') +
  ylab('Number of entities') + xlab('yrs BP (1950)') +
  theme_bw() +
  theme(legend.position = 'none',
        panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank(),
        plot.margin = unit(c(10,15,0,5), 'pt'),
        axis.text=element_text(colour = 'black', size=13),
        axis.title = element_text(colour = 'black', size=13, face = 'bold'),
        axis.line = element_line(colour = 'black')) +
  scale_x_reverse(breaks = seq(0, (max(dt_bins$max_age, na.rm = T) - 1), by = 200), expand = c(0, 0)) +
  scale_y_continuous(breaks = seq(0, length(dt_bins$entity_id), by = 10), expand = c(0, 0)) +
  expand_limits(y = 70) +
  geom_text(x = -(0.98*(max_age - min(dt_bins$min_age, na.rm = T))) - min(dt_bins$min_age, na.rm = T), y = (0.05*70), hjust = 0, label = paste("(a) Past 2kyrs,  bin size = ", bin_size, 'yrs', sep = ''), size = 14*(5/14))

# Make histogram for the past approximately 22000 years

min_age = -500 # min_age in years BP(1950)
max_age = 22000 # man_age in years BP(1950)
bin_size = 500 # bin size in years

# subset and count the number of samples in each bin
dt_bins <- subset_tbbinsize(full_sample_tb, min_age, max_age, bin_size)
# convert all the ages to ka instead of years
dt_bins$mid_age <- dt_bins$mid_age/1000
dt_bins$min_age <- dt_bins$min_age/1000
dt_bins$max_age <- dt_bins$max_age/1000
min_age <- min_age/1000
max_age <- max_age/1000
bin_size <- bin_size/1000

# plot using ggplot
pb <- ggplot(dt_bins, aes(x = mid_age)) +
  geom_histogram(binwidth = bin_size, boundary = min_age, fill = 'grey') +
  ylab('Number of entities') + xlab('kyrs BP (1950)') +
  theme_bw() +
  theme(legend.position = 'none',
        panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank(),
        plot.margin = unit(c(10,15,0,5), 'pt'),
        axis.title.y = element_text(margin = margin(t = 0, r = -1, b = 0, l = 0)),
        axis.text=element_text(colour = 'black', size=13),
        axis.title = element_text(colour = 'black', size=13, face = 'bold'),
        axis.line = element_line(colour = 'black')) +
  scale_x_reverse(breaks = seq(0, (max(dt_bins$max_age, na.rm = T) - 1), by = 2), expand = c(0, 0)) +
  scale_y_continuous(breaks = seq(0, length(dt_bins$entity_id), by = 10), expand = c(0, 0)) +
  expand_limits(y = 120) +
  geom_text(x = -(0.98*(max_age - min(dt_bins$min_age, na.rm = T))) - min(dt_bins$min_age, na.rm = T), y = (0.05*120), hjust = 0, label = paste("(b) Past 22kyrs,  bin size = ", bin_size, 'kyrs', sep = ''), size = 14*(5/14))

# Make histogram for the Last Interglacial (115000 - 130000 years BP(1950))

min_age = 115000 # min_age in years BP(1950)
max_age = 130000 # man_age in years BP(1950)
bin_size = 1000 # bin size in years

# subset and count the number of samples in each bin
dt_bins <- subset_tbbinsize(full_sample_tb, min_age, max_age, bin_size)

# convert all ages to ka instead of years
dt_bins$mid_age <- dt_bins$mid_age/1000
dt_bins$min_age <- dt_bins$min_age/1000
dt_bins$max_age <- dt_bins$max_age/1000
min_age <- min_age/1000
max_age <- max_age/1000
bin_size <- bin_size/1000
bins = (max_age - min_age)/bin_size

# plot using ggplot
pc <- ggplot(dt_bins, aes(x = mid_age)) +
  geom_histogram(binwidth = bin_size, boundary = (min_age), fill = 'grey') +
  ylab('Number of entities') + xlab('kyrs BP (1950)') +
  theme_bw() +
  theme(legend.position = 'none',
        panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank(),
        plot.margin = unit(c(10,15,0,5), 'pt'),
        axis.text=element_text(colour = 'black', size=13),
        axis.title = element_text(colour = 'black', size=13, face = 'bold'),
        axis.line = element_line(colour = 'black')) +
  scale_x_reverse(breaks = seq(min_age, (max(dt_bins$max_age, na.rm = T)) -1, by = 1), expand = c(0, 0)) +
  scale_y_continuous(breaks = seq(0, length(dt_bins$entity_id), by = 4), expand = c(0, 0)) +
  expand_limits(y = 32) +
  geom_text(x = -(0.98*(max_age - min_age)) - min_age, y = (0.05*32), hjust = 0, label = paste("(c) Last Interglacial,  bin size = ", bin_size, 'kyrs', sep = ''), size = 14*(5/14))

pdf('Figure2.pdf', 8.27, 11.69)
multiplot(pa,pb,pc)
dev.off()

