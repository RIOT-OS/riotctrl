"""Helper utilities.
"""

import collections.abc


class MultiKeyDict(collections.abc.MutableMapping):
    """Works like a dict, but returns another dict, when used with tuples
    as a key:

    >>> a = MultiKeyDict({0: 'zero', 1: 'one', 2: 'two'})
    >>> len(a)
    3
    >>> a[0]
    'zero'
    >>> a[1]
    'one'
    >>> a[2]
    'two'
    >>> a[0,1]
    {0: 'zero', 1: 'one'}
    >>> a[3] = 'three'
    >>> a[0,1] = 'foobar'
    >>> a
    {0: 'foobar', 1: 'foobar', 2: 'two', 3: 'three'}
    >>> del a[1,2]
    >>> a
    {0: 'foobar', 3: 'three'}
    >>> del a[0]
    >>> a
    {3: 'three'}
    """
    def __init__(self, dictionary=None):
        if dictionary is None:
            self._dict = {}
        else:
            self._dict = dict(dictionary)

    def __str__(self):
        return str(self._dict)

    def __repr__(self):
        return str(self)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return type(self)(
                {k: self._dict[k] for k in key}
            )
        return self._dict[key]

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            for k in key:
                self._dict[k] = value
        else:
            self._dict[key] = value

    def __delitem__(self, key):
        if isinstance(key, tuple):
            for k in key:
                del self._dict[k]
        else:
            del self._dict[key]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)
