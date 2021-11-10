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

####  this example of parameterization compares multiple types of experiments using one particular season ###

#### CHANGE THE PARAMETERS HERE ####

base_directory2 <-paste('/storage/karine/alifej2021', sep='')

analysis = 'analysis/measures'
output_directory = paste(base_directory2,'/',analysis ,sep='')

experiments_type = c("scaffincinv", "scaffinc", "scaffeq", "staticplane", "scaffeqinv", "statictilted")
experiments_type = c("scaffeq", "scaffeqinv","scaffeq", "scaffeqinv","scaffeq", "scaffeqinv")
experiments_labels = c("scaffincinv", "scaffinc", "scaffeq", "staticplane", "scaffeqinv", "statictilted")

runs = list(
            c(1:20),
            c(1:20),
            c(1:20),
            c(1:20),
            c(1:20),
            c(1:20))

# methods are product of experiments_type VS environments and should be coupled with colors.
# make sure to define methods_labels in alphabetic order, and experiments_type accordingly
methods_labels = c(
                   'Inv Incr',
                   'Incr',
                   'Equal',
                   'Flat',
                   'Inv Equal',
                   'Tilted'
                   )


#aggregations = c('min', 'Q25','mean', 'median', 'Q75','max')
aggregations = c( 'Q25', 'median', 'Q75')

gens = 100
pop = 100

#gens_box_comparisons = c(gens-1)
gens_box_comparisons = c(99)

measures_names = c(
  'displacement_velocity_hill',
  'head_balance',
  'branching',
  #'branching_modules_count',
  'limbs',
  'extremities',
  'length_of_limbs',
  #'extensiveness',
  'coverage',
  'joints',
  #'hinge_count',
  #'active_hinges_count',
  #'brick_count',
  #'touch_sensor_count',
  #'brick_sensor_count',
  'proportion',
  #'width',
  #'height',
  'absolute_size',
  'sensors',
  'symmetry'#,
  #'avg_period',
  #'dev_period',
  #'avg_phase_offset',
  #'dev_phase_offset',
  #'avg_amplitude',
  #'dev_amplitude',
  #'avg_intra_dev_params',
  #'avg_inter_dev_params',
  #'sensors_reach',
  #'recurrence',
  #'synaptic_reception'
)

# add proper labels soon...
measures_labels = c(
  'Speed (cm/s)',
  'Balance',
  'Branching',
  #'branching_modules_count',
  'Rel number of limbs',
  'Number of Limbs',
  'Rel. Length of Limbs',
  #'Extensiveness',
  'Coverage',
  'Rel. Number of Joints',
  #'hinge_count',
  #'active_hinges_count',
  #'brick_count',
  #'touch_sensor_count',
  #'brick_sensor_count',
  'Proportion',
  #'width',
  #'height',
  'Size',
  'Sensors',
  'Symmetry'#,
  #'Average Period',
  #'Dev Period',
  #'Avg phase offset',
  #'Dev phase offset',
  #'Avg Amplitude',
  #'Dev amplitude',
  #'Avg intra dev params',
  #'Avg inter dev params',
  #'Sensors Reach',
  #'Recurrence',
  #'Synaptic reception'
)

more_measures_names = c(
  # 'novelty',
  'novelty_pop',
  'fitness',
  'cons_fitness'
)

more_measures_labels = c(
  #'Novelty (+archive)',
  'Novelty',
  'Fitness',
  'Number of slaves'
)

#### CHANGE THE PARAMETERS HERE ####


methods = c()
for (exp in 1:length(experiments_type))
{
    methods = c(methods, paste(experiments_type[exp], sep='_'))
}

measures_snapshots_all = NULL

for (exp in 1:length(experiments_type))
{
  for(run in runs[[exp]])
  {
 
      measures_snapshots = read.table(paste(base_directory2,paste(experiments_type[exp], run, "snapshots_full.tsv", sep='_'), sep='/'),
                               header = TRUE)
      
      for( m in 1:length(measures_names))
      {
        measures_snapshots[measures_names[m]] = as.numeric(as.character(measures_snapshots[[measures_names[m]]]))
      }
      
      measures_snapshots$run = run
      measures_snapshots$displacement_velocity_hill =   measures_snapshots$displacement_velocity_hill*100
      measures_snapshots$run = as.factor(measures_snapshots$run)
      measures_snapshots$method = paste(experiments_type[exp], sep='_')
      measures_snapshots$method_label =  methods_labels[exp]

      if ( is.null(measures_snapshots_all)){
        measures_snapshots_all = measures_snapshots
      }else{
        measures_snapshots_all = rbind(measures_snapshots_all, measures_snapshots)
      }
    
  }
}


fail_test = sqldf(paste("select method,run,generation,count(*) as c from measures_snapshots_all group by 1,2,3 having c<",pop," order by 4"))
measures_snapshots_all = sqldf("select * from measures_snapshots_all where cons_fitness IS NOT NULL")

measures_names = c(measures_names, more_measures_names)
measures_labels = c(measures_labels, more_measures_labels)

for( m in 1:length(more_measures_names)){
  measures_snapshots_all[more_measures_names[m]] = as.numeric(as.character(measures_snapshots_all[[more_measures_names[m]]]))
}


#####
# heatmap
all_runs = FALSE
random_runs = paste('(', paste(sample(runs[[1]], 10), collapse=', ' ), ')')


  query = paste("select method_label, run, generation, robot_id, novelty_pop as value from measures_snapshots_all ")
  if (!all_runs){
    query = paste(query, "where run in ",random_runs)
  }

  measures_heat = sqldf(query)
  measures_heat = measures_heat %>%
    group_by(method_label, run, generation) %>%
    mutate(rank = order(order(value)))
  
  #measures_heat =  sqldf(paste("select * from measures_heat where rank>65 "))

  heat <-ggplot(measures_heat, aes(generation, rank, fill=value))+
    geom_tile(color= "white",size=0.1)+
    scale_fill_viridis(option ="C")
  heat <-heat + facet_grid(method_label~run)
  heat <-heat + scale_y_continuous(breaks =c())
  heat <-heat + scale_x_continuous(breaks =c())
  heat <-heat + labs(title="Novelty", x="Generations", y="Robots", fill="Novelty")
  heat <-heat + theme(legend.position = "none")+
    theme(legend.key.size = unit(1.5, 'cm'))+
    theme(plot.title=element_text(size=48))+
    theme(axis.text.y=element_text(size=38)) +
    theme(axis.text.x=element_text(size=36)) +
    theme(axis.title=element_text(size=47)) +
    theme(strip.text.y=element_text(size=51)) +
    theme(strip.text.x=element_text(size=41)) +
    theme(strip.background = element_rect(colour="white"))+
    theme(plot.title=element_text(hjust=0))+
    theme(axis.ticks=element_blank())+
    theme(legend.title=element_text(size=40))+
    theme(legend.text=element_text(size=40))#+
  #removeGrid()

  if (!all_runs){
    ggsave(paste(output_directory,"/novelty_heat.png",sep = ""), heat, device = "png", height=22, width = 49)
  }else{
    ggsave(paste(output_directory,"/novelty_heat.png",sep = ""), heat, device = "png", height=22, width = 50, limitsize = FALSE)
  }

