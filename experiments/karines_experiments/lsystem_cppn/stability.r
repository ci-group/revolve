library(ggplot2)
library(sqldf)
library(dplyr)
library(tidyr)
library(ggsignif)

base_directory <-paste('data', sep='')

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


colnames(measures) <- c("method_run","eval", "id", "speed")

measures=measures %>%
  separate(method_run, c("method", "run"), "coding_")

measures=measures %>%
  separate(method, c("trash", "method"), "/lsystem_cppn/lsystem_cppn/")

measures = sqldf("select thirty.*,speed_sixty,  speed_sixty/speed_thirty as ratio from
        (select method, run, id, speed as speed_thirty from measures where eval='30') as thirty
          inner join
        (select id, speed as speed_sixty from measures where eval='60') as sixty
          where thirty.id=sixty.id")

measures = sqldf("select method, run, median(ratio) as avg_ratio from measures group by 1, 2 ")


g1 <-  ggplot(data=measures, aes(x= method , y=ratio, color=method  )) +
  geom_boxplot(position = position_dodge(width=0.9),lwd=2,  outlier.size = 4) +
  labs( x="Method", y="Stability ratio", title="")

g1 = g1 +  scale_color_manual(values=  experiments_type_colors  )

g1 = g1 + theme(legend.position="none" , text = element_text(size=50) ,
                plot.title=element_text(size=50),  axis.text=element_text(size=50),
                axis.title=element_text(size=55),
                axis.text.x = element_text(angle = 0, hjust = 0.9),
                plot.margin=margin(t = 0.5, r = 0.5, b = 0.5, l =  1.3, unit = "cm"))+
  stat_summary(fun.y = mean, geom="point" ,shape = 16,  size=11)
g1 = g1 + geom_signif( test="wilcox.test", size=1, textsize=18,
                       comparisons = c('plasti', 'hyperplasti'),
                       map_signif_level=c() )

ggsave(paste(output_directory,"/stability.pdf",sep = ""), g1, device = "pdf", height=18, width = 10)



