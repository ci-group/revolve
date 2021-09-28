library(sqldf)
require('magick')

##### change paths/labels/params here #####


paths = c(
          'plasticodingscaffolding_inc_inv',
          'plasticodingscaffolding_inv' )

environments = list(
  c('tilted1', 'plane', 'plane'),
  c('tilted1', 'plane', 'plane')
)

# transitions between once season and another
inc_seq   = c(69, 70, 99)
equal_seq = c(84, 85, 99)

seqs = list(
  inc_seq,
  equal_seq
)

colors = list(
               c('#ffffff'),
               c('#ffffff'))

base_directory <- paste('jim/', sep='')
base_directory2 <-paste('karine/alife2021/', sep='')

analysis = 'analysis/2dseq'

runs = list(c(1:9), c(1:10))
pop = 100
top = 1

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

      bests =  sqldf(paste("select robot_id, cons_fitness from measures inner join ids_gens using (robot_id, generation) order by random() limit ", top))
      
      for(b in 1:nrow(bests))
      {
        sqldf("select robot_id, cons_fitness from measures inner join ids_gens using (robot_id, generation)  limit 1")
        writeLines( paste(paths[m],'exp',exp,bests[b,'robot_id'] , g, bests[b,'cons_fitness'] ), file )
        print( paste(paths[m],'exp',exp,'robot',bests[b,'robot_id'] ,'gen', g, b,bests[b,'cons_fitness'] ))
        
        phenotype= bests[b,'robot_id']
    
        patha = paste(input_directory, environments[[m]][envn], "/selectedpop_",g,sep="")
        
        body <- list.files(patha, paste("body_robot_",phenotype,".png$",sep=""), full.names = TRUE)
        body = image_read(body)
        body = image_scale(body, "100x100")
    
        body = image_border(image_background(body, colors[[m]][1] ), "transparent", "5x5")
        
        if(b==1 && envn == 1)
        {
          bodies = body
        }else{
          bodies = c(bodies, body)
        }
   
      }
    }
    
    side_by_side = image_append(bodies, stack=F)
    image_write(side_by_side, path = paste(output_directory,"/",paths[m], "_bodies_seq_",exp,".png",sep=''), format = "png")
    
 
  }
}


close(file)
