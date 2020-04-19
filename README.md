# slurmjobs
Automating Slurm job generation.

Generate a set of `.sbatch` files over a grid of parameters to be searched over. A run script is created which will submit all generated jobs as once.

You can also use `ShellBatch` which removes the slurm/module references so you can test & run on your local machine or test server.

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

# ** everything was generated ** - now let's see the outputted paths.

print('I just generated', len(job_paths), 'job scripts:')
for p in job_paths:
    print('\t', p)
print()

print('To submit all jobs, run:')
print('.', run_script)
print()

print('An example command:\n\t',
  batch.make_command(kernel_size=2, nb_stacks=1))

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

An example command:
   python train.py --kernel-size=2 --nb_stacks=1
```

See [below](#sample) for sample files.

## Notes and Caveats
Basically, I built this package to address my own use cases:
  - python machine learning (with anaconda) in NYU HPC environment.

### Defaults

The default assumptions made are:
  - slurm:
      - module command exists
      - modules `cudnn/9.0v7.3.0.29` & `cuda/9.0.176` exist and are the right cuda version (???)
	  - using a conda environment
  - shell:
    - using a conda environment

I'm not sure how common `module` is, so:
 - To disable `module` set `modules=None`.
 - To pass your own modules set `modules=['mymodule/5.4.3.2', ...]`
 - To disable any and all conda references, set `conda_env=None`.

> I wrote this to reduce the amount of code that I need to write to generate jobs at NYU. If you have different project requirements and/or suggestions about how to better generalize this, please submit an issue/pull request! I have limited experience these systems, so I am unaware of different environment configurations.

### Argument Formatting

Currently we support:
 - `Fire`: (e.g. `python script.py some_func 5 10 --asdf=[1,2,3] --zxcv={a:5,b:7}`)
 - `argparse`: (e.g. `python script.py some_action -a -b --asdf 1 2 3`)
 - `sacred`: (e.g. `python script.py with some_cfg asdf=[1,2,3] a=True`)
 - any thing else? lmk and look at `slurmjobs.args.Argument` and subclasses for examples on how to create a new formatter.

Fire is the default. You can set your own parser using:
`SlurmBatch(cli='argparse')`.

## Customizing behavior

The main things you can customize:
 - the config / default config
 - the script templates (individual job, and batch run script)
 - the directory structure
 - argument formatter

### Config

You can customize in 2 ways
```python
from slurmjobs import SlurmBatch

CMD = 'python train.py'

# ad-hoc config - disable conda and any `module` commands
batch = SlurmBatch(CMD, conda_env=None, modules=None)

# or something more permanent:
class MySlurmBatch(SlurmBatch):
    default_params = dict(
        SlurmBatch.default_params,
        conda_env=None,
        modules=None)

batch = MySlurmBatch(CMD)
```

### Script Templates
Just pass a jinja template as `job_tpl` and/or `run_tpl`.

```python
from slurmjobs import SlurmBatch

CMD = 'python train.py'

# pass in your custom template
batch = SlurmBatch(CMD, my_custom_thing='are you ready??')

batch.generate(job_tpl='''
echo {{ my_custom_thing }}
something {{ command }} &> /dev/null &
''')
```

### Directory Structure

The directories are defined using a package called [pathtree](https://github.com/beasteers/pathtree) (`path-tree` on pip). See docs for more info.

Here's an example:
```python
def get_paths(self, name, root_dir='jobs', **kw):
      paths = pathtree.tree(root_dir, {'{name}': {
          '': 'batch_dir',
          '{job_name}.sbatch': 'job',
          'run_{name}.sh': 'run',
          'slurm/slurm_%j__{job_name}.log': 'output',
      }}).update(name=name, **kw)
      return paths
```

- `batch_dir`: this should point to the complete batch directory for the proposed set of jobs.
   -  if `backup=True`, any existing folder will be renamed to `{ batch_dir}_{i}`
   - if `backup=False`, any existing folder and contained files will be removed
   - if `batch_dir` is omitted, neither will be performed, but you run the risk of having two batches merged into one which makes things messy.
- `job`: this is the individual job file. runs a single job instance.
- `run`: this is the batch run script. it is used to run/submit all job files.
- `output`: this is the std out/err file for each job. You can omit this if you add your own template without a reference to `paths.output`.

### Argument Formatter

You can define your own formatter by subclassing `Argument`. If your class name ends with `'Argument'`, you can omit that when

Example:
```python
import slurmjobs
class MyCustomArgument(slurmjobs.args.Argument):
  @classmethod
  def format_arg(cls, k, v=None):
    if v is not None:
      return str(k)
    return '{}@{}'.format(k, cls.format_value(v)) # size@10

batch = slurmjobs.SlurmBatch('echo', cli='mycustom')
```

----
## Sample

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
