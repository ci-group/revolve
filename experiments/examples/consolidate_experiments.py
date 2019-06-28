import os

# set these variables according to your experiments #
dirpath = '../'
experiments_type = [
                    'default_experiment'
                    ]
runs = 1
# set these variables according to your experiments #

def build_headers(path):
    print(path + "/all_measures.txt")
    file_summary = open(path + "/all_measures.tsv", "w+")
    file_summary.write('robot_id\t')
    with open(path + '/data_fullevolution/descriptors/behavior_desc_robot_1.txt') as file:
        for line in file:
            measure, value = line.strip().split(' ')
            file_summary.write(measure+'\t')
    with open(path + '/data_fullevolution/descriptors/phenotype_desc_robot_1.txt') as file:
        for line in file:
            measure, value = line.strip().split(' ')
            file_summary.write(measure+'\t')
    file_summary.write('fitness\n')
    file_summary.close()

    file_summary = open(path + "/snapshots_ids.tsv", "w+")
    file_summary.write('generation\trobot_id\n')
    file_summary.close()

for exp in experiments_type:
    for run in range(1, runs+1):

        print(exp, run)
        path = dirpath + str(exp) + '_' + str(run)
        build_headers(path)

        file_summary = open(path + "/all_measures.tsv", "a")
        for r, d, f in os.walk(path+'/data_fullevolution/fitness'):
            for file in f:

                robot_id = file.split('.')[0].split('_')[-1]
                file_summary.write(robot_id+'\t')
                with open(path+'/data_fullevolution/descriptors/behavior_desc_robot_'+robot_id+'.txt') as file:
                    for line in file:
                        measure, value = line.strip().split(' ')
                        file_summary.write(value+'\t')

                with open(path+'/data_fullevolution/descriptors/phenotype_desc_robot_'+robot_id+'.txt') as file:
                    for line in file:
                        measure, value = line.strip().split(' ')
                        file_summary.write(value+'\t')

                file = open(path+'/data_fullevolution/fitness/fitness_robot_'+robot_id+'.txt', 'r')
                fitness = file.read()
                file_summary.write(fitness + '\n')
        file_summary.close()

        file_summary = open(path + "/snapshots_ids.tsv", "a")
        for r, d, f in os.walk(path):
            for dir in d:
                if 'selectedpop' in dir:
                    gen = dir.split('_')[1]
                    for r2, d2, f2 in os.walk(path + '/selectedpop_' + str(gen)):
                        for file in f2:
                            if 'body' in file:
                                id = file.split('.')[0].split('_')[-1]
                                file_summary.write(gen+'\t'+id+'\n')
        file_summary.close()