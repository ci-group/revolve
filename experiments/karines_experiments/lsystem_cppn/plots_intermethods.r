library(ggplot2)
library(sqldf)
library(plyr)
library(dplyr)
library(trend)
library(purrr)
library(ggsignif)
library(stringr)
library(reshape)

####  this example of parameterization compares multiple types of experiments using one particular season ###

#### CHANGE THE PARAMETERS HERE ####

base_directory <-paste('data', sep='')
analysis = 'analysis'
output_directory = paste(base_directory,'/',analysis ,sep='')

experiments_type = c('hyperplasticoding',
                     'plasticoding')
experiments_labels = c( 'hyperplasticoding',
                        'plasticoding')
runs = list(c(1:20),
            c(1:20))
environments = list( c( 'plane'),
                     c( 'plane') )

# methods are product of experiments_type VS environments and should be coupled with colors.
# make sure to define methods_labels in alphabetic order, and experiments_type accordingly
methods_labels = c('CPPN',
                   'L-System')
experiments_type_colors = c('#EE8610', # orange
                            '#009900') # green

#aggregations = c('min', 'Q25','mean', 'median', 'Q75','max')
aggregations = c( 'Q25', 'median', 'Q75')

gens = 150
pop = 100

#gens_box_comparisons = c(gens-1)
gens_box_comparisons = c(0, 49, 149)

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
  'synaptic_reception'
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
  'Symmetry',
  'Average Period',
  'Dev Period',
  'Avg phase offset',
  'Dev phase offset',
  'Avg Amplitude',
  'Dev amplitude',
  'Avg intra dev params',
  'Avg inter dev params',
  'Sensors Reach',
  'Recurrence',
  'Synaptic reception'
)

more_measures_names = c(
  # 'novelty',
  'novelty_pop',
  'fitness'#,
  #'cons_fitness'
)

more_measures_labels = c(
  #'Novelty (+archive)',
  'Novelty',
  'Fitness'#,
  #'Number of slaves'
)

#### CHANGE THE PARAMETERS HERE ####



methods = c()
for (exp in 1:length(experiments_type))
{
  for (env in 1:length(environments[[exp]]))
  {
    methods = c(methods, paste(experiments_type[exp], environments[[exp]][env], sep='_'))
  }
}

measures_snapshots_all = NULL

