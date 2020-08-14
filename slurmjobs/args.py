'''

Argument Formatters

'''
from . import util


class ArgGroup:
    def __init__(self, *a, **kw):
        self.args = a
        self.kwargs = kw


NoArgVal = object()


def flat_join(xs):
    return ' '.join(str(x) for x in util.flatten(xs) if x)


class Argument(util.Factory):
    prefix = suffix = ''
    default_cls = 'fire'

    @classmethod
    def get(cls, key=None):
        # key=fire -> FireArgument, key=None -> Argument
        return cls.__children__(suffix='argument').get((
            key or cls.default_cls).lower())

    @classmethod
    def _format_args(cls, *args, **kw):
        args = [cls.format_arg_or_group(v) for v in args]
        kw = {k: cls.format_arg_or_group(k, v) for k, v in kw.items()}
        return args, kw

    @classmethod
    def build(cls, cmd, *a, **kw):
        a, kw = cls._format_args(*a, **kw)
        all_ = flat_join([cls.prefix] + a + list(kw.values()) + [cls.suffix])
        return cmd.format(*a, **kw, __all__=all_)

    @classmethod
    def build_args(cls, *a, **kw):
        return cls.build('{__all__}', *a, **kw)

    @classmethod
    def format_arg_or_group(cls, k, v=NoArgVal):
        possible_group = k if v is NoArgVal else v
        if isinstance(possible_group, ArgGroup):
            return cls.format_group(possible_group)
        return cls.format_arg(k, v)

    @classmethod
    def format_group(cls, v):
        args, kw = cls._format_args(*v.args, **v.kwargs)
        return flat_join(args + list(kw.values()))

    @classmethod
    def format_arg(cls, k, v=NoArgVal):
        raise NotImplementedError

    @classmethod
    def format_value(cls, v):
        return util.shlex_repr(v)



class FireArgument(Argument):
    kw_fmt = '--{key}={value}'

    @classmethod
    def format_arg(cls, k, v=NoArgVal):
        if v is NoArgVal:
            return cls.format_value(k)
        return cls.kw_fmt.format(key=k, value=cls.format_value(v))



class ArgparseArgument(Argument):
    short_opt, long_opt = '-', '--'

    @classmethod
    def format_arg(cls, k, v=NoArgVal):
        key = cls.format_key(k)
        if v is True or v is NoArgVal:
            return key
        if v is False or v is None:
            return ''
        if not isinstance(v, (list, tuple, set)):
            v = [v]
        return [key] + [cls.format_value(x) for x in v]

    @classmethod
    def format_key(cls, k):
        return '{}{}'.format(cls.long_opt if len(k) > 1 else cls.short_opt, k)


class SacredArgument(FireArgument):
    prefix = 'with'
    kw_fmt = '{key}={value}'

    @classmethod
    def format_arg(cls, k, v=NoArgVal):
        if v is NoArgVal:
            return cls.format_value(k)
        return cls.kw_fmt.format(key=k, value=cls.format_value(v))
