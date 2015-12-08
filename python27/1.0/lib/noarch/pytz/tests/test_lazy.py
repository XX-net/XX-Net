from operator import *
import os.path
import sys
import unittest
import warnings


if __name__ == '__main__':
    # Only munge path if invoked as a script. Testrunners should have setup
    # the paths already
    sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, os.pardir)))


from pytz.lazy import LazyList, LazySet


class LazyListTestCase(unittest.TestCase):
    initial_data = [3,2,1]

    def setUp(self):
        self.base = [3, 2, 1]
        self.lesser = [2, 1, 0]
        self.greater = [4, 3, 2]

        self.lazy = LazyList(iter(list(self.base)))

    def test_unary_ops(self):
        unary_ops = [str, repr, len, bool, not_]
        try:
            unary_ops.append(unicode)
        except NameError:
            pass  # unicode no longer exists in Python 3.

        for op in unary_ops:
            self.assertEqual(
                op(self.lazy),
                op(self.base), str(op))

    def test_binary_ops(self):
        binary_ops = [eq, ge, gt, le, lt, ne, add, concat]
        try:
            binary_ops.append(cmp)
        except NameError:
            pass  # cmp no longer exists in Python 3.

        for op in binary_ops:
            self.assertEqual(
                op(self.lazy, self.lazy),
                op(self.base, self.base), str(op))
            for other in [self.base, self.lesser, self.greater]:
                self.assertEqual(
                    op(self.lazy, other),
                    op(self.base, other), '%s %s' % (op, other))
                self.assertEqual(
                    op(other, self.lazy),
                    op(other, self.base), '%s %s' % (op, other))

        # Multiplication
        self.assertEqual(self.lazy * 3, self.base * 3)
        self.assertEqual(3 * self.lazy, 3 * self.base)

        # Contains
        self.assertTrue(2 in self.lazy)
        self.assertFalse(42 in self.lazy)

    def test_iadd(self):
        self.lazy += [1]
        self.base += [1]
        self.assertEqual(self.lazy, self.base)

    def test_bool(self):
        self.assertTrue(bool(self.lazy))
        self.assertFalse(bool(LazyList()))
        self.assertFalse(bool(LazyList(iter([]))))

    def test_hash(self):
        self.assertRaises(TypeError, hash, self.lazy)

    def test_isinstance(self):
        self.assertTrue(isinstance(self.lazy, list))
        self.assertFalse(isinstance(self.lazy, tuple))

    def test_callable(self):
        try:
            callable
        except NameError:
            return  # No longer exists with Python 3.
        self.assertFalse(callable(self.lazy))

    def test_append(self):
        self.base.append('extra')
        self.lazy.append('extra')
        self.assertEqual(self.lazy, self.base)

    def test_count(self):
        self.assertEqual(self.lazy.count(2), 1)

    def test_index(self):
        self.assertEqual(self.lazy.index(2), 1)

    def test_extend(self):
        self.base.extend([6, 7])
        self.lazy.extend([6, 7])
        self.assertEqual(self.lazy, self.base)

    def test_insert(self):
        self.base.insert(0, 'ping')
        self.lazy.insert(0, 'ping')
        self.assertEqual(self.lazy, self.base)

    def test_pop(self):
        self.assertEqual(self.lazy.pop(), self.base.pop())
        self.assertEqual(self.lazy, self.base)

    def test_remove(self):
        self.base.remove(2)
        self.lazy.remove(2)
        self.assertEqual(self.lazy, self.base)

    def test_reverse(self):
        self.base.reverse()
        self.lazy.reverse()
        self.assertEqual(self.lazy, self.base)

    def test_reversed(self):
        self.assertEqual(list(reversed(self.lazy)), list(reversed(self.base)))

    def test_sort(self):
        self.base.sort()
        self.assertNotEqual(self.lazy, self.base, 'Test data already sorted')
        self.lazy.sort()
        self.assertEqual(self.lazy, self.base)

    def test_sorted(self):
        self.assertEqual(sorted(self.lazy), sorted(self.base))

    def test_getitem(self):
        for idx in range(-len(self.base), len(self.base)):
            self.assertEqual(self.lazy[idx], self.base[idx])

    def test_setitem(self):
        for idx in range(-len(self.base), len(self.base)):
            self.base[idx] = idx + 1000
            self.assertNotEqual(self.lazy, self.base)
            self.lazy[idx] = idx + 1000
            self.assertEqual(self.lazy, self.base)

    def test_delitem(self):
        del self.base[0]
        self.assertNotEqual(self.lazy, self.base)
        del self.lazy[0]
        self.assertEqual(self.lazy, self.base)

        del self.base[-2]
        self.assertNotEqual(self.lazy, self.base)
        del self.lazy[-2]
        self.assertEqual(self.lazy, self.base)

    def test_iter(self):
        self.assertEqual(list(iter(self.lazy)), list(iter(self.base)))

    def test_getslice(self):
        for i in range(-len(self.base), len(self.base)):
            for j in range(-len(self.base), len(self.base)):
                for step in [-1, 1]:
                    self.assertEqual(self.lazy[i:j:step], self.base[i:j:step])

    def test_setslice(self):
        for i in range(-len(self.base), len(self.base)):
            for j in range(-len(self.base), len(self.base)):
                for step in [-1, 1]:
                    replacement = range(0, len(self.base[i:j:step]))
                    self.base[i:j:step] = replacement
                    self.lazy[i:j:step] = replacement
                    self.assertEqual(self.lazy, self.base)

    def test_delslice(self):
        del self.base[0:1]
        del self.lazy[0:1]
        self.assertEqual(self.lazy, self.base)

        del self.base[-1:1:-1]
        del self.lazy[-1:1:-1]
        self.assertEqual(self.lazy, self.base)


