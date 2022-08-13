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
        jobs = slurmjobs.Slurm(
            COMMAND, email=EMAIL,
            root_dir=os.path.join(ROOT, 'slurm'),
            conda_env=CONDA_ENV,
            sbtach={},
            backup=False)

    # set batch parameters
    jobs = slurmjobs.Slurm(
        COMMAND, email=EMAIL,
        root_dir=os.path.join(ROOT, 'slurm'),
        conda_env=CONDA_ENV,
        modules=['cuda9'],
        sbatch={'n_gpus': 2},
        backup=False)
    assert jobs.name == NAME

    print(jobs.options['sbatch'])
    # assert jobs.options['sbatch']['cpus-per-task'] == 2
    assert jobs.options['sbatch']['gres'] == 'gpu:2'

    assert all(m in jobs.options['modules'] for m in jobs.module_presets['cuda9'])

    # generate scripts
    run_script, job_paths = jobs.generate([
        ('kernel_size', [2, 3, 5]),
        ('nb_stacks', [1, 2]),
        ('lr', [1e-4, 1e-3]),
    ], receptive_field=6)#, dependency=lambda d: jobs.format_job_id(d, name='prepare-xxxxxx')
    job_paths = [str(p) for p in job_paths]
    print(run_script, job_paths)
    assert len(job_paths) == 2 * 2 * 3

    # check job files
    found_job_paths = jobs.paths.job.glob()
    assert set(job_paths) == set(found_job_paths)
    job_content = pathtrees.Path(job_paths[0]).read_text()
    print(job_content)
    print([x for x in (NAME, COMMAND, CONDA_ENV, EMAIL) if x not in job_content])
    assert all(x in job_content for x in (NAME, COMMAND, CONDA_ENV, EMAIL))#, '--dependency', 'prepare-xxxxxx'

    # check run file
    run_content = jobs.paths.run.read_text()
    assert all(path in run_content for path in job_paths)

    # test single generate
    run_script, job_paths = jobs.generate(receptive_field=6)
    print(run_script, job_paths)
    assert len(job_paths) == 1

def test_shell():
    NAME = 'some.thing'
    COMMAND = 'python /some/thing.py train'
    CONDA_ENV = 'dfakjsdfhajkh43981hrt4138r91gh4'

    # set batch parameters
    jobs = slurmjobs.Shell(
        COMMAND, root_dir=os.path.join(ROOT, 'shell'),
        conda_env=CONDA_ENV, backup=False)
    assert jobs.name == NAME

    # generate scripts
    run_script, job_paths = jobs.generate([
        ('kernel_size', [2, 3, 5]),
        ('nb_stacks', [1, 2]),
        ('lr', [1e-4, 1e-3]),
    ], receptive_field=6)
    job_paths = [str(p) for p in job_paths]
    print(run_script, job_paths)

    # check job files
    found_job_paths = jobs.paths.job.glob()
    assert set(job_paths) == set(found_job_paths)
    job_content = pathtrees.Path(job_paths[0]).read_text()
    assert all(x in job_content for x in (NAME, COMMAND, CONDA_ENV))

    # check run file
    run_content = jobs.paths.run.read_text()
    assert all(path in run_content for path in job_paths)


@pytest.mark.parametrize("n_gpus", [0, 2])
def test_sing(n_gpus):
    NAME = f'some.thing-gpu{n_gpus}'
    COMMAND = 'python /some/thing.py train'
    CONDA_ENV = 'dfakjsdfhajkh43981hrt4138r91gh4'
    MEM = '33GB'
    OVERLAY = 'overlay-5GB-200K.ext3'
    SIF = 'cuda11.0-cudnn8-devel-ubuntu18.04.sif'

    # set batch parameters
    jobs = slurmjobs.Singularity(
        COMMAND, OVERLAY, SIF,
        root_dir=os.path.join(ROOT, 'sing'), name=NAME,
        conda_env=CONDA_ENV, backup=False, n_gpus=n_gpus,
        sbatch=dict(mem=MEM))
    assert jobs.name == NAME

    print(jobs.options)

    # generate scripts
    run_script, job_paths = jobs.generate([
        ('kernel_size', [2, 3, 5]),
        ('nb_stacks', [1, 2]),
        ('lr', [1e-4, 1e-3]),
    ], receptive_field=6) #, dependency=lambda d: jobs.format_job_id(d, name='prepare-xxxxxx')
    job_paths = [str(p) for p in job_paths]
    print(run_script, job_paths)

    # check job files
    found_job_paths = jobs.paths.job.glob()
    assert set(job_paths) == set(found_job_paths)
    job_content = pathtrees.Path(job_paths[0]).read_text()
    for x in (NAME, COMMAND, CONDA_ENV):
        assert x in job_content
    if n_gpus:
        assert '--nv' in job_content
        assert f'#SBATCH --gres=gpu:{n_gpus}' in job_content
        assert f'#SBATCH --mem={MEM}' in job_content
    #, '--dependency', 'prepare-xxxxxx'

    # check run file
    run_content = jobs.paths.run.read_text()
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

#     jobs = slurmjobs.SlurmBatch(
#         CMD, name='blah', root_dir=os.path.join(ROOT, 'slurm'),
#         multicmd=True, backup=False)

#     # generate scripts
#     run_script, job_paths = jobs.generate(**kwargs)
#     print(run_script, job_paths)

#     # check job files
#     found_job_paths = jobs.paths.job.glob()
#     assert set(job_paths) == set(found_job_paths)
#     job_content = pathtree.Path(job_paths[0]).read_text()
#     print(job_content)
#     assert EXPECTED in job_content






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
