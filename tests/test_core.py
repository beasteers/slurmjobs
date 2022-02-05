'''
TODO:
 - test backup
 - test command+args in job_content

'''
import os
import itertools
import slurmjobs
import pathtrees
import pytest

ROOT = os.path.dirname(__file__)

def test_basic():
    NAME = 'some.thing'
    COMMAND = 'python /some/thing.py train'
    CONDA_ENV = 'dfakjsdfhajkh43981hrt4138r91gh4'
    EMAIL = 'bea.steers@gmail.com'

    with pytest.raises(TypeError):
        batcher = slurmjobs.Slurm(
            COMMAND, email=EMAIL,
            root_dir=os.path.join(ROOT, 'slurm'),
            conda_env=CONDA_ENV,
            sbtach={},
            backup=False)

    # set batch parameters
    batcher = slurmjobs.Slurm(
        COMMAND, email=EMAIL,
        root_dir=os.path.join(ROOT, 'slurm'),
        conda_env=CONDA_ENV,
        modules=['cuda9'],
        sbatch={'n_gpus': 2},
        backup=False)
    assert batcher.name == NAME

    print(batcher.options['sbatch'])
    # assert batcher.options['sbatch']['cpus-per-task'] == 2
    assert batcher.options['sbatch']['gres'] == 'gpu:2'

    assert all(m in batcher.options['modules'] for m in batcher.module_presets['cuda9'])

    # generate scripts
    run_script, job_paths = batcher.generate([
        ('kernel_size', [2, 3, 5]),
        ('nb_stacks', [1, 2]),
        ('lr', [1e-4, 1e-3]),
    ], receptive_field=6)
    job_paths = [str(p) for p in job_paths]
    print(run_script, job_paths)
    assert len(job_paths) == 2 * 2 * 3

    # check job files
    found_job_paths = batcher.paths.job.glob()
    assert set(job_paths) == set(found_job_paths)
    job_content = pathtrees.Path(job_paths[0]).read_text()
    print(job_content)
    print([x for x in (NAME, COMMAND, CONDA_ENV, EMAIL) if x not in job_content])
    assert all(x in job_content for x in (NAME, COMMAND, CONDA_ENV, EMAIL))

    # check run file
    run_content = batcher.paths.run.read_text()
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
    batcher = slurmjobs.Shell(
        COMMAND, root_dir=os.path.join(ROOT, 'shell'),
        conda_env=CONDA_ENV, backup=False)
    assert batcher.name == NAME

    # generate scripts
    run_script, job_paths = batcher.generate([
        ('kernel_size', [2, 3, 5]),
        ('nb_stacks', [1, 2]),
        ('lr', [1e-4, 1e-3]),
    ], receptive_field=6)
    job_paths = [str(p) for p in job_paths]
    print(run_script, job_paths)

    # check job files
    found_job_paths = batcher.paths.job.glob()
    assert set(job_paths) == set(found_job_paths)
    job_content = pathtrees.Path(job_paths[0]).read_text()
    assert all(x in job_content for x in (NAME, COMMAND, CONDA_ENV))

    # check run file
    run_content = batcher.paths.run.read_text()
    assert all(path in run_content for path in job_paths)


