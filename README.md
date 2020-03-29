# slurmjobs
Automating Slurm job generation.

Generate a set of `.sbatch` files over a grid of parameters to be searched over. A run script is created which will submit all generated jobs as once.

## Install

```bash
pip install slurmjobs
```

## Usage

```python
from slurmjobs import SlurmBatch

batch = SlurmBatch(
    'python train.py',
    email='me@something.com',
    conda_env='my_env')

# generate jobs across parameter grid
run_script, job_paths = batch.generate([
    ('kernel_size', [2, 3, 5]),
    ('nb_stacks', [1, 2]),
    ('lr', [1e-4, 1e-3]),
], receptive_field=6)

print('I just generated', len(job_paths), 'job scripts:')
for p in job_paths:
    print('\t', p)
print()

print('To submit all jobs, run:')
print('.', run_script)
print()

```

Outputs:
```
I just generated 12 job scripts:
	 sbatch/train/train,kernel_size-2,lr-0.0001,nb_stacks-1.sbatch
	 sbatch/train/train,kernel_size-2,lr-0.001,nb_stacks-1.sbatch
	 sbatch/train/train,kernel_size-2,lr-0.0001,nb_stacks-2.sbatch
	 sbatch/train/train,kernel_size-2,lr-0.001,nb_stacks-2.sbatch
	 sbatch/train/train,kernel_size-3,lr-0.0001,nb_stacks-1.sbatch
	 sbatch/train/train,kernel_size-3,lr-0.001,nb_stacks-1.sbatch
	 sbatch/train/train,kernel_size-3,lr-0.0001,nb_stacks-2.sbatch
	 sbatch/train/train,kernel_size-3,lr-0.001,nb_stacks-2.sbatch
	 sbatch/train/train,kernel_size-5,lr-0.0001,nb_stacks-1.sbatch
	 sbatch/train/train,kernel_size-5,lr-0.001,nb_stacks-1.sbatch
	 sbatch/train/train,kernel_size-5,lr-0.0001,nb_stacks-2.sbatch
	 sbatch/train/train,kernel_size-5,lr-0.001,nb_stacks-2.sbatch

To submit all jobs, run:
. sbatch/train/run_train.sh
```

### Generated Examples

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


## TODO

 - add run / stop commands with job id tracking - need to test/verify
    - change run script: `sbatch --parseable asdf.sbatch >> run_id.sh`
    - run(): `os.system('. {}'.format(self.paths.run))`
    - stop(): `for l in open('run_ids.sh'): os.system('scancel {}'.format(l))`
    - stop_user(): `os.system('scancel -u')`
    - list jobs, get status/durations
 - allow user to break run scripts into chunks
 - right now the parameters are a bit precarious and are probably not good defaults in a general case. - implement different profiles? basic, gpu, etc.
    - how to extend parameters for a new class
