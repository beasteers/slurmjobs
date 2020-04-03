import pathtree
from .base import BaseBatch
from . import util

__all__ = ['ShellBatch', 'SlurmBatch', 'PySlurmBatch']


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


MODULE_PRESETS = {
    'cuda9': ['cudnn/9.0v7.3.0.29', 'cuda/9.0.176'],
}

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
        modules=['cuda9'],
        sbatch_options=dict(
            time='7-0',
            mem='48GB',
        ),
    )

    module_presets = MODULE_PRESETS

    DEFAULT_JOB_TEMPLATE = 'job.default.sbatch.j2'
    DEFAULT_RUN_TEMPLATE = 'run.default.sbatch.j2'

    def __init__(self, *a, modules=None, **kw):
        modules = util.flatten(
            self.module_presets.get(m, m) for m in (modules or ()))
        super().__init__(*a, modules=modules, **kw)

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
