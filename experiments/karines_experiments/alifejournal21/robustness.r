library(ggplot2)
library(sqldf)
library(plyr)
library(dplyr)
library(trend)
library(purrr)
library(ggsignif)
library(stringr)
library(reshape)
library(viridis)
library(ggpubr)

####  this example of parameterization compares multiple types of experiments using one particular season ###

#### CHANGE THE PARAMETERS HERE ####

base_directory2 <-paste('/storage/karine/alifej2021', sep='')

analysis = 'analysis/measures'
output_directory = paste(base_directory2,'/',analysis ,sep='')

experiments_type = c("scaffeq", "staticplane", "scaffeqinv", "scaffinc", "scaffincinv", "statictilted")

runs = list(
            c(1:20),
            c(1:20),
            c(1:20),
            c(1:20),
            c(1:20),
            c(1:20))

# methods are product of experiments_type VS environments and should be coupled with colors.
# make sure to define methods_labels in alphabetic order, and experiments_type accordingly
methods_labels =  c('5-Equal','1-Flat','2-Inv Equal','6-Incr','3-Inv Incr', '4-Tilted' )

experiments_type_colors = c('#FF00FF',
                            '#0000CD') 

robutness_method_all = NULL
for (exp in 1:length(experiments_type))
{
  for(run in runs[[exp]])
  {
   
     filenm= paste(base_directory2,paste(experiments_type[exp], run, sep='_'),"data_fullevolution/robustness.txt", sep='/')
     if (file.exists(filenm)){
        robutness_method = read.table(filenm, header = FALSE)
     }else { robutness_method=NULL}
     
      robutness_method$experiments_type = methods_labels[exp]
      robutness_method$V4=robutness_method$V4*100
      
      print(paste(experiments_type[exp], run))
      print(nrow(robutness_method))
      
      if ( is.null(robutness_method_all)){
        robutness_method_all = robutness_method
      }else{
        robutness_method_all = rbind(robutness_method_all, robutness_method)
      }
    
  }
}

#sqldf("select V1,count(*) from robutness_method_all group by 1 order by 1")

write.csv(robutness_method_all,paste(output_directory,"/robustness_cons.csv",sep=''), row.names = FALSE)

robutness_method_all$V2 <- gsub('plane', 'Flat', robutness_method_all$V2)
robutness_method_all$V2 <- gsub('tilted5', 'Tilted', robutness_method_all$V2)
robutness_method_all_avg = sqldf("select V1, v2 as env, experiments_type, avg(V4) as speed from robutness_method_all group by 1,2 ")

test_plane_inv = wilcox.test(robutness_method_all_avg[robutness_method_all_avg$env == 'Flat' & robutness_method_all_avg$experiments_type == "2-Inv Equal", "speed"], 
                             robutness_method_all_avg[robutness_method_all_avg$env == 'Flat' & robutness_method_all_avg$experiments_type == "3-Inv Incr", "speed"])$p.value
test_tilted_inv = wilcox.test(robutness_method_all_avg[robutness_method_all_avg$env == 'Tilted' & robutness_method_all_avg$experiments_type == "2-Inv Equal", "speed"], 
                              robutness_method_all_avg[robutness_method_all_avg$env == 'Tilted' & robutness_method_all_avg$experiments_type == "3-Inv Incr", "speed"])$p.value
test_plane = wilcox.test(robutness_method_all_avg[robutness_method_all_avg$env == 'Flat' & robutness_method_all_avg$experiments_type == "5-Equal", "speed"], 
                          robutness_method_all_avg[robutness_method_all_avg$env == 'Flat' & robutness_method_all_avg$experiments_type == "6-Incr", "speed"])$p.value
test_tilted = wilcox.test(robutness_method_all_avg[robutness_method_all_avg$env == 'Tilted' & robutness_method_all_avg$experiments_type == "5-Equal", "speed"], 
                          robutness_method_all_avg[robutness_method_all_avg$env == 'Tilted' & robutness_method_all_avg$experiments_type == "6-Incr", "speed"])$p.value


  g1 <- ggplot(data=robutness_method_all_avg, aes(x= experiments_type , y=speed, fill= env )) +
geom_boxplot(position = position_dodge(width=0.9), outlier.size = 0.5) +
labs( x="Environmental scenario", y="Speed (cm/s)")+
guides(fill=guide_legend("Environment of test"))+
theme(legend.position="bottom" , text = element_text(size=25), legend.key.size = unit(3,"line"),
axis.text.x = element_text(angle = 20, hjust = 1))+
stat_summary(fun.y = mean, geom="point" , size=3, position = position_dodge(width = 0.9)) +
stat_compare_means(method = "wilcox.test", size=9, label = "p.signif", label.y = 5.5) +
geom_signif(annotation='ns', y_position=3.6, xmin=2.29, xmax=3.31, tip_length = c(0.05,0.05), textsize=7)+
geom_signif(annotation='ns', y_position=4.6, xmin=1.75, xmax=2.75, tip_length = c(0.05, 0.05), textsize=7)+
geom_signif(annotation='ns', y_position=3.7, xmin=4.8, xmax=5.8, tip_length = c(0.05,0.05), textsize=7)+
geom_signif(annotation='**', y_position=4.7, xmin=5.3, xmax=6.3, tip_length = c(0.05, 0.05), textsize=7)

#'           p = ',formatC(test_plane, digits=2))
ggsave(paste(output_directory,"/robustness.png",sep = ""), g1, device = "png", height=8, width = 10.5)


