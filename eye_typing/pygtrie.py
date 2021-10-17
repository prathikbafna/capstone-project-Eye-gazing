import collections as _collections

if hasattr(dict, 'iteritems'):
    # pylint: disable=invalid-name
    _iteritems = lambda d: d.iteritems()
    _iterkeys = lambda d: d.iterkeys()
    def _sorted_iteritems(d):
        """Returns d's items in sorted order."""
        items = d.items()
        items.sort()
        return iter(items)
else:
    _sorted_iteritems = lambda d: sorted(d.items())  # pylint: disable=invalid-name
    _iteritems = lambda d: iter(d.items())  # pylint: disable=invalid-name
    _iterkeys = lambda d: iter(d.keys())  # pylint: disable=invalid-name

try:
    _basestring = basestring
except NameError:
    _basestring = str


class ShortKeyError(KeyError):
    pass


_SENTINEL = object()


class _Node(object):
    __slots__ = ('children', 'value')

    def __init__(self):
        self.children = {}
        self.value = _SENTINEL

    def iterate(self, path, shallow, iteritems):
        # Use iterative function with stack on the heap so we don't hit Python's
        # recursion depth limits.
        node = self
        stack = []
        while True:
            if node.value is not _SENTINEL:
                yield path, node.value

            if (not shallow or node.value is _SENTINEL) and node.children:
                stack.append(iter(iteritems(node.children)))
                path.append(None)

            while True:
                try:
                    step, node = next(stack[-1])
                    path[-1] = step
                    break
                except StopIteration:
                    stack.pop()
                    path.pop()
                except IndexError:
                    return

    def traverse(self, node_factory, path_conv, path, iteritems):
        def children():

            for step, node in iteritems(self.children):
                yield node.traverse(node_factory, path_conv, path + [step],
                                    iteritems)

        args = [path_conv, tuple(path), children()]

        if self.value is not _SENTINEL:
            args.append(self.value)

        return node_factory(*args)

    def __eq__(self, other):
        # Like iterate, we don't recurse so this works on deep tries.
        a, b = self, other
        stack = []
        while True:
            if a.value != b.value or len(a.children) != len(b.children):
                return False
            if a.children:
                stack.append((_iteritems(a.children), b.children))

            while True:
                try:
                    key, a = next(stack[-1][0])
                    b = stack[-1][1].get(key)
                    if b is None:
                        return False
                    break
                except StopIteration:
                    stack.pop()
                except IndexError:
                    return True

        return self.value == other.value and self.children == other.children

    def __ne__(self, other):
        return not self.__eq__(other)

    def __bool__(self):
        return bool(self.value is not _SENTINEL or self.children)

    __nonzero__ = __bool__

    __hash__ = None

    def __getstate__(self):
        # Like iterate, we don't recurse so pickling works on deep tries.
        state = [] if self.value is _SENTINEL else [0]
        last_cmd = 0
        node = self
        stack = []
        while True:
            if node.value is not _SENTINEL:
                last_cmd = 0
                state.append(node.value)
            stack.append(_iteritems(node.children))

            while True:
                try:
                    step, node = next(stack[-1])
                except StopIteration:
                    if last_cmd < 0:
                        state[-1] -= 1
                    else:
                        last_cmd = -1
                        state.append(-1)
                    stack.pop()
                    continue
                except IndexError:
                    if last_cmd < 0:
                        state.pop()
                    return state

                if last_cmd > 0:
                    last_cmd += 1
                    state[-last_cmd] += 1
                else:
                    last_cmd = 1
                    state.append(1)
                state.append(step)
                break

    def __setstate__(self, state):

        self.__init__()
        state = iter(state)
        stack = [self]
        for cmd in state:
            if cmd < 0:
                del stack[cmd:]
            else:
                while cmd > 0:
                    stack.append(type(self)())
                    stack[-2].children[next(state)] = stack[-1]
                    cmd -= 1
                stack[-1].value = next(state)


_NONE_PAIR = type('NonePair', (tuple,), {
    '__nonzero__': lambda _: False,
    '__bool__': lambda _: False,
    '__slots__': (),
})((None, None))


