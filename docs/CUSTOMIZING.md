# Customizing behavior

The main things you can customize:
 - the configuration options
  - this includes things like `conda_env`, `ngpus`, `ncpus`, `email`, `modules`, `run_dir`, etc. Look at `SlurmBatch.default_options` for the full list of defaults.
  - Use `sbatch_options` for general sbatch options (`time`, `mem`, etc.).
  - Use `init_script` to run arbitrary commands at the beginning of the job file.
 - the script templates (individual job, and batch run script)
  - the job and run scripts are generated from Jinja2 templates under `slurmjobs/templates/*.j2`. You are able to duplicate and modify those as you see fit.
 - the directory structure
  - this can be done through subclassing and providing a new `path-tree` object.
 - argument formatter

### Config

You can customize in 2 ways
```python
from slurmjobs import SlurmBatch

CMD = 'python train.py'

# ad-hoc config - set conda and `modules`
batch = SlurmBatch(CMD, conda_env='asdf', modules=['cuda10'])

# or something more permanent:
class MySlurmBatch(SlurmBatch):
    default_params = dict(
        SlurmBatch.default_params,
        conda_env='asdf',
        modules=['cuda10'])

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

You can define your own formatter by subclassing `Argument`. If your class name ends with `'Argument'`, you can omit that when passing the cli name. This works by gathering subclasses matching the passed string against their names. If the class ends with 'Argument', the suffix will be removed. If you don't want a class to be used, prefix the name with an underscore.

Example:
```python
import slurmjobs
class MyCustomArgument(slurmjobs.args.Argument):
  @classmethod
  def format_arg(cls, k, v=None):
    if v is not None:
      return str(k)
    return '..{}@{}'.format(k, cls.format_value(v)) # ..size@10

batch = slurmjobs.SlurmBatch('echo', cli='mycustom')
batch.make_command(size=10, blah='blorp')
# echo ..size@10 ..blah@blorp
```
