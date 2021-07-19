import os
import time
import hashlib
import functools
import pprint
import json


class Receipt:
    '''Make a receipt for a function call. Uses string representation of the
    function's arguments.'''
    ROOT_DIR = './receipts'
    TEST = False
    def __init__(self, name='', *a, __dir__=None, **kw):
        if callable(name):
            name = getattr(name, '__qualname__') or getattr(name, '__name__')
        assert name or a or kw, 'you must pass some identifiable information to be used for a hash.'
        self.name = name
        self.id = (name or '') + hashlib.md5((
            str(a) + str(sorted(kw.items()))
        ).encode()).hexdigest()
        self.ROOT_DIR = __dir__ or self.ROOT_DIR
        self.fname = os.path.join(self.ROOT_DIR, self.id)

    def __str__(self):
        return '<Receipt exists={} file={}>'.format(
            self.exists, self.fname)

    @property
    def exists(self):
        return os.path.isfile(self.fname)

    def make(self, **meta):
        os.makedirs(self.ROOT_DIR, exist_ok=True)
        with open(self.fname, 'w') as f:
            os.utime(self.fname)
            try:
                json.dump(meta, f)
            except Exception as e:
                json.dump({
                    'error': type(e).__name__,
                    'description': str(e),
                    'data': str(meta)
                }, f)

    def clear(self):
        if self.exists:
            os.remove(self.fname)

    @property
    def meta(self):
        if os.path.isfile(self.fname):
            with open(self.fname, 'r') as f:
                try:
                    s = f.read()
                    return json.loads(s) if s else {}
                except json.decoder.JSONDecodeError as e:
                    print('error:', e, s)
                    return s



def fallbacks(*xs):
    for x in xs:
        if x is not None:
            return x


def use_receipt(func, receipt_dir=None, test=None):
    @functools.wraps(func)
    def inner(*a, overwrite_=False, test=None, receipt_dir_=None, **kw):
        test = fallbacks(test, inner.TEST, Receipt.TEST)
        receipt_dir_ = fallbacks(receipt_dir_, inner.ROOT_DIR, Receipt.ROOT_DIR)
        r = Receipt(func, *a, __dir__=receipt_dir_, **kw)
        name = r.name
        if test:
            print('''
------------------------
-- Test Run --

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
            start_time = time.time()
            try:
                result = func(*a, **kw)
            except BaseException as e:
                r.clear()
                print('''
------------------------
-- Error during receipted function {}. --
Receipt: {}
Error: ({}) {}

No receipt is written.
------------------------
                '''.format(name, r, type(e).__name__, e))
                raise
            r.make(duration_secs=time.time() - start_time, time=time.time())

            print('''
------------------------
-- Receipt written for {} --
Receipt: {}

Took: {} seconds.
------------------------
            '''.format(name, r, (r.meta or {}).get('duration_secs')))
            return result
        else:
            print('''
------------------------
-- Receipt exists for {} --
Receipt: {}

Skipping.
------------------------
            '''.format(name, r, (r.meta or {}).get('duration_secs')))
    inner.TEST, inner.ROOT_DIR = test, receipt_dir
    return inner


# so that setting attributes will set receipt instead
class _DeprecatedSetAttr:
    func = None
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)

    def __call__(self, *a, **kw):
        return self.func(*a, **kw)

    def __setattr__(self, k, v):
        print(k, v, k not in self.__dict__)
        if k not in self.__dict__:
            setattr(Receipt, k, v)
            return
        super().__setattr__(k, v)