class Trie(_collections.MutableMapping):

    def __init__(self, *args, **kwargs):
        """Initialises the trie.

        Arguments are interpreted the same way :func:`Trie.update` interprets
        them.
        """
        self._root = _Node()
        self._sorted = False
        self.update(*args, **kwargs)

    @property
    def _iteritems(self):
        return _sorted_iteritems if self._sorted else _iteritems

    def enable_sorting(self, enable=True):
        self._sorted = enable

    def clear(self):
        """Removes all the values from the trie."""
        self._root = _Node()

    def update(self, *args, **kwargs):
        """Updates stored values.  Works like :func:`dict.update`."""
        if len(args) > 1:
            raise ValueError('update() takes at most one positional argument, '
                             '%d given.' % len(args))
        # We have this here instead of just letting MutableMapping.update()
        # handle things because it will iterate over keys and for each key
        # retrieve the value.  With Trie, this may be expensive since the path
        # to the node would have to be walked twice.  Instead, we have our own
        # implementation where iteritems() is used avoiding the unnecessary
        # value look-up.
        if args and isinstance(args[0], Trie):
            for key, value in _iteritems(args[0]):
                self[key] = value
            args = ()
        super(Trie, self).update(*args, **kwargs)

    def copy(self):
        """Returns a shallow copy of the trie."""
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, keys, value=None):
        trie = cls()
        for key in keys:
            trie[key] = value
        return trie

    def _get_node(self, key, create=False):
        node = self._root
        trace = [(None, node)]
        for step in self.__path_from_key(key):
            if create:
                node = node.children.setdefault(step, _Node())
            else:
                node = node.children.get(step)
                if not node:
                    raise KeyError(key)
            trace.append((step, node))
        return node, trace

    def __iter__(self):
        return self.iterkeys()

    # pylint: disable=arguments-differ

    def iteritems(self, prefix=_SENTINEL, shallow=False):
        node, _ = self._get_node(prefix)
        for path, value in node.iterate(list(self.__path_from_key(prefix)),
                                        shallow, self._iteritems):
            yield (self._key_from_path(path), value)

    def iterkeys(self, prefix=_SENTINEL, shallow=False):
        for key, _ in self.iteritems(prefix=prefix, shallow=shallow):
            yield key

    def itervalues(self, prefix=_SENTINEL, shallow=False):
        node, _ = self._get_node(prefix)
        for _, value in node.iterate(list(self.__path_from_key(prefix)),
                                     shallow, self._iteritems):
            yield value

    def items(self, prefix=_SENTINEL, shallow=False):
        return list(self.iteritems(prefix=prefix, shallow=shallow))

    def keys(self, prefix=_SENTINEL, shallow=False):
        return list(self.iterkeys(prefix=prefix, shallow=shallow))

    def values(self, prefix=_SENTINEL, shallow=False):
        return list(self.itervalues(prefix=prefix, shallow=shallow))

    # pylint: enable=arguments-differ

    def __len__(self):
        return sum(1 for _ in self.itervalues())

    def __nonzero__(self):
        return bool(self._root)

    HAS_VALUE = 1
    HAS_SUBTRIE = 2

    def has_node(self, key):
        try:
            node, _ = self._get_node(key)
        except KeyError:
            return 0
        return ((self.HAS_VALUE * int(node.value is not _SENTINEL)) |
                        (self.HAS_SUBTRIE * int(bool(node.children))))

    def has_key(self, key):
        return bool(self.has_node(key) & self.HAS_VALUE)

    def has_subtrie(self, key):
        return bool(self.has_node(key) & self.HAS_SUBTRIE)

    @staticmethod
    def _slice_maybe(key_or_slice):
        if isinstance(key_or_slice, slice):
            if key_or_slice.stop is not None or key_or_slice.step is not None:
                raise TypeError(key_or_slice)
            return key_or_slice.start, True
        return key_or_slice, False

    def __getitem__(self, key_or_slice):
        if self._slice_maybe(key_or_slice)[1]:
            return self.itervalues(key_or_slice.start)
        node, _ = self._get_node(key_or_slice)
        if node.value is _SENTINEL:
            raise ShortKeyError(key_or_slice)
        return node.value

    def _set(self, key, value, only_if_missing=False, clear_children=False):
        node, _ = self._get_node(key, create=True)
        if not only_if_missing or node.value is _SENTINEL:
            node.value = value
        if clear_children:
            node.children.clear()
        return node.value

    def __setitem__(self, key_or_slice, value):
        key, is_slice = self._slice_maybe(key_or_slice)
        self._set(key, value, clear_children=is_slice)

    def setdefault(self, key, value=None):
        return self._set(key, value, only_if_missing=True)

    @staticmethod
    def _cleanup_trace(trace):
        i = len(trace) - 1  # len(path) >= 1 since root is always there
        step, node = trace[i]
        while i and not node:
            i -= 1
            parent_step, parent = trace[i]
            del parent.children[step]
            step, node = parent_step, parent

    def _pop_from_node(self, node, trace, default=_SENTINEL):
        if node.value is not _SENTINEL:
            value = node.value
            node.value = _SENTINEL
            self._cleanup_trace(trace)
            return value
        elif default is _SENTINEL:
            raise ShortKeyError()
        else:
            return default

    def pop(self, key, default=_SENTINEL):
        try:
            return self._pop_from_node(*self._get_node(key))
        except KeyError:
            if default is not _SENTINEL:
                return default
            raise

    def popitem(self):
        if not self:
            raise KeyError()
        node = self._root
        trace = [(None, node)]
        while node.value is _SENTINEL:
            step = next(_iterkeys(node.children))
            node = node.children[step]
            trace.append((step, node))
        return (self._key_from_path((step for step, _ in trace[1:])),
                        self._pop_from_node(node, trace))

    def __delitem__(self, key_or_slice):
        key, is_slice = self._slice_maybe(key_or_slice)
        node, trace = self._get_node(key)
        if is_slice:
            node.children.clear()
        elif node.value is _SENTINEL:
            raise ShortKeyError(key)
        node.value = _SENTINEL
        self._cleanup_trace(trace)

    def prefixes(self, key):
        node = self._root
        path = self.__path_from_key(key)
        pos = 0
        while True:
            if node.value is not _SENTINEL:
                yield self._key_from_path(path[:pos]), node.value
            if pos == len(path):
                break
            node = node.children.get(path[pos])
            if not node:
                break
            pos += 1

    def shortest_prefix(self, key):
        return next(self.prefixes(key), _NONE_PAIR)

    def longest_prefix(self, key):
        ret = _NONE_PAIR
        for ret in self.prefixes(key):
            pass
        return ret

    def __eq__(self, other):
        return self._root == other._root  # pylint: disable=protected-access

    def __ne__(self, other):
        return self._root != other._root  # pylint: disable=protected-access

    def __str__(self):
        return 'Trie(%s)' % (
                ', '.join('%s: %s' % item for item in self.iteritems()))

    def __repr__(self):
        if self:
            return  'Trie((%s,))' % (
                    ', '.join('(%r, %r)' % item for item in self.iteritems()))
        else:
            return 'Trie()'

    def __path_from_key(self, key):
        return () if key is _SENTINEL else self._path_from_key(key)

    def _path_from_key(self, key):  # pylint: disable=no-self-use
        return key

    def _key_from_path(self, path):
        return tuple(path)

    def traverse(self, node_factory, prefix=_SENTINEL):

        node, _ = self._get_node(prefix)
        return node.traverse(node_factory, self._key_from_path,
                             list(self.__path_from_key(prefix)),
                             self._iteritems)

