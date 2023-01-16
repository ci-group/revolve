#!/bin/bash
set -e
set -x

#export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

exp_folder="experiments/ballpit"
run=1
echo "Experimental folder: ${exp_folder}"
fr=0.1
density=10
lin_damp=1
ang_damp=1
for ball_r in 0.05 #0.015 0.02 0.025 0.035 0.05 0.1 0.2 0.5
  do
    exp_name="${fr}_${ball_r}"
    data_folder="${exp_folder}/data/${exp_name}/logs_${run}"
    mkdir -p ${data_folder}
    ls ${data_folder}
    echo ball_r:$ball_r > ${data_folder}/env_config.txt
    echo density:$density >> ${data_folder}/env_config.txt
    echo friction:$fr >> ${data_folder}/env_config.txt
    echo lin_damp:$lin_damp >> ${data_folder}/env_config.txt
    echo ang_damp:$ang_damp >> ${data_folder}/env_config.txt

    echo "Environment config:"
    cat ${data_folder}/env_config.txt
    ls -la ${data_folder}

    logfile="${data_folder}/experiment_${exp_name}.log"
    #logfile="/tmp/experiment_${exp_name}.log"
    touch $logfile
    nice -n19 \
    ./revolve.py \
        --manager=${exp_folder}/manager_direct_ballpit.py \
        --experiment-name ${exp_name} --run ${run} \
        --recovery-enabled True \
        --dbname "revolve_${exp_name}_${run}" \
        --dbusername matteo \
        --evaluation-time=60 \
        --grace-time=120 \
        2>&1 |tee $logfile

    pg_dump "revolve_${exp_name}_${run}" > "${data_folder}/revolve.sql"
  done
