from shutil import copyfile
encodings = ['baseline', 'plastic']
envs = ['plane','tilted5']
runs = 20

path='/storage/karine/journal2/'
to = '/home/karinemiras/Documents/plasticoding_baseline_data'
for en in encodings:
   for r in range(1, runs+1):
      for e in envs:
         path1 = path+en+'_big_'+str(r)+'/data_fullevolution/'+e+'/all_measures.tsv'
         copyfile(path1, to+'/'+en+'_'+str(r)+'_'+e+'_all_measures.tsv')
         path2 = path + en + '_big_' + str(r) + '/selectedpop_' + e + '/snapshots_ids.tsv'
         copyfile(path2, to + '/' + en + '_' + str(r) + '_' + e + '_snapshots_ids.tsv')
         print(path1,  to+'/'+en+'_'+str(r)+'_'+e+'/all_measures.tsv')
         print(path2, to + '/' + en + '_' + str(r) + '_' + e + 'snapshots_ids.tsv')


