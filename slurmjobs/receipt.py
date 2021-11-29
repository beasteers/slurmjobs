import os
import time
import hashlib
import functools
import pprint
import json


class Receipt:
    '''Make a receipt for a function call. This allows you skip over a function if 
    it was successfully ran. This is useful if a long script fails in the middle and 
    you want to re-run it, but you don't need to re-run the first part. 

    This will cache the function execution history using the string representation 
    of the function's arguments. This works well as 99% of things have some sort of 
    string representation, however, if you have a string representation that doesn't
    stay consistent, like an object that prints out its ID, then the receipt won't work.

    To resolve this, you can either:

     * subclass this method and override ``Receipt.hash_args(*a, **kw)`` to return something invariant
       for your
     * Provide your own ``receipt_id`` to the function call.
     * submit a PR for a better hash function!
    
    .. code-block:: python

        receipt = Receipt(func.__name__, *a, **kw)

        if not receipt.exists():
            try:
                do_something()
                receipt.make()
                # yay we can skip it next time!
            except Exception:
                """Oh well. It failed, but we'll just try again next time."""

        else:
            """Oh good it ran completely last time so we can skip it and move to the next one."""
    '''
    ROOT_DIR = './receipts'
    TEST = False
    def __init__(self, name='', *a, receipt_id=None, __dir__=None, **kw):
        if callable(name):
            name = getattr(name, '__qualname__') or getattr(name, '__name__')
        assert name or a or kw, 'you must pass some identifiable information to be used for a hash.'
        self.name = name
        self.id = '{}{}'.format(name or '', receipt_id or self.hash_args(*a, **kw))
        self.ROOT_DIR = __dir__ or self.ROOT_DIR
        self.fname = os.path.join(self.ROOT_DIR, self.id)

    def __str__(self):
        return '<Receipt exists={} file={}>'.format(
            self.exists, self.fname)

    def hash_args(self, *a, **kw):
        '''Take the function arguments and return a hash string for them.'''
        return hashlib.md5((
            str(a) + str(sorted(kw.items()))
        ).encode()).hexdigest()

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



def _fallbacks(*xs):
    for x in xs:
        if x is not None:
            return x


def use_receipt(func, receipt_dir=None, test=None):
    '''Use a receipt for a function call, which lets us skip a result if the function completed successfully
    the last run. This is just a wrapper around ``Receipt`` that handles the receipt checking/making logic for you.

    .. code-block:: python

        # do step 1. If it already ran successfully it will skip and do nothing.
        use_receipt(my_step1_function)(**step1_kwargs)

        # do step 2. here we're passing a custom receipt ID
        custom_receipt_id = ...
        use_receipt(my_step2_function)(**step2_kwargs, receipt_id=custom_receipt_id)

        # do step 3
        use_receipt(my_step3_function)(**step3_kwargs)
    '''
    @functools.wraps(func)
    def inner(*a, overwrite_=False, test=None, receipt_dir_=None, **kw):
        test = _fallbacks(test, inner.TEST, Receipt.TEST)
        receipt_dir_ = _fallbacks(receipt_dir_, inner.ROOT_DIR, Receipt.ROOT_DIR)
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
