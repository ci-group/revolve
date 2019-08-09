library(ggplot2)
library(sqldf)
library(plyr)
library(dplyr)
library(trend)

base_directory <- paste('../', sep='')
output_directory = base_directory


#### CHANGE THE PARAMETERS HERE ####

experiments_type = c(
                'default_experiment'
                )

initials = c('d')

experiments_labels = c('default_experiment')

runs = c(1,2,3,4,5,6,7,8,9,10)
gens = 100
pop = 100
sig = 0.05
line_size = 30
show_markers = TRUE
show_legends = TRUE
experiments_type_colors = c( '#009900',  '#FF8000', '#BA1616', '#000099')  # DARK:green, orange, red,  blue

#### CHANGE THE PARAMETERS HERE ####



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
                   'fitness'
)

# add proper labels soon...
measures_labels = c(
  'Speed',
  'Balance',
  'Contacts',
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
  'Fitness'
)


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
    measures_snapshots$method = experiments_type[exp]

    if ( is.null(measures_snapshots_all)){
      measures_snapshots_all = measures_snapshots
    }else{
      measures_snapshots_all = rbind(measures_snapshots_all, measures_snapshots)
    }
  }
}


fail_test = sqldf(paste("select method,run,generation,count(*) as c from measures_snapshots_all group by 1,2,3 having c<",gens," order by 4"))


measures_snapshots_all = sqldf("select * from measures_snapshots_all where fitness IS NOT NULL")



measures_averages_gens_1 = list()
measures_averages_gens_2 = list()

measures_ini = list()
measures_fin = list()

