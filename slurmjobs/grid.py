'''Parameter grids!

This lets you do basic grid expansion and grid arithmetic.

.. code-block:: python

    g = Grid([
        ('a', [1, 2]),
        ('b', [1, 2]),
    ], name='train')

    # append two configurations
    g = g + LiteralGrid([{'a': 5, 'b': 5}, {'a': 10, 'b': 10}])

    # create a bigger grid from the product of another grid
    g = g * Grid([
        ('c', [5, 6])
    ], name='dataset')

    assert list(g) == [
        {'a': 1, 'b': 1, 'c': 5},
        {'a': 1, 'b': 1, 'c': 6},
        {'a': 1, 'b': 2, 'c': 5},
        {'a': 1, 'b': 2, 'c': 6},
        {'a': 2, 'b': 1, 'c': 5},
        {'a': 2, 'b': 1, 'c': 6},
        {'a': 2, 'b': 2, 'c': 5},
        {'a': 2, 'b': 2, 'c': 6},
        {'a': 5, 'b': 5, 'c': 5},
        {'a': 5, 'b': 5, 'c': 6},
        {'a': 10, 'b': 10, 'c': 5},
        {'a': 10, 'b': 10, 'c': 6},
    ]


'''
import itertools
import collections

# Parameter Grids


class BaseGrid:
    '''The base class for all grids. Use this if you want to extend another grid.
    
    You just need to implement:

     * ``__iter__``: This should yield all items generated by the grid
     * ``__len__``: This should tell you the number of items in the grid. If you cannot
       determine the length of a grid, then raise a TypeError (as the other grids do).
     * ``__repr__``: A nice string representation of the grid
    '''
    grid = ()

    def __repr__(self):
        '''A nice string representation of the grid.'''
        return '{}({})'.format(self.__class__.__name__, ', '.join(map(repr(self.grid))))

    def __str__(self):
        ''''''  # NOTE: not sure if this should be different or if we should switch str/repr
        return repr(self)

    def __len__(self):
        '''Get the number of iterations in the grid.
        
        Note that any use of generators or functions without a length will 
        cause this to raise a TypeError.
        '''
        raise NotImplemented

    def __iter__(self):
        '''Yield all combinations from the parameter grid.'''
        raise NotImplemented

    def __add__(self, other):
        '''Combine two parameter grids sequentially.'''
        return GridChain(self, other)

    def __mul__(self, other):
        '''Create a grid as the combination of two grids.'''
        return GridCombo(self, other)

    @classmethod
    def as_grid(cls, grid):
        '''Ensure that a value is a grid.'''
        if isinstance(grid, BaseGrid):
            return grid
        if isinstance(grid, (list, tuple)):
            if all(isinstance(g, dict) for g in grid):
                return LiteralGrid(grid)
        return Grid(grid)