def test_sing():
    NAME = 'some.thing'
    COMMAND = 'python /some/thing.py train'
    CONDA_ENV = 'dfakjsdfhajkh43981hrt4138r91gh4'

    # set batch parameters
    batcher = slurmjobs.Singularity(
        COMMAND, root_dir=os.path.join(ROOT, 'sing'),
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
    assert all(x in job_content for x in (NAME, COMMAND, CONDA_ENV))
    job_content = pathtrees.Path(job_paths[0]).read_text()

    # check run file
    run_content = batcher.paths.run.read_text()
    assert all(path in run_content for path in job_paths)



def test_arg_format():
    Args = slurmjobs.args.Argument
    assert isinstance(Args.get('fire'), slurmjobs.args.FireArgument)
    assert isinstance(Args.get('argparse'), slurmjobs.args.ArgparseArgument)
    assert isinstance(Args.get('sacred'), slurmjobs.args.SacredArgument)
    assert isinstance(Args.get('hydra'), slurmjobs.args.HydraArgument)

    args = Args.get('fire')(
        5, 'hi', 'hi hey', arg1=[1, 2], a='asdf', b='asdf adf')
    print('fire', args)
    assert args == "5 hi 'hi hey' --arg1='[1, 2]' --a=asdf --b='asdf adf'"

    args = Args.get('argparse')(
        'hi', flag=True, other=False, arg1=[1, 2], a='asdf', b='asdf adf')
    print('argparse', args)
    assert args == "--hi --flag --no-other --arg1 1 2 -a asdf -b 'asdf adf'"

    args = Args.get('sacred')(
        'hi', 'hi hey', arg1=[1, 2], a='asdf', b='asdf adf')
    print('sacred', args)
    assert args == "with hi 'hi hey' arg1='[1, 2]' a=asdf b='asdf adf'"


    # test
    args = Args.get('fire')(
        arg1=['a', 'b'], arg2={'a': 5, 'b': 6, 'c': [1, 'b']})
    print('fire', args)
    assert args == '--arg1=\'["a", "b"]\' --arg2=\'{"a": 5, "b": 6, "c": [1, "b"]}\''

    args = Args.get('hydra')(
        arg1=['a', 'b'], arg2={'a': 5, 'b': 6, 'c': [1, 'b']})
    print('hydra', args)
    assert args == '+arg1=\'["a", "b"]\' +arg2=\'{"a": 5, "b": 6, "c": [1, "b"]}\''

    args = Args.get('hydra')(
        **{
            'x': 5,
            'arg1.x': ['a', 'b'],
            'arg2.y': {'a': 5, 'b': 6, 'c': [1, 'b']},
            '++y': 6,
        })
    print('hydra', args)
    assert args == '+x=5 +arg1.x=\'["a", "b"]\' +arg2.y=\'{"a": 5, "b": 6, "c": [1, "b"]}\' ++y=6'

    args = Args.get('hydra', '++')(**{
        'x': 5,
        'arg1.x': ['a', 'b'],
        'arg2.y': {'a': 5, 'b': 6, 'c': [1, 'b']},
        '++y': 6,
    })
    print('hydra', args)
    assert args == '++x=5 ++arg1.x=\'["a", "b"]\' ++arg2.y=\'{"a": 5, "b": 6, "c": [1, "b"]}\' ++y=6'


    args = Args.get('hydra', '')(**{
        'x': 5,
        'arg1.x': ['a', 'b'],
        'arg2.y': {'a': 5, 'b': 6, 'c': [1, 'b']},
        '++y': 6,
    })
    print('hydra', args)
    assert args == 'x=5 arg1.x=\'["a", "b"]\' arg2.y=\'{"a": 5, "b": 6, "c": [1, "b"]}\' ++y=6'



# def test_multicmd_arg_format():
#     Args = slurmjobs.args.Argument

#     CMD = '''
# python blah.py {__all__}
# python blorp.py {a} {b}
# python blorp.py {b} {arg1}
# python blorp.py {arg1}
#     '''
#     EXPECTED = '''
# python blah.py --arg1='[1, 2]' --a=asdf --b='asdf adf' --job_id=blah
# python blorp.py --a=asdf --b='asdf adf'
# python blorp.py --b='asdf adf' --arg1='[1, 2]'
# python blorp.py --arg1='[1, 2]'
#     '''

#     kwargs = dict(arg1=[1, 2], a='asdf', b='asdf adf')
#     cmd = Args.get('fire')(CMD, **kwargs, job_id='blah')
#     print('fire', cmd)
#     assert cmd == EXPECTED

#     batcher = slurmjobs.SlurmBatch(
#         CMD, name='blah', root_dir=os.path.join(ROOT, 'slurm'),
#         multicmd=True, backup=False)

#     # generate scripts
#     run_script, job_paths = batcher.generate(**kwargs)
#     print(run_script, job_paths)

#     # check job files
#     found_job_paths = batcher.paths.job.glob()
#     assert set(job_paths) == set(found_job_paths)
#     job_content = pathtree.Path(job_paths[0]).read_text()
#     print(job_content)
#     assert EXPECTED in job_content


def test_parameter_grid():
    g = slurmjobs.Grid([
        ('something', [1, 2]),
        ('nodes', [ (1, 2, 3), (4, 5, 6), (7, 8, 9) ]),
        (('a', 'b'), [ (1, 2), (3, 5) ]),
        ('some_flag', (True,))
    ])

    assert g['something'] == [1, 2]
    g['something'] = [3, 4]
    assert g['something'] == [3, 4]
    g['something'] = [1, 2]
    assert g['something'] == [1, 2]

    # assert g['b'] == (3, 5)
    # print(g[('a', 'b')])
    # g['b'] = [3, 4]
    # assert g['b'] == [3, 4]
    # g['b'] = (3, 5)
    # assert g['b'] == (3, 5)

    _compare_grid(g, [
        # something - 1
        {'something': 1, 'nodes': (1, 2, 3), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 1, 'nodes': (1, 2, 3), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 1, 'nodes': (4, 5, 6), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 1, 'nodes': (4, 5, 6), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 1, 'nodes': (7, 8, 9), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 1, 'nodes': (7, 8, 9), 'a': 2, 'b': 5, 'some_flag': True},

        # something - 2
        {'something': 2, 'nodes': (1, 2, 3), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 2, 'nodes': (1, 2, 3), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 2, 'nodes': (4, 5, 6), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 2, 'nodes': (4, 5, 6), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 2, 'nodes': (7, 8, 9), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 2, 'nodes': (7, 8, 9), 'a': 2, 'b': 5, 'some_flag': True},
    ])

    g = slurmjobs.Grid([
        ('a', [1, 2]),
        ('b', [1, 2]),
    ], name='train')

    # appends a configuration
    g = g + slurmjobs.LiteralGrid([{'a': 5, 'b': 5}, {'a': 10, 'b': 10}])

    g = g * slurmjobs.Grid([
        ('c', [5, 6])
    ], name='dataset')

    _compare_grid(g, [
        # g * c=5
        {'a': 1, 'b': 1, 'c': 5},
        {'a': 1, 'b': 1, 'c': 6},
        {'a': 1, 'b': 2, 'c': 5},
        {'a': 1, 'b': 2, 'c': 6},
        {'a': 2, 'b': 1, 'c': 5},
        {'a': 2, 'b': 1, 'c': 6},
        {'a': 2, 'b': 2, 'c': 5},
        {'a': 2, 'b': 2, 'c': 6},
        {'a': 5, 'b': 5, 'c': 5},
        {'a': 5, 'b': 5, 'c': 6},
        {'a': 10, 'b': 10, 'c': 5},
        {'a': 10, 'b': 10, 'c': 6},
    ])

    xs = [1, 2]
    g = slurmjobs.Grid([
        # basic
        ('a', xs),
        # paired
        (('b', 'c'), ([1, 1, 2, 2], [1, 2, 1, 2])),
        # literal
        [{'d': i} for i in xs],
        # dict generator
        ({'e': i} for i in xs),
        # function
        lambda: [{'f': i} for i in xs],
        # function that returns a generator
        lambda: ({'g': i} for i in xs),
    ])
    keys = 'abcdefg'
    _compare_grid(g, [
        dict(zip(keys, vals)) for vals in
        itertools.product(*([xs]*len(keys)))
    ], no_len=True)

    # raise NotImplementedError("Write tests for grid sum/mult/sub/literal")


def _compare_grid(g, expected, no_len=False):
    try:
        assert list(g) == expected
        try:
            assert len(g) == len(expected)
        except TypeError:
            if not no_len:
                raise
        else:
            if no_len:
                raise RuntimeError("This grid should not have a length.")
    except Exception:
        for d in g:
            print(d)
        raise





def do_something(fname, content='hi'):
    with open(fname, 'w') as f:
        f.write(content)

def do_something_wrong():
    raise RuntimeError('jkasjkasfdjkajkhajkdh')

def test_receipts(tmpdir):
    out_file = os.path.join(tmpdir, 'asdf')
    slurmjobs.Receipt.ROOT_DIR = tmpdir

    r = slurmjobs.Receipt(do_something, out_file)
    r.clear()
    
    # creates a file cuz it's the first time it runs
    assert not r.exists
    slurmjobs.use_receipt(do_something)(out_file)
    assert os.path.isfile(out_file)
    assert r.exists

    assert not os.path.exists('./receipts')

    os.remove(out_file)
    assert not os.path.isfile(out_file)

    # the receipt is written so it shouldn't do it again
    assert r.exists
    slurmjobs.use_receipt(do_something)(out_file)
    assert not os.path.isfile(out_file)
    assert r.exists

    # now it should
    assert r.exists
    r.clear()
    assert not r.exists
    slurmjobs.use_receipt(do_something)(out_file)
    assert os.path.isfile(out_file)
    assert r.exists

    os.remove(out_file)
    assert not os.path.isfile(out_file)

    # test dry run
    r.clear()
    slurmjobs.use_receipt(do_something)(out_file, test=True)
    assert not os.path.isfile(out_file)
    assert not r.exists


    # try function taht fails
    with pytest.raises(RuntimeError):
        slurmjobs.use_receipt(do_something_wrong)()
        assert not r.exists


    # creates a file
    slurmjobs.use_receipt(do_something)(out_file)
    assert os.path.isfile(out_file)

    os.remove(out_file)
    assert not os.path.isfile(out_file)

    # doesn't run again
    slurmjobs.use_receipt(do_something)(out_file)
    assert not os.path.isfile(out_file)

    # overwrites
    slurmjobs.use_receipt(do_something)(out_file, overwrite_=True)
    assert os.path.isfile(out_file)

    assert set(r.meta) == {'duration_secs', 'time'}
