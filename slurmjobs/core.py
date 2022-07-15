'''Automating Slurm job generation.

Generate a set of `.sbatch` files over a grid of parameters to be searched over. 
A run script is created which will submit all generated jobs as once.

You can also use `ShellBatch` which excludes the slurm/module references so you can 
test & run on your local machine or test server.

> NOTE: because NYU switched to Greene which now utilizes singularity, the previous 
workflow regarding loading modules is not as necessary. Therefore, I will likely be 
experimenting and changing how things are done to suit the new workflow. If you want 
to keep the old setup, pin to `<=0.1.2`. (Sorry I should have just did a `0.2` bump 
off the bat).



'''
import os
import time
import pprint
import jinja2
import pathtrees
from .grid import *
from . import util
from .args import Argument

loader = jinja2.ChoiceLoader([
    jinja2.PackageLoader('slurmjobs', 'templates')
])
env = jinja2.Environment(loader=loader)
env.filters['prettyjson'] = util.prettyjson
env.filters['prefixlines'] = util.prefixlines
env.filters['pprint'] = pprint.pformat
env.filters['comment'] = lambda x, ns=1, ch='#', nc=1: util.prefixlines(x, ch*nc+' '*ns)


class Jobs:
    '''The base class for Job generation. Sub-class this if you want to provide your own

    .. code-block:: python

        import slurmjobs

        batch = slurmjobs.SlurmBatch(
            'python train.py',
            email='mynetid@nyu.edu',
            conda_env='my_env')

        # generate jobs across parameter grid
        run_script, job_paths = batch.generate([
            ('kernel_size', [2, 3, 5]),
            ('nb_stacks', [1, 2]),
            ('lr', [1e-4, 1e-3]),
        ], receptive_field=6)


    We use Jinja2 for our script templating. See https://jinja.palletsprojects.com/en/3.0.x/templates/ 
    for documentation about its syntax and structure.
    
    Attributes:
        options (dict): Template options. Anything here is made available to the template. 
        template (str): The Jinja2 template for the sbatch script. 
        job_template (str): The Jinja2 template for the jobs script that launches the sbatch files.
        cli (str, slurmjobs.args.Argument): The command line argument format your script uses.
            By default, this uses Fire. See ``args.FireArgument``.

        job_id_arg (str): The argument name to use for passing the job ID. 
            Set to None to ignore omit the job ID.
        job_id_key_sep (str): The separator between key and value used in the job ID.
        job_id_item_sep (str): The separator between key-value items in the job ID. 
        
        allowed_job_id_chars (str, list): Characters (other than alphanumeric) allowed in the job ID.
            Other characters are removed.
        special_character_replacement (str): A string that can be used in place of 
            special characters not found in ``allowed_job_id_chars``. Default is empty.
        key_abbreviations (dict): A mapping from full name to abbreviation for keys in the job ID.
        abbreviate_length (int): The length to abbreviate keys in the job ID.
        float_precision (int): The number of decimals to limit float values in the job ID.



    '''
    options = {
        'email': None,
        'conda_env': None,
        'run_dir': None,
        'bashrc': True,
        'set_e': False,
    }
    cli = 'fire'
    root_dir = 'jobs'

    # make script templating clearer and more simple
    template = '''{% extends 'job.base.j2' %}
    '''
    run_template = '''{% extends 'run.base.j2' %}
    '''

    job_id_arg = 'job_id'
    job_id_key_sep = '-'
    job_id_item_sep = ','
    allowed_job_id_chars = ',._-'
    special_character_replacement = ''
    omit_missing_keys_from_job_id = True
    
    key_abbreviations = {}
    abbreviate_length = None
    float_precision = None

    def __init__(self, command, name=None, cli=None, 
                 root_dir=None, backup=True, job_id=True, 
                 template=None, run_template=None,
                 **options):
        self.template = template or self.template
        self.run_template = run_template or self.run_template

        # raise an error if any unrecognized arguments were passed.
        wrong_options = set(options) - set(self.options)
        if wrong_options:
            raise TypeError(
                f"Unrecognized options: {wrong_options}. If you extended your template to use additional options, "
                "please give them default values in your Class.options dictionary.")
        
        # copy the options dict and add in new values
        self.options = dict(self.options)
        for k, v in options.items():
            dft = self.options[k]
            if isinstance(dft, dict):
                v = dict(dft, **(v or {}))
            self.options[k] = v

        self.command = command
        self.name = name or util.command_to_name(command)
        self.cli = Argument.get(self.cli if cli is None else cli)
        self.job_id_arg = self.job_id_arg if job_id is True else job_id or None

        # paths
        self.root_dir = root_dir or self.root_dir
        self.paths = self.get_paths()
        if 'batch_dir' in self.paths and len(self.paths.batch_dir.glob('*')):
            if backup:
                pathtrees.backup(self.paths.batch_dir)
            else:
                import shutil
                assert os.path.abspath(str(self.paths.batch_dir)) != '/', "Ummmmm..... what do you think you're doing... rm -rf / ???"
                shutil.rmtree(str(self.paths.batch_dir))

    def format_id_item(self, k, v):
        '''Formats a key-value pair for the job ID. 

        You can override this to change how each key-value pair in a 
        job ID is formatted.

        Arguments:
            k (str): The argument key.
            value (any): The argument value.

        Returns:
            Return a tuple if you want it to be joined using ``job_id_key_sep``. Return a string
            to be used as is. Return None to omit it from the job ID. 

        Be warned that omitting key/value pairs runs the risk of filename collisions which will mean 
        multiple jobs overwritting each other in the same file.
        '''
        # key formatting
        if k in self.key_abbreviations:
            k = self.key_abbreviations[k]
        elif self.abbreviate_length:
            k = k[:self.abbreviate_length]
        # TODO do before abbreviate_length
        k = ''.join(
            c if c in self.allowed_job_id_chars or c.isalnum() else self.special_character_replacement
            for c in k)

        # value formatting
        if self.float_precision is not None and isinstance(v, float):
            v = f'{v:.{self.float_precision}g}'
        return k, v

    def format_job_id(self, args, keys=None, name=None, ignore_keys=None):
        '''Convert a dictionary to a job ID.

        Arguments:
            args (GridItem): The job dictionary.
            keys (list, tuple): The keys that we want to include in the job ID.
            name (str): The job name to include in the job ID. By default
                this will be the name associated with the Jobs object. Pass 
                ``False`` to use no name.
        '''
        name = name or self.name if name is not False else False
        # format each key
        parts = []
        keys = getattr(args, 'grid_keys', args) if keys is None else keys
        if ignore_keys:
            keys = (k for k in keys if k not in ignore_keys)
        for k in keys:
            if k not in args:
                if self.omit_missing_keys_from_job_id:
                    continue
            formatted = self.format_id_item(k, args.get(k))
            if isinstance(formatted, (list, tuple)):
                parts.append(self.job_id_key_sep.join(map(str, formatted)))
            elif formatted is not None:
                parts.append(str(formatted))

        # join them together
        job_id = self.job_id_item_sep.join(map(str, [name]*bool(name) + parts))
        return job_id.replace(' ', '').replace('\n', '').replace('\t', '')


    def generate(self, grid_=None, *a, ignore_job_id_keys=None, **kw):
        '''Generate slurm jobs for every combination of parameters.
        
        Arguments:
            grid_ (Grid, list): The parameter grid.
            *a: Positional arguments to add to the command.
            **kw: Additional keyword arguments to pass to the command.

        Returns:
            tuple:

                str: The path to the run script.

                list[str]: The list of paths for each job file.
        '''
        # generate jobs
        # kw = dict(kw, **(kwargs_ or {})) # for taken keys.
        grid = Grid.as_grid([{}] if grid_ is None else grid_)

        used = set()
        job_paths = []
        for d in grid:
            d.positional += a
            d.update(kw)
            job_id = self.format_job_id(
                d, d.grid_keys, name=self.name, 
                ignore_keys=ignore_job_id_keys)
            if job_id in used:
                raise RuntimeError(f"Duplicate job ID: {job_id}")
            job_paths.append(self.generate_job(job_id, _grid=grid, _args=d))

        # generate run file
        run_script = self.generate_run_script(job_paths, _grid=grid)

        # store the current timestamp
        if 'time_generated' in self.paths.paths:
            self.paths.time_generated.write_text(str(time.time()))

        return run_script, job_paths
    
    def generate_job(self, job_id, *a, _args=None, _grid=None, **params):
        '''Generate a single slurm job file'''
        # build command
        paths = self.paths.specify(job_id=job_id)
        if self.job_id_arg:
            params[self.job_id_arg] = job_id
        
        args = _args
        if args is None:
            args = GridItem()
        args.update(params)
        args.positional += a

        # generate job file
        paths.job.parent.mkdir(parents=True, exist_ok=True)
        with open(paths.job, "w") as f:
            f.write(env.from_string(self.template).render(
                job_id=job_id,
                command=self.command,
                paths=paths,
                args=args,
                cli=self.cli,
                grid=_grid,
                **self.options,
            ).lstrip())

        if 'output' in paths.paths:
            paths.output.parent.mkdir(parents=True, exist_ok=True)

        return paths.job.format()

    def generate_run_script(self, _job_paths, _grid=None, **kw):
        '''Generate a job run script that will submit all jobs.'''
        # Generate run script
        file_path = self.paths.run
        with open(file_path, "w") as f:
            f.write(env.from_string(self.run_template).render(
                name=self.name,
                command=self.command,
                job_paths=_job_paths,
                paths=self.paths,
                cli=self.cli,
                grid=_grid,
                **self.options, **kw))
        util.make_executable(file_path)
        return file_path

    def get_paths(self, **kw):
        paths = pathtrees.tree(self.root_dir, {'{name}': {
            '': 'batch_dir',
            '{job_id}.job.sh': 'job',
            'run.sh': 'run',
            # optional
            'output/{job_id}.log': 'output',
            'time_generated': 'time_generated',
        }}).update(name=self.name, **kw)
        return paths



