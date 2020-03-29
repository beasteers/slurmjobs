import os
import time
import shlex
import jinja2
import pathtree
from . import util

env = jinja2.Environment(
    loader=jinja2.PackageLoader('slurmjobs', 'templates'))
env.filters['prettyjson'] = util.prettyjson
env.filters['prefixlines'] = util.prefixlines

SBATCH_DIR = 'sbatch'


class SlurmBatch:
    default_params = dict(
        n_gpus=1,
        conda_env=None,
        run_dir='.',
        conda_version='5.3.1',
        email=None,
        modules=[
            'cudnn/9.0v7.3.0.29',
            'cuda/9.0.176',
        ],
        sbatch_options=dict(
            time='7-0',
            mem='48GB',
        ),
    )

    JOB_ID_KEY = 'job_id'

    def __init__(self, command, name=None, sbatch_dir=SBATCH_DIR, paths=None,
                 cli_fmt=None, backup=True, **kw):
        self.command = command
        self.name = name or util.command_to_name(command)

        self.paths = paths or get_paths(self.name, sbatch_dir, backup=backup)
        self.sbatch_args = dict(self.default_params, **kw)
        self.cli_fmt = cli_fmt

    def generate(self, params, verbose=False, **kw):
        '''Generate slurm jobs for every combination of parameters.'''
        # generate jobs
        job_paths = [
            self.generate_job(
                util.get_job_name(self.name, pms),
                verbose=verbose, **kw, **pms)
            for pms in util.expand_param_grid(params)
        ]

        # generate run file
        run_script = self.generate_run_script(
            job_paths, params=dict(params, **kw),
            verbose=verbose)
        self.paths.time_generated.write(time.time())
        return run_script, job_paths


    def generate_job(self, job_name, *a, tpl=None, verbose=False, **params):
        '''Generate a single slurm job file'''
        paths = self.paths.specify(job_name=job_name)
        params[self.JOB_ID_KEY] = job_name
        args = util.Argument.get(self.cli_fmt).build(*a, **params)
        command = f"{self.command} {args or ''}"

        with open(paths.job, "w") as f:
            f.write(get_template(tpl, 'job.default.sbatch.j2').render(
                job_name=job_name,
                command=command,
                output_path=paths.output,
                params=params,
                **self.sbatch_args,
            ))

        if verbose:
            print('Command:\n\t', command)
            print('SBatch File:', paths.job)
            print('Slurm Output:', paths.output)
            print()
        return paths.job


    def generate_run_script(self, job_paths, tpl=None, verbose=False, **kw):
        '''Generate a slurm '''
        # Open shell file
        file_path = self.paths.run
        with open(file_path, "w") as f:
            f.write(get_template(tpl, 'run.default.sbatch.j2').render(
                name=self.name,
                command=self.command,
                job_paths=job_paths,
                **self.sbatch_args, **kw,
            ))
        util.make_executable(file_path)

        if verbose:
            print(f'Wrote shell file to {file_path} with {len(job_paths)} jobs.')
            print('To start, run:')
            print(f'. {file_path}')
            print()
        return file_path

    # def run(self):
    #     import subprocess
    #     os.system(f'. {self.path.run.s}')
    #
    # def stop(self):
    #     pass


class PySlurmBatch(SlurmBatch):
    '''

    batcher = PySlurmBatch('my_script.py')
    batcher = PySlurmBatch('my.module', m=True)

    '''
    def __init__(self, command, *a, m=False, bin='python', **kw):
        # if isinstance(bin, (int, float)):
        #     bin = 'python{}'.format(bin)
        command = (
            '{} -m {}'.format(bin, command) if m else
            '{} {}'.format(bin, command))
        super().__init__(command, *a, **kw)



def get_template(tpl, default):
    return jinja2.Template(tpl) if tpl else env.get_template(default)


def get_paths(name, sbatch_dir=SBATCH_DIR, backup=True, **kw):
    paths = pathtree.tree(sbatch_dir, {'{name}': {
        '': 'batch_dir',
        '{job_name}.sbatch': 'job',
        'run_{name}.sh': 'run',
        'slurm/slurm_%j__{job_name}.log': 'output',
        'time_generated': 'time_generated',
    }}).update(name=name, **kw)

    if backup:
        util.maybe_backup(paths.batch_dir)
    else:
        paths.batch_dir.rmglob(include=True)
    paths.output.up().make()
    return paths
