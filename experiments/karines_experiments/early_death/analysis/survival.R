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


#### CHANGE THE PARAMETERS HERE ####

base_directory <- c('/storage/karine/early_death',
                    '/storage/karine/early_death')

#base_directory <- c('data', 'data')



analysis = 'analysis_plane'
output_directory = paste(base_directory[1],'/',analysis ,sep='')

experiments_type = c('tilteddeath',
                     'planedeath')
runs = list(c(1:20),
            c(1:20))


# methods are product of experiments_type VS environments and should be coupled with colors.
# make sure to define methods_labels in alphabetic order, and experiments_type accordingly
methods_labels = c( 'Plane death',
                    'Tilted death') # note that labels of Plane death and Tilted death are INVERTED on purpose, to fix the mistake done when naming the experiments.

experiments_type_colors = c('#EE8610',
                            '#0000ff')

measures_names = c('n')


all_survival = NULL

for (exp in 1:length(experiments_type))
{
  for(run in runs[[exp]])
  {
      survival   = read.table(paste(base_directory[exp],paste(experiments_type[exp],'_', run,sep=''), 'data_fullevolution', 'individuals_early_survived.txt', sep='/'),
                              header = FALSE, fill=TRUE)

      survival = sqldf("select V1 as generation, max(V2) as n from survival group by 1")

      survival$run = run
      survival$method_label =  methods_labels[exp]
      survival$method =  experiments_type[exp]

      if ( is.null(all_survival)){
        all_survival = survival
      }else{
        all_survival = rbind(all_survival, survival)
      }

  }
}



measures_averages_gens_1 = list()
measures_averages_gens_2 = list()

for (met in 1:length(experiments_type))
{
  measures_aux = c()
  p <- c(0.25, 0.75)
  p_names <- map_chr(p, ~paste0('Q',.x*100, sep=""))
  p_funs <- map(p, ~partial(quantile, probs = .x, na.rm = TRUE)) %>%
    set_names(nm = p_names)

  query ='select run, generation'
  for (i in 1:length(measures_names))
  {
    query = paste(query,', avg(',measures_names[i],') as ', experiments_type[met], '_',measures_names[i],'_mean', sep='')
    query = paste(query,', median(',measures_names[i],') as ', experiments_type[met], '_',measures_names[i],'_median', sep='')
    query = paste(query,', min(',measures_names[i],') as ', experiments_type[met], '_',measures_names[i],'_min', sep='')
    query = paste(query,', max(',measures_names[i],') as ', experiments_type[met], '_',measures_names[i],'_max', sep='')
    measures_aux = c(measures_aux, measures_names[i])
  }
  query = paste(query,' from all_survival
                where method="', experiments_type[met],'" group by run, generation', sep='')
  inner_measures = sqldf(query)

  quantiles = data.frame(all_survival %>%
                           filter(method==experiments_type[met]) %>%
                           group_by(run, generation) %>%
                           summarize_at(vars(  measures_aux), funs(!!!p_funs)) )
  quantiles = sqldf(paste('select run, generation, Q25 as ',experiments_type[met],'_n_Q25, Q75 as ',experiments_type[met], '_n_Q75 from quantiles', sep=''))

 # for (i in 1:length(measures_names)){
  # # for(q in c('Q25', 'Q75')){
   #   variable =  paste(measures_names[i], q, sep='_')
   #   names(quantiles)[names(quantiles) == variable] <- paste(experiments_type[met], '_',variable, sep='')
  #  }
  #}

  inner_measures = sqldf('select * from inner_measures inner join quantiles using (run, generation)')

  measures_averages_gens_1[[met]] = inner_measures

  inner_measures = measures_averages_gens_1[[met]]

  inner_measures$generation = as.numeric(inner_measures$generation)

  measures_aux = c()
  query = 'select generation'
  for (i in 1:length(measures_names))
  {
    query = paste(query,', median(', experiments_type[met],'_',measures_names[i],'_mean) as ' , experiments_type[met],'_',measures_names[i],'_mean_median', sep='')
    query = paste(query,', median(', experiments_type[met],'_',measures_names[i],'_median) as ', experiments_type[met],'_',measures_names[i],'_median_median', sep='')
    query = paste(query,', median(', experiments_type[met],'_',measures_names[i],'_min) as ', experiments_type[met],'_',measures_names[i],'_min_median', sep='')
    query = paste(query,', median(', experiments_type[met],'_',measures_names[i],'_max) as ', experiments_type[met],'_',measures_names[i],'_max_median', sep='')
    query = paste(query,', median(', experiments_type[met],'_',measures_names[i],'_Q25) as ', experiments_type[met],'_',measures_names[i],'_Q25_median', sep='')
    query = paste(query,', median(', experiments_type[met],'_',measures_names[i],'_Q75) as ', experiments_type[met],'_',measures_names[i],'_Q75_median', sep='')

    measures_aux = c(measures_aux, paste(experiments_type[met],'_',measures_names[i],'_mean', sep='') )
    measures_aux = c(measures_aux, paste(experiments_type[met],'_',measures_names[i],'_median', sep='') )
    measures_aux = c(measures_aux, paste(experiments_type[met],'_',measures_names[i],'_min', sep='') )
    measures_aux = c(measures_aux, paste(experiments_type[met],'_',measures_names[i],'_max', sep='') )
    measures_aux = c(measures_aux, paste(experiments_type[met],'_',measures_names[i],'_Q25', sep='') )
    measures_aux = c(measures_aux, paste(experiments_type[met],'_',measures_names[i],'_Q75', sep='') )
  }
  query = paste(query,' from inner_measures group by generation', sep="")
  outter_measures = sqldf(query)

  quantiles = data.frame(inner_measures %>%
                           group_by(generation) %>%
                           summarize_at(vars(  measures_aux), funs(!!!p_funs)) )

  measures_averages_gens_2[[met]] = sqldf('select * from outter_measures inner join quantiles using (generation)')

}


for (met in 1:length(experiments_type))
{
  if(met==1){
    measures_averages_gens = measures_averages_gens_2[[1]]
  }else{
    measures_averages_gens = merge(measures_averages_gens, measures_averages_gens_2[[met]], all=TRUE, by = "generation")
  }
}




graph <- ggplot(data=measures_averages_gens, aes(x=generation))

for(m in 1:length(experiments_type)){


    graph = graph + geom_ribbon(aes_string(ymin=paste(experiments_type[m],'_',measures_names[i],'_median_Q25',sep=''),
                                           ymax=paste(experiments_type[m],'_',measures_names[i],'_median_Q75',sep='') ),
                                fill=experiments_type_colors[m], alpha=0.2, size=0)

    graph = graph + geom_line(aes_q(y = as.name(paste(experiments_type[m],'_',measures_names[i],'_median_median', sep='')) ,
                                    colour=methods_labels[m]), size=1)

}

graph = graph + coord_cartesian(ylim = c(20, 60))

graph = graph  +  labs(y="Survivors", x="Generation", title="")

graph = graph +   scale_color_manual(values=experiments_type_colors) + guides(colour = guide_legend(override.aes = list(size=10)))

graph = graph  + theme(legend.title= element_blank(), legend.position="bottom" ,  legend.text=element_text(size=25), axis.text=element_text(size=32), axis.title=element_text(size=30),
                       plot.subtitle=element_text(size=30 ), plot.title=element_text(size=30 ))

ggsave(paste( output_directory,'/survival.png',  sep=''), graph , device='png', height = 10, width = 10)




