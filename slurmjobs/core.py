import pathtree
from .base import BaseBatch
from . import util

__all__ = ['ShellBatch', 'SlurmBatch', 'PySlurmBatch']


class ShellBatch(BaseBatch):
    default_options = dict(
        conda_env=None,
        run_dir='.',
        init_script='',
    )

    DEFAULT_JOB_TEMPLATE = 'shell.job.default.sh.j2'
    DEFAULT_RUN_TEMPLATE = 'shell.run.default.sh.j2'

    def get_paths(self, name, root_dir='sbatch', **kw):
        paths = pathtree.tree(root_dir, {'{name}': {
            '': 'batch_dir',
            'jobs/{job_name}.sh': 'job',
            'run.sh': 'run',
            # optional
            'output/{job_name}.log': 'output',
            'time_generated': 'time_generated',
        }}).update(name=name, **kw)
        return paths


MODULE_PRESETS = {
    'cuda9': ['cudnn/9.0v7.3.0.29', 'cuda/9.0.176'],
    'cuda10': ['cuda/10.0.130', 'cudnn/10.0v7.4.2.24'],
    'cuda10.1': ['cuda/10.1.105', 'cudnn/10.1v7.6.5.32'],
}


class SlurmBatch(BaseBatch):
    '''

    batcher = SlurmBatch('my_script.py')
    batcher = PySlurmBatch('my.module', m=True)

    '''
    default_options = dict(
        n_gpus=0,
        n_cpus=1,
        nodes=1,
        conda_env=None,
        run_dir='.',
        conda_version='5.3.1',
        email=None,
        modules=[],
        sbatch_options=dict(
            time='7-0',
            mem='48GB',
        ),
        init_script='',
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
            'run.sh': 'run',
            'slurm/slurm_%j__{job_name}.log': 'output',
            'time_generated': 'time_generated',
        }}).update(name=name, **kw)
        return paths


class PySlurmBatch(SlurmBatch):
    '''

    batcher = PySlurmBatch('my_script.py')
    batcher = PySlurmBatch('my.module', m=True)

    '''
    DEFAULT_JOB_TEMPLATE = 'job.default.sbatch.j2'
    DEFAULT_RUN_TEMPLATE = 'run.default.sbatch.j2'

    def __init__(self, cmd, *a, m=False, bin='python', **kw):
        # if isinstance(bin, (int, float)):
        #     bin = 'python{}'.format(bin)
        name, cmd = cmd, (
            '{} -m {}'.format(bin, cmd) if m else
            '{} {}'.format(bin, cmd))
        super().__init__(cmd, name, *a, **kw)


class Jupyter(SlurmBatch):
    DEFAULT_JOB_TEMPLATE = 'jupyter.sbatch.j2'

    INIT_SCRIPT = '''
port=$(shuf -i 10000-65500 -n 1)

/usr/bin/ssh -N -f -R $port:localhost:$port log-0
/usr/bin/ssh -N -f -R $port:localhost:$port log-1

~C-R $port:localhost:$port

cat<<EOF

Jupyter server is running on: $(hostname)
Job starts at: $(date)

Step 1:
    If you are working in NYU campus, please open an terminal window, run command

    # replace prince if it is named differently in your ssh config
    ssh -L $port:localhost:$port $USER@prince

Step 2:
    Keep the terminal window in the previouse step open. Now open browser, find the line with
    The Jupyter Notebook is running at: $(hostname)

    the URL is something: http://localhost:${port}/?token=XXXXXXXX (see your token below)

    you should be able to connect to jupyter notebook running remotly on prince compute node with above url

EOF

unset XDG_RUNTIME_DIR
if [ "$SLURM_JOBTMP" != "" ]; then
    export XDG_RUNTIME_DIR=$SLURM_JOBTMP
fi
    '''

    def __init__(self, cmd, *a, lab=True, name='jupyter', **kw):
        # jupyter {{ server }} --no-browser --port $port --notebook-dir=$(pwd)
        cmd = f'jupyter {"lab" if lab else "notebook"} --no-browser --port $port --notebook-dir=$(pwd) {cmd}'
        super().__init__(cmd, *a, name=name, **kw)

    def generate(self, *a, grid=None, **kw):
        super().generate(*a, grid=grid, **kw)
