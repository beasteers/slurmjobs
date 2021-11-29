# slurmjobs

[![pypi](https://badge.fury.io/py/slurmjobs.svg)](https://pypi.python.org/pypi/slurmjobs/)
![tests](https://github.com/beasteers/slurmjobs/actions/workflows/ci.yaml/badge.svg)
[![docs](https://readthedocs.org/projects/slurmjobs/badge/?version=latest)](http://slurmjobs.readthedocs.io/?badge=latest)
[![License](https://img.shields.io/pypi/l/slurmjobs.svg)](https://github.com/beasteers/slurmjobs/blob/main/LICENSE.md)


Automating Slurm job generation.

Generate a set of `.sbatch` files over a grid of parameters to be searched over. A run script is created which will submit all generated jobs as once.

You can also use `ShellBatch` which excludes the slurm/module references so you can test & run on your local machine or test server.

> NOTE: because NYU switched to Greene which now utilizes singularity, the previous workflow regarding loading modules is not as necessary. Therefore, I will likely be experimenting and changing how things are done to suit the new workflow. If you want to keep the old setup, pin to `<=0.1.2`. (Sorry I should have just did a `0.2` bump off the bat).

## Install

```bash
pip install slurmjobs
```

## Usage

```python
import slurmjobs

jobs = slurmjobs.Singularity(
    'python train.py', email='me@nyu.edu',
    template='''{% extends 'job.singularity.j2' %}
  
{% block main %}
echo "hi! I'm running right before the main command!"
echo "you can do initialization stuff here. but no pressure. it's completely optional."

{{ super() }}

echo "hi! I'm running right after the main command!"
{% endblock %}
    ''')

# generate jobs across parameter grid
run_script, job_paths = jobs.generate([
    ('model', ['AVE', 'AVOL']),
    ('audio_channels', [1, 2]),
], epochs=500)

slurmjobs.util.summary(run_script, job_paths)
```

Outputs:
```
Generated 12 job scripts:
     jobs/train/train,kernel_size-2,lr-0.0001,nb_stacks-1.sbatch
     jobs/train/train,kernel_size-2,lr-0.001,nb_stacks-1.sbatch
     jobs/train/train,kernel_size-2,lr-0.0001,nb_stacks-2.sbatch
     jobs/train/train,kernel_size-2,lr-0.001,nb_stacks-2.sbatch
     jobs/train/train,kernel_size-3,lr-0.0001,nb_stacks-1.sbatch
     jobs/train/train,kernel_size-3,lr-0.001,nb_stacks-1.sbatch
     jobs/train/train,kernel_size-3,lr-0.0001,nb_stacks-2.sbatch
     jobs/train/train,kernel_size-3,lr-0.001,nb_stacks-2.sbatch
     jobs/train/train,kernel_size-5,lr-0.0001,nb_stacks-1.sbatch
     jobs/train/train,kernel_size-5,lr-0.001,nb_stacks-1.sbatch
     jobs/train/train,kernel_size-5,lr-0.0001,nb_stacks-2.sbatch
     jobs/train/train,kernel_size-5,lr-0.001,nb_stacks-2.sbatch

To submit all jobs, run:
. jobs/train/run_train.sh
```

## Notes and Caveats
Basically, I built this package to address my own use cases:
  - python machine learning (with anaconda, tensorflow-gpu) in NYU HPC environment.

Previously, I had a bunch of defaults set - `n_gpus=1`, `modules=['cuda...']`, etc. Recently, I've made default behavior make as few assumptions as possible.

So if you don't specify a `conda_env`, anaconda won't be loaded. And if you don't specify any modules (with no `conda_env`), then you can operate on a system without `module load`.

I've added module aliases (because I can never remember the exact cuda versions that 1. works with my tf version, 2. are available on HPC, 3. that are compatible together). So specifying the module shorthand will load the modules to the right. (I haven't fully tested these across tf versions. lmk if there's an issue. getting tf+cuda running is always a nightmare.)
 - `cuda9`  => [`cudnn/9.0v7.3.0.29`, `cuda/9.0.176`] (tf 1.12)
 - `cuda10` => [`cuda/10.0.130`, `cudnn/10.0v7.4.2.24`] (tf 1.13, 1.14, 2.0)
 - `cuda10.1` => `cuda/10.1.105`, `cudnn/10.1v7.6.5.32`] (tf 2.1)

For more info about tensorflow version matching: https://www.tensorflow.org/install/source#tested_build_configurations

If you have different project requirements and/or suggestions about how to better generalize this, please submit an issue/pull request! I have limited experience with these systems, so I am unfamiliar with different environment configurations.

I designed this to be as customizable and extensible as possible, so I hope it's easy to make it work for your own use case. See [Customizing Behavior](docs/CUSTOMIZING.md) for tips.

----

## TODO
  - allow user to break run scripts into chunks
  - implement different defaults profiles? basic, gpu, etc.
  - add run / stop commands with job id tracking - simpler way? sbatch groups?
    - change run script: `sbatch --parseable asdf.sbatch >> run_id.sh`
    - run(): `os.system('. {}'.format(self.paths.run))`
    - stop(): `for l in open('run_ids.sh'): os.system('scancel {}'.format(l))`
    - stop_user(): `os.system('scancel -u')`
    - list jobs, get status/durations
  - any singularity helpers?
