'''Batch generate slurm/shell jobs.

Examples:
$ # this will generate slurm sbatch files
$ python -m slurmjobs slurm --cmd='python train.py' generate "{kernel_size: [2,3,5], lr: [1e-4, 1e-3]}"
$ # this will generate shell files that run commands in the background using nohup
$ python -m slurmjobs sh --cmd='python train.py' generate "{kernel_size: [2,3,5], lr: [1e-4, 1e-3]}"

NOTE: Python Fire requires that class __init__ args use keyword notation (--cmd=MY_CMD)

Fire User Guide: https://github.com/google/python-fire/blob/master/docs/guide.md
'''
from slurmjobs import *

if __name__ == '__main__':
    import fire
    fire.Fire({
        'sh': Shell,
        'slurm': Slurm,
    })
