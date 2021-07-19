'''

Argument Formatters

'''
from collections import namedtuple
from . import util


DEFAULT_CLI = 'fire'


NoArgVal = '((((SLURMJOBS: NO ARG VALUE))))'


class Arg(namedtuple('Arg', 'key value format')):
    def __new__(self, key, value=NoArgVal, format=True):
        return super().__new__(self, key, value, format)


class ArgGroup(namedtuple('Arg', 'args kwargs')):
    def __new__(self, *a, **kw):
        return super().__new__(self, a, kw)


def flat_join(xs):
    return ' '.join(str(x) for x in util.flatten(xs) if x)


class Argument(util.Factory):
    prefix = suffix = ''

    @classmethod
    def get(cls, key='fire', *a, **kw):
        # key=fire -> FireArgument, key=None -> Argument
        if not key:
            return cls
        if isinstance(key, cls):
            return key
        if isinstance(key, type) and issubclass(key, cls):
            return key(*a, **kw)
        return cls.__children__(suffix='argument').get(key.lower())(*a, **kw)

    def _format_args(self, *args, **kw):
        args = [self.format_arg_or_group(v) for v in args]
        kw = {k: self.format_arg_or_group(k, v) for k, v in kw.items()}
        return args, kw

    def build(self, cmd, *a, **kw):
        a2, kw2 = self._format_args(*a, **kw)
        values = {f'_{k}': v for k, v in dict(enumerate(a), **kw).items()}
        all_ = flat_join([self.prefix] + a2 + list(kw2.values()) + [self.suffix])
        return cmd.format(*a2, **kw2, __all__=all_, **values)

    def build_args(self, *a, **kw):
        return self.build('{__all__}', *a, **kw)

    def format_arg_or_group(self, k, v=NoArgVal):
        value = k if v is NoArgVal else v
        if isinstance(value, ArgGroup):
            return self.format_group(value)
        if isinstance(value, Arg):
            if not value.format:
                return value.key if value.value is NoArgVal else value.value
            k, v = value.key, value.value
        return self.format_arg(k, v)

    def format_group(self, v):
        args, kw = self._format_args(*v.args, **v.kwargs)
        return flat_join(args + list(kw.values()))

    def format_arg(self, k, v=NoArgVal):
        return self.format_value(k) if v is NoArgVal else self.format_value(v)

    def format_value(self, v):
        return util.shlex_repr(v)



class FireArgument(Argument):
    kw_fmt = '--{key}={value}'

    def format_arg(self, k, v=NoArgVal):
        if v is NoArgVal:
            return self.format_value(k)
        return self.kw_fmt.format(key=k, value=self.format_value(v))



class ArgparseArgument(Argument):
    short_opt, long_opt = '-', '--'

    def format_arg(self, k, v=NoArgVal):
        key = self.format_key(k)
        if v is True or v is NoArgVal:
            return key
        if v is False or v is None:
            return ''
        if not isinstance(v, (list, tuple, set)):
            v = [v]
        return [key] + [self.format_value(x) for x in v]

    def format_key(self, k):
        return '{}{}'.format(self.long_opt if len(k) > 1 else self.short_opt, k)


class SacredArgument(FireArgument):
    prefix = 'with'
    kw_fmt = '{key}={value}'


class HydraArgument(FireArgument):
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

    def format_arg(self, k, v=NoArgVal):
        if v is NoArgVal:
            return self.format_value(k)
        kw_fmt = (
            self.kw_fmt
            if any(k.startswith(pfx) for pfx in self.available_prefixes if pfx)
            else self.kw_fmt_prefixed)
        return kw_fmt.format(key=k, value=self.format_value(v))
