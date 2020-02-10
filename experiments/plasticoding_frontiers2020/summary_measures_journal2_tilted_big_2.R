  library(ggplot2)
  library(sqldf)
  library(plyr)
  library(dplyr)
  library(trend)
  library(purrr)
  library(ggsignif)
  
  base_directory <-paste('data', sep='') 
  
analysis = 'analysis_journal2_tilted_big_2'
  
output_directory = paste(base_directory,'/',analysis ,sep='')
  
#### CHANGE THE PARAMETERS HERE ####

experiments_type = c('baseline_big', 'plastic_big' )

environments = list( c( 'plane'), c( 'plane') )

methods = c()
for (exp in 1:length(experiments_type))
{
  for (env in 1:length(environments[[exp]]))
  {
    methods = c(methods, paste(experiments_type[exp], environments[[exp]][env], sep='_'))
  }
}

initials =   c( 'b', 'p' )
  
experiments_labels = c(  'Baseline' ,  'Plastic')

  runs = list( c(1:20),  c(1,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,21,22) )
 
  gens = 200
  pop = 100
  
  #### CHANGE THE PARAMETERS HERE ####
  
  sig = 0.05
  line_size = 30
  show_markers = FALSE
  show_legends = FALSE 
  experiments_type_colors = c(  '#00ff00',  '#006600'  )  #  light green; dark green;
  
  measures_names = c(
                     'displacement_velocity_hill',
                     'head_balance',
                     'contacts', 
                     'displacement_velocity',
                     'branching',
                     'branching_modules_count',
                     'limbs',
                     'extremities',
                     'length_of_limbs',
                     'extensiveness',
                     'coverage',
                     'joints',
                     'hinge_count',
                     'active_hinges_count',
                     'brick_count',
                     'touch_sensor_count',
                     'brick_sensor_count',
                     'proportion',
                     'width',
                     'height',
                     'absolute_size',
                     'sensors',
                     'symmetry',
                     'avg_period',
                     'dev_period',
                     'avg_phase_offset',
                     'dev_phase_offset',
                     'avg_amplitude',
                     'dev_amplitude',
                     'avg_intra_dev_params',
                     'avg_inter_dev_params',
                     'sensors_reach',
                     'recurrence',
                     'synaptic_reception',
                     'fitness',
                     'cons_fitness'
  )
  
  # add proper labels soon...
  measures_labels = c(
    'Speed (cm/s)',
    'Balance',
    'Contacts', 
    'displacement_velocity',
    'Branching',
    'branching_modules_count',
    'Rel number of limbs',
    'extremities',
    'Rel. Length of Limbs',
    'extensiveness',
    'coverage',
    'Rel. Number of Joints',
    'hinge_count',
    'active_hinges_count',
    'brick_count',
    'touch_sensor_count',
    'brick_sensor_count',
    'Proportion',
    'width',
    'height',
    'Size',
    'sensors',
    'Symmetry',
    'Average Period',
    'dev_period',
    'avg_phase_offset',
    'dev_phase_offset',
    'avg_amplitude',
    'dev_amplitude',
    'avg_intra_dev_params',
    'avg_inter_dev_params',
    'sensors_reach',
    'recurrence',
    'synaptic_reception',
    'Fitness', 
    'Number of slaves'
  )
  
  
  measures_snapshots_all = NULL
  
  for (exp in 1:length(experiments_type))
  {
    for(run in runs[[exp]])
    {
      for (env in 1:length(environments[[exp]]))
      {
        input_directory  <-  paste(base_directory, '/', 
                                   experiments_type[exp], '_',sep='')
        
        measures   = read.table(paste(input_directory, run, '/data_fullevolution/',
                                      environments[[exp]][env], "/all_measures.tsv", sep=''), header = TRUE, fill=TRUE)
        for( m in 1:length(measures_names))
        { 
          measures[measures_names[m]] = as.numeric(as.character(measures[[measures_names[m]]]))
        }
        
        snapshots   = read.table(paste(input_directory, run,'/selectedpop_',
                                       environments[[exp]][env],"/snapshots_ids.tsv", sep=''), header = TRUE)
        
        measures_snapshots = sqldf('select * from snapshots inner join measures using(robot_id) order by generation')
    
        measures_snapshots$run = run
        measures_snapshots$displacement_velocity_hill =   measures_snapshots$displacement_velocity_hill*100
        measures_snapshots$run = as.factor(measures_snapshots$run)
        measures_snapshots$method = paste(experiments_type[exp], environments[[exp]][env],sep='_')
        
        if ( is.null(measures_snapshots_all)){
          measures_snapshots_all = measures_snapshots
        }else{
          measures_snapshots_all = rbind(measures_snapshots_all, measures_snapshots)
        }
      }
    }
  }
  
  
  fail_test = sqldf(paste("select method,run,generation,count(*) as c from measures_snapshots_all group by 1,2,3 having c<",gens," order by 4"))
  
  
  measures_snapshots_all = sqldf("select * from measures_snapshots_all where cons_fitness IS NOT NULL") 
  
  
  
  # densities
  
  measures_snapshots_all_densities = sqldf(paste("select * from measures_snapshots_all where generation=199 ",sep='' )) 
  
  measures_names_densities = c('length_of_limbs','proportion', 'absolute_size','head_balance','joints', 'limbs')
  measures_labels_densities = c('Rel. Length of Limbs','Proportion', 'Size','Balance','Rel. Number of Joints', 'Rel. Number of Limbs')
  
  for (i in 1:length(measures_names_densities)) 
  {
    
    for (j in 1:length(measures_names_densities)) 
    {
      
      if(i != j)
      {
        
        graph <- ggplot(measures_snapshots_all_densities, aes_string(x=measures_names_densities[j], y= measures_names_densities[i]))+ 
          geom_density_2d(aes(colour = method ), alpha=0.7, size=3 )+
          scale_color_manual(values =  experiments_type_colors  )+  
          labs( x = measures_labels_densities[j], y= measures_labels_densities[i] )+
          theme(legend.position="none" ,   axis.text=element_text(size=21),axis.title=element_text(size=22),
                plot.subtitle=element_text(size=25 )) +
          coord_cartesian(ylim = c(0, 1), xlim = c(0, 1))
        ggsave(paste( output_directory ,'/density_',measures_names_densities[i],'_', measures_names_densities[j],'.png',  sep=''), graph , 
               device='png', height = 6, width = 6)
      }
      
    }
  }
  
  measures_averages_gens_1 = list()
  measures_averages_gens_2 = list()
  
  measures_ini = list()
  measures_fin = list()
  
  for (met in 1:length(methods))
  {
     
      measures_aux = c()
      query ='select run, generation'
      for (i in 1:length(measures_names))
      {
        query = paste(query,', avg(',measures_names[i],') as ', methods[met], '_',measures_names[i],'_avg', sep='') 
      }
      query = paste(query,' from measures_snapshots_all 
                    where method="', methods[met],'" group by run, generation', sep='')
      
      temp = sqldf(query)
  
      measures_averages_gens_1[[met]] = temp
      
      temp = measures_averages_gens_1[[met]] 
      
      temp$generation = as.numeric(temp$generation)
      
      measures_ini[[met]] = sqldf(paste("select * from temp where generation=0"))
      measures_fin[[met]] = sqldf(paste("select * from temp where generation=",gens-1))
      query = 'select generation'
      for (i in 1:length(measures_names))
      {
          # later renames vars _avg_SUMMARY, just to make it in the same style as the quantile variables
        query = paste(query,', avg(', methods[met], '_',measures_names[i],'_avg) as '
                      ,methods[met],'_',measures_names[i],'_avg', sep='') 
        query = paste(query,', max(', methods[met],'_',measures_names[i],'_avg) as '
                      ,methods[met],'_',measures_names[i],'_max', sep='') 
        query = paste(query,', stdev(', methods[met],'_',measures_names[i],'_avg) as '
                      , methods[met],'_',measures_names[i],'_stdev', sep='')
        query = paste(query,', median(', methods[met],'_',measures_names[i],'_avg) as '
                      , methods[met],'_',measures_names[i],'_median', sep='')
        
      