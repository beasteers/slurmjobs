import os
import json
import shlex
import types
import itertools
import collections



def summary(run_script, job_paths):
    '''Print out a nice summary of the job sbatch files and the run script.'''
    print('Generated', len(job_paths), 'job scripts:')
    for p in job_paths:
        print('\t', p)
    print()

    print('To submit all jobs, run:')
    print('.', run_script)
    print()


'''

Misc / template utils

'''

def command_to_name(command):
    '''Convert a bash command into a usable job name.
    
    NOTE: This was originally to turn 'python my/script.py' into 'my.script'
          but obviously this is just a special case and I never really found
          a nice, general way to do this.
    '''
    fbase = os.path.splitext(shlex.split(command)[1])[0]
    return fbase.replace('/', '.').lstrip('.').replace(' ', '-')


def as_chunks(lst, n=1):
    return [lst[i:i + n] for i in range(0, len(lst), n)]



def make_executable(file_path):
    '''Grant permission to execute a file.'''
    # https://stackoverflow.com/a/30463972
    mode = os.stat(file_path).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(file_path, mode)


def maybe_backup(path, prefix='~'):
    '''Backup a path if it exists.'''
    # create backup
    if path.exists():
        bkp_previous_path = path.prefix(prefix).next_unique(1)
        os.rename(path, bkp_previous_path)
        print('moved existing', path, 'to', bkp_previous_path)



def prettyjson(value):
    '''Pretty-print data using json.'''
    return json.dumps(value, sort_keys=True, indent=4) if value else ''


def prefixlines(text, prefix='# '):
    '''Prefix each line. Can be used to comment a block of text.'''
    return ''.join(prefix + l for l in str(text).splitlines(keepends=True))


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
    '''Flatten iterables into a flat generator.'''
    if isinstance(args, cls):
        yield from (a for arg in args for a in flatten(arg))
    elif args is not None:
        yield args


def clsattrdiff(cls, base_cls=None, funcs=False):
    '''Get the non-function attributes that exist on ``cls``, but not on ``base_cls``.'''
    attrs = dict()
    base_dict = base_cls.__dict__ if base_cls is not None else {}
    i = cls.__mro__.index(base_cls) if base_cls is not None else None
    for cls_i in cls.__mro__[:i][::-1]:
        for k, v in cls_i.__dict__.items():
            if (not k.startswith('_') and 
                    k not in base_dict and 
                    (funcs or not callable(v))):
                attrs[k] = v
    return attrs


'''

Argument

'''


def all_subclasses(cls):
    '''Return all recursive subclasses of a class.'''
    return set(cls.__subclasses__()).union(
        s for c in cls.__subclasses__() for s in all_subclasses(c))


def subclass_lookup(cls, prefix='', suffix='', name_override=None):
    '''Get a dictionary of name to subclass (removing any common prefix/suffix).'''
    return {
        (getattr(c, name_override, None) if name_override else None) 
            or stripstr(c.__name__.lower(), prefix, suffix): c
        for c in all_subclasses(cls)
        if not c.__name__.startswith('_')}


def shlex_repr(v):
    '''Prepare a variable for bash. This will serialize the object using json 
    and then quote the variable if it contains any spaces/bash-specific characters.
    '''
    # v = repr(v)
    v = json.dumps(v)
    # if v is a quoted string, remove the quotes
    if len(v) >= 2 and v[0] == v[-1] and v[0] in '"\'':
        v = v[1:-1]
    return shlex.quote(v) # only quote if necessary (has spaces or bash chars)


def escape(txt, chars='"\''):
    '''Escape certain characters from a string. By default, it's quotes.'''
    for c in chars:
        txt = txt.replace(c, '\\' + c)
    return txt


def stripstr(text, prefix='', suffix=''):
    '''Strip a prefix and/or suffix from a string.'''
    text = text[len(prefix):] if prefix and text.startswith(prefix) else text
    text = text[:-len(suffix)] if suffix and text.endswith(suffix) else text
    return text


def get_available_tensorflow_cuda_versions():
    '''Load the tensorflow-cuda lookup table.'''
    # https://www.tensorflow.org/install/source#gpu
    import csv
    with open(os.path.join(os.path.dirname(__file__), 'cuda_versions.csv'), 'r') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    versions = ({
        'cuda': d['CUDA'], 'cudnn': d['cuDNN'], 
        'python': d["Python version"].split(', '),
        'version': d['Version'].split('-')[-1]
    } for d in rows)
    return {d['version']: d for d in versions}


def find_tensorflow_cuda_version(version, latest=False):
    '''Given a tensorflow version, lookup the correct'''
    import fnmatch
    versions = get_available_tensorflow_cuda_versions()
    version = str(version).split('.')[:2]
    version = '.'.join(version + ['*']*(3 - len(version)))
    matched = sorted(v for v in versions if fnmatch.fnmatch(v, version))
    if not matched:
        raise ValueError('No value matching {!r}'.format(version))
    return versions[matched[-1 if latest else 0]]

if __name__ == '__main__':
    import fire
    fire.Fire()