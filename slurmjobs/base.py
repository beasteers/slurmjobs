import time
import pprint
import jinja2
from . import util
from .args import Argument, DEFAULT_CLI

env = jinja2.Environment(
    loader=jinja2.PackageLoader('slurmjobs', 'templates'))
env.filters['prettyjson'] = util.prettyjson
env.filters['prefixlines'] = util.prefixlines
env.filters['pprint'] = pprint.pformat
env.filters['comment'] = lambda x, ns=1, ch='#', nc=1: util.prefixlines(x, ch*nc+' '*ns)

IGNORE = object()


class BaseBatch:
    default_options = dict()
    JOB_ID_KEY = 'job_id'
    DEFAULT_JOB_TEMPLATE = None
    DEFAULT_RUN_TEMPLATE = None
    DEFAULT_CLI = DEFAULT_CLI
    INIT_SCRIPT = ''
    RUN_INIT_SCRIPT = ''
    POST_SCRIPT = ''

    def __init__(self, cmd, name=None, root_dir='jobs', paths=None,
                 cli=None, backup=True, job_id=True, multicmd=False, cmd_wrapper=None,
                 init_script=None, run_init_script=None, post_script=None, **kw):
        # name
        self.cmd = cmd
        self.name = name or util.command_to_name(cmd)
        self.multicmd = multicmd
        self.cmd_wrapper = cmd_wrapper

        # paths
        self.paths = paths or self.get_paths(self.name, root_dir)
        if 'batch_dir' in self.paths and len(self.paths.batch_dir.join('*').glob()):
            if backup:
                util.maybe_backup(self.paths.batch_dir)
            else:
                self.paths.batch_dir.rmglob(include=True)

        # job arguments
        init_script = '\n\n'.join((self.INIT_SCRIPT or '', init_script or ''))
        run_init_script = '\n\n'.join((self.RUN_INIT_SCRIPT or '', run_init_script or ''))
        post_script = '\n\n'.join((self.POST_SCRIPT or '', post_script or ''))

        if job_id is not True:
            self.JOB_ID_KEY = job_id or None

        self.job_args = dict(
            self.default_options,
            init_script=init_script,
            post_script=post_script,
            run_init_script=run_init_script, **kw)
        self.cli_fmt = self.DEFAULT_CLI if cli is None else cli

    def make_args(self, *a, **kw):
        return Argument.get(self.cli_fmt).build('{__all__}', *a, **kw)

    def make_command(self, *a, **kw):
        cmd = self.cmd if self.multicmd else '{} {{__all__}}'.format(self.cmd)
        cmd = Argument.get(self.cli_fmt).build(cmd, *a, **kw)
        if self.cmd_wrapper:
            if callable(self.cmd_wrapper):
                cmd = self.cmd_wrapper(cmd)
            else:
                cmd = self.cmd_wrapper.format(cmd)
        return cmd

    def generate(self, grid=None, *posargs, verbose=False, job_tpl=None, run_tpl=None,
                 job_name_tpl=None, job_name_allowed=",._-",
                 kwargs=None, summary=False, expand_grid=True, **kw):
        '''Generate slurm jobs for every combination of parameters.'''
        kw = dict(kw, **(kwargs or {})) # for taken keys.

        # prepare parameter grid
        if grid is None:
            grid = [{}]
        grid_literals = []
        if isinstance(grid, (list, tuple)):
            grid, grid_literals = util.split_cond(lambda x: isinstance(x, dict), grid, [False, True])
        unexpanded_grid = grid
        if expand_grid:
            grid = util.expand_grid(grid)
        grid.extend(grid_literals)

        # generate jobs
        job_paths = [
            self.generate_job(
                util.get_job_name(self.name, pms, job_name_tpl=job_name_tpl,
                                  allowed=job_name_allowed),
                *posargs, verbose=verbose, tpl=job_tpl, **kw, **pms)
            for pms in grid]

        # generate run file
        run_script = self.generate_run_script(
            job_paths, params=dict(unexpanded_grid, **kw) if unexpanded_grid else kw,
            tpl=run_tpl, verbose=verbose)

        # store the current timestamp
        if 'time_generated' in self.paths.paths:
            self.paths.time_generated.write(time.time())

        if summary:
            util.summary(run_script, job_paths)
        return run_script, job_paths


    def generate_job(self, job_name, *a, tpl=None, verbose=False, **params):
        '''Generate a single slurm job file'''
        # build command
        paths = self.paths.specify(job_name=job_name)
        if self.JOB_ID_KEY:
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

        if 'output' in paths.paths:
            paths.output.up().make()

        if verbose:
            print('Command:\n\t', cmd)
            print('Job File:', paths.job)
            if 'output' in paths.paths:
                print('Output File:', paths.output)
            print()
        return paths.job.format()


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

    def summary(self):
        print('Name:', self.name)
        print('Command:', self.name)
        util.summary((self.paths.run.glob() or [None])[0], self.paths.job.glob())


def get_template(tpl, default):
    return jinja2.Template(tpl) if tpl else env.get_template(default)
