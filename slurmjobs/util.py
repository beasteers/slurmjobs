import os
import json
import shlex
import types
import itertools
import collections


'''

Naming Transformers

'''

def command_to_name(command):
    fbase = os.path.splitext(shlex.split(command)[1])[0]
    return fbase.replace('/', '.').lstrip('.').replace(' ', '-')

def get_job_name(name, params, job_name_tpl=None, allowed=",._-"):
    # Define job name using the batch name and job parameters
    params = {k: format_value_for_name(v) for k, v in params.items()}
    param_names, param_vals = zip(*sorted(params.items()))
    job_name_tpl = job_name_tpl or make_job_name_tpl(param_names)
    job_name = name + ',' + job_name_tpl.format(*param_vals, **params)
    job_name = ''.join(x for x in job_name if (x.isalnum() or x in allowed))
    return job_name

def make_job_name_tpl(names):
    # create a python format string for all parameters
    return ','.join(f'{n}-{{{n}}}' for n in names)

def format_value_for_name(x):
    # Format parameter values so that they are filename safe
    if isinstance(x, dict):
        return '_'.join('{}-{}'.format(k, v) for k, v in sorted(dict.items()))
    if isinstance(x, (list, tuple)):
        return '({})'.format(','.join(x))
    return x


'''

Parameter Expansion

'''

def expand_param_grid(params):
    '''
    e.g.
    params = [
        ('latent_dim', [1,2,4]),
        (('a', 'b'), [ (1, 3), (2, 5) ]),
        ('lets_overfit', (True,))
    ]
    assert list(expand_paired_params(params)) == [
        {'latent_dim': 1, 'a': 1, 'b': 3, 'lets_overfit': True},
        {'latent_dim': 1, 'a': 2, 'b': 5, 'lets_overfit': True},
        {'latent_dim': 2, 'a': 1, 'b': 3, 'lets_overfit': True},
        {'latent_dim': 2, 'a': 2, 'b': 5, 'lets_overfit': True},
        {'latent_dim': 4, 'a': 1, 'b': 3, 'lets_overfit': True},
        {'latent_dim': 4, 'a': 2, 'b': 5, 'lets_overfit': True},
    ]
    '''
    param_names, param_grid = zip(*(
        params.items() if isinstance(params, dict) else params))

    for ps in itertools.product(*param_grid):
        yield expand_paired_params(zip(param_names, ps))

def expand_paired_params(params):
    '''Flatten tuple dict key/value pairs
    e.g.
    assert (
        expand_paired_params([
            ('latent_dim', 2),
            (('a', 'b'), (1, 2)),
            ('lets_overfit', True)
        ])
        == {'latent_dim': 1, 'a': 1, 'b': 2, 'lets_overfit': True},)
    '''
    params = params.items() if isinstance(params, dict) else params
    ps = {}
    for n, v in params:
        if isinstance(n, tuple):
            # ((a, b), (1, 2)) =>
            for ni, vi in zip(n, v):
                ps[ni] = vi
        else:
            ps[n] = v
    return ps


'''

Misc / template utils

'''

def make_executable(file_path):
    # Grant permission to execute the shell file.
    # https://stackoverflow.com/a/30463972
    mode = os.stat(file_path).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(file_path, mode)

def maybe_backup(path):
    # create backup
    if path.exists():
        bkp_previous_path = path.next_unique(1)
        os.rename(path, bkp_previous_path)
        print('moved existing', path, 'to', bkp_previous_path)



def prettyjson(value):
    return json.dumps(value, sort_keys=True, indent=4) if value else ''

def prefixlines(text, prefix='# ', sep='\n'):
    return sep.join(prefix + l for l in text.splitlines())

def dict_merge(*ds, depth=-1, **kw):
    '''Recursive dict merge.

    Arguments:
        *ds (dicts): dicts to be merged.
        depth (int): the max depth to be merged.
        **kw: extra keys merged on top of the final dict.

    Returns:
        merged (dict).
    '''
    def merge(dicta, dictb, depth=-1):
        '''Recursive dict merge.

        Arguments:
            dicta (dict): dict to be merged into.
            dictb (dict): merged into dicta.
        '''
        for k in dictb:
            if (depth != 0 and k in dicta
                    and isinstance(dicta[k], dict)
                    and isinstance(dictb[k], collections.Mapping)):
                dict_merge(dicta[k], dictb[k], depth=depth - 1)
            else:
                dicta[k] = dictb[k]

    mdict = {}
    for d in ds + (kw,):
        merge(mdict, d, depth=depth)
    return mdict


def flatten(args, cls=(list, tuple, set, types.GeneratorType)):
    if isinstance(args, cls):
        return [a for arg in args for a in flatten(arg)]
    return [args]
'''

Argument

'''

class Factory:
    @classmethod
    def __children__(cls, prefix='', suffix=''):
        return {
            stripstr(c.__name__.lower(), prefix, suffix): c
            for c in all_subclasses(cls)}

def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        s for c in cls.__subclasses__() for s in all_subclasses(c))

def shlex_repr(v):
    v = repr(v)
    # if v is a quoted string, remove the quotes
    if len(v) >= 2 and v[0] == v[-1] and v[0] in '"\'':
        v = v[1:-1]
    return shlex.quote(v) # only quote if necessary (has spaces or bash chars)


def stripstr(text, prefix='', suffix=''):
    text = text[len(prefix):] if prefix and text.startswith(prefix) else text
    text = text[:-len(suffix)] if suffix and text.endswith(suffix) else text
    return text