class Grid(BaseGrid):
    '''A parameter grid! To get all combinations from the grid, just do ``list(Grid(...))``.

    Arguments:
        grid (list, dict): The parameter grid. Should be either a dict
            or a list of key values, where the values are a list of values
            to use in the grid. Examples of valid inputs:

            .. code-block:: python
                
                # simple grid
                Grid([ ('a', [1, 2]), ('b', [1, 2]) ])
                Grid({ 'a': [1, 2], 'b': [1, 2] })

                # paired parameters
                Grid([
                    ('a', [1, 2]), 
                    (('b', 'c'), ([1, 2], [1, 2])) 
                ])
                Grid([ 
                    ('a', [1, 2]),
                    [{'b': 1, 'c': 1}, {'b': 2, 'c': 2}],
                ])

                # any of these are valid grid specs
                g = slurmjobs.Grid([
                    # basic
                    ('a', [1, 2]),
                    # paired
                    (('b', 'c'), ([1, 1, 2, 2], [1, 2, 1, 2])),

                    # literal list of dicts
                    [{'d': i} for i in [1, 2]],
                    # dict generator
                    ({'e': i} for i in [1, 2]),
                    # function
                    lambda: [{'f': i} for i in [1, 2]],
                    # function that returns a generator
                    lambda: ({'g': i} for i in [1, 2]),

                    # basic generator
                    ('h', (x for x in [1, 2])),
                    # basic function
                    ('i', lambda: [x for x in [1, 2]]),
                ])
                keys = 'abcdefghi'
                assert list(g) == [
                    dict(zip(keys, vals)) for vals in
                    itertools.product(*([ [1, 2] ]*len(keys)))
                ]

        name (str): The name of this grid. Can be used to search 
            for the parameters from this grid.
        **constants: Extra parameters to add to the grid that don't vary.
            These will not be included in the job_id name.

    .. .. code-block:: python

    ..     g = Grid([
    ..         ('a', [1, 2]),
    ..         ('b', [1, 2]),
    ..     ])
    ..     assert list(g) == [
    ..         {'a': 1, 'b': 1},
    ..         {'a': 2, 'b': 1},
    ..         {'a': 1, 'b': 2},
    ..         {'a': 2, 'b': 2},
    ..     ]

    .. You can also do pairwise parameter expansion.

    .. .. code-block:: python

    ..     g = Grid([
    ..         ('a', [1, 2]),
    ..         (('b', 'c'), ([1, 2], [3, 4])),
    ..     ])
    ..     assert list(g) == [
    ..         {'a': 1, 'b': 1, 'c': 3},
    ..         {'a': 2, 'b': 1, 'c': 3},
    ..         {'a': 1, 'b': 2, 'c': 4},
    ..         {'a': 2, 'b': 2, 'c': 4},
    ..     ]

    Just a heads up, there is nothing stopping you from passing an infinite generator,
    meaning that you can make some fancy sampling grid generators, but ``slurmjobs`` will
    take that and not know when to stop. If you want to use an infinite generator, just 
    wrap it in ``itertools.islice`` which will let you provide a limit.

    Obviously, ``slurmjobs`` doesn't operate anywhere near the memory scale where you'd need to 
    even use generators in the first place, but I figured why limit the implementation if 
    it can be used for other things too.
    '''
    def __init__(self, grid, name=None, **constants):
        self.grid = list(grid.items()) if isinstance(grid, dict) else grid
        self.name = name
        self.constants = constants

    def __repr__(self):
        return '[\n{}]'.format(''.join(map('  {!r},\n'.format, self.grid)))

    def __len__(self):
        return prod(self._as_grid_length(g) for g in self.grid)

    def _as_grid_length(self, xs):
        '''Determine the length of a grid product item.'''
        try:
            l = len(xs)
            if l == 2 and not isinstance(xs[0], dict):
                if isinstance(xs[0], (list, tuple)):
                    return max(len(x) for x in xs[1])
                return len(xs[1])
            return l
        except (TypeError, IndexError):
            raise TypeError("Could not determine accurate length from grid item: {}".format(repr(xs)))
        

    def _as_grid_product_iter(self, xs):
        '''This returns one iteration to use in the product.
        '''
        if callable(xs):
            xs = xs()
        # checking the first value
        try:
            first = xs[0]  # list of dicts?
        except TypeError:
            # generator of dicts: ({'a': ...} for _ in ...)
            firsts, xs = peek(xs)
            if not firsts:
                return []
            first = firsts[0]
        except IndexError:  # empty list
            return []
        # [{'a': 1, 'b': 1}, {'a': 2, 'b': 2}]
        if isinstance(first, dict):
            return xs
        
        # asserting it's length 2
        key, values = xs
        # if any of the values are functions, call them
        values = [v() if callable(v) else v for v in values]
        # (('a', 'b'), ([1, 2, 3], [3, 4, 5]))
        if isinstance(key, (list, tuple)):
            return (
                collections.OrderedDict([(k, v) for k, v in zip(key, vs) if v != ...])
                for vs in itertools.zip_longest(*values, fillvalue=...))
        # ('a', [1, 2, 3])
        return ({key: v} for v in values)

    def __iter__(self):
        grid = [self._as_grid_product_iter(xs) for xs in self.grid]
        for ds in itertools.product(*grid):
            # expand grid pairs [('a', 'b'), ([1, 2, 3], [1, 2, 3])]
            yield GridItem(
                dict({k: v for d in ds for k, v in d.items()}, **self.constants), 
                [k for d in ds for k in d], self.name)


class LiteralGrid(BaseGrid):
    '''A parameter grid, specified as a flattened list. This
    doesn't do any grid expansion, it lets you specify the grid
    as you want.

    Arguments:
        grid (list, dict): The parameter list. Should be a list of 
            dicts, each corresponding to a parameter config.
        name (str): The name of this grid. Can be used to search 
            for the parameters from this grid.

    .. code-block:: python

        g = LiteralGrid([
            {'a': 1, 'b': 1},
            {'a': 1, 'b': 2},
            {'a': 2, 'b': 2},
        ])
        assert list(g) == [
            {'a': 1, 'b': 1},
            {'a': 1, 'b': 2},
            {'a': 2, 'b': 2},
        ]
    '''
    def __init__(self, grid, name=None, **constants):
        self.grid = [grid] if isinstance(grid, dict) else grid
        self.name = name
        self.constants = constants

    def __repr__(self):
        return '[\n{}]'.format(''.join(map('  {!r},\n'.format, self.grid)))

    def __len__(self):
        return len(self.grid)

    def __iter__(self):
        for d in self.grid:
            # expand grid pairs [('a', 'b'), ([1, 2, 3], [1, 2, 3])]
            yield GridItem(dict(d, **self.constants), list(d), self.name)
            # should we just use dict's internal ordering for the keys?



