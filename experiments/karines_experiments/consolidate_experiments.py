import os


# set these variables according to your experiments #
dirpath = 'data'
experiments_type = [
                    'plane',
                    'lava'
                    ]
runs = 10
# set these variables according to your experiments #


def build_headers(path):

    print(path + "/all_measures.txt")
    file_summary = open(path + "/all_measures.tsv", "w+")
    file_summary.write('robot_id\t')

    behavior_headers = []
    with open(path + '/data_fullevolution/descriptors/behavior_desc_robot_1.txt') as file:
        for line in file:
            measure, value = line.strip().split(' ')
            behavior_headers.append(measure)
            file_summary.write(measure+'\t')

    phenotype_headers = []
    with open(path + '/data_fullevolution/descriptors/phenotype_desc_robot_1.txt') as file:
        for line in file:
            measure, value = line.strip().split(' ')
            phenotype_headers.append(measure)
            file_summary.write(measure+'\t')
    file_summary.write('fitness\n')
    file_summary.close()

    file_summary = open(path + "/snapshots_ids.tsv", "w+")
    file_summary.write('generation\trobot_id\n')
    file_summary.close()

    return behavior_headers, phenotype_headers


for exp in experiments_type:
    for run in range(1, runs+1):

        print(exp, run)
        path = os.path.join(dirpath, str(exp), str(run))
        behavior_headers, phenotype_headers = build_headers(path)

        file_summary = open(path + "/all_measures.tsv", "a")
        for r, d, f in os.walk(path+'/data_fullevolution/fitness'):
            for file in f:

                robot_id = file.split('.')[0].split('_')[-1]
                file_summary.write(robot_id+'\t')

                bh_file = path+'/data_fullevolution/descriptors/behavior_desc_robot_'+robot_id+'.txt'
                if os.path.isfile(bh_file):
                    with open(bh_file) as file:
                        for line in file:
                            measure, value = line.strip().split(' ')
                            file_summary.write(value+'\t')
                else:
                    for h in behavior_headers:
                        file_summary.write('None'+'\t')

                pt_file = path+'/data_fullevolution/descriptors/phenotype_desc_robot_'+robot_id+'.txt'
                if os.path.isfile(pt_file):
                    with open(pt_file) as file:
                        for line in file:
                            measure, value = line.strip().split(' ')
                            file_summary.write(value+'\t')
                else:
                    for h in phenotype_headers:
                        file_summary.write('None'+'\t')

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