for (exp in 1:length(experiments_type))
{

  query ='select run, generation'
  for (i in 1:length(measures_names))
  {
    query = paste(query,', avg(',measures_names[i],') as ',experiments_type[exp],'_',measures_names[i],'_avg', sep='')
  }
  query = paste(query,' from measures_snapshots_all
                where method="',experiments_type[exp],'" group by run, generation', sep='')


  measures_averages_gens_1[[exp]] = sqldf(query)

  temp = measures_averages_gens_1[[exp]]

  measures_ini[[exp]] = sqldf(paste("select * from temp where generation=1"))
  measures_fin[[exp]] = sqldf(paste("select * from temp where generation=",gens-1))
  query = 'select generation'
  for (i in 1:length(measures_names))
  {
    query = paste(query,', avg(',experiments_type[exp],'_',measures_names[i],'_avg) as ',experiments_type[exp],'_',measures_names[i],'_avg', sep='')
    query = paste(query,', max(',experiments_type[exp],'_',measures_names[i],'_avg) as ',experiments_type[exp],'_',measures_names[i],'_max', sep='')
    query = paste(query,', stdev(',experiments_type[exp],'_',measures_names[i],'_avg) as ',experiments_type[exp],'_',measures_names[i],'_stdev', sep='')
    query = paste(query,', median(',experiments_type[exp],'_',measures_names[i],'_avg) as ',experiments_type[exp],'_',measures_names[i],'_median', sep='')
  }
  query = paste(query,' from temp group by generation', sep="")

  measures_averages_gens_2[[exp]] = sqldf(query)

  measures_averages_gens_2[[exp]]$generation = as.numeric(measures_averages_gens_2[[exp]]$generation)

}


for (exp in 1:length(experiments_type))
{
  if(exp==1){
    measures_averages_gens = measures_averages_gens_2[[1]]
  }else{
    measures_averages_gens = merge(measures_averages_gens, measures_averages_gens_2[[exp]], by = "generation")
  }
}

file <-file(paste(output_directory,'/trends.txt',sep=''), open="w")

#tests trends in curves and difference between ini and fin generations


# ini VS fin
array_wilcoxon = list()
array_wilcoxon2 = list()

# curve
array_mann = list()


for (m in 1:length(experiments_type))
{

  array_wilcoxon[[m]] = list()
  array_mann[[m]] = list()

  for (i in 1:length(measures_names))
  {

    writeLines(paste(experiments_type[m],measures_names[i],'ini avg ',as.character(
      mean(c(array(measures_ini[[m]][paste(experiments_type[m],"_",measures_names[i],"_avg",sep='')]) )[[1]]) ) ,sep=" "), file )


    writeLines(paste(experiments_type[m],measures_names[i],'fin avg ',as.character(
      mean(c(array(measures_fin[[m]][paste(experiments_type[m],"_",measures_names[i],"_avg",sep='')]) )[[1]]) ) ,sep=" "), file )

    array_wilcoxon[[m]][[i]]  = wilcox.test(c(array(measures_ini[[m]][paste(experiments_type[m],"_",measures_names[i],"_avg",sep='')]))[[1]] ,
                                            c(array(measures_fin[[m]][paste(experiments_type[m],"_",measures_names[i],"_avg",sep='')]))[[1]]
    )

    writeLines(c(
      paste(experiments_type[m],'iniVSfin',measures_names[i],'wilcox p: ',as.character(round(array_wilcoxon[[m]][[i]]$p.value,4)), sep=' ')
      ,paste(experiments_type[m],'iniVSfin',measures_names[i],'wilcox est: ',as.character(round(array_wilcoxon[[m]][[i]]$statistic,4)), sep=' ')

    ), file)


    #tests  trends
    array_mann[[m]][[i]] =  mk.test(c(array(measures_averages_gens_2[[m]][paste(experiments_type[m],"_",measures_names[i],'_median',sep='')]) )[[1]],
                                    continuity = TRUE)


    writeLines(c(
      paste(experiments_type[m],measures_names[i], ' Mann-Kendall median p', as.character(round(array_mann[[m]][[i]]$p.value,4)),sep=' '),
      paste(experiments_type[m],measures_names[i], ' Mann-Kendall median s', as.character(round(array_mann[[m]][[i]]$statistic,4)),sep=' ')
    ), file)

  }

}



# tests final generation among experiments_type

aux_m = length(experiments_type)

if (aux_m>1)
{

  # fins
  array_wilcoxon2[[1]] = list()
  array_wilcoxon2[[2]] = list()

aux_m = aux_m -1
count_pairs = 0
for(m in 1:aux_m)
{
  aux = m+1
  for(m2 in aux:length(experiments_type))
  {

    count_pairs = count_pairs+1
    array_wilcoxon2[[1]][[count_pairs]] = list()

    for (i in 1:length(measures_names))
    {

      writeLines(paste(experiments_type[m],measures_names[i],'fin avg ',as.character(
        mean(c(array(measures_fin[[m]][paste(experiments_type[m],"_",measures_names[i],"_avg",sep='')]) )[[1]]) ) ,sep=" "), file )

      writeLines(paste(experiments_type[m2],measures_names[i],'fin avg ',as.character(
        mean(c(array(measures_fin[[m2]][paste(experiments_type[m2],"_",measures_names[i],"_avg",sep='')]) )[[1]]) ) ,sep=" "), file )

      array_wilcoxon2[[1]][[count_pairs]][[i]]  = wilcox.test(c(array(measures_fin[[m]][paste(experiments_type[m],"_",measures_names[i],"_avg",sep='')]))[[1]] ,
                                                              c(array(measures_fin[[m2]][paste(experiments_type[m2],"_",measures_names[i],"_avg",sep='')]))[[1]]
      )

      writeLines(c(
        paste(experiments_type[m],'VS',experiments_type[m2],measures_names[i],'fin avg wilcox p: ',as.character(round(array_wilcoxon2[[1]][[count_pairs]][[i]]$p.value,4)), sep=' ')
        ,paste(experiments_type[m],'VS',experiments_type[m2],measures_names[i],'fin avg wilcox est: ',as.character(round(array_wilcoxon2[[1]][[count_pairs]][[i]]$statistic,4)), sep=' ')

      ), file)

    }


      array_wilcoxon2[[2]][[count_pairs]] = paste(initials[m],initials[m2],sep='')

  }
}

}

close(file)

# plots measures

for (i in 1:length(measures_names))
{
  tests1 = ''
  tests2 = ''
  tests3 = ''
  break_aux = 0

  graph <- ggplot(data=measures_averages_gens, aes(x=generation))
  for(m in 1:length(experiments_type))
  {
    graph = graph + geom_errorbar(aes_string(ymin=paste(experiments_type[m],'_',measures_names[i],'_avg','-',experiments_type[m],'_',measures_names[i],'_stdev',sep=''),
                                             ymax=paste(experiments_type[m],'_',measures_names[i],'_avg','+',experiments_type[m],'_',measures_names[i],'_stdev',sep='') ),
                                  color=experiments_type_colors[m],
                                  alpha=0.35,size=0.5,width=0.001)
  }

  for(m in 1:length(experiments_type))
  {
    if(show_legends == TRUE){
      graph = graph + geom_line(aes_string(y=paste(experiments_type[m],'_',measures_names[i],'_avg',sep=''), colour=shQuote(experiments_labels[m]) ), size=2)
    }else{
      graph = graph + geom_line(aes_string(y=paste(experiments_type[m],'_',measures_names[i],'_avg',sep='')   ),size=2, color = experiments_type_colors[m])
    }
    # graph = graph + geom_line(aes_string(y=paste(experiments_type[m],'_',measures_names[i],'_median',sep='')   ),size=2, color = colors_median[m])

    if (length(array_mann)>0)
    {
      if (length(array_mann[[m]])>0)
      {
        if(!is.na(array_mann[[m]][[i]]$p.value))
        {
          if(array_mann[[m]][[i]]$p.value<=sig)
          {
            if(array_mann[[m]][[i]]$statistic>0){ direction = "/  "} else { direction = "\\  "}
            tests1 = paste(tests1, initials[m],direction,sep="")
          }
        }
      }
    }
  }

  if (length(array_wilcoxon[[m]])>0)
  {
    for(m in 1:length(experiments_type))
    {
      if(!is.na(array_wilcoxon[[m]][[i]]$p.value))
      {
        if(array_wilcoxon[[m]][[i]]$p.value<=sig)
        {
          tests2 = paste(tests2, initials[m],'C  ', sep='')
        }
      }
    }
  }

  if (length(array_wilcoxon2)>0)
    {
      for(p in 1:length(array_wilcoxon2[[1]]))
      {
        if (length(array_wilcoxon2[[1]][[p]])>0)
        {
          if(!is.na(array_wilcoxon2[[1]][[p]][[i]]$p.value))
          {
            if(array_wilcoxon2[[1]][[p]][[i]]$p.value<=sig)
            {
              if(nchar(tests3)>line_size && break_aux == 0){
                tests3 = paste(tests3, '\n')
                break_aux = 1
              }
              tests3 = paste(tests3, array_wilcoxon2[[2]][[p]],'D  ',sep='')
            }
          }
        }
      }
  }

  graph = graph  +
    #coord_cartesian(ylim = c(0, 1))+
    labs( y=measures_labels[i], x="Generation")
  if(show_markers == TRUE){
    graph = graph  + labs( y=measures_labels[i], x="Generation", subtitle = paste(tests1,'\n', tests2, '\n', tests3, sep=''))
  }
  graph = graph  + theme(legend.position="bottom" ,  legend.text=element_text(size=20), axis.text=element_text(size=30),axis.title=element_text(size=39),
                         plot.subtitle=element_text(size=25 ))

  ggsave(paste( output_directory,'/' ,measures_names[i],'_generations.pdf',  sep=''), graph , device='pdf', height = 8, width = 10)
}