class Shell(Jobs):
    '''Generate batch jobs to be run without a task scheduler.
    This will create a grid of scripts that will be run using ``nohup``,
    a program that will keep running your script even if the parent 
    process (e.g. your ssh session) dies.

    This is mainly just for doing small tests and whatnot.

    .. code-block:: python

        import slurmjobs

        jobs = Shell('python myscript.py')
        jobs.generate([
            ('a', [1, 2]),
            ('b', [1, 2]),
        ])

    '''

    options = dict(
        Jobs.options,
        background=False,
    )

    template = '''{% extends 'job.shell.j2' %}
    '''




class Slurm(Jobs):
    '''Generate jobs for sbatch. This was used for HPC Prince. 
    For HPC Greene, please use ``Singularity``.

    This is functionally equivalent to:

    .. code-block:: python

        # sbatch_args
        #SBATCH --nodes=...
        #SBATCH --cpus-per-task=...
        #SBATCH --gres=gpu:...
        #SBATCH --mail-user=...
        ...

        {# shell_code_body #}
    
    '''
    # make sbatch args more isomorphic
    # while also providing helpers for setting cpus to the number of gpus by default (for example)
    options = dict(
        Jobs.options,
        # sbatch arguments
        # see: https://slurm.schedmd.com/sbatch.html
        sbatch={
            'time': '3-0',
            'mem': '48GB',
            # 'n_gpus': None,
            # 'n_cpus': None,
            # 'nodes': None,
        },
        # n_gpus=0,
        # n_cpus=None,
        # nodes=None,
        modules=None,  # no need for modules with singularity
        bashrc=False,  # disable bashrc by default
    )
    template = '''{% extends 'job.sbatch.j2' %}
    '''
    run_template = '''{% extends 'run.sbatch.j2' %}
    '''

    module_presets = {
        'cuda9': ['cudnn/9.0v7.3.0.29', 'cuda/9.0.176'],
        'cuda10': ['cuda/10.0.130', 'cudnn/10.0v7.4.2.24'],
        'cuda10.1': ['cuda/10.1.105', 'cudnn/10.1v7.6.5.32'],
        'cuda10.2': ['cuda/10.2.89'],
        'cuda11': ['cuda/11.0.194'],
        'cuda11.1': ['cuda/11.1.74'],
        'cuda11.3': ['cuda/11.3.1'],
        'conda': ['anaconda3/2020.07'],
        'anaconda': ['anaconda3/2020.07'],
        'anaconda3': ['anaconda3/2020.07'],
    }

    def __init__(self, *a, sbatch=None, modules=None, n_gpus=None, n_cpus=None, nv=None, **kw):
        modules = util.flatten(
            self.module_presets.get(m, m) for m in (modules or ()))
        super().__init__(*a, modules=modules, sbatch=sbatch, **kw)

        # handle n_cpus n_gpus
        sbatch = self.options['sbatch']
        n_cpus = n_cpus if n_cpus is not None else sbatch.pop('n_cpus', None)
        n_gpus = n_gpus if n_gpus is not None else sbatch.pop('n_gpus', None)
        gres = sbatch.get('gres')
        if n_cpus:
            if sbatch.get('cpus-per-task'):
                raise ValueError("n_cpus specified as well as cpus-per-task")
            sbatch['cpus-per-task'] = n_gpus or 1 if n_cpus is None else n_cpus
        if n_gpus:
            if sbatch.get('gres'):
                raise ValueError("n_gpus specified as well as gres. Please choose one or the other.")
            sbatch['gres'] = f'gpu:{n_gpus or 0}'
            # sbatch['gpus-per-task'] = n_gpus or 0
        if gres and isinstance(gres, int):
            sbatch['gres'] = f'gpu:{gres}'
        self.options['nv'] = bool(n_gpus or sbatch.get('gres')) if nv is None else nv

    def get_paths(self, **kw):
        paths = pathtrees.tree(self.root_dir, {'{name}': {
            '': 'batch_dir',
            '{job_id}.sbatch': 'job',
            'run.sh': 'run',
            'slurm/slurm_%j__{job_id}.log': 'output',
            'time_generated': 'time_generated',
        }}).update(name=self.name, **kw)
        return paths