for (exp in 1:length(experiments_type))
{
  for(run in runs[[exp]])
  {
    for (env in 1:length(environments[[exp]]))
    {
      measures   = read.table(paste(base_directory,paste(experiments_type[exp], environments[[exp]][env], run,"all_measures.tsv", sep='_'), sep='/'),
                              header = TRUE, fill=TRUE)

      for( m in 1:length(measures_names))
      {
        measures[measures_names[m]] = as.numeric(as.character(measures[[measures_names[m]]]))
      }

      snapshots   = read.table(paste(base_directory,paste(experiments_type[exp], environments[[exp]][env], run, "snapshots_ids.tsv", sep='_'), sep='/'),
                               header = TRUE)

      measures_snapshots = sqldf('select * from snapshots inner join measures using(robot_id) order by generation')

      measures_snapshots$run = run
      measures_snapshots$displacement_velocity_hill =   measures_snapshots$displacement_velocity_hill*100
      measures_snapshots$run = as.factor(measures_snapshots$run)
      measures_snapshots$method = paste(experiments_type[exp], environments[[exp]][env],sep='_')
      measures_snapshots$method_label =  methods_labels[exp]

      if ( is.null(measures_snapshots_all)){
        measures_snapshots_all = measures_snapshots
      }else{
        measures_snapshots_all = rbind(measures_snapshots_all, measures_snapshots)
      }
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

for (i in 1:length(measures_names)){

  query = paste("select method_label,'Run '||run as run, generation, robot_id, ",
                measures_names[i]," as value from measures_snapshots_all ")
  if (!all_runs){
    random_runs = paste('(', paste(sample(runs[[1]], 3), collapse=', ' ), ')')
    query = paste(query, "where run in ",random_runs)
  }

  measures_heat = sqldf(query)
  measures_heat = measures_heat %>%
    group_by(method_label, run, generation) %>%
    mutate(rank = order(order(value)))

  heat <-ggplot(measures_heat, aes(generation, rank, fill=value))+
    geom_tile(color= "white",size=0.1) +
    scale_fill_viridis(option ="C")
  heat <-heat + facet_grid(method_label~run)
  heat <-heat + scale_y_continuous(breaks =c())
  heat <-heat + scale_x_continuous(breaks =c(0, 50, 149))
  heat <-heat + labs(title=measures_labels[i], x="Generations", y="Robots", fill=measures_labels[i])
  heat <-heat + theme(legend.position = "none")+
    theme(legend.key.size = unit(1.5, 'cm'))+
    theme(plot.title=element_text(size=37))+
    theme(axis.text.y=element_text(size=31)) +
    theme(axis.text.x=element_text(size=28)) +
    theme(axis.title=element_text(size=35)) +
    theme(strip.text.y=element_text(size=38)) +
    theme(strip.text.x=element_text(size=30)) +
    theme(strip.background = element_rect(colour="white"))+
    theme(plot.title=element_text(hjust=0))+
    theme(axis.ticks=element_blank())+
    theme(legend.title=element_text(size=36))+
    theme(legend.text=element_text(size=36))+
    removeGrid()

  if (!all_runs){
    ggsave(paste(output_directory,"/",measures_names[i],"_heat.png",sep = ""), heat, device = "png", height=10, width = 20)
  }else{
    ggsave(paste(output_directory,"/",measures_names[i],"_heat.png",sep = ""), heat, device = "png", height=10, width = 140, limitsize = FALSE)
  }

}

####

# density maps

#pairs = list(
 # c('head_balance', 'limbs') ,
 # c('head_balance', 'symmetry') ,
 # c('head_balance', 'proportion'),
 # c('displacement_velocity_hill', 'limbs') ,
 # c('displacement_velocity_hill', 'symmetry') ,
 # c('displacement_velocity_hill', 'proportion'),
  #c('displacement_velocity_hill', 'head_balance' )
  #)

#for (pair in 1:length(pairs))
 # {

  #measures_snapshots_all_final = sqldf(paste("select method_label, ",
       #                                      pairs[[pair]][1],",",
        #                                     pairs[[pair]][2],"
                   #                          from measures_snapshots_all where generation=", gens-1) )

  #graph <- ggplot(measures_snapshots_all_final, aes_string(x=pairs[[pair]][1], y=pairs[[pair]][2]))+
  #  geom_density_2d(aes(colour = method_label ), alpha=0.7, size=3 )+
  #  scale_color_manual(values = experiments_type_colors )+
  #  labs( x = pairs[[pair]][1], y= pairs[[pair]][2] )+
  #  theme(legend.position="bottom" ,   axis.text=element_text(size=21),axis.title=element_text(size=22),  plot.subtitle=element_text(size=25 ))
  #ggsave(paste( output_directory ,'/density_',pairs[[pair]][1],'_', pairs[[pair]][2],'.png',  sep=''), graph , device='png', height = 6, width = 6)


  #graph = ggplot(measures_snapshots_all_final, aes_string(x=pairs[[pair]][1], y=pairs[[pair]][2], colour="method_label"))+
   # geom_point(alpha=0.7, size=3)+
   ## labs(x=pairs[[pair]][1], y=pairs[[pair]][2])+
   # theme(legend.position="bottom" ,   axis.text=element_text(size=21),axis.title=element_text(size=22),  plot.subtitle=element_text(size=25 )) +
   # scale_color_manual(values = experiments_type_colors )
  #ggsave(paste( output_directory ,'/scatter_',pairs[[pair]][1],'_', pairs[[pair]][2],'.png',  sep=''), graph , device='png', height = 6, width = 6)


#}

pairs = list(
  c('head_balance', 'limbs', 0.6, 1, 0, 1) ,
  c('head_balance', 'symmetry', 0.6, 1, 0, 1) ,
  c('head_balance', 'proportion', 0.6, 1, 0, 1),
  c('displacement_velocity_hill', 'limbs', 0, 8, 0, 1) ,
  c('displacement_velocity_hill', 'symmetry', 0, 8, 0, 1) ,
  c('displacement_velocity_hill', 'proportion', 0, 8, 0, 1),
  c('displacement_velocity_hill', 'head_balance', 0, 8, 0.6, 1)
)

for (pair in 1:length(pairs))
{

  for (met in 1:length(methods))
  {
    measures_snapshots_all_final = sqldf(paste("select method, ",
                                               pairs[[pair]][1],",",
                                               pairs[[pair]][2],"
                                               from measures_snapshots_all where generation=", gens-1,
                                               " and method='", methods[met], "'", sep='') )

    graph <- ggplot(measures_snapshots_all_final, aes_string(x=pairs[[pair]][1], y=pairs[[pair]][2]))+
      geom_density_2d(aes(colour = method ), alpha=0.7, size=3 )+
      scale_color_manual(values = experiments_type_colors[met] )+
      labs( x = pairs[[pair]][1], y= pairs[[pair]][2] )+
      theme(legend.position="none" ,   axis.text=element_text(size=21),axis.title=element_text(size=22),  plot.subtitle=element_text(size=25 )) +
      coord_cartesian(xlim = c( as.numeric(pairs[[pair]][3]),  as.numeric(pairs[[pair]][4])),
                      ylim = c( as.numeric(pairs[[pair]][5]),  as.numeric(pairs[[pair]][6])))
    ggsave(paste( output_directory ,'/density_',methods[met],'_',pairs[[pair]][1],'_', pairs[[pair]][2],'.png',  sep=''), graph , device='png', height = 6, width = 6)
  }
}


###

measures_averages_gens_1 = list()
measures_averages_gens_2 = list()

for (met in 1:length(methods))
{
  measures_aux = c()
  p <- c(0.25, 0.75)
  p_names <- map_chr(p, ~paste0('Q',.x*100, sep=""))
  p_funs <- map(p, ~partial(quantile, probs = .x, na.rm = TRUE)) %>%
    set_names(nm = p_names)

  query ='select run, generation'
  for (i in 1:length(measures_names))
  {
    query = paste(query,', avg(',measures_names[i],') as ', methods[met], '_',measures_names[i],'_mean', sep='')
    query = paste(query,', median(',measures_names[i],') as ', methods[met], '_',measures_names[i],'_median', sep='')
    query = paste(query,', min(',measures_names[i],') as ', methods[met], '_',measures_names[i],'_min', sep='')
    query = paste(query,', max(',measures_names[i],') as ', methods[met], '_',measures_names[i],'_max', sep='')
    measures_aux = c(measures_aux, measures_names[i])
  }
  query = paste(query,' from measures_snapshots_all
                where method="', methods[met],'" group by run, generation', sep='')
  inner_measures = sqldf(query)

  quantiles = data.frame(measures_snapshots_all %>%
                           filter(method==methods[met]) %>%
                           group_by(run, generation) %>%
                           summarize_at(vars(  measures_aux), funs(!!!p_funs)) )
  for (i in 1:length(measures_names)){
    for(q in c('Q25', 'Q75')){
      variable =  paste(measures_names[i], q, sep='_')
      names(quantiles)[names(quantiles) == variable] <- paste(methods[met], '_',variable, sep='')
    }
  }
  inner_measures = sqldf('select * from inner_measures inner join quantiles using (run, generation)')

  measures_averages_gens_1[[met]] = inner_measures

  inner_measures = measures_averages_gens_1[[met]]

  inner_measures$generation = as.numeric(inner_measures$generation)

  measures_aux = c()
  query = 'select generation'
  for (i in 1:length(measures_names))
  {
    query = paste(query,', median(', methods[met],'_',measures_names[i],'_mean) as ' , methods[met],'_',measures_names[i],'_mean_median', sep='')
    query = paste(query,', median(', methods[met],'_',measures_names[i],'_median) as ', methods[met],'_',measures_names[i],'_median_median', sep='')
    query = paste(query,', median(', methods[met],'_',measures_names[i],'_min) as ', methods[met],'_',measures_names[i],'_min_median', sep='')
    query = paste(query,', median(', methods[met],'_',measures_names[i],'_max) as ', methods[met],'_',measures_names[i],'_max_median', sep='')
    query = paste(query,', median(', methods[met],'_',measures_names[i],'_Q25) as ', methods[met],'_',measures_names[i],'_Q25_median', sep='')
    query = paste(query,', median(', methods[met],'_',measures_names[i],'_Q75) as ', methods[met],'_',measures_names[i],'_Q75_median', sep='')

    measures_aux = c(measures_aux, paste(methods[met],'_',measures_names[i],'_mean', sep='') )
    measures_aux = c(measures_aux, paste(methods[met],'_',measures_names[i],'_median', sep='') )
    measures_aux = c(measures_aux, paste(methods[met],'_',measures_names[i],'_min', sep='') )
    measures_aux = c(measures_aux, paste(methods[met],'_',measures_names[i],'_max', sep='') )
    measures_aux = c(measures_aux, paste(methods[met],'_',measures_names[i],'_Q25', sep='') )
    measures_aux = c(measures_aux, paste(methods[met],'_',measures_names[i],'_Q75', sep='') )
  }
  query = paste(query,' from inner_measures group by generation', sep="")
  outter_measures = sqldf(query)

  quantiles = data.frame(inner_measures %>%
                           group_by(generation) %>%
                           summarize_at(vars(  measures_aux), funs(!!!p_funs)) )

  measures_averages_gens_2[[met]] = sqldf('select * from outter_measures inner join quantiles using (generation)')

}


for (met in 1:length(methods))
{
  if(met==1){
    measures_averages_gens = measures_averages_gens_2[[1]]
  }else{
    measures_averages_gens = merge(measures_averages_gens, measures_averages_gens_2[[met]], all=TRUE, by = "generation")
  }
}




all_na = colSums(is.na(measures_averages_gens)) == nrow(measures_averages_gens)
for (i in 1:length(measures_names))
{

  #  line plots


  # finding values for scaling
  max_y =  0
  min_y = 10000000
  for(a in 1:length(aggregations)){
    for(m in 1:length(methods)){
      max_value = max(measures_averages_gens[paste(methods[m],'_',measures_names[i],'_', aggregations[a], '_Q75',sep='')], na.rm = TRUE)
      min_value = min(measures_averages_gens[paste(methods[m],'_',measures_names[i],'_', aggregations[a], '_Q25',sep='')], na.rm = TRUE)
      if(max_value > max_y){ max_y = max_value }
      if(min_value < min_y){ min_y = min_value }
    }
  }
  #if (measures_names[i] == 'absolute_size' )  {    max_y = 16}

  for(a in 1:length(aggregations)){

    graph <- ggplot(data=measures_averages_gens, aes(x=generation))

    for(m in 1:length(methods)){

      is_all_na = all_na[paste(methods[m],'_',measures_names[i],'_', aggregations[a], '_median', sep='')]

      if (is_all_na == FALSE) {

        graph = graph + geom_ribbon(aes_string(ymin=paste(methods[m],'_',measures_names[i],'_', aggregations[a],'_Q25',sep=''),
                                               ymax=paste(methods[m],'_',measures_names[i],'_', aggregations[a],'_Q75',sep='') ),
                                    fill=experiments_type_colors[m], alpha=0.2, size=0)

        graph = graph + geom_line(aes_q(y = as.name(paste(methods[m],'_',measures_names[i],'_', aggregations[a], '_median', sep='')) ,
                                        colour=paste(methods_labels[m], aggregations[a], sep='_')), size=1)
      }
    }

    if (max_y>0) {
      graph = graph + coord_cartesian(ylim = c(min_y, max_y))
    }
    graph = graph  +  labs(y=measures_labels[i], x="Generation", title="")

    graph = graph +   scale_color_manual(values=experiments_type_colors)
    graph = graph  + theme(legend.position="bottom" ,  legend.text=element_text(size=25), axis.text=element_text(size=32), axis.title=element_text(size=30),
                           plot.subtitle=element_text(size=30 ), plot.title=element_text(size=30 ))

    ggsave(paste( output_directory,'/',measures_names[i], '_', aggregations[a], '_lines.pdf',  sep=''), graph , device='pdf', height = 10, width = 10)



    # creates one box plot per measure, and one extra in case outlier removal is needeed
    outliers = c('full', 'filtered')
    for (out in outliers)
    {
      has_outliers = FALSE

      for(gc in gens_box_comparisons)
      {

        all_final_values = data.frame()
        for (met in 1:length(methods))
        {

          met_measures = measures_averages_gens_1[[met]]
          gen_measures = sqldf(paste("select * from met_measures where generation=", gc, sep=''))

          temp = data.frame( c(gen_measures[paste(methods[met],'_',measures_names[i],'_', aggregations[a], sep='')]))
          colnames(temp) <- 'values'

          if (out == 'filtered'){
            if (!all(is.na(temp$values))){

              num_rows_before = nrow(temp)
              upperl <- quantile(temp$values)[4] + 1.5*IQR(temp$values)
              lowerl <- quantile(temp$values)[2] - 1.5*IQR(temp$values)
              temp = temp %>% filter(values <= upperl & values >= lowerl )

              if (num_rows_before > nrow(temp)){
                has_outliers = TRUE
              }
            }
          }

          temp$type = methods_labels[met]
          all_final_values = rbind(all_final_values, temp)
        }

        g1 <-  ggplot(data=all_final_values, aes(x= type , y=values, color=type )) +
          geom_boxplot(position = position_dodge(width=0.9),lwd=2,  outlier.size = 4) +
          labs( x="Method", y=measures_labels[i], title=str_to_title(aggregations[a]))

        g1 = g1 +  scale_color_manual(values=  experiments_type_colors  )

        g1 = g1 + theme(legend.position="none" , text = element_text(size=50) ,
                        plot.title=element_text(size=50),  axis.text=element_text(size=50),
                        axis.title=element_text(size=55),
                        axis.text.x = element_text(angle = 20, hjust = 0.9),
                        plot.margin=margin(t = 0.5, r = 0.5, b = 0.5, l =  1.3, unit = "cm"))+
          stat_summary(fun.y = mean, geom="point" ,shape = 16,  size=11)

        # in this list, use the desired pairs names from methods_labels
        comps = list( methods_labels )

        max_y =  0
        #if (measures_names[i] == 'absolute_size' )  {    max_y = 16}
        if (max_y>0) {
          graph = graph + coord_cartesian(ylim = c(min_y, max_y))
        }

        g1 = g1 + geom_signif( test="wilcox.test", size=1, textsize=18,
                               comparisons = comps,
                               map_signif_level=c() )

        if (out == 'full' || (out == 'filtered' &&  has_outliers == TRUE) ){
          ggsave(paste(output_directory,"/",measures_names[i],"_",gc,"_", aggregations[a],'_', out,"_boxes.pdf",sep = ""), g1, device = "pdf", height=18, width = 10)
        }

      }

    }

  }

}

