#!/bin/bash
#SBATCH -p psych_day,psych_gpu,psych_scavenge,psych_week
#SBATCH --job-name=test_sl
#SBATCH --output=logs/%A_%a.out
#SBATCH --requeue
#SBATCH --time=24:00:00
#SBATCH --mem-per-cpu=90G
#SBATCH -n 4

set -e
cd /gpfs/milgram/project/turk-browne/projects/brainiak
. /gpfs/milgram/apps/hpc.rhel7/software/Python/Anaconda3/etc/profile.d/conda.sh
conda activate brainiak

#echo srun --mpi=pmi2 python3 -u /gpfs/milgram/project/turk-browne/projects/brainiak/examples/searchlight/kpTest/example_searchlight.py ${SLURM_ARRAY_TASK_ID}
#srun --mpi=pmi2 python3 -u /gpfs/milgram/project/turk-browne/projects/brainiak/examples/searchlight/kpTest/example_searchlight.py ${SLURM_ARRAY_TASK_ID}

echo mpirun -n 4 python3 -u /gpfs/milgram/project/turk-browne/projects/brainiak/examples/searchlight/kpTest/example_searchlight.py ${SLURM_ARRAY_TASK_ID}
mpirun -n 4 python3 -u /gpfs/milgram/project/turk-browne/projects/brainiak/examples/searchlight/kpTest/example_searchlight.py ${SLURM_ARRAY_TASK_ID}

echo "done"

#示例用法  sbatch --array=1-1 /gpfs/milgram/project/turk-browne/projects/brainiak/examples/searchlight/kpTest/example_searchlight.sh



##SBATCH --mem=30G
##SBATCH --time=24:00:00
##SBATCH --mem-per-cpu=300G
###SBATCH -n 4