# alias
SBatch = Slurm


class Singularity(Slurm):
    '''Generate jobs for sbatch + singularity. Use this for HPC Greene.
    
    This is functionally equivalent to:

    .. code-block:: python

        {# sbatch_args #}

        # execute it inside the container
        singularity exec --overlay ... ... /bin/bash << EOF

        . /ext3/env.sh

        {# shell_code_body #}

        EOF

    To setup a singularity overlay with a anaconda python environment, 
    please feel free to use https://gist.github.com/beasteers/84cf1eb2e5cc7bc4cb2429ef2fe5209e
    I'm in the process of integrating it with ``slurmjobs``.

    Source Tutorial: https://sites.google.com/a/nyu.edu/nyu-hpc/services/Training-and-Workshops/tutorials/singularity-on-greene

    
    '''
    sif_dir = '/scratch/work/public/singularity/'
    options = dict(
        Slurm.options,
        sif='cuda11.0-cudnn8-devel-ubuntu18.04.sif',
        overlay='overlay-5GB-200K.ext3',
        readonly=True,
        overlays=None,
        readonly_overlays=None,
        singularity_init_script='source /ext3/env.sh',
    )
    template = '''{% extends 'job.singularity.j2' %}
    '''
    def __init__(self, command, overlay=None, sif=None, *a, **kw):
        if overlay is not None:
            kw['overlay'] = overlay
        if sif is not None:
            kw['sif'] = sif
        super().__init__(command, *a, **kw)
        self.options['sif'] = self.options['sif'] and os.path.join(
            self.sif_dir, self.options['sif'])
