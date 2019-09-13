#library(ggplot2)
#library(dplyr)
#library(viridis)
#ibrary(Interpol.T)
#library(lubridate)
#library(ggExtra)
#library(tidyr)
#library(trend)
#library(poweRlaw)
#library(plyr)
library(sqldf)
require('magick')

##### change paths/labels/params here #####


paths = c(
  'plane',
  'lava',
  'lavacost',
  'lavacostold',
  'lavaold'
)



base_directory <- paste('projects/revolve/experiments/karines_experiments/data/', sep='')

experiments = 30
gens = 100
pop = 100
num_top = 3

analysis = '1images'

##### change paths/labels/params here #####

output_directory = paste(base_directory, '/',analysis, sep='')


file <-file(paste(output_directory,'/best.txt',sep=''), open="w")

# for each method
for(m in 1:length(paths))
{
  
  # for each repetition
  for (exp in 1:experiments) 
    {
    
      input_directory  <-    paste(base_directory, paths[m],'_',exp,sep='')
      
      ids_gens = data.frame()
      list = strsplit(list.files(paste(input_directory, '/selectedpop_',gens-1, sep='')), ' ')
      for(geno in 1:pop)
      {
        genome =  data.frame(cbind(c(gens), c(strsplit(strsplit(list [[geno]],'_')[[1]][3],'.png')[[1]][1] )))
        names(genome)<-c('generation','robot_id')
        ids_gens = rbind(ids_gens,genome)
      }
  
      measures   =  read.table(paste(input_directory,"/all_measures.tsv", sep=''), header = TRUE)
      bests =  sqldf(paste("select robot_id, fitness from measures inner join ids_gens using (robot_id) order by fitness desc limit",num_top))
    
      for(b in 1:nrow(bests))
      {
        
         writeLines( paste(paths[m],'exp',exp,bests[b,'robot_id'] ,bests[b,'fitness'] ), file )
 
         phenotype= bests[b,'robot_id'] 
     
         patha = paste(base_directory,paths[m],'_',exp,"/selectedpop_",gens-1,sep="")
         
         body <- list.files(patha, paste("body_robot_",phenotype,".png$",sep=""), full.names = TRUE)
         body = image_read(body)
         body = image_border(image_background(body, "white"), "white", "20x33")
         
    
        if(b == 1)
        {
          bodies = body
        }else{
          bodies = c(bodies, body)
        }
      }
        
      side_by_side = image_append(bodies, stack=F)
      image_write(side_by_side, path = paste(output_directory,"/",paths[m],"_bodies_best_",exp,".pdf",sep=''), format = "pdf")
      
    }
}


close(file)
