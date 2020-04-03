'''

Argument Formatters

'''
from . import util


class NoArgVal: pass

class Argument(util.Factory):
    prefix = suffix = ''
    default_cls = 'fire'

    @classmethod
    def get(cls, key=None):
        # key=fire -> FireArgument, key=None -> Argument
        return cls.__children__(suffix='argument').get((
            key or cls.default_cls).lower())

    @classmethod
    def build(cls, *args, **kw):
        arglist = util.flatten(
            [cls.prefix] +
            [cls.format_arg(v) for v in args] +
            [cls.format_arg(k, v) for k, v in kw.items()] +
            [cls.suffix])
        return ' '.join(str(a) for a in arglist if a)

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
    def format_arg(cls, k, v=True):
        key = cls.format_key(k)
        if v is True:
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
