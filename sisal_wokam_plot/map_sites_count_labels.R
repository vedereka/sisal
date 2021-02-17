rm(list=ls()) 
graphics.off()

library(ggplot2) # fortify and plotting
library (dplyr) # filter
library(ggrepel) # non overlapping labels
# work with spatial data; sp package will load with rgdal.
library(rgdal)
library(rgeos)
# for metadata/attributes- vectors or rasters
library(raster)


# set directories
# set directories
plotpath <- (paste(getwd(),"/sisal_wokam_plot/output/",sep=""))
datapath <- (paste(getwd(),"/sisal_wokam_plot/input/",sep=""))

# load the site data
# info required: lat, lon, site name and entity counts
t<-read.csv(paste(datapath,"data_test.csv",sep = "")) 

# Read in WOKAM shape file for plotting
shapefile_wokam <- readOGR(dsn=paste(datapath,"wokam/wokam_final_WGS84.shp",sep=""))
shapefile_wokam_df <- fortify(shapefile_wokam)

# Read in coastal shape file for plotting
shapefile <- readOGR(dsn=paste(datapath,"ne_110m_land/ne_110m_land.shp", sep=""),layer = 'ne_110m_land') 
shapefile_df <- fortify(shapefile)

# prepare shapefiles for plotting map with sites (change continent colour, transparency, line thickness here)
mapWorld <- geom_polygon(data= shapefile, aes(x = long, y = lat, group = group), fill = 'grey87', colour = 'grey', size = 0.05, alpha=0.7)
mapWokam <- geom_polygon(data= shapefile_wokam_df, aes(x = long, y = lat, group = group), fill = 'grey67', size = 0.05, alpha=0.7)

mp <- ggplot() +
  coord_fixed(xlim = c(-180,180), ylim = c(-60,80), expand = F) + # change these coordinates for plotting regions instead of global
  theme_bw() +
  xlab('Longitude [deg]') +
  ylab('Latitude [deg]') +
  theme(axis.title.x = element_text(size = rel(0.8))) + #these lines just reduce the size of the labelling
  theme(axis.text.x = element_text(size = rel(0.8))) +
  theme(axis.title.y = element_text(size = rel(0.8))) + 
  theme(axis.text.y = element_text(size = rel(0.8))) +
  mapWorld+ # adds coastlines and continent
  mapWokam  # adds wokam (just in one colour, no idea how to add the different colours for the different types of karsts...)

# Add location of sites
# geom_text_repel makes the site labels not to overlap. You can remove that line if you don't want to plot the site names
# dot size is based on the entity counts. If you want to remove that, you need to delete "size = t$counts*0.8" in geom_point and
# adjust the labs (size= "Number of samples"), which is the legend title.

p <- mp +  geom_point(data = t, aes (x = lon, y = lat, size = counts*0.8),
                      alpha = 1, stroke = 1, show.legend = T, inherit.aes = F, color='orangered3',fill='grey60') + 
  geom_text_repel (data = t, aes(x=lon, y=lat, label=name), size=3.5, parse=F, box.padding = 0.45, point.padding = 0.2,
                   min.segment.length	=0.1) +
  theme_bw() + # apply bw them
    labs(#title = "ADD TITLE HERE", # change labels
     size = "Number of samples") +
  theme(legend.position=c(0.095, 0.24), legend.box = "horizontal") +
  theme(legend.title = element_text(colour="black", size=8, face="bold")) +# legend title
  theme(legend.text = element_text(colour="black", size=8)) + # legend labels
  theme(legend.background = element_rect(fill="white",
                                         size=0.4, linetype="solid", 
                                         colour ="black"))
  
cairo_pdf(paste(plotpath,'map_sites_count_labels_plot.pdf',sep=""), width = 11.69, height = 8.27, onefile = T)
  
print(p)
graphics.off()
