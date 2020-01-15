
library(sqldf)
require('magick')

##### change paths/labels/params here #####


paths = c( 'baseline','plastic')

environments = c( 'plane','tilted5')

base_directory <- paste('data/', sep='')

experiments = 30
gens = 100
pop = 100
num_top = 1

analysis = 'images'

##### change paths/labels/params here #####

output_directory = paste(base_directory,analysis, sep='')


file <-file(paste(output_directory,'/best.txt',sep=''), open="w")

# for each method
for(m in 1:length(paths))
{
    # for each repetition
    for (exp in 1:experiments) 
      {
  
        input_directory1  <-    paste(base_directory, paths[m],'_',exp, '/data_fullevolution/',environments[1],sep='')
        input_directory2  <-    paste(base_directory, paths[m],'_',exp, '/selectedpop_', sep='')
        
        ids_gens = data.frame()
        list = strsplit(list.files(paste(input_directory2, environments[1],'/selectedpop_',gens-1, sep='')), ' ')
        for(geno in 1:pop)
        {
          genome =  data.frame(cbind(c(gens), c(strsplit(strsplit(list [[geno]],'_')[[1]][3],'.png')[[1]][1] )))
          names(genome)<-c('generation','robot_id')
          ids_gens = rbind(ids_gens,genome)
        }
    
        measures   =  read.table(paste(input_directory1,"/all_measures.tsv", sep=''), header = TRUE)
        bests =  sqldf(paste("select robot_id, cons_fitness from measures inner join ids_gens using (robot_id) order by cons_fitness desc limit",num_top))
      
        for(b in 1:nrow(bests))
        {
          
           writeLines( paste(paths[m],'exp',exp,bests[b,'robot_id'] ,bests[b,'cons_fitness'] ), file )
          print( paste(paths[m],'exp',exp,bests[b,'robot_id'] ,bests[b,'cons_fitness'] ))
   
           phenotype= bests[b,'robot_id'] 
       
           for (env in 1:length(environments))
           {
               patha = paste(input_directory2, environments[env], "/selectedpop_",gens-1,sep="")
               
               body <- list.files(patha, paste("body_robot_",phenotype,".png$",sep=""), full.names = TRUE)
               body = image_read(body)
               body = image_scale(body, "100x100")
               body = image_border(image_background(body, "white"), "white", "5x5")
               
              if(b == 1 && env == 1)
              {
                bodies = body
              }else{
                bodies = c(bodies, body)
              }
          }
        }
          
        side_by_side = image_append(bodies, stack=F)
        image_write(side_by_side, path = paste(output_directory,"/",paths[m],'_', environments[env], "_bodies_best_",exp,".png",sep=''), format = "png")
        
    }
}


close(file)
