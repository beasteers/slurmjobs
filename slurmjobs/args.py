'''Argument Formatters
'''
from . import util
from . import grid


class Argument:
    '''The base-class for all argument formatters.
    If you want to provide a new argument formatter, 
    just override this class and change either the:

     * ``format_arg`` method that is used to format positional and key-value pairs, or 
     * ``format_value`` (which is called in ``format_arg``) to format python values as a string.
       This is often some form of quoted repr or json formatting.

    
    '''
    prefix = suffix = ''

    @classmethod
    def get(cls, key='fire', *a, **kw):
        '''Return an instance of an argument formatter, based on its name.'''
        # key=fire -> FireArgument, key=None -> Argument
        if not key:
            return cls
        if isinstance(key, cls):
            return key
        if isinstance(key, type) and issubclass(key, cls):
            return key(*a, **kw)
        return util.subclass_lookup(cls, suffix='argument').get(key.lower())(*a, **kw)

    def _format_args(self, *a, **kw):
        '''This prepares all arguments and returns them as positional and keyword arguments.

        The keyword arguments contain both the key and value flag, as applicable.
        '''
        if a and isinstance(a[0], grid._BaseGridItem):
            a, kw = (a[0].positional + a[1:], dict(a[0], **kw))
        a = [self.format_arg(v) for v in a]
        kw = {k: self.format_arg(k, v) for k, v in kw.items()}
        return a, kw

    def __call__(self, *a, indent=None, **kw):
        '''Format arguments as a string.
        
        Arguments:
            *a: positional arguments for the CLI.
            indent (int): The indentation (in spaces) for each argument. If
                ``indent`` is ``None`` the arguments are inline, otherwise 
                the arguments are each on their own line.
            **kw: Keyword arguments for the CLI.

        Returns:
            str: The command-line arguments formatted and ready to be outputted
                to a bash command.
        '''
        a2, kw2 = self._format_args(*a, **kw)
        items = (
            [self.prefix]*bool(self.prefix) + 
            a2 + [x for xs in kw2.values() if xs for x in xs] + 
            [self.suffix]*bool(self.suffix))

        indent = '\\\n' + ' '*indent if indent is not None else ''
        return ' '.join((
            f'{indent}{" ".join(x) if isinstance(x, list) else x}' 
            for x in items))

    def format_arg(self, k, v=...):
        '''Format a key-value pair for the command-line.
        
        If it is a positional argument, the value will be in key and the value
        will be ``...``.

        Arguments:
            k: The key (or value, for positional arguments).
            v: The value. If it's a positional argument, it will be ``v=...``
        '''
        return [self.format_value(k) if v is ... else self.format_value(v)]

    def format_value(self, v):
        '''Format a value for the command-line.'''
        return util.shlex_repr(v)



class FireArgument(Argument):
    '''Argument formatting for Python Fire.

    Example: ``python script.py a b --arg1 c --arg2 d``
    
    * Docs: https://google.github.io/python-fire/guide/
    * Github: https://github.com/google/python-fire
    '''
    kw_fmt = '--{key}={value}'

    def format_arg(self, k, v=...):
        if v is ...:
            return [self.format_value(k)]
        return [self.kw_fmt.format(key=k, value=self.format_value(v))]



class ArgparseArgument(Argument):
    '''Argument formatting for Python's builtin argparse.

    Example: ``python script.py a b --arg1 c --arg2 d``
    
    * Docs: https://docs.python.org/3/library/argparse.html
    '''
    short_opt, long_opt = '-', '--'

    def format_arg(self, k, v=...):
        if v is False:
            return [self.format_key(f'no-{k}')]
        key = self.format_key(k)
        if v is True or v is ...:
            return [key]
        if v is None:
            return []
        if not isinstance(v, (list, tuple, set)):
            v = [v]
        # this will all be joined to gether as strings. The extra
        # list on the outside means that it will appear on the same line
        # when indentation is requested
        vs = [self.format_value(x) for x in v]
        return [ [key] + vs ]

    def format_key(self, k):
        return '{}{}'.format(self.long_opt if len(k) > 1 else self.short_opt, k)


class SacredArgument(FireArgument):
    '''Formatting for sacred.

    Example: ``python script.py with arg1=a arg2=b``
    
    * Docs: https://sacred.readthedocs.io/en/stable/
    * Github: https://github.com/IDSIA/sacred
    '''
    prefix = 'with'
    kw_fmt = '{key}={value}'


class HydraArgument(FireArgument):
    '''Formatting for hydra.

    Example: ``python script.py  db.user=root db.pass=1234``
    
    * Docs: https://hydra.cc/docs/intro/
    * Github: https://github.com/facebookresearch/hydra
    '''
    kw_fmt = '{key}={value}'
    available_prefixes = ['+', '++', '~', '']
    # https://hydra.cc/docs/advanced/override_grammar/basic

    def __init__(self, default_prefix='+', **kw):
        default_prefix = default_prefix or ''
        if default_prefix not in self.available_prefixes:
            raise ValueError('invalid hydra prefix: {}. Must be one of {}'.format(
                default_prefix, self.available_prefixes))
        self.kw_fmt_prefixed = default_prefix + self.kw_fmt
        super().__init__(**kw)

    def format_arg(self, k, v=...):
        if v is ...:
            return [self.format_value(k)]
        kw_fmt = (
            self.kw_fmt
            if any(k.startswith(pfx) for pfx in self.available_prefixes if pfx)
            else self.kw_fmt_prefixed)
        return [kw_fmt.format(key=k, value=self.format_value(v))]
