import os
import math
import pandas as pd
import numpy as np

# set these variables according to your experiments #

# run from karine_experiments
dirpath = 'data/lsystem_cppn/'


experiments_type = [
      'hyperplasticoding'#,
     # 'plasticoding'

]
environments = {
   'hyperplasticoding': ['plane']#,
   #'plasticoding': ['plane']

                 }

runs = range(1, 1+1)


for exp in experiments_type:

    for env in environments[exp]:

        for run in runs:

            all_measures = dirpath + exp + '_' + env + '_' + str(run) + "_all_measures.tsv"
            all_measures = pd.read_csv(all_measures, sep='\t')
            all_measures = all_measures.replace('None', np.nan)
            all_measures = all_measures.apply(pd.to_numeric)

            snapshots_ids = dirpath + exp + '_' + env + '_' + str(run) + "_snapshots_ids.tsv"
            snapshots_ids = pd.read_csv(snapshots_ids, sep='\t')
            snapshots_ids = snapshots_ids.replace('None', np.nan)
            snapshots_ids = snapshots_ids.apply(pd.to_numeric)

            print(all_measures.dtypes)
            print(all_measures)

            print(snapshots_ids.dtypes)
            print(snapshots_ids)
