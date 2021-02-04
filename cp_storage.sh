set -e
set -x

runs=(14 15 16 17 18 19 20)
  for experiment in "${runs[@]}"
do

  cp -r experiments/karines_experiments/data/early_death/plane-death_$experiment;
   cp plane-death_$experiment.log  /storage/karine/early_death;
  cp -r experiments/karines_experiments/data/early_death/tilted-death_$experiment  /storage/karine/early_death;
   cp tilted-death_$experiment.log  /storage/karine/early_death;

done