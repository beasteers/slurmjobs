# Sample

This will show you examples of the generated output.

```python
from slurmjobs import SlurmBatch

batch = SlurmBatch(
    'python train.py', email='me@something.com',
    conda_env='my_env', sbatch_dir='sample')

# generate scripts
run_script, job_paths = batch.generate([
    ('kernel_size', [2, 3, 5]),
    ('lr', [1e-4, 1e-3]),
], dataset='audioset')

```

#### Generated Files
```
$ ls sample
train/ # the job name
    run_train.sh # the batch run script - your entrypoint
    # the job scripts
    train,kernel_size-2,lr-0.0001.sbatch
    train,kernel_size-2,lr-0.001.sbatch
    train,kernel_size-3,lr-0.0001.sbatch
    train,kernel_size-3,lr-0.001.sbatch
    train,kernel_size-5,lr-0.0001.sbatch
    train,kernel_size-5,lr-0.001.sbatch
    slurm/ # where the slurm logs get output
```

#### Generated Job File: train,kernel_size-2,lr-0.0001.sbatch

```bash
#SBATCH --job-name=train,kernel_size-2,lr-0.0001
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:1
#SBATCH --time=
#SBATCH --mem=
#SBATCH --mail-type=ALL
#SBATCH --mail-user=me@something.com
#SBATCH --output=sample/train/slurm/slurm_%j__train,kernel_size-2,lr-0.0001.log
#SBATCH --time=7-0
#SBATCH --mem=48GB

#########################
#
# Job: train,kernel_size-2,lr-0.0001
#
#########################


##### Load Modules
module purge
    module load cudnn/9.0v7.3.0.29
    module load cuda/9.0.176



##### Setup Environment
# activate conda environment
module load anaconda3/5.3.1
    . deactivate
    source activate my_env



##### Run Command
cd .
# run script with arguments
python train.py --dataset='"audioset"' --kernel_size=2 --lr=0.0001 --job_id='"train,kernel_size-2,lr-0.0001"'
```

#### Generated Batch Script: run_train.sh

```bash

#########################
#
# Job Batch: train
# Params:
# {
#     "dataset": "audioset",
#     "kernel_size": [
#         2,
#         3,
#         5
#     ],
#     "lr": [
#         0.0001,
#         0.001
#     ]
# }
#
#########################



sbatch "sample/train/train,kernel_size-2,lr-0.0001.sbatch"
sbatch "sample/train/train,kernel_size-2,lr-0.001.sbatch"
sbatch "sample/train/train,kernel_size-3,lr-0.0001.sbatch"
sbatch "sample/train/train,kernel_size-3,lr-0.001.sbatch"
sbatch "sample/train/train,kernel_size-5,lr-0.0001.sbatch"
sbatch "sample/train/train,kernel_size-5,lr-0.001.sbatch"

```
