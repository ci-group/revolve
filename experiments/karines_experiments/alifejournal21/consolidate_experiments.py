import os
import math
import sys
import glob

# set these variables according to your experiments #

# run from karine_experiments
dirpath = '/storage/karine/alifej2021/'
dirpath_write = '/storage/karine/alifej2021/'

experiments_type = ["scaffeq", "scaffeqinv", "scaffinc", "scaffincinv", "staticplane", "statictilted"]

environments = {
    'scaffeq': ['unique'],
    'scaffeqinv': ['unique'],
    'scaffinc': ['unique'],
    'scaffincinv': ['unique'],
    'staticplane': ['plane'],
    'statictilted': ['tilted5']
}

runs = {
  'scaffeq': range(1, 20+1),
  'scaffeqinv': range(1, 20+1),
  'scaffinc':  range(1, 20+1),
  'scaffincinv':  range(1, 20+1),
  'staticplane':  range(1, 20+1),
  'statictilted':  range(1, 20+1)
}

# set these variables according to your experiments #

def build_headers(path, path1):

    file_summary = open(path + "_snapshots_full.tsv", "w+")
    file_summary.write('generation\trobot_id\tfitness\tnovelty\tnovelty_pop\tcons_fitness\t')

    behavior_headers = []

    behavior_headers.append('velocity')
    file_summary.write(behavior_headers[-1]+'\t')
    behavior_headers.append('displacement_velocity')
    file_summary.write(behavior_headers[-1]+'\t')
    behavior_headers.append('displacement_velocity_hill')
    file_summary.write(behavior_headers[-1]+'\t')
    behavior_headers.append('head_balance')
    file_summary.write(behavior_headers[-1]+'\t')
    behavior_headers.append('contacts')
    file_summary.write(behavior_headers[-1]+'\t')

    phenotype_headers = []
    pt_file = path1 + '/descriptors/phenotype_desc_robot_1.txt'
    num_lines = sum(1 for line in open(pt_file))

    with open(pt_file) as file:
        for idx, line in enumerate(file):
            measure, value = line.strip().split(' ')
            phenotype_headers.append(measure)
            file_summary.write(measure)

            if idx < num_lines - 1:
                file_summary.write('\t')
            else:
                file_summary.write('\n')

    file_summary.close()

    return behavior_headers, phenotype_headers


for exp in experiments_type:
    for run in runs[exp]:

        path0 = dirpath + exp + '_' + str(run) + '/data_fullevolution'
        behavior_headers, phenotype_headers = build_headers(dirpath_write + exp + '_' + str(run), path0+'/'+environments[exp][0])

        path1 = path0 + '/' + environments[exp][0]
        path2 = dirpath + exp + '_' + str(run) + '/selectedpop_' + environments[exp][0]

        file_summary = open(dirpath_write + exp + '_' + str(run) + "_snapshots_full.tsv", "a")
        for r, d, f in os.walk(path2):
            for dir in d:
                if 'selectedpop' in dir:
                    gen = dir.split('_')[1]

                    for r2, d2, f2 in os.walk(path2 + '/selectedpop_' + str(gen)):
                        for file in f2:
                            if 'body' in file:
                                robot_id = file.split('.')[0].split('_')[-1]
                                file_summary.write(gen+'\t'+robot_id+'\t')
                                filen = path1 + '/fitness/fitness_' + gen + '_robot_' + robot_id + '.txt'
                                if os.path.isfile(filen):
                                    cf_file = open(filen, 'r')
                                    fitness = cf_file.read()
                                    file_summary.write(fitness + '\t')
                                else:
                                    file_summary.write('None' + '\t')

                                filen = path1 + '/novelty/novelty_'+gen+'_robot_'+robot_id+'.txt'
                                if os.path.isfile(filen):
                                    cf_file = open(filen, 'r')
                                    novelty = cf_file.read()
                                    file_summary.write(novelty + '\t')
                                else:
                                    file_summary.write('None' + '\t')

                                filen = path1 + '/novelty/novelty_pop_'+gen+'_robot_'+robot_id+'.txt'
                                if os.path.isfile(filen):
                                    cf_file = open(filen, 'r')
                                    novelty_pop = cf_file.read()
                                    file_summary.write(novelty_pop + '\t')
                                else:
                                    file_summary.write('None' + '\t')

                                filen = path0 + '/consolidated_fitness/consolidated_fitness_'+gen+'_robot_' + robot_id + '.txt'
                                if os.path.isfile(filen):
                                    cf_file = open(filen, 'r')
                                    cons_fitness = cf_file.read()
                                    file_summary.write(cons_fitness + '\t')
                                else:
                                    file_summary.write('None' + '\t')

                                if exp in ("staticplane", "statictilted"):
                                    bh_file = path1 + '/descriptors/behavior_desc_robot_' + robot_id + '.txt'
                                else:
                                    bh_file = path1 + '/descriptors/behavior_desc_' + gen + '_robot_' + robot_id + '.txt'
                                    # if it is an old parent being reevaluated, use the latest eval before that gen
                                    if not(os.path.isfile(bh_file)):
                                        behvs = sorted(glob.glob(path1+'/descriptors/behavior_*_robot_' + robot_id + '.txt'), key=os.path.getmtime)
                                        previous = []
                                        for file in behvs:
                                            if int(file.split('behavior_desc_')[1].split('_robot_')[0]) < int(gen):
                                                previous.append(file)
                                        bh_file = previous[-1]

                                if os.path.isfile(bh_file):
                                    if os.stat(bh_file).st_size > 0:
                                        with open(bh_file) as file:
                                            for line in file:
                                                if line != 'None':
                                                    measure, value = line.strip().split(' ')
                                                    file_summary.write(value + '\t')
                                                else:
                                                    for h in behavior_headers:
                                                        file_summary.write('None' + '\t')
                                    else:
                                        print(f'robot {robot_id} has empty behavior file!')
                                        for h in behavior_headers:
                                            file_summary.write('None' + '\t')
                                else:
                                    for h in behavior_headers:
                                        file_summary.write('None' + '\t')

                                pt_file = path1 + '/descriptors/phenotype_desc_robot_' + robot_id + '.txt'
                                if os.path.isfile(pt_file):
                                    num_lines = sum(1 for line in open(pt_file))
                                    with open(pt_file) as file:
                                        for idx, line in enumerate(file):

                                            measure, value = line.strip().split(' ')
                                            file_summary.write(value)

                                            if idx < num_lines - 1:
                                                file_summary.write('\t')
                                            else:
                                                file_summary.write('\n')
                                else:
                                    file_summary.write('None' + '\n')

        print('exp', exp, 'env', environments[exp][0], 'run', run)

        file_summary.close()

