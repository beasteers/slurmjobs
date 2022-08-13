import itertools
import slurmjobs



def test_parameter_grid():
    g = slurmjobs.Grid([
        ('something', [1, 2]),
        ('nodes', [ (1, 2, 3), (4, 5, 6), (7, 8, 9) ]),
        (('a', 'b'), [ (1, 2), (3, 5) ]),
        ('some_flag', (True,))
    ])

    assert g['something'] == [1, 2]
    g['something'] = [3, 4]
    assert g['something'] == [3, 4]
    g['something'] = [1, 2]
    assert g['something'] == [1, 2]

    # assert g['b'] == (3, 5)
    # print(g[('a', 'b')])
    # g['b'] = [3, 4]
    # assert g['b'] == [3, 4]
    # g['b'] = (3, 5)
    # assert g['b'] == (3, 5)

    _compare_grid(g, [
        # something - 1
        {'something': 1, 'nodes': (1, 2, 3), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 1, 'nodes': (1, 2, 3), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 1, 'nodes': (4, 5, 6), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 1, 'nodes': (4, 5, 6), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 1, 'nodes': (7, 8, 9), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 1, 'nodes': (7, 8, 9), 'a': 2, 'b': 5, 'some_flag': True},

        # something - 2
        {'something': 2, 'nodes': (1, 2, 3), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 2, 'nodes': (1, 2, 3), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 2, 'nodes': (4, 5, 6), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 2, 'nodes': (4, 5, 6), 'a': 2, 'b': 5, 'some_flag': True},

        {'something': 2, 'nodes': (7, 8, 9), 'a': 1, 'b': 3, 'some_flag': True},
        {'something': 2, 'nodes': (7, 8, 9), 'a': 2, 'b': 5, 'some_flag': True},
    ])


def test_concat():
    g = slurmjobs.Grid([
        ('a', [1, 2]),
        ('b', [1, 2]),
    ], name='train')

    # appends a configuration
    g = g + slurmjobs.LiteralGrid([{'a': 5, 'b': 5}, {'a': 10, 'b': 10}])

    g = g * slurmjobs.Grid([
        ('c', [5, 6])
    ], name='dataset')

    _compare_grid(g, [
        # g * c=5
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
    ])

def test_grid_multitype():
    xs = [1, 2]
    g = slurmjobs.Grid([
        # basic
        ('a', xs),
        # paired
        (('b', 'c'), ([1, 1, 2, 2], [1, 2, 1, 2])),
        # literal
        [{'d': i} for i in xs],
        # dict generator
        ({'e': i} for i in xs),
        # function
        lambda: [{'f': i} for i in xs],
        # function that returns a generator
        lambda: ({'g': i} for i in xs),
    ])
    keys = 'abcdefg'
    _compare_grid(g, [
        dict(zip(keys, vals)) for vals in
        itertools.product(*([xs]*len(keys)))
    ], no_len=True)

    # raise NotImplementedError("Write tests for grid sum/mult/sub/literal")


def test_add_grid():
    g = slurmjobs.LiteralGrid([{'a': 5}, {'a': 6}])
    g = g + slurmjobs.LiteralGrid([{'a':7}, {'a': 8}])
    _compare_grid(g, [{'a': 5}, {'a': 6}, {'a':7}, {'a': 8}])

def test_subtract_grid():
    g = slurmjobs.LiteralGrid([{'a': 5}, {'a': 6}, {'a':7}, {'a': 8}])
    g = g - slurmjobs.LiteralGrid([{'a': 8}, {'a': 9}])
    _compare_grid(g, [{'a': 5}, {'a': 6}, {'a':7}])

def test_mult_grid():
    g = slurmjobs.LiteralGrid([{'a': 5}, {'a': 6}])
    g = g * slurmjobs.LiteralGrid([{'b': 7}, {'b': 8}])
    _compare_grid(g, [
        {'a': 5, 'b': 7}, 
        {'a': 5, 'b': 8}, 
        {'a': 6, 'b': 7}, 
        {'a': 6, 'b': 8}, 
    ])

def test_filter_grid():
    g = slurmjobs.LiteralGrid([{'a': 5}, {'a': 6}, {'a':7}, {'a': 8}, {'a': 9}])
    g = g | (lambda d: [d, {**d, 'b': 10}] if d['a'] == 7 else {**d, 'aaa': 15} if d['a'] == 8 else d if d['a'] != 9 else None)
    _compare_grid(g, [{'a': 5}, {'a': 6}, {'a': 7}, {'a': 7, 'b': 10}, {'a': 8, 'aaa': 15}])



def _compare_grid(g, expected, no_len=False):
    try:
        assert list(g) == expected
        try:
            assert len(g) == len(expected)
        except TypeError:
            if not no_len:
                raise
        else:
            if no_len:
                raise RuntimeError("This grid should not have a length.")
    except Exception:
        for d in g:
            print(d)
        raise

