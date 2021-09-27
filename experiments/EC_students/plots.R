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

base_directory <- c(
  'data',  'data')

analysis = 'analysis_2'
output_directory = paste(base_directory[2],'/',analysis ,sep='')

experiments_type = c(  'evo_only_merge' ,
                       'evo_revdeknn'
                       
)
runs = list(
  c(1:10),
  c(1:10))
environments = list( c('plane'),
                     c('plane')
)

# methods are product of experiments_type VS environments and should be coupled with colors.
# make sure to define methods_labels in alphabetic order, and experiments_type accordingly
methods_labels = c( 
  
  'evolution only' ,
  'evolution+learning'
) # note that labels of Plane death and Tilted death are INVERTED on purpose, to fix the mistake done when naming the experiments.

experiments_type_colors = c(
  '#00BFFF', #deep skyblue
  #'#2a9df4', #blue
  '#9370db', #medium purple
  '#009900', #green
  '#009900', #green
  # '#00BFFF', #deep skyblue
  # '#80DAEB'  #medium sky blue
  
  #'#876044'  #brown
  # '#009900', #green
  # '#EE8610', #orange
  # '#7550ff', #purple 
)

ribbon_colors = c(
  '#00BFFF', #deep skyblue
  #'#2a9df4', #blue
  '#9370db' #medium purple
)

#aggregations = c('min', 'Q25','mean', 'median', 'Q75','max')
aggregations = c('mean', 'median','max')

gens = 30
pop = 100
num_heatmaps = 1

gens_box_comparisons = c(gens-1)

measures_names = c(
  'velocity',
  'displacement_velocity',
  'displacement_velocity_hill',
  'head_balance',
  'contact',
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
  'z_depth',
  'absolute_size',
  'sensors',
  'symmetry',
  'vertical_symmetry',
  'height_base_ratio',
  'base_density',
  'bottom_layer',
  'parents_1',
  'parents_2',
  'fitness',
  'fitness_before_learn'
)

measures_labels = c(
  'velocity (cm/s)',
  'displacement velocity (cm/s)',
  'displacement velocity hill (cm/s)',
  'head balance',
  'contact',
  'branching',
  'no of branching modules',
  'relative no of limbs',
  'extremities',
  'length of limbs',
  'extensiveness',
  'coverage',
  'no of joints',
  'no of hinges',
  'no of active hinges',
  'no of bricks',
  'no of touch sensors',
  'no of brick sensors',
  'proportion',
  'width',
  'height',
  'z depth',
  'absolute size',
  'no of sensors',
  'symmetry',
  'vertical symmetry',
  'ratio of height & base',
  'base density',
  'bottom layer',
  'parents_1',
  'parents_2',
  'fitness',
  'fitness before learning'
)


#' more_measures_names = c(
#'   # 'novelty',
#'   'novelty_pop',
#'   #'cons_fitness'
#' )
#' 
#' more_measures_labels = c(
#'   #'Novelty (+archive)',
#'   'Novelty',
#'   #'Number of slaves'
#' )

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
      measures   = read.table(paste(base_directory[exp],experiments_type[exp], run,"all_measures.tsv", sep='/'),
                              header = TRUE, fill=TRUE)
      
      for( m in 1:length(measures_names))
      {
        measures[measures_names[m]] = as.numeric(as.character(measures[[measures_names[m]]]))
      }
      
      snapshots   = read.table(paste(base_directory[exp],experiments_type[exp], run,"snapshots_ids.tsv", sep='/'),
                               header = TRUE, fill=TRUE)
      
      measures_snapshots = sqldf('select * from snapshots inner join measures using(robot_id) order by generation')
      
      measures_snapshots$run = run
      measures_snapshots$displacement_velocity_hill =   measures_snapshots$displacement_velocity_hill*100
      measures_snapshots$velocity =   measures_snapshots$velocity*100
      measures_snapshots$displacement_velocity =   measures_snapshots$displacement_velocity*100
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
measures_snapshots_all = sqldf("select * from measures_snapshots_all where fitness IS NOT NULL")

file_name=paste(base_directory[exp],"summary_2.csv",sep = '/')
write.csv(measures_snapshots_all,file_name)

# measures_names = c(measures_names, more_measures_names)
# measures_labels = c(measures_labels, more_measures_labels)