class _BaseGridItem(dict):
    positional = ()
    # def variant_items(self):
    #     return [(k, self[k]) for k in self.grid_keys]


class GridItem(_BaseGridItem):
    '''Represents a dictionary of arguments, the keys that vary, 
    and a name for the group of args.
    '''
    def __init__(self, grid=None, keys=(), name=None, positional=()):
        self.grid_keys = keys
        self.name = name
        self.positional = positional or ()
        super().__init__(() if grid is None else grid)

    def __getitem__(self, key):
        return super().__getitem__(key)

    def find(self, name):
        return self if self.name == name else None

    

class GridItemBundle(_BaseGridItem):
    '''Merges GridItems/GridBundles. Merges the dict, keys, and any groups.
    Can use ``.find(name)`` so search for a subset of items.
    '''
    def __init__(self, *grids, name=None):
        merged = {}
        groups = {}
        keys = []
        for d in grids:
            merged.update(d)
            keys.extend(d.grid_keys or ())
            for ki, di in getattr(d, 'groups', {}).items():
                groups[ki] = dict(groups.get(ki, ()), **di)
            k = d.name
            if k is not None:
                groups[k] = dict(groups.get(k, ()), **d)
        if name is not None:
            groups[name] = dict(groups.get(name, ()), **merged)

        self.name = name
        self.grid_keys = unique(keys)
        self.groups = groups
        super().__init__(merged)

    def __getitem__(self, key):
        if key in self.groups:
            return self.groups[key]
        return super().__getitem__(key)

    def __getattr__(self, key):
        return self.__getitem__(key)

    def find(self, name):
        return self.groups.get(name)



class GridChain(BaseGrid):
    '''This handles the addition of two grids (one after the other).

    You can create this doing ``grid_a + grid_b``. The only reason to 
    use this directly is if you want to give it a name.
    
    .. code-block:: python

        a = Grid(('a', [1, 2]), ('b', [1, 2]))
        b = Grid(('c', [1, 2]))

        # functionally equivalent
        c = a + b
        c = GridChain(a, b, name='my-a-then-b-grid')
        c_items = list(a) + list(b)
    '''
    def __init__(self, *grids, name=None):
        self.grid = grids
        self.name = name

    def __repr__(self):
        return ' + '.join(map(repr, self.grid))

    def __len__(self):
        return sum(len(g) for g in self.grid)

    def __iter__(self):
        for g in self.grid:
            yield from g


class GridCombo(BaseGrid):
    '''This handles the multiplication of two grids (combinations). It 
    will create a grid as a product of all provided grids.

    You can create this doing ``grid_a * grid_b``. The only reason to 
    use this directly is if you want to give it a name or if you want to
    make a grid product of 3 or more grids.
    
    .. code-block:: python

        a = Grid(('a', [1, 2]), ('b', [1, 2]))
        b = Grid(('c', [1, 2]))

        # functionally equivalent
        c = a * b
        c = GridCombo(a, b, name='my-a-b-combo-grid')
        c_items = [
            dict(da, **db)
            for da, db in itertools.product(a, b)
        ]
    '''
    def __init__(self, *grids, name=None):
        self.grid = grids
        self.name = name

    def __repr__(self):
        return ' * '.join(map('({!r})'.format, self.grid))
        
    def __len__(self):
        return prod(len(g) for g in self.grid)

    def __iter__(self):
        for gs in itertools.product(*self.grid):
            yield GridItemBundle(*gs, name=self.name)


class GridOmission(BaseGrid):
    '''This handles the subtraction of two grids (combinations). It will 
    yield only dicts from ``grid_a`` that don't appear in ``grid_b``.

    You can create this doing ``grid_a - grid_b``. The only reason to 
    use this directly is if you want to give it a name.
    
    .. code-block:: python

        a = Grid(('a', [1, 2]), ('b', [1, 2]))
        b = Grid(('a', [2]), ('b', [1]))

        # functionally equivalent
        c = a - b
        c = GridOmission(a, b, name='my-a-minus-b-grid')
        omit = list(b)
        c_items = [da for da in a if da not in omit]
    '''
    def __init__(self, grid, omission, name=None):
        self.grid = grid
        self.omission = omission
        self.name = name

    def __repr__(self):
        return ' - '.join(map('({!r})'.format, [self.grid, self.omission]))
        
    def __len__(self):
        return sum(1 for d in self)

    def __iter__(self):
        omit = list(self.omission)
        for d in self.grid:
            if d not in omit:
                yield d





def prod(ns):
    '''Like ``sum()`` but for products.'''
    total = 1
    for n in ns:
        total *= n
        if total == 0:
            break
    return total


def unique(xs):
    used = set()
    return [x for x in xs if not (x in used or used.add(x))]


def peek(it, n=1):
    it = iter(it)
    first = [x for i, x in zip(range(n), it)]
    return first, (x for xs in (first, it) for x in xs)