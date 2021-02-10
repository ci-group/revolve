library(ggplot2)
library(sqldf)
library(dplyr)
library(tidyr)
library(ggsignif)

base_directory <-paste('data', sep='')
base_directory <-paste('/storage/karine/lsystem_cppn/lsystem_cppn/', sep='')

experiments_type = c('hyperplasticoding',
                     'plasticoding')
runs = list(c(1:20),
            c(1:20))
experiments_type_colors = c('#EE8610',
                            '#009900')
analysis = 'analysis'
output_directory = paste(base_directory,'/',analysis ,sep='')

measures_all = NULL
for (exp in 1:length(experiments_type))
{
  for(run in runs[[exp]])
  {
    measures = read.table(paste(base_directory, paste(experiments_type[exp], '_',run,'/data_fullevolution',"/stability.txt", sep=''), sep='/'), header = FALSE, fill=TRUE)

    #measures   = read.table(paste(base_directory,"stability.txt", sep='/'), header = FALSE, fill=TRUE)
    if ( is.null(measures_all)){
      measures_all = measures
    }else{
      measures_all = rbind(measures_all, measures)
    }

  }
}

# removing rare cases of duplicity given redundancy in the extraction (only 7 out of 8007 were duplicated)
measures_all = sqldf("select V1,V2,V3,max(V4) as V4 from measures_all group by 1,2,3")

colnames(measures_all) <- c("method_run","eval", "id", "speed")

measures_all=measures_all %>%
  separate(method_run, c("method", "run"), "coding_")

measures_all=measures_all %>%
  separate(method, c("trash", "method"), "/lsystem_cppn/lsystem_cppn/")

measures_all = sqldf("select thirty.*,speed_sixty,  speed_sixty-speed_thirty as diff  from
        (select method, run, id, speed as speed_thirty from measures_all where eval='30') as thirty
          inner join
        (select method, run, id, speed as speed_sixty from measures_all where eval='60') as sixty
          where thirty.method=sixty.method and thirty.run=sixty.run and thirty.id=sixty.id")
measures_all = sqldf("select * from measures_all where diff is not NULL ")

measures_all = sqldf("select method, run, median(diff)*100 as avg_diff from measures_all group by 1, 2 ")


g1 <-  ggplot(data=measures_all, aes(x= method , y=avg_diff, color=method  )) +
  geom_boxplot(position = position_dodge(width=0.9),lwd=2,  outlier.size = 4) +
  labs( x="Method", y="Stability of Speed (cm/s)", title="")

g1 = g1 +  scale_color_manual(values=  experiments_type_colors  )

g1 = g1 + theme(legend.position="none" , text = element_text(size=50) ,
                plot.title=element_text(size=50),  axis.text=element_text(size=50),
                axis.title=element_text(size=55),
                axis.text.x = element_text(angle = 0, hjust = 0.9),
                plot.margin=margin(t = 0.5, r = 0.5, b = 0.5, l =  1.3, unit = "cm"))+
                stat_summary(fun = mean, geom="point" ,shape = 16,  size=11)
                #+scale_y_continuous( breaks = c(0, 0.33, 0.6, 1.3, 1, 1.5))

g1 = g1 + geom_signif( test="wilcox.test", size=1, textsize=18,
                       comparisons = list(c('hyperplasti','plasti'))
                       ,map_signif_level=c("***"=0.001,"**"=0.01, "*"=0.05)
                        )

ggsave(paste(output_directory,"/stability.pdf",sep = ""), g1, device = "pdf", height=18, width = 10)




