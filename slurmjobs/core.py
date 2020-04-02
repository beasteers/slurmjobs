import os
import time
import shlex
import jinja2
import pathtree
from . import util

__all__ = ['ShellBatch', 'SlurmBatch', 'PySlurmBatch']

env = jinja2.Environment(
    loader=jinja2.PackageLoader('slurmjobs', 'templates'))
env.filters['prettyjson'] = util.prettyjson
env.filters['prefixlines'] = util.prefixlines
env.filters['comment'] = lambda x, ns=1, ch='#', nc=1: util.prefixlines(x, ch*nc+' '*ns)




class BaseBatch:
    default_params = dict()
    JOB_ID_KEY = 'job_id'
    DEFAULT_JOB_TEMPLATE = None
    DEFAULT_RUN_TEMPLATE = None

    def __init__(self, cmd, name=None, root_dir='jobs', paths=None,
                 cli_fmt=None, backup=True, **kw):
        # name
        self.cmd = cmd
        self.name = name or util.command_to_name(cmd)

        # paths
        self.paths = paths or self.get_paths(self.name, root_dir)
        if backup:
            util.maybe_backup(self.paths.batch_dir)
        else:
            self.paths.batch_dir.rmglob(include=True)

        # job arguments
        self.job_args = dict(self.default_params, **kw)
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
            job_paths, params=dict(params, **kw), verbose=verbose)

        # store the current timestamp
        if 'time_generated' in self.paths.paths:
            self.paths.time_generated.write(time.time())
        return run_script, job_paths


    def generate_job(self, job_name, *a, tpl=None, verbose=False, **params):
        '''Generate a single slurm job file'''
        # build command
        paths = self.paths.specify(job_name=job_name)
        params[self.JOB_ID_KEY] = job_name
        args = util.Argument.get(self.cli_fmt).build(*a, **params)
        cmd = f"{self.cmd} {args or ''}"

        # generate job file
        paths.job.up().make()
        with open(paths.job, "w") as f:
            f.write(get_template(tpl, self.DEFAULT_JOB_TEMPLATE).render(
                job_name=job_name,
                command=cmd,
                paths=paths,
                params=params,
                **self.job_args,
            ))

        if verbose:
            print('Command:\n\t', cmd)
            print('Job File:', paths.job)
            if 'output' in paths.paths:
                print('Output File:', paths.output)
            print()
        return paths.job


    def generate_run_script(self, job_paths, tpl=None, verbose=False, **kw):
        '''Generate a job run script that will submit all jobs.'''
        # Generate run script
        file_path = self.paths.run
        with open(file_path, "w") as f:
            f.write(get_template(tpl, self.DEFAULT_RUN_TEMPLATE).render(
                name=self.name,
                command=self.cmd,
                job_paths=job_paths,
                paths=self.paths,
                **self.job_args, **kw))
        util.make_executable(file_path)

        if verbose:
            print(f'Wrote shell file to {file_path} with {len(job_paths)} jobs.')
            print('To start, run:')
            print(f'. {file_path}')
            print()
        return file_path

    def get_paths(self, name, root_dir='jobs'):
        raise NotImplementedError


class ShellBatch(BaseBatch):
    default_params = dict(
        conda_env=None,
        run_dir='.',
    )

    DEFAULT_JOB_TEMPLATE = 'shell.job.default.sh.j2'
    DEFAULT_RUN_TEMPLATE = 'shell.run.default.sh.j2'

    def get_paths(self, name, root_dir='sbatch', **kw):
        paths = pathtree.tree(root_dir, {'{name}': {
            '': 'batch_dir',
            'jobs/{job_name}.sh': 'job',
            'run_{name}.sh': 'run',
            # optional
            'output/{job_name}.log': 'output',
            'time_generated': 'time_generated',
        }}).update(name=name, **kw)
        paths.output.up().make()
        return paths


class SlurmBatch(BaseBatch):
    '''

    batcher = SlurmBatch('my_script.py')
    batcher = PySlurmBatch('my.module', m=True)

    '''
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

    DEFAULT_JOB_TEMPLATE = 'job.default.sbatch.j2'
    DEFAULT_RUN_TEMPLATE = 'run.default.sbatch.j2'

    def get_paths(self, name, root_dir='sbatch', **kw):
        paths = pathtree.tree(root_dir, {'{name}': {
            '': 'batch_dir',
            '{job_name}.sbatch': 'job',
            'run_{name}.sh': 'run',
            'slurm/slurm_%j__{job_name}.log': 'output',
            'time_generated': 'time_generated',
        }}).update(name=name, **kw)
        paths.output.up().make()
        print(paths)
        return paths



class PySlurmBatch(SlurmBatch):
    '''

    batcher = PySlurmBatch('my_script.py')
    batcher = PySlurmBatch('my.module', m=True)

    '''
    def __init__(self, cmd, *a, m=False, bin='python', **kw):
        # if isinstance(bin, (int, float)):
        #     bin = 'python{}'.format(bin)
        cmd = (
            '{} -m {}'.format(bin, cmd) if m else
            '{} {}'.format(bin, cmd))
        super().__init__(cmd, *a, **kw)



def get_template(tpl, default):
    return jinja2.Template(tpl) if tpl else env.get_template(default)
