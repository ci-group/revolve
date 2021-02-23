library(ggplot2)
library(sqldf)
library(plyr)
require('magick')


####  this example of parameterization compares multiple types of experiments using one particular season ###

#### CHANGE THE PARAMETERS HERE ####

base_directory <-paste('/storage/karine/lsystem_cppn/consolidated_files', sep='')
base_directory2 <-paste('/storage/karine/lsystem_cppn/lsystem_cppn_2', sep='')

analysis = 'cubes'
output_directory = paste(base_directory,'/',analysis ,sep='')

experiments_type = c('plasticodingrep', 'hyperplasticodingrep')
runs = list(c(1:20), c(1:20))
environments = list( c( 'plane'),c( 'plane') )

max_gen = 49
offspringsize = 50
max_top_bins = 10

measures_names = c(
  'branching',
  'limbs',
  'length_of_limbs',
  'coverage',
  'joints',
  'proportion',
  'symmetry'
)


#### CHANGE THE PARAMETERS HERE ####


for (exp in 1:length(experiments_type))
{

  for(run in runs[[exp]])
  {

      for (env in 1:length(environments[[exp]]))
      {
        measures   = read.table(paste(base_directory,paste(experiments_type[exp], environments[[exp]][env], run,"all_measures.tsv", sep='_'), sep='/'),
                                header = TRUE, fill=TRUE)

        for( m in 1:length(measures_names))
        {
          measures[measures_names[m]] = as.numeric(as.character(measures[[measures_names[m]]]))
        }

        measures$run = run
        measures$run = as.factor(measures$run)

        # creates bins of the cube
        aux_query = ''
        for (m in measures_names){
          aux_query = paste(aux_query, " '|' || replace(cast(round(", m, "*100, 0) as text), '.0', '') || ", sep='')
        }

        # only robots from the stage of searching for novelty
        bins_robots = sqldf(paste("select robot_id,",aux_query," '|'  as bin from measures where run=",run," and robot_id<=", max_gen*offspringsize+(offspringsize*2)))
        bins = sqldf("select bin,count(*) as nrobots from bins_robots group by 1 order by nrobots desc")
        seqid = rep(1: nrow(bins))
        bins = cbind(seqid, bins)

        graph <- ggplot(data=bins, aes(x = seqid, y = nrobots) ) +
          geom_bar(stat="identity" ) + xlab("Cubes") + ylab("Frequency")+
          theme(title=element_text(size=40),  axis.text=element_text(size=38),axis.title=element_text(size=47), legend.text=element_text(size=40) )+
          coord_cartesian(ylim=c(0,100), xlim=c(0,300))

        ggsave(paste(output_directory,"/",experiments_type[exp],'_',run,"_cubes.pdf",sep = ""), graph, device = "pdf", height=11, width = 14)


        bins_robots = sqldf("select bins.*, bins_robots.robot_id from bins_robots inner join bins where bins_robots.bin==bins.bin")
        top_bins = sqldf(paste("select * from bins limit ", max_top_bins) )
        top_bins_robots =  sqldf(paste("select * from bins_robots where bin in (select bin from top_bins) order by seqid, robot_id") )
        # max is an arbritrary chooice, when any robot would be fine to choose a representative for the bin
        top_bins_robots = sqldf(paste("select  seqid, max(robot_id) as robot_id from top_bins_robots group by 1  order by seqid") )
        for (r in 1:nrow(top_bins_robots))
        {

          patha = paste(base_directory2, '/',experiments_type[exp],'_',run, "/data_fullevolution/", environments[[exp]][env], "/phenotype_images", sep='')
          body = list.files(patha, paste("body_robot_", top_bins_robots$robot_id[r],".png",sep=""), full.names = TRUE)
          body = image_read(body)
          body = image_scale(body, "100x100")
          body = image_border(image_background(body, "white" ), "transparent", "5x5")

          if(top_bins_robots$seqid[r] == 1)
          {
            bodies = body
          }else{
            bodies = c(bodies, body)
          }

        }

        side_by_side = image_append(bodies, stack=F)
        image_write(side_by_side, path = paste(output_directory,"/",experiments_type[exp],'_',run,"_robots_cubes.png",sep=''), format = "png")



      }
    }
}



