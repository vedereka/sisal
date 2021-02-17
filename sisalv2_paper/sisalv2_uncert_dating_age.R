# Script to create Figure 6 of Comas-Bru et al., 2020 (ESSD)
# Created by Laia Comas-Bru in January 2020
# Source: SISALv2 database (https://doi.org/10.17864/1947.256)

rm(list=ls()) 
graphics.off()

library (RColorBrewer)
library(ggplot2)
library(RMariaDB) 
library(tidyverse)


con = dbConnect(MariaDB(), user='root', 
                password='password', 
                dbname='sisalv2', 
                host='localhost')


query <- paste("SELECT entity.entity_id,
avg(original_chronology.interp_age_uncert_pos) as 'orig_pos', avg(original_chronology.interp_age_uncert_neg) as 'orig_neg'
FROM entity 
LEFT JOIN sample USING (entity_id)
LEFT JOIN original_chronology USING(sample_id)
WHERE interp_age IS NOT NULL
GROUP BY entity_id;")

data_orig_chrono <- dbGetQuery(con, query)


query <- paste("SELECT entity.entity_id,
avg(sisal_chronology.lin_interp_age_uncert_pos) as 'lin_interp_pos',
avg(sisal_chronology.lin_reg_age_uncert_pos) as 'lin_reg_pos',
avg(sisal_chronology.Bchron_age_uncert_pos) as 'Bchron_pos',
avg(sisal_chronology.Bacon_age_uncert_pos) as 'Bacon_pos',
avg(sisal_chronology.OxCal_age_uncert_pos) as 'OxCal_pos',
avg(sisal_chronology.copRa_age_uncert_pos) as 'copRa_pos',
avg(sisal_chronology.StalAge_age_uncert_pos) as 'StalAge_pos',
avg(sisal_chronology.lin_interp_age_uncert_neg) as 'lin_interp_neg',
avg(sisal_chronology.lin_reg_age_uncert_neg) as 'lin_reg_neg',
avg(sisal_chronology.Bchron_age_uncert_neg) as 'Bchron_neg',
avg(sisal_chronology.Bacon_age_uncert_neg) as 'Bacon_neg',
avg(sisal_chronology.OxCal_age_uncert_neg) as 'OxCal_neg',
avg(sisal_chronology.copRa_age_uncert_neg) as 'copRa_neg',
avg(sisal_chronology.StalAge_age_uncert_neg) as 'StalAge_neg'
FROM entity
LEFT JOIN sample USING(entity_id)
LEFT JOIN sisal_chronology USING(sample_id)
GROUP BY entity_id;")

data_sisal_chrono <- dbGetQuery(con, query)

query <- paste("SELECT entity.entity_id,
avg(dating.corr_age_uncert_pos) as 'corr_pos',
avg(dating.corr_age_uncert_neg) as 'corr_neg'
FROM entity
LEFT JOIN dating USING(entity_id)
GROUP BY entity_id;")

data_dating <- dbGetQuery(con, query)

dbDisconnect(con)

# overlapping entities
data_sisal_chrono <- data_sisal_chrono %>% filter(entity_id %in% data_orig_chrono$entity_id)
data_dating <- data_dating %>% filter(entity_id %in% data_orig_chrono$entity_id)

# calculate mean uncertainties
data_sisal_chrono$mean_sisal <- rowMeans(data_sisal_chrono[,c(seq(from=2, to=15, by=1))], na.rm=TRUE)
data_orig_chrono$mean_orig <- rowMeans(data_orig_chrono[,c(2,3)], na.rm=TRUE)
data_dating$mean_date <- rowMeans(data_dating[,c(2,3)], na.rm=TRUE)

df1 <- data_sisal_chrono[, c(1,16)]
df2 <- data_orig_chrono[, c(1,4)]
df3 <- data_dating[, c(1,4)]

# merge sisal/orig data to plot 
total <- merge(df1,df2,by="entity_id")
total <- merge(total,df3,by="entity_id")

#scatterplot
cairo_pdf(paste(getwd(), '/sisalv2_paper/output/scatterplot_all_AM.pdf', sep=""),  width = 11.69, height = 8.27, onefile = T)

p <- ggplot(total, aes(x = mean_sisal, y=mean_date)) + 
  geom_point()+
  theme(axis.line = element_blank(), 
        plot.title = element_text(hjust=0.5),
        axis.text.x = element_text(size = rel(1)),
        axis.title.x = element_text(size = rel(1.3)),
        axis.text.y = element_text(size = rel(1)),
        axis.title.y = element_text(size = rel(1.3))) + 
          labs(x="mean sisal chrono uncertainties (log scale)", 
               y="mean dating uncertainties (log scale)"#, 
               #title="Pie Chart of class", 
               #caption="Source: sisalv2."
               )+
          scale_x_log10() +
          scale_y_log10() +
          geom_smooth(method='lm', formula= y~x)

print(p)

# by AM technique
total2 <- merge(data_sisal_chrono,data_dating,by="entity_id")
#remove mean_sisal
total2 <- total2[, -c(16:18)]

#merge pos and neg uncerttainties for each AM
aa <- data.frame(entity_id=total2[,1], lin_interp=rowMeans(total2[,2:9],na.rm=T),lin_reg=rowMeans(total2[,3:10],na.rm=T)
                 ,Bchron=rowMeans(total2[,4:11],na.rm=T),Bacon=rowMeans(total2[,5:12],na.rm=T),
                 OxCal=rowMeans(total2[,6:13],na.rm=T),copRa=rowMeans(total2[,7:14],na.rm=T),
                 StalAge=rowMeans(total2[,8:15],na.rm=T),mean_date=total2$mean_date)

df_melt <- reshape2::melt(aa[,2:9], id.var = 'mean_date')
df_melt <- df_melt [complete.cases(df_melt), ]

cairo_pdf(paste(getwd(), '/sisalv2_paper/output/scatterplot_by_AM.pdf', sep=""),  width = 11.69, height = 8.27, onefile = T)

p <- ggplot(df_melt, aes(x = mean_date, y=value, fill=factor(variable))) + 
  geom_smooth(method='lm', show.legend = NA,inherit.aes = TRUE,formula = y ~x, se = TRUE,
              weight=0.5, color = "black", size = 0.5)+
  geom_point(colour="black",pch=21, size=2, alpha=0.8)+
  theme(axis.line = element_line(colour = "black"),
#        plot.title = element_text(hjust=0.5),
        axis.text.x = element_text(size = rel(1.05)),
        axis.title.x = element_text(size = rel(1.3)),
        axis.text.y = element_text(size = rel(1.05)),
        axis.title.y = element_text(size = rel(1.3)),
        legend.position=c(0.85, 0.23),
        legend.box = "horizontal",
        legend.title = element_text(colour="black", size=11, face="bold"),
        legend.text = element_text(colour="black", size=10),
        legend.background = element_rect(fill="white",size=0.4, linetype="solid", colour = NA),
        legend.key = element_rect(fill = NA),
        panel.background = element_rect(colour = "black", size=0.5, fill=NA),#element_blank(),
        panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank())+
        #panel.border = element_rect(colour = "black", fill=NA, size=1))+
  labs(x="mean dating uncertainties [yrs]", 
       y="mean uncertainties of sisal_chronology [yrs]",
      fill = "Age-depth model")+ 
       #title="Pie Chart of class", 
  scale_x_log10() +
  scale_y_log10()+
  scale_fill_manual(values=rev(brewer.pal(7,"Paired")), 
                      name="Age-depth model type",
                      breaks=c("lin_interp", "lin_reg", "Bchron", "Bacon", "OxCal", "copRa", "StalAge"),
                      labels = c("Linear Interpolation", "Linear Regression", "Bchron", "Bacon", "OxCal", "copRa", "StalAge"))
mp<- p + geom_abline(intercept = 0,slope=1)

print(mp)

r <- ggplot(df_melt, aes(x = value)) +
  geom_histogram(binwidth = 0.05) +
  scale_x_log10() 
  
print(r)
graphics.off()
