
library(sqldf)
require('magick')

##### change paths/labels/params here #####


paths <- c('/storage/karine/baselines/plasticoding_seasons',
            '/storage/karine/early_death',
            '/storage/karine/early_death')


methods = c('plasticoding_seasons',
            'tilteddeath',
            'planedeath' )

methods_correct_label= c('plasticoding_seasons',
                         'planedeath',
                         'tilteddeath')# note that labels of Plane death and Tilted death are INVERTED



environments = list(
  c( 'tilted5') , c( 'tilted5'), c( 'tilted5')
)

colors = list( c( '#ffffff'), c('#ffffff') , c('#ffffff') )

base_directory <- paste('/storage/karine/early_death/', sep='')

analysis = 'analysis_tilted'

runs = list( c(1:20), c(1:20), c(1:20))
pop = 100
num_top = 1

gens = c(199)
criteria = c('desc')

##### change paths/labels/params here #####


output_directory = paste(base_directory,analysis, sep='')


file <-file(paste(output_directory,'/best.txt',sep=''), open="w")

# for each method
for(m in 1:length(paths))
{
  # for each repetition
  for (exp in runs[[m]])
  {
    input_directory2  <-    paste( paths[m], '/',methods[m], '_',exp, '/selectedpop_', sep='')
    
    # highest in criteria in gen
    for (g in 1:length(gens))
    {
      
      ids_gens = data.frame()
      list = strsplit(list.files(paste(input_directory2, environments[[m]][1],'/selectedpop_',gens[g], sep='')), ' ')
      for(geno in 1:pop)
      {
        genome =  data.frame(cbind(c(gens[g]), c(strsplit(strsplit(list [[geno]],'_')[[1]][3],'.png')[[1]][1] )))
        names(genome)<-c('generation','robot_id')
        ids_gens = rbind(ids_gens,genome)
      }
      measures   =  read.table(paste( paths[m],'/',methods[m], '_', environments[[m]][1],'_', exp, "_snapshots_ids.tsv", sep=''), header = TRUE, fill=TRUE)
      measures$cons_fitness = as.numeric(measures$cons_fitness)
      measures$generation = as.character(measures$generation)
      measures$robot_id = as.character(measures$robot_id)
      
      if (criteria[g] == 'random'){
        order_clause = ' random()' }else{
          order_clause = paste('cons_fitness', criteria[g])
        }
      
      bests =  sqldf(paste("select robot_id, cons_fitness from measures inner join ids_gens using (robot_id, generation) order by ",order_clause," limit",num_top))

      for(b in 1:nrow(bests))
      {
        sqldf("select robot_id, cons_fitness from measures inner join ids_gens using (robot_id, generation)  limit 1")
        writeLines( paste(methods_correct_label[m],'exp',exp,bests[b,'robot_id'] , gens[g], criteria[g], bests[b,'cons_fitness'] ), file )
        print( paste(methods_correct_label[m],'exp',exp,bests[b,'robot_id'] , gens[g], criteria[g], bests[b,'cons_fitness'] ))
        
        phenotype= bests[b,'robot_id']
        
        for (env in 1:length(environments[[m]]))
        {
          patha = paste(input_directory2, environments[[m]][env], "/selectedpop_",gens[g],sep="")
          
          body <- list.files(patha, paste("body_robot_",phenotype,".png$",sep=""), full.names = TRUE)
          body = image_read(body)
          body = image_scale(body, "100x100")
          #body = image_annotate(body, paste(round(bests[b,'cons_fitness']*100,2), '(cm/s)'), size = 20,    location = "+5+13" )
          
          body = image_border(image_background(body, colors[[m]][env] ), "transparent", "5x5")
          
          if(b == 1 && env == 1)
          {
            bodies = body
          }else{
            bodies = c(bodies, body)
          }
        }
      }
      
      if (length(environments[[m]])>1){
        env_file_name = 'seasons'
      }else{
        env_file_name = environments[[m]][env]
      }
      
      side_by_side = image_append(bodies, stack=F)
      image_write(side_by_side, path = paste(output_directory,"/",methods_correct_label[m],'_', env_file_name,'_',gens[g],'_',criteria[g], "_bodies_best_",exp,".png",sep=''), format = "png")
    }
  }
}


close(file)
