#set -e
#set -x

runs=20
experiments=("hyperplasticoding-rep"  "plasticoding-rep")
experiments2=("hyperplasticodingrep"  "plasticodingrep")
exps=1



for i in $(seq $runs)
do
      for j in $(seq 0 $exps)
        do



             mv  /storage/karine/lsystem_cppn/lsystem_cppn_2/"${experiments[j]}_${i}"  /storage/karine/lsystem_cppn/lsystem_cppn_2/"${experiments2[j]}_${i}"

    done

done