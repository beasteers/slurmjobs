# slurmjobs
Automating Slurm job generation.

Generate a set of `.sbatch` files over a grid of parameters to be searched over. A run script is created which will submit all generated jobs as once.

You can also use `ShellBatch` which excludes the slurm/module references so you can test & run on your local machine or test server.

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
    conda_env='my_env',
    init_script='''
echo "hi! I'm running before the main command!"
echo "you can do initialization stuff here. but no pressure. it's completely optional."
# NOTE: this runs after modules are loaded and your conda environment is setup,
#       but before you switch to `run_dir`.
    ''')

# generate jobs across parameter grid
run_script, job_paths = batch.generate([
    ('kernel_size', [2, 3, 5]),
    ('nb_stacks', [1, 2]),
    ('lr', [1e-4, 1e-3]),
], receptive_field=6)

# NOTE:
#       extra keywords (e.g. receptive_field) are also passed as arguments
#       to the scripts. They have constant values across all scripts.

#       the values in the parameter grid are used to generate `job_id`, but
#       the constant arguments are not included in the job name.

# ******************************
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

### Parameter Grids

Parameter grids are how you can define specific parameter combinations that you want to search over. It is very similar to `sklearn.model_selection.GridSearchCV`.

```python
params = [
    # basic variable type
    ('something', [1, 2]),
    # variable with list type is ok too
    ('nodes', [ [1, 2, 3], [4, 5, 6], [7, 8, 9] ]),
    # these are co-occurring variables -  so we do:
    #   (--a 1 --b 3) &  (--a 2 --b 5) but not:
    #   (--a 2 --b 3) or (--a 1 --b 5)
    (('a', 'b'), [ (1, 3), (2, 5) ]),
    # single variables expand fine too.
    ('some_flag', (True,))
]

assert list(slurmjobs.util.expand_grid(params)) == [
    {'something': 1, 'nodes': [1, 2, 3], 'a': 1, 'b': 3, 'some_flag': True},
    {'something': 1, 'nodes': [1, 2, 3], 'a': 2, 'b': 5, 'some_flag': True},

    {'something': 1, 'nodes': [4, 5, 6], 'a': 1, 'b': 3, 'some_flag': True},
    {'something': 1, 'nodes': [4, 5, 6], 'a': 2, 'b': 5, 'some_flag': True},

    {'something': 1, 'nodes': [7, 8, 9], 'a': 1, 'b': 3, 'some_flag': True},
    {'something': 1, 'nodes': [7, 8, 9], 'a': 2, 'b': 5, 'some_flag': True},

    {'something': 2, 'nodes': [1, 2, 3], 'a': 1, 'b': 3, 'some_flag': True},
    {'something': 2, 'nodes': [1, 2, 3], 'a': 2, 'b': 5, 'some_flag': True},

    {'something': 2, 'nodes': [4, 5, 6], 'a': 1, 'b': 3, 'some_flag': True},
    {'something': 2, 'nodes': [4, 5, 6], 'a': 2, 'b': 5, 'some_flag': True},

    {'something': 2, 'nodes': [7, 8, 9], 'a': 1, 'b': 3, 'some_flag': True},
    {'something': 2, 'nodes': [7, 8, 9], 'a': 2, 'b': 5, 'some_flag': True},
]
```

### Multi-line Commands
Initially, I had written this with a narrow scope of generating jobs for argument grid searches on a single script. But a coworker started asking how to handle jobs with multiple sequential commands so I spoke with her and managed to find a solution that can handle both cases.

For single script commands (like above), you don't need to add any format keys (like before). If `multicmd=False` (the default), it will automatically append `'{__all__}'` to the end of the command which will insert all of the specified arguments to the end of the string.

For situations where you want to pass arguments to multiple commands, it's not always so trivial, especially when you need to designate which arguments go to which commands.

To address this, you can use python format strings (`'mycommand {arg1} {arg2}' => --arg1 4 --arg2 5`) to specify particular arguments. This will insert the entire command line flag so doing (`'{year}' => --year 2017`).

I prefer this because it decouples your job generation from your argument format, but it does add some trouble when you're trying to do more complicated things (insert variables into other variables for example). To access the original variable without any added flag, you can just preceed the name with an underscore (e.g. to access `year`, do `{_year} => `2017`)

**But**, after experimenting with this on a project, it can easily get complicated, especially if your scripts have inconsistent naming (`audio_output_dir` then `audio_output_folder`, etc.)

So I'm happy to keep this functionality, but you probably want to consider just making a wrapper script that will run your multiple steps from a single command. It will probably also reduce the degrees of freedom you have to handle between script arguments.

I use `fire` for creating my command line interfaces and it definitely decreases the amount of duplication from having to write argparse parsers.

To pass everything to a script (including the added `job_id` argument), you can use `{__all__}` as a key.

```python
import slurmjobs

batch = slurmjobs.SlurmBatch('''
python move_files.py {dates} {sensors}
python convert_to_hdf5.py {dates} {sensors}
python calculate_stats.py  # it's fine to not have arguments.
python get_embeddings.py {dates} {sensors} {job_id}

python predict.py {__all__}
# (or equivalently)
# python predict.py {dates} {sensors} {tax_path} {job_id}
''', multicmd=True)

# generate jobs across parameter grid
run_script, job_paths = batch.generate([
    ('sensors', [1, 2, 3, 5]),
    ('dates', [1, 2])),
], tax_path='path/to/taxonomy.json')
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