class LazySetTestCase(unittest.TestCase):
    initial_data = set([3,2,1])

    def setUp(self):
        self.base = set([3, 2, 1])
        self.lazy = LazySet(iter(set(self.base)))

    def test_unary_ops(self):
        # These ops just need to work.
        unary_ops = [str, repr]
        try:
            unary_ops.append(unicode)
        except NameError:
            pass  # unicode no longer exists in Python 3.

        for op in unary_ops:
            op(self.lazy)  # These ops just need to work.

        # These ops should return identical values as a real set.
        unary_ops = [len, bool, not_]

        for op in unary_ops:
            self.assertEqual(
                op(self.lazy),
                op(self.base), '%s(lazy) == %r' % (op, op(self.lazy)))

    def test_binary_ops(self):
        binary_ops = [eq, ge, gt, le, lt, ne, sub, and_, or_, xor]
        try:
            binary_ops.append(cmp)
        except NameError:
            pass  # cmp no longer exists in Python 3.

        for op in binary_ops:
            self.assertEqual(
                op(self.lazy, self.lazy),
                op(self.base, self.base), str(op))
            self.assertEqual(
                op(self.lazy, self.base),
                op(self.base, self.base), str(op))
            self.assertEqual(
                op(self.base, self.lazy),
                op(self.base, self.base), str(op))

        # Contains
        self.assertTrue(2 in self.lazy)
        self.assertFalse(42 in self.lazy)

    def test_iops(self):
        try:
            iops = [isub, iand, ior, ixor]
        except NameError:
            return  # Don't exist in older Python versions.
        for op in iops:
            # Mutating operators, so make fresh copies.
            lazy = LazySet(self.base)
            base = self.base.copy()
            op(lazy, set([1]))
            op(base, set([1]))
            self.assertEqual(lazy, base, str(op))

    def test_bool(self):
        self.assertTrue(bool(self.lazy))
        self.assertFalse(bool(LazySet()))
        self.assertFalse(bool(LazySet(iter([]))))

    def test_hash(self):
        self.assertRaises(TypeError, hash, self.lazy)

    def test_isinstance(self):
        self.assertTrue(isinstance(self.lazy, set))

    def test_callable(self):
        try:
            callable
        except NameError:
            return  # No longer exists with Python 3.
        self.assertFalse(callable(self.lazy))

    def test_add(self):
        self.base.add('extra')
        self.lazy.add('extra')
        self.assertEqual(self.lazy, self.base)

    def test_copy(self):
        self.assertEqual(self.lazy.copy(), self.base)

    def test_method_ops(self):
        ops = [
            'difference', 'intersection', 'isdisjoint',
            'issubset', 'issuperset', 'symmetric_difference', 'union',
            'difference_update', 'intersection_update',
            'symmetric_difference_update', 'update']
        for op in ops:
            if not hasattr(set, op):
                continue  # Not in this version of Python.
            # Make a copy, as some of the ops are mutating.
            lazy = LazySet(set(self.base))
            base = set(self.base)
            self.assertEqual(
                getattr(self.lazy, op)(set([1])),
                getattr(self.base, op)(set([1])), op)
            self.assertEqual(self.lazy, self.base, op)

    def test_discard(self):
        self.base.discard(1)
        self.assertNotEqual(self.lazy, self.base)
        self.lazy.discard(1)
        self.assertEqual(self.lazy, self.base)

    def test_pop(self):
        self.assertEqual(self.lazy.pop(), self.base.pop())
        self.assertEqual(self.lazy, self.base)

    def test_remove(self):
        self.base.remove(2)
        self.lazy.remove(2)
        self.assertEqual(self.lazy, self.base)

    def test_clear(self):
        self.lazy.clear()
        self.assertEqual(self.lazy, set())


if __name__ == '__main__':
    warnings.simplefilter("error") # Warnings should be fatal in tests.
    unittest.main()
