library(sqldf)
require('magick')

##### change paths/labels/params here #####


paths = c('plasticodingscaffolding2_equal',
          'static_plane',
          'static_tilted',
          'plasticodingscaffolding_inv' )

environments = list(
  c('tilted1', 'tilted2', 'tilted3', 'tilted4', 'tilted5', 'tilted5'),
  c('plane','plane','plane','plane','plane', 'plane'),
  c('tilted5','tilted5','tilted5','tilted5','tilted5', 'tilted5'),
  c('tilted4', 'tilted3', 'tilted2', 'tilted1', 'plane', 'plane')
)

seqs = list(
  c(17, 34, 51, 68, 85, 99),
  c(17, 34, 51, 68, 85, 99),
  c(17, 34, 51, 68, 85, 99),
  c(17, 34, 51, 68, 85, 99)
)

colors = list( c('#ffffff'),
               c('#ffffff'),
               c('#ffffff'),
               c('#ffffff'))

base_directory <- paste('jim/', sep='')
base_directory2 <-paste('karine/alife2021/', sep='')

analysis = 'analysis/2dseqbest2'

runs = list( c(1:8), c(1:10), c(1:10), c(1:10))
pop = 100

criteria = c('desc', 'desc', 'desc', 'desc')

##### change paths/labels/params here #####


output_directory = paste(base_directory2, analysis, sep='')

file <- file(paste(output_directory,'/best.txt',sep=''), open="w")

# for each method
for(m in 1:length(paths))
{
  # for each repetition
  for (exp in runs[[m]])
  {
    input_directory  <-    paste(base_directory, paths[m],'_',exp, '/selectedpop_', sep='')
    
    envn=0
    for (g in seqs[[m]])
    {
      envn=envn+1
      
      ids_gens = data.frame()
      list = strsplit(list.files(paste(input_directory, environments[[m]][envn],'/selectedpop_', g, sep='')), ' ')
      for(geno in 1:pop)
      {
        genome =  data.frame(cbind(c(g), c(strsplit(strsplit(list [[geno]],'_')[[1]][3],'.png')[[1]][1] )))
        names(genome)<-c('generation','robot_id')
        ids_gens = rbind(ids_gens,genome)
      }
      measures   =  read.table(paste(base_directory2, paths[m], '_', exp, "_snapshots_full.tsv", sep=''), header = TRUE, fill=TRUE)
      measures$cons_fitness = as.numeric(measures$cons_fitness)
      measures$generation = as.character(measures$generation)
      measures$robot_id = as.character(measures$robot_id)

      bests =  sqldf(paste("select robot_id, cons_fitness from measures inner join ids_gens using (robot_id, generation) order by cons_fitness desc limit 1"))
      
      sqldf("select robot_id, cons_fitness from measures inner join ids_gens using (robot_id, generation)  limit 1")
      writeLines( paste(paths[m],'exp',exp,bests[1,'robot_id'] , g, 'desc', bests[1,'cons_fitness'] ), file )
      print( paste(paths[m],'exp',exp,bests[1,'robot_id'] , g, 'desc', bests[1,'cons_fitness'] ))
      
      phenotype= bests[1,'robot_id']
  
      patha = paste(input_directory, environments[[m]][envn], "/selectedpop_",g,sep="")
      
      body <- list.files(patha, paste("body_robot_",phenotype,".png$",sep=""), full.names = TRUE)
      body = image_read(body)
      body = image_scale(body, "100x100")
  
      body = image_border(image_background(body, colors[[m]][1] ), "transparent", "5x5")
      
      if(envn == 1)
      {
        bodies = body
      }else{
        bodies = c(bodies, body)
      }
      
    }
    
    side_by_side = image_append(bodies, stack=F)
    image_write(side_by_side, path = paste(output_directory,"/",paths[m], "_bodies_best_",exp,".png",sep=''), format = "png")
    
  }
}


close(file)
