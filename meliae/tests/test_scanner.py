# Copyright (C) 2009 Canonical Ltd
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU General Public License and
# the GNU Lesser General Public License along with this program.  If
# not, see <http://www.gnu.org/licenses/>.

"""The core routines for scanning python references and dumping memory info."""

import tempfile

from meliae import (
    scanner,
    tests,
    )
from meliae.tests import test__scanner


class TestDumpAllReferenced(tests.TestCase):

    def assertDumpAllReferenced(self, ref_objs, obj):
        t = tempfile.TemporaryFile(prefix='meliae-')
        # On some platforms TemporaryFile returns a wrapper object with 'file'
        # being the real object, on others, the returned object *is* the real
        # file object
        t_file = getattr(t, 'file', t)
        scanner.dump_all_referenced(t_file, obj)
        t.flush()
        t.seek(0)
        # We don't care if the same entries are printed multiple times, just
        # that they are all correct
        lines = t.readlines()
        # py_dump_object_info will create a string that covers multpile lines,
        # so we need to split it back into 1-line-per-record
        ref_lines = [test__scanner.py_dump_object_info(ref_obj)
                     for ref_obj in ref_objs]
        ref_lines = set(''.join(ref_lines).splitlines(True))
        self.assertEqual(sorted(ref_lines), sorted(lines))

    def test_dump_str(self):
        s = 'a test string'
        self.assertDumpAllReferenced([s], s)

    def test_dump_obj(self):
        o = object()
        self.assertDumpAllReferenced([o], o)

    def test_dump_simple_tuple(self):
        k = 10245
        v = 'a value string'
        t = (k, v)
        self.assertDumpAllReferenced([k, v, t], t)

    def test_dump_list_of_tuple(self):
        k = 10245
        v = 'a value string'
        t = (k, v)
        l = [k, v, t]
        self.assertDumpAllReferenced([k, v, l, t], l)

    def test_dump_recursive(self):
        a = 1
        b = 'str'
        c = {}
        l = [a, b, c]
        c[a] = l
        # We have a reference cycle here, but we should not loop endlessly :)
        self.assertDumpAllReferenced([a, b, c, l], l)
        self.assertDumpAllReferenced([a, b, c, l], c)


class TestGetRecursiveSize(tests.TestCase):

    def assertRecursiveSize(self, n_objects, total_size, obj):
        self.assertEqual((n_objects, total_size),
                         scanner.get_recursive_size(obj))

    def test_single_object(self):
        i = 1
        self.assertRecursiveSize(1, scanner.size_of(i), i)
        d = {}
        self.assertRecursiveSize(1, scanner.size_of(d), d)
        l = []
        self.assertRecursiveSize(1, scanner.size_of(l), l)

    def test_referenced(self):
        s1 = 'this is a simple string'
        s2 = 'and this is another one'
        s3 = s1 + s2
        s4 = 'this is a' + ' simple string'# same as s1, but diff object
        self.assertTrue(s1 is not s4)
        self.assertTrue(s1 == s4)
        d = {s1:s2, s3:s4}
        total_size = (scanner.size_of(s1) + scanner.size_of(s2)
                      + scanner.size_of(s3) + scanner.size_of(s4)
                      + scanner.size_of(d))
        self.assertRecursiveSize(5, total_size, d)

    def test_recursive(self):
        s1 = 'this is a simple string'
        s2 = 'and this is another one'
        l = [s1, s2]
        l.append(l)
        total_size = (scanner.size_of(s1) + scanner.size_of(s2)
                      + scanner.size_of(l))
        self.assertRecursiveSize(3, total_size, l)
