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

experiments_type = c(  "scaffincinv", "scaffeqinv")

runs = list(
  c(1:20),
  c(1:20))

# methods are product of experiments_type VS environments and should be coupled with colors.
# make sure to define methods_labels in alphabetic order, and experiments_type accordingly
methods_labels =  c( "scaffincinv", "scaffeqinv")

experiments_type_colors = c('#FF00FF',
                            '#7F00FF', 
                            '#00FF00',
                            '#D2691E') 

#aggregations = c('min', 'Q25','mean', 'median', 'Q75','max')
aggregations = c( 'Q25', 'median', 'Q75')

gens = 100
pop = 100

#gens_box_comparisons = c(gens-1)
gens_box_comparisons = c(99)

measures_names = c(
  'displacement_velocity_hill',
  'head_balance',
  #'branching',
  #'branching_modules_count',
  # 'limbs',
  #'extremities',
  # 'length_of_limbs',
  #'extensiveness',
  # 'coverage',
  'joints',
  #'hinge_count',
  #'active_hinges_count',
  #'brick_count',
  #'touch_sensor_count',
  #'brick_sensor_count',
  'proportion',
  #'width',
  #'height',
  'absolute_size'#,
  #'sensors',
  #'symmetry',
  #'avg_period'#,
  #'dev_period',
  #'avg_phase_offset',
  #'dev_phase_offset',
  #'avg_amplitude',
  #'dev_amplitude',
  # 'avg_intra_dev_params',
  #'avg_inter_dev_params'#,
  #'sensors_reach',
  #'recurrence',
  #'synaptic_reception'
)

# add proper labels soon...
measures_labels = c(
  'Speed (cm/s)',
  'Balance',
  #'Branching',
  #'branching_modules_count',
  # 'Rel number of limbs',
  #'Number of Limbs',
  # 'Rel. Length of Limbs',
  #'Extensiveness',
  #'Coverage',
  'Rel. Number of Joints',
  #'hinge_count',
  #'active_hinges_count',
  #'brick_count',
  #'touch_sensor_count',
  #'brick_sensor_count',
  'Proportion',
  #'width',
  #'height',
  'Size'#,
  # 'Sensors',
  # 'Symmetry',
  #'Average Period'#,
  #'Dev Period',
  #'Avg phase offset',
  #'Dev phase offset',
  #'Avg Amplitude',
  #'Dev amplitude',
  # 'Avg intra dev params',
  #'Avg inter dev params'#,
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




file <-file(paste(output_directory,'/compare_drops.txt',sep=''), open="w")
exps_stages = list()
exps_stages[[1]] = c(3,4,  12,13,  26,27,  45,46,  69,70)
exps_stages[[2]] = c(16,17,  33,34,  50,51,  67,68,  84,85)

for (met in 1:length(methods))
{
  
  met_measures = measures_averages_gens_1[[met]]
 
  for (s in c(1,3,5,7,9)){
    query1 = paste("select ",methods[met],"_displacement_velocity_hill_median as s from met_measures where ",
                  " generation=",exps_stages[[met]][s],sep='')
    query2 = paste("select ",methods[met],"_displacement_velocity_hill_median as s from met_measures where ",
                   "generation=", exps_stages[[met]][s+1],sep='')

    values1 = sqldf(query1)
    values2 = sqldf(query2)
    res=paste(methods[met], 
                exps_stages[[met]][s], round(mean(values1$s),2),
                exps_stages[[met]][s+1], round(mean(values2$s),2),
                 wilcox.test(values1$s,values2$s)$p.value  )
    print(res)
    writeLines(res, file )
  
  }
}

close(file)





#method_label, run,",measures_names2[i],",displacement_velocity_hill
measures_stage = sqldf(paste("select * from measures_snapshots_all where (generation=70 and method_label='scaffincinv')
                             or (generation=85 and method_label='scaffeqinv') order by method_label, run,displacement_velocity_hill"))
measures_stage=measures_stage %>% group_by(method_label,run) %>% mutate(counter = row_number(run))
measures_stage$med <- ifelse(measures_stage$counter > 15,"high", "low")

measures_names2 = c('head_balance','joints','proportion', 'absolute_size')
measures_labels2 = c('Balance', 'Rel. Number of Joints', 'Proportion', 'Size')
for (i in 1:length(measures_names2))
{
  
  measure_stage = sqldf(paste("select method_label, run, med, avg(",measures_names2[i],") as "
                              ,measures_names2[i]," from measures_stage group by 1,2,3"))
   
  g1 <-  ggplot(data=measure_stage, aes_string(x= "method_label" , y=measures_names2[i], fill= "med")) +
    geom_boxplot(position = position_dodge(width=0.9), outlier.size = 0.5) +
    labs( x="method", y=measures_labels2[i])+ 
    guides(fill=guide_legend("Environment of test"))+
    theme(legend.position="bottom" , text = element_text(size=25), legend.key.size = unit(3,"line"),
          axis.text.x = element_text(angle = 20, hjust = 1))+ 
    stat_summary(fun.y = mean, geom="point" ,  size=3, position = position_dodge(width = 0.9)) +
    stat_compare_means(method = "wilcox.test", size=9, label = "p.signif" ) 

  #ggsave(paste(output_directory,"/",measures_names2[i],"_comp.png",sep = ""), g1, device = "png", height=8, width = 10.5)
  
  
}

 
