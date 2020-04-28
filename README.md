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
import slurmjobs

batch = slurmjobs.SlurmBatch(
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

slurmjobs.util.summary(run_script, job_paths)

print('An example command:\n\t',
  batch.make_command(kernel_size=2, nb_stacks=1))

```

Outputs:
```
Generated 12 job scripts:
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

### More:
 - [Customizing Behavior](docs/CUSTOMIZING.md) - in case you have different requirements.
 - [Generated Code Sample](docs/SAMPLE.md) - how the outputs actually look.

### Argument Formatting

Currently we support:
 - `fire`: (e.g. `python script.py some_func 5 10 --asdf=[1,2,3] --zxcv={a:5,b:7}`)
 - `argparse`: (e.g. `python script.py some_action -a -b --asdf 1 2 3`)
 - `sacred`: (e.g. `python script.py with some_cfg asdf=[1,2,3] a=True`)
 - any thing else? lmk! and look at `slurmjobs.args.Argument` and subclasses for
   examples on how to subclass your own formatter.

`fire` ([Fire](https://github.com/google/python-fire)) is the default (trust me it's greattttt you'll never go back.). You can set your own parser using:
`SlurmBatch(cli='argparse')`.

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
