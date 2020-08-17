'''
TODO:
 - test backup
 - test command+args in job_content

'''
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
    found_job_paths = batcher.paths.job.glob()
    assert set(job_paths) == set(found_job_paths)
    job_content = pathtree.Path(job_paths[0]).read()
    assert all(x in job_content for x in (NAME, COMMAND, CONDA_ENV, EMAIL))

    # check run file
    run_content = batcher.paths.run.read()
    assert all(path in run_content for path in job_paths)

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
    found_job_paths = batcher.paths.job.glob()
    assert set(job_paths) == set(found_job_paths)
    job_content = pathtree.Path(job_paths[0]).read()
    assert all(x in job_content for x in (NAME, COMMAND, CONDA_ENV))

    # check run file
    run_content = batcher.paths.run.read()
    assert all(path in run_content for path in job_paths)


def test_arg_format():
    Args = slurmjobs.args.Argument
    assert Args.get('fire') == slurmjobs.args.FireArgument
    assert Args.get('argparse') == slurmjobs.args.ArgparseArgument
    assert Args.get('sacred') == slurmjobs.args.SacredArgument

    CMD = 'python blah.py'
    CMD_ = CMD + ' {__all__}'
    cmd = Args.get('fire').build(
        CMD_, 5, 'hi', 'hi hey', arg1=[1, 2], a='asdf', b='asdf adf')
    print('fire', cmd)
    assert cmd == CMD + " 5 hi 'hi hey' --arg1='[1, 2]' --a=asdf --b='asdf adf'"

    cmd = Args.get('argparse').build(
        CMD_, 'hi', flag=True, other=False, arg1=[1, 2], a='asdf', b='asdf adf')
    print('argparse', cmd)
    assert cmd == CMD + " --hi --flag --arg1 1 2 -a asdf -b 'asdf adf'"

    cmd = Args.get('sacred').build(
        CMD_, 'hi', 'hi hey', arg1=[1, 2], a='asdf', b='asdf adf')
    print('sacred', cmd)
    assert cmd == CMD + " with hi 'hi hey' arg1='[1, 2]' a=asdf b='asdf adf'"


    # test
    cmd = Args.get('fire').build(
        CMD_, arg1=['a', 'b'], arg2={'a': 5, 'b': 6, 'c': [1, 'b']})
    print('fire', cmd)
    assert cmd == CMD + ' --arg1=\'["a", "b"]\' --arg2=\'{"a": 5, "b": 6, "c": [1, "b"]}\''


def test_multicmd_arg_format():
    Args = slurmjobs.args.Argument

    CMD = '''
python blah.py {__all__}
python blorp.py {a} {b}
python blorp.py {b} {arg1}
python blorp.py {arg1}
    '''
    EXPECTED = '''
python blah.py --arg1='[1, 2]' --a=asdf --b='asdf adf' --job_id=blah
python blorp.py --a=asdf --b='asdf adf'
python blorp.py --b='asdf adf' --arg1='[1, 2]'
python blorp.py --arg1='[1, 2]'
    '''

    kwargs = dict(arg1=[1, 2], a='asdf', b='asdf adf')
    cmd = Args.get('fire').build(CMD, **kwargs, job_id='blah')
    print('fire', cmd)
    assert cmd == EXPECTED

    batcher = slurmjobs.SlurmBatch(
        CMD, name='blah', root_dir=os.path.join(ROOT, 'slurm'),
        multicmd=True, backup=False)

    # generate scripts
    run_script, job_paths = batcher.generate(**kwargs)
    print(run_script, job_paths)

    # check job files
    found_job_paths = batcher.paths.job.glob()
    assert set(job_paths) == set(found_job_paths)
    job_content = pathtree.Path(job_paths[0]).read()
    print(job_content)
    assert EXPECTED in job_content


def test_parameter_grid():
    params = [
        ('something', [1, 2]),
        ('nodes', [ (1, 2, 3), (4, 5, 6), (7, 8, 9) ]),
        (('a', 'b'), [ (1, 3), (2, 5) ]),
        ('some_flag', (True,))
    ]

    assert list(slurmjobs.util.expand_grid(params)) == [
        # something - 1
        {'something': 1, 'nodes': (1, 2, 3), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 1, 'nodes': (1, 2, 3), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 1, 'nodes': (4, 5, 6), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 1, 'nodes': (4, 5, 6), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 1, 'nodes': (7, 8, 9), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 1, 'nodes': (7, 8, 9), 'a': 2, 'b': 5, 'some_flag': True},

        # something - 1
        {'something': 2, 'nodes': (1, 2, 3), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 2, 'nodes': (1, 2, 3), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 2, 'nodes': (4, 5, 6), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 2, 'nodes': (4, 5, 6), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 2, 'nodes': (7, 8, 9), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 2, 'nodes': (7, 8, 9), 'a': 2, 'b': 5, 'some_flag': True},
    ]