class CharTrie(Trie):
    def _key_from_path(self, path):
        return ''.join(path)


class StringTrie(Trie):


    def __init__(self, *args, **kwargs):
        separator = kwargs.pop('separator', '/')
        if not isinstance(separator, _basestring):
            raise TypeError('separator must be a string')
        if not separator:
            raise ValueError('separator can not be empty')
        self._separator = separator
        super(StringTrie, self).__init__(*args, **kwargs)

    @classmethod
    def fromkeys(cls, keys, value=None, separator='/'):  # pylint: disable=arguments-differ
        trie = cls(separator=separator)
        for key in keys:
            trie[key] = value
        return trie

    def _path_from_key(self, key):
        return key.split(self._separator)

    def _key_from_path(self, path):
        return self._separator.join(path)


class PrefixSet(_collections.MutableSet):  # pylint: disable=abstract-class-not-used


    def __init__(self, iterable=None, factory=Trie, **kwargs):
        super(PrefixSet, self).__init__()
        trie = factory(**kwargs)
        if iterable:
            trie.update((key, True) for key in iterable)
        self._trie = trie

    def copy(self):
        return self.__class__(self._trie)

    def clear(self):
        self._trie.clear()

    def __contains__(self, key):
        return bool(self._trie.shortest_prefix(key)[1])

    def __iter__(self):
        return self._trie.iterkeys()

    def iter(self, prefix=_SENTINEL):
        if prefix is _SENTINEL:
            return iter(self)
        elif self._trie.has_node(prefix):
            return self._trie.iterkeys(prefix=prefix)
        elif prefix in self:
            # Make sure the type of returned keys is consistent.
            # pylint: disable=protected-access
            return self._trie._key_from_path(self._trie._path_from_key(prefix)),
        else:
            return ()

    def __len__(self):
        return len(self._trie)

    def add(self, key):

        if key not in self:
            self._trie[key:] = True

    def discard(self, key):
        raise NotImplementedError(
            'Removing keys from PrefixSet is not implemented.')

    def remove(self, key):
        raise NotImplementedError(
            'Removing keys from PrefixSet is not implemented.')

    def pop(self):
        raise NotImplementedError(
            'Removing keys from PrefixSet is not implemented.')
