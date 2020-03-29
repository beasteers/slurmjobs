import os
from slurmjobs import SlurmBatch, util
import pathtree

SBATCH_DIR = os.path.join(os.path.dirname(__file__), 'slurm')

def test_basic():
    NAME = 'some.thing'
    COMMAND = 'python /some/thing.py train'
    CONDA_ENV = 'dfakjsdfhajkh43981hrt4138r91gh4'
    EMAIL = 'bea.steers@gmail.com'

    # set batch parameters
    batcher = SlurmBatch(
        COMMAND, email=EMAIL,
        sbatch_dir=SBATCH_DIR,
        conda_env=CONDA_ENV,
        backup=False)
    assert batcher.name == NAME

    # generate scripts
    run_script, job_paths = batcher.generate([
        ('kernel_size', [2, 3, 5]),
        ('nb_stacks', [1, 2]),
        ('lr', [1e-4, 1e-3]),
    ], receptive_field=6)
    print(run_script, job_paths)

    # check job files
    job_paths = batcher.paths.job.glob()
    assert job_paths
    job_content = pathtree.Path(job_paths[0]).read()
    assert all(x in job_content for x in (NAME, COMMAND, CONDA_ENV, EMAIL))

    # check run file
    run_content = batcher.paths.run.read()
    assert all(x in run_content for x in job_paths)


def test_arg_format():
    pass
