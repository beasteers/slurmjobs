import os
import slurmjobs
import pathtree

ROOT = os.path.dirname(__file__)

def test_basic():
    NAME = 'some.thing'
    COMMAND = 'python /some/thing.py train'
    CONDA_ENV = 'dfakjsdfhajkh43981hrt4138r91gh4'
    EMAIL = 'bea.steers@gmail.com'

    # set batch parameters
    batcher = slurmjobs.SlurmBatch(
        COMMAND, email=EMAIL,
        root_dir=os.path.join(ROOT, 'slurm'),
        conda_env=CONDA_ENV,
        modules=['cuda9'],
        backup=False)
    assert batcher.name == NAME

    assert all(m in batcher.job_args['modules'] for m in slurmjobs.core.MODULE_PRESETS['cuda9'])

    # generate scripts
    run_script, job_paths = batcher.generate([
        ('kernel_size', [2, 3, 5]),
        ('nb_stacks', [1, 2]),
        ('lr', [1e-4, 1e-3]),
    ], receptive_field=6)
    print(run_script, job_paths)
    assert len(job_paths) == 2 * 2 * 3

    # check job files
    job_paths = batcher.paths.job.glob()
    assert job_paths
    job_content = pathtree.Path(job_paths[0]).read()
    assert all(x in job_content for x in (NAME, COMMAND, CONDA_ENV, EMAIL))

    # check run file
    run_content = batcher.paths.run.read()
    assert all(x in run_content for x in job_paths)

    # test single generate
    run_script, job_paths = batcher.generate(receptive_field=6)
    print(run_script, job_paths)
    assert len(job_paths) == 1

def test_shell():
    NAME = 'some.thing'
    COMMAND = 'python /some/thing.py train'
    CONDA_ENV = 'dfakjsdfhajkh43981hrt4138r91gh4'

    # set batch parameters
    batcher = slurmjobs.ShellBatch(
        COMMAND, root_dir=os.path.join(ROOT, 'shell'),
        conda_env=CONDA_ENV, backup=False)
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
    assert all(x in job_content for x in (NAME, COMMAND, CONDA_ENV))

    # check run file
    run_content = batcher.paths.run.read()
    assert all(x in run_content for x in job_paths)

def test_arg_format():
    Args = slurmjobs.args.Argument
    assert Args.get('fire') == slurmjobs.args.FireArgument
    assert Args.get('argparse') == slurmjobs.args.ArgparseArgument
    assert Args.get('sacred') == slurmjobs.args.SacredArgument

    arg = Args.get('fire').build(
        5, 'hi', 'hi hey', arg1=[1, 2], a='asdf', b='asdf adf')
    print('fire', arg)
    assert arg == "5 hi 'hi hey' --arg1='[1, 2]' --a=asdf --b='asdf adf'"

    arg = Args.get('argparse').build(
        'hi', flag=True, other=False, arg1=[1, 2], a='asdf', b='asdf adf')
    print('argparse', arg)
    assert arg == "--hi --flag --arg1 1 2 -a asdf -b 'asdf adf'"

    arg = Args.get('sacred').build(
        'hi', 'hi hey', arg1=[1, 2], a='asdf', b='asdf adf')
    print('sacred', arg)
    assert arg == "with hi 'hi hey' arg1='[1, 2]' a=asdf b='asdf adf'"
