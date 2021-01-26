
library(sqldf)
require('magick')

##### change paths/labels/params here #####


paths = c('hyperplasticoding',
          'plasticoding' )

environments = list(
  c( 'plane') ,
  c( 'plane')
)

print(getwd())

colors = list( c( '#ffffff'),
               c('#ffffff') )

base_directory <- paste('../data/lsystem_cppn/', sep='')

runs = list( c(1:20), c(1:20))
gens = 150
pop = 100
num_top = 3
criteria = c('asc', 'desc')
analysis = 'analysis'

##### change paths/labels/params here #####


output_directory = paste(base_directory,analysis, sep='')


file <-file(paste(output_directory,'/best.txt',sep=''), open="w")

# for each method
for(m in 1:length(paths))
{
  # for each repetition
  for (exp in runs[[m]])
  {
    input_directory2  <-    paste(base_directory, paths[m],'_',exp, '/selectedpop_', sep='')
    
    ids_gens = data.frame()
    list = strsplit(list.files(paste(input_directory2, environments[[m]][1],'/selectedpop_',gens-1, sep='')), ' ')
    for(geno in 1:pop)
    {
      genome =  data.frame(cbind(c(gens-1), c(strsplit(strsplit(list [[geno]],'_')[[1]][3],'.png')[[1]][1] )))
      names(genome)<-c('generation','robot_id')
      ids_gens = rbind(ids_gens,genome)
    }
    measures   =  read.table(paste(base_directory, paths[m], '_', environments[[m]][1],'_', exp, "_snapshots_ids.tsv", sep=''), header = TRUE, fill=TRUE)
    measures$cons_fitness = as.numeric(measures$cons_fitness)
    measures$generation = as.character(measures$generation)
    measures$robot_id = as.character(measures$robot_id)


    # best and worst fit in gen
    for (crit in 1:length(criteria))
    {
        bests =  sqldf(paste("select robot_id, cons_fitness from measures inner join ids_gens using (robot_id, generation) order by cons_fitness ",criteria[crit],"limit",num_top))

        for(b in 1:nrow(bests))
        {

          writeLines( paste(paths[m],'exp',exp,bests[b,'robot_id'] , criteria[crit], bests[b,'cons_fitness'] ), file )
          print( paste(paths[m],'exp',exp,bests[b,'robot_id'] ,bests[b,'cons_fitness'] ))

          phenotype= bests[b,'robot_id']

          for (env in 1:length(environments[[m]]))
          {
            patha = paste(input_directory2, environments[[m]][env], "/selectedpop_",gens-1,sep="")

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
        image_write(side_by_side, path = paste(output_directory,"/",paths[m],'_', env_file_name,'_',criteria[crit], "_bodies_best_",exp,".png",sep=''), format = "png")
    }
  }
}


close(file)
