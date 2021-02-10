#set -e
#set -x

runs=20
experiments=("plane-death"  "tilted-death")
experiments2=("planedeath"  "tilteddeath")
exps=1



for i in $(seq $runs)
do
      for j in $(seq 0 $exps)
        do

       #    mv /storage/karine/early_death/"${experiments[j]}_${i}"_all_measures.tsv /storage/karine/early_death/"${experiments2[j]}_${i}"_all_measures.tsv
       #     mv /storage/karine/early_death/"${experiments[j]}_${i}"_snapshots_ids.tsv /storage/karine/early_death/"${experiments2[j]}_${i}"_snapshots_ids.tsv
       # mv /storage/karine/early_death/"${experiments[j]}_${i}".log /storage/karine/early_death/"${experiments2[j]}_${i}".log



        #     mv /storage/karine/early_death/"${experiments[j]}_${i}" /storage/karine/early_death/"${experiments2[j]}_${i}"

    done

done