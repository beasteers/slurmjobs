import time
import jinja2
from . import util
from .args import Argument

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
                 cli=None, backup=True, **kw):
        # name
        self.cmd = cmd
        self.name = name or util.command_to_name(cmd)

        # paths
        self.paths = paths or self.get_paths(self.name, root_dir)
        if 'batch_dir' in self.paths:
            if backup:
                util.maybe_backup(self.paths.batch_dir)
            else:
                self.paths.batch_dir.rmglob(include=True)

        # job arguments
        self.job_args = dict(self.default_params, **kw)
        self.cli_fmt = cli

    def make_args(self, *a, **kw):
        return Argument.get(self.cli_fmt).build(*a, **kw) or ''

    def make_command(self, *a, **kw):
        return '{} {}'.format(self.cmd, self.make_args(*a, **kw))

    def generate(self, params, verbose=False, job_tpl=None, run_tpl=None, **kw):
        '''Generate slurm jobs for every combination of parameters.'''
        # generate jobs
        job_paths = [
            self.generate_job(
                util.get_job_name(self.name, pms),
                verbose=verbose, tpl=job_tpl, **kw, **pms)
            for pms in util.expand_param_grid(params)
        ]

        # generate run file
        run_script = self.generate_run_script(
            job_paths, params=dict(params, **kw), tpl=run_tpl,
            verbose=verbose)

        # store the current timestamp
        if 'time_generated' in self.paths.paths:
            self.paths.time_generated.write(time.time())
        return run_script, job_paths


    def generate_job(self, job_name, *a, tpl=None, verbose=False, **params):
        '''Generate a single slurm job file'''
        # build command
        paths = self.paths.specify(job_name=job_name)
        params[self.JOB_ID_KEY] = job_name
        cmd = self.make_command(*a, **params)

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


def get_template(tpl, default):
    return jinja2.Template(tpl) if tpl else env.get_template(default)
