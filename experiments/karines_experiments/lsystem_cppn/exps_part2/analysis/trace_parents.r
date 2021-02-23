library(sqldf)
require('magick')

base_directory <-paste('/storage/karine/lsystem_cppn/lsystem_cppn_2', sep='')

analysis = 'parents'
environment = 'plane'
experiments = c('hyperplasticodingrep_2', 'plasticodingrep_3')
max_gens = 5
base_gen = 59
examples = 100

output_directory = paste('/storage/karine/lsystem_cppn/consolidated_files','/',analysis ,sep='')
file <-file(paste(output_directory,'/trace.txt',sep=''), open="w")

for (exp in 1:length(experiments))
{

  genotypes_parents = read.table(paste(base_directory, experiments[exp], "data_fullevolution/genotypes_parents.txt", sep='/'), sep="\t")
  patha = paste(base_directory, experiments[exp], "data_fullevolution",environment, "phenotype_images", sep='/')

  list = strsplit(list.files(paste(base_directory, '/',experiments[exp], "/selectedpop_",environment,'/selectedpop_',base_gen, '',sep='')), ' ')
  # only body files
  list = list[1:(length(list)/2)]
  list = sample(list, examples)

  for (r in 1:examples)
  {

    robot_id = strsplit(strsplit(list [[r]],'_')[[1]][3],'.png')[[1]][1]
    current_robot_id = robot_id

    body = list.files(patha, paste("body_robot_",current_robot_id,".png$",sep=""), full.names = TRUE)
    body = image_read(body)
    body = image_scale(body, "100x100")
    body = image_border(image_background(body, "white" ), "green", "5x5")
    bodies = body

    parent1 = ''
    i = 0
    while ( !is.na(parent1) && i<max_gens)
    {
      genotype_parents = sqldf( paste("select * from genotypes_parents where V1='robot_'||", current_robot_id, sep='') )
      parent1 = strsplit(as.character(genotype_parents$V2), ' ')[[1]][1]

      print( paste(experiments[exp], 'robot',current_robot_id, 'has parent', parent1) )
      writeLines( paste(experiments[exp], 'robot',current_robot_id, 'has parent', parent1), file )

      body = list.files(patha, paste("body_robot_",parent1,".png$",sep=""), full.names = TRUE)
      body = image_read(body)
      body = image_scale(body, "100x100")
      body = image_border(image_background(body, "white" ), "transparent", "5x5")

      bodies = c(bodies, body)
      side_by_side = image_append(bodies, stack=F)

      current_robot_id = parent1
      i = i+1

    }

    image_write(side_by_side, path = paste(output_directory,"/",experiments[exp],"_robot_", robot_id,".png",sep=''), format = "png")

  }
}
close(file)