#!/bin/bash --login

#SBATCH --time=00:40:00
#SBATCH --ntasks=1   # number of processor cores (i.e. tasks)
#SBATCH --nodes=1   # number of nodes
#SBATCH --gpus=1
#SBATCH --mem-per-cpu=16384M   # memory per CPU core
#SBATCH -J "cs280finetune"   # job name
#SBATCH --mail-user=jay.orten@gmail.com   # email address
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL

module load cuda/10.1
module load cudnn/7.6
conda activate venv

python3 ./model_script.py $1 $2 $3 $4 $5 > ./results/$1_$2_$3_$4_$5.txt