# for( m in 1:length(more_measures_names)){
#   measures_snapshots_all[more_measures_names[m]] = as.numeric(as.character(measures_snapshots_all[[more_measures_names[m]]]))
# }


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
  
  # file_name=paste(base_directory[exp],"inner_measures_2.csv",sep = '/')
  # write.csv(inner_measures,file_name)
  
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

# file_name=paste(base_directory[exp],"measure_averages_gens_2.csv",sep = '/')
# write.csv(measures_averages_gens,file_name)


all_na = colSums(is.na(measures_averages_gens)) == nrow(measures_averages_gens)
for (i in 1:length(measures_names))
{
  
  #  line plots
  
  for(a in 1:length(aggregations)){
    
    graph <- ggplot(data=measures_averages_gens, aes(x=generation))
    
    for(m in 1:length(methods)){
      
      is_all_na = all_na[paste(methods[m],'_',measures_names[i],'_', aggregations[a], '_median', sep='')]
      
      if (is_all_na == FALSE) {
        
        graph = graph + geom_ribbon(aes_string(ymin=paste(methods[m],'_',measures_names[i],'_', aggregations[a],'_Q25',sep=''),
                                               ymax=paste(methods[m],'_',measures_names[i],'_', aggregations[a],'_Q75',sep='') ),
                                    fill=ribbon_colors[m], alpha=0.2, size=0)
        
        graph = graph + geom_line(aes_q(y = as.name(paste(methods[m],'_',measures_names[i],'_', aggregations[a], '_median', sep='')) ,
                                        colour=paste(methods_labels[m], aggregations[a], sep='_')), size=1)
      }
    }
    
    
    
    # finding values for scaling
    max_y =  0
    
    
    if (max_y>0) {
      graph = graph + coord_cartesian(ylim = c(min_y, max_y))
    }
    graph = graph  +  labs(y=measures_labels[i], x="generation", title="")
    
    graph = graph +   scale_color_manual(values=experiments_type_colors, labels = c("evolution only", "evolution + learning"))
    graph = graph  + theme_bw()
    graph = graph  + theme(legend.position="top" ,  legend.text=element_text(size=25), 
                           #legend.background = element_rect(fill = "darkgray",color = NA),
                           legend.background = element_rect(color = "steelblue", linetype = "solid"),
                           axis.text=element_text(size=30), axis.title=element_text(size=30),
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
          geom_boxplot(position = position_dodge(width=0.5),lwd=2,  outlier.size = 2.5, width=0.4) +
          labs( 
            #x="Method", 
            x=NULL,
            y=measures_labels[i], 
            # title=str_to_title(aggregations[a])
          )
        
        g1 = g1 +  scale_color_manual(values=experiments_type_colors)
        g1 = g1 + theme_bw()
        g1 = g1 + theme(legend.position="none" , 
                        text = element_text(size=30) , #50
                        #plot.title=element_text(size=25),  #50
                        axis.text=element_text(size=30, color='black'),
                        #axis.text.x = element_text(angle = 20, hjust = 0.9),
                        plot.margin=margin(t = 0.5, r = 0.5, b = 0.5, l =  1.3, unit = "cm"))+
          stat_summary(fun.y = mean, geom="point" ,shape = 20,  size=8, color="cyan")
        
        
        
        # in this list, use the desired pairs names from methods_labels
        # comps = list(  c( 'base tilted', 'plastic tilted' ),
        #                c( 'base tilted', 'tilted' ),
        #                c( 'tilted', 'plastic tilted' )
        # )
        
        comps = list(methods_labels)
        
        
        if (max_y>0) {
          g1 = g1 + coord_cartesian(ylim = c(min_y, max_y))
          
        }
        
        g1 = g1 + geom_signif( test="wilcox.test", size=1, textsize=10, step_increase=0.15,
                               comparisons = comps,
                               # map_signif_level=c("***"=0.001,"**"=0.01, "*"=0.05)  )
                               map_signif_level=c( )  )
        
        if (out == 'full' || (out == 'filtered' &&  has_outliers == TRUE) ){
          ggsave(paste(output_directory,"/",measures_names[i],"_",gc,"_", aggregations[a],'_', out,"_boxes.pdf",sep = ""), g1, device = "pdf", height=10, width = 10)
        }
        
      }
      
    }
    
  }
  
}
