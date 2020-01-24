  
  
  library(ggplot2)
  library(sqldf)
  library(plyr)
  library(dplyr)
  library(trend)
  library(purrr)
  
  base_directory <- paste('data', sep='') #paste('projects/revolve/experiments/karines_experiments/data', sep='')
  
 analysis = 'analysis2_plane_tilted'
  
  output_directory = paste(base_directory,'/',analysis ,sep='')
  
  #### CHANGE THE PARAMETERS HERE ####

  
  experiments_type_colors = c('#FF8000', '#009900')  # DARK: green, orange  
  
  experiments_type = c( 'plane', 'tilted5')
  
  experiments_type_label = c( '2-Plane', '1-Tilted')

  
  runs = c(1:60) 
  gens = 100
  pop = 100
  
  #### CHANGE THE PARAMETERS HERE ####
  
  sig = 0.05
  line_size = 30
  show_markers = TRUE
  show_legends = FALSE 
  
  
  measures_names = c('length_of_limbs','proportion', 'absolute_size','head_balance','joints', 'limbs')
  
  measures_labels = c('Rel. Length of Limbs','Proportion', 'Size','Balance','Rel. Number of Joints', 'Rel. Number of Limbs')
  
  measures_snapshots_all = NULL
  
  for (exp in 1:length(experiments_type))
  {
    for(run in runs)
    {
      input_directory  <-  paste(base_directory, '/', experiments_type[exp], '_', run, sep='')
      measures   = read.table(paste(input_directory,"/all_measures.tsv", sep=''), header = TRUE)
      for( m in 1:length(measures_names))
      { 
        measures[measures_names[m]] = as.numeric(as.character(measures[[measures_names[m]]]))
      }
      
      snapshots   = read.table(paste(input_directory,"/snapshots_ids.tsv", sep=''), header = TRUE)
      measures_snapshots = sqldf('select * from snapshots inner join measures using(robot_id) order by generation')
      
      measures_snapshots$run = run
      measures_snapshots$run = as.factor(measures_snapshots$run)
      measures_snapshots$method = experiments_type_label[exp]
      
      if ( is.null(measures_snapshots_all)){
        measures_snapshots_all = measures_snapshots
      }else{
        measures_snapshots_all = rbind(measures_snapshots_all, measures_snapshots)
      }
    }
  }
  
  measures_snapshots_all_final = sqldf("select * from measures_snapshots_all where generation=99")
  
   
    for (i in 1:length(measures_names)) 
    {
        
      for (j in 1:length(measures_names)) 
      {
   
         if(i != j)
           {
      
            graph <- ggplot(measures_snapshots_all_final, aes_string(x=measures_names[j], y= measures_names[i]))+ 
                  geom_density_2d(aes(colour = method ), alpha=0.7, size=3 )+
                  scale_color_manual(values = experiments_type_colors )+  
                  labs( x = measures_labels[j], y= measures_labels[i] )+
                            theme(legend.position="none" ,   axis.text=element_text(size=21),axis.title=element_text(size=22),
                      plot.subtitle=element_text(size=25 )) +
             coord_cartesian(ylim = c(0, 1), xlim = c(0, 1))
          ggsave(paste( output_directory ,'/',measures_names[i],'_', measures_names[j],'.tiff',  sep=''), graph , 
                 device='tiff', height = 6, width = 6)
      }
      
      }
    }
   
  
   
  
  
   