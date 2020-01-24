
library(ggplot2)
library(sqldf)

base_directory <-paste('data', sep='') 

analysis = 'analysis_journal2_tilted'

output_directory = paste(base_directory,'/',analysis ,sep='')

experiments_type = c( 'baseline2','plastic2') 

labels_type = c( 'Baseline','Plastic') 

environments = c( 'plane','tilted5')

labels = c('Speed (cm/s) in Flat', 'Speed (cm/s) in Tilted')


runs = list( c(1:20), 
             c(1:20))

 

measures_all = NULL

for (exp in 1:length(experiments_type))
{
  for(run in runs[[exp]])
  {
    measures_envs = NULL
    for (env in 1:length(environments))
    {
      input_directory  <-  paste(base_directory, '/', 
                                 experiments_type[exp], '_',sep='')
      
      measures   = read.table(paste(input_directory, run, '/data_fullevolution/',
                                    environments[env], "/all_measures.tsv", sep=''), header = TRUE)
      measures = sqldf('select robot_id, displacement_velocity_hill from measures')
      measures[paste('speed_',environments[env],sep='')] = as.numeric(as.character(measures[['displacement_velocity_hill']]))
      measures[paste('speed_',environments[env],sep='')] = measures[paste('speed_',environments[env],sep='')] * 100
      measures$run = run
      
      if(env==1){
        measures_envs = measures
      }else{
        measures_envs = merge(measures_envs, measures, by = "robot_id")
      }
      
    }
    
    if ( is.null(measures_all)){
      measures_all = measures_envs
    }else{
      measures_all = rbind(measures_all, measures_envs)
    }
  }
  
  
  measures_all = sqldf('select * from measures_all order by robot_id  ')
  
  graph = ggplot(measures_all, aes(x=speed_plane, y=speed_tilted5, colour=robot_id))+ 
             geom_point(alpha=0.5, size=3)+
             labs(subtitle=labels_type[exp], x=labels[1], y=labels[2])+
              coord_cartesian(ylim = c(-5, 5), xlim = c(-5, 5)) 
  
  ggsave(paste( output_directory,'/',experiments_type[exp],'_scatter.pdf',  sep=''), graph , device='pdf', height = 10, width = 10)
  
}



