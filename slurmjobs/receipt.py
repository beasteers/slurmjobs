import os
import hashlib
import functools
import pprint


class Receipt:
    '''Make a receipt for a function call. Uses string representation of the
    function's arguments.'''
    root_dir = './receipts'
    def __init__(self, name='', *a, __dir__=None, **kw):
        assert name or a or kw, 'you must pass some identifiable information to be used for a hash.'
        self.id = (name or '') + hashlib.md5((
            str(a) + str(sorted(kw.items()))
        ).encode()).hexdigest()
        self.root_dir = __dir__ or self.root_dir
        self.fname = os.path.join(self.root_dir, self.id)

    def __str__(self):
        return '<Receipt exists={} file={}>'.format(self.exists, self.fname)

    @property
    def exists(self):
        return os.path.isfile(self.fname)

    def make(self):
        os.makedirs(self.root_dir, exist_ok=True)
        with open(self.fname, 'a'):
            os.utime(self.fname)

    def clear(self):
        if self.exists:
            os.remove(self.fname)


def use_receipt(func):
    @functools.wraps(func)
    def inner(*a, overwrite_=False, test=None, **kw):
        name = getattr(func, '__qualname__') or getattr(func, '__name__')
        r = Receipt(name, *a, **kw)
        if test or inner.TEST:
            print('''
------------------------
Function: {}
Receipt: {}
*args:
{}
**kwargs:
{}
------------------------
            '''.format(name, r, pprint.pformat(a), pprint.pformat(kw)))
            return
        if overwrite_ or not r.exists:
            try:
                result = func(*a, **kw)
            except BaseException as e:
                r.clear()
                raise
            r.make()
            return result
    inner.TEST = use_receipt.TEST
    return inner
use_receipt.TEST = False
