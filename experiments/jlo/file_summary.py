import os

# set these variables according to your experiments #
dirpath = 'data'
experiments_type = [
    'evo_revdeknn'
]
runs = 5


# set these variables according to your experiments #


def build_headers(path):
    # print(path + "/all_measures.txt")
    file_summary = open(path + "/all_measures.tsv", "w+")
    file_summary.write('robot_id\t')

    behavior_headers = []
    with open(path + '/data_fullevolution/descriptors/behavioural/behavior_desc_1.txt') as file:
        for line in file:

            # print(file)
            # print(line)
            if (' ' in line.strip()):
                measure, value = line.strip().split(' ')
                behavior_headers.append(measure)
                file_summary.write(measure + '\t')
            else:
                file_summary.write('\t')
    # behavior_headers = []
    # behavior_headers.append('velocity')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('displacement_velocity')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('displacement_velocity_hill')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('head_balance')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('contacts')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('gaitAngleErr')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('Avgstepsize')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('SumArea')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('MeanHeadDeviation')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('DisplacementSum')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('x_axis_displacement')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('displacement_full_avg')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('gaitAngleErrorCumulative')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('EffectiveMovement')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('DifFromIdealMovement')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('DifFromIdealMovementX')
    # file_summary.write(behavior_headers[-1] + '\t')
    # behavior_headers.append('DifFromIdealMovementY')
    # file_summary.write(behavior_headers[-1] + '\t')

    # phenotype_headers = []
    # with open(path + '/data_fullevolution/descriptors/phenotype_desc_1.txt') as file:
    #     for line in file:
    #         measure, value = line.strip().split(' ')
    #         phenotype_headers.append(measure)
    #         file_summary.write(measure+'\t')

    phenotype_headers = []
    phenotype_headers.append('branching')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('branching_modules_count')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('limbs')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('extremities')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('length_of_limbs')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('extensiveness')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('coverage')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('joints')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('hinge_count')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('active_hinges_count')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('brick_count')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('touch_sensor_count')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('brick_sensor_count')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('proportion')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('width')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('height')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('z_depth')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('absolute_size')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('sensors')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('symmetry')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('vertical_symmetry')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('height_base_ratio')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('base_density')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('bottom_layer')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('parents_1')
    file_summary.write(phenotype_headers[-1] + '\t')
    phenotype_headers.append('parents_2')
    file_summary.write(phenotype_headers[-1] + '\t')

    file_summary.write('fitness\t')
    file_summary.write('fitness_before_learn\n')
    file_summary.close()

    file_summary = open(path + "/snapshots_ids.tsv", "w+")
    file_summary.write('generation\trobot_id\n')
    file_summary.close()

    return behavior_headers, phenotype_headers


for exp in experiments_type:
    for run in range(1, runs + 1):

        # print(exp, run)
        path = os.path.join(dirpath, str(exp), str(run))
        behavior_headers, phenotype_headers = build_headers(path)

        file_summary = open(path + "/all_measures.tsv", "a")
        for r, d, f in os.walk(path + '/data_fullevolution/genotypes'):
            for file in f:

                robot_id = file.split('.')[0].split('_')[-1]
                file_summary.write(robot_id + '\t')

                bh_file = path + '/data_fullevolution/descriptors/behavioural/behavior_desc_' + robot_id + '.txt'
                if os.path.isfile(bh_file):
                    with open(bh_file) as file:
                        for line in file:
                            # print(bh_file)
                            # print(line)
                            if (' ' in line.strip()):
                                measure, value = line.strip().split(' ')
                                file_summary.write(value + '\t')
                            else:
                                file_summary.write('\t')

                else:
                    for h in behavior_headers:
                        file_summary.write('None' + '\t')

                pt_file = path + '/data_fullevolution/descriptors/phenotype_desc_' + robot_id + '.txt'
                if os.path.isfile(pt_file):
                    with open(pt_file) as file:
                        for line in file:
                            measure, value = line.strip().split(' ')
                            if measure in phenotype_headers:
                                file_summary.write(value + '\t')
                else:
                    for h in phenotype_headers:
                        file_summary.write('None' + '\t')

                kt_file = path + '/data_fullevolution/phylogeny/parents_' + robot_id + '.txt'
                if os.path.isfile(kt_file):
                    with open(kt_file) as file:
                        for line in file:
                            measure, value = line.strip().split(':')
                            if measure + '_1' in phenotype_headers:
                                file_summary.write(value.split(',')[0] + '\t')

                else:
                    for h in phenotype_headers:
                        file_summary.write('None' + '\t')

                dt_file = path + '/data_fullevolution/phylogeny/parents_' + robot_id + '.txt'
                if os.path.isfile(dt_file):
                    with open(dt_file) as file:
                        for line in file:
                            measure, value = line.strip().split(':')
                            if measure + '_2' in phenotype_headers:
                                file_summary.write(value.split(',')[-1] + '\t')

                else:
                    for h in phenotype_headers:
                        file_summary.write('None' + '\t')


                fitness_file = path + '/data_fullevolution/fitness/fitness_robot_' + robot_id + '.txt'
                if os.path.isfile(fitness_file):
                    with open(fitness_file) as file:
                        fitness = file.read()
                        file_summary.write(fitness + '\t')
                else:
                    file_summary.write('0' + '\t')

                fb_file = path+'/data_fullevolution/fitness/fitness_robot_'+robot_id+'_revdeknn_9.txt'
                if os.path.isfile(fb_file):
                    with open(fb_file) as file:
                        fitness_before_learn = file.read()
                        file_summary.write(fitness_before_learn + '\n')
                else:
                    file_summary.write('0' + '\n')

        file_summary.close()

        file_summary = open(path + "/snapshots_ids.tsv", "a")
        for r, d, f in os.walk(path + '/generations'):
            for dir in d:
                if 'generation' in dir:
                    gen = dir.split('_')[1]
                    for r2, d2, f2 in os.walk(path + '/generations/generation_' + str(gen)):
                        for file in f2:
                            if 'body' in file:
                                id = file.split('.')[0].split('_')[1]
                                # print(id)
                                file_summary.write(gen + '\t' + id + '\n')
        file_summary.close()
