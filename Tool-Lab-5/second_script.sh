#!/bin/bash --login  #login flag is super important to open conda on the compute node

# <SBATCH_headers_here>
#SBATCH --time=00:40:00

module load cuda/10.1
module load cudnn/7.6
conda activate venv

python3 <your_python_training_script_here> <your_args>
