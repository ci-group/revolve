
library(ggplot2)
library(sqldf)

base_directory <-paste('data', sep='') 

analysis = 'analysis3'

output_directory = paste(base_directory,'/',analysis ,sep='')

experiments_type = c( 'baseline3','plastic3') 

labels_type = c( 'Baseline','Plastic') 

environments = c( 'plane','tilted5')

labels = c('Speed (cm/s) in Flat', 'Speed (cm/s) in Tilted')


runs = list( c(1:10), 
             c(1:10))

 

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
      
      snapshots   = read.table(paste(input_directory, run,'/selectedpop_',
                                     environments[env],"/snapshots_ids.tsv", sep=''), header = TRUE)
      
      measures_snapshots = sqldf('select * from snapshots inner join measures using(robot_id) order by generation')
      
      #measures_snapshots = sqldf('select * from measures_snapshots where generation in (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99)')
      measures_snapshots = sqldf('select * from measures_snapshots where generation in (0, 30, 60, 99)')
      
      if(env==1){
        measures_envs = measures_snapshots
      }else{
        measures_envs = merge(measures_envs, measures_snapshots, by = "robot_id")
      }
      
    }
    
    if ( is.null(measures_all)){
      measures_all = measures_envs
    }else{
      measures_all = rbind(measures_all, measures_envs)
    }
  }
  
  
  measures_all = sqldf('select * from measures_all order by robot_id  ')
  
  graph = ggplot(measures_all, aes(x=speed_plane, y=speed_tilted5, colour=generation.x))+ 
             geom_point(alpha=0.5, size=3)+
             labs(subtitle=labels_type[exp], x=labels[1], y=labels[2])+
              coord_cartesian(ylim = c(-5, 5), xlim = c(-5, 5)) 
  
  ggsave(paste( output_directory,'/',experiments_type[exp],'_scatter.pdf',  sep=''), graph , device='pdf', height = 10, width = 10)
  
}



