#!/usr/bin/env python

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                os.path.pardir,
                                os.path.pardir))

from gsdview import pluginmanager
from gsdview.pluginmanager import VERSION_CHECK_RE

import unittest

class TestVersinonCheckRe(unittest.TestCase):

    def test_name(self):
        m = VERSION_CHECK_RE.match('gsdview')
        self.assertEqual(m.group('name'), 'gsdview')

    def test_name_only(self):
        m = VERSION_CHECK_RE.match('gsdview')
        self.assertEqual(m.group('name'), 'gsdview')
        self.assertFalse(m.group('spec'))
        self.assertFalse(m.group('op'))
        self.assertFalse(m.group('version'))

    def test_invalid_name1(self):
        # spaces before name

        for s in (' gsdview', '\tgsdview', '  gsdview', '\t gsdview',
                  '\n gsdview'):
            m = VERSION_CHECK_RE.match(s)
            self.assertFalse(m)

    def test_invalid_name2(self):
        # spaces after name

        for s in ('gsdview ', 'gsdview  ', 'gsdview\t', 'gsdview \t',
                  'gsdview\t '):
            m = VERSION_CHECK_RE.match(s)
            self.assertFalse(m)

    def test_invalid_name3(self):
        # nawline after name

        for s in ('gsdview\n', 'gsdview \n', 'gsdview\n ', 'gsdview \n '):
            m = VERSION_CHECK_RE.match(s)
            self.assertFalse(m)

    def test_spec(self):
        for s in ('gsdview==1.0', 'gsdview== 1.0', 'gsdview ==1.0',
                  'gsdview == 1.0'):
            m = VERSION_CHECK_RE.match(s)
            self.assertEqual(m.group('name'), 'gsdview')
            self.assertTrue(m.group('spec'))
            self.assertEqual(m.group('op'), '==')
            self.assertEqual(m.group('version'), '1.0')

    def test_invalid_spec(self):
        for s in ('gsdview\n==1.0', 'gsdview \n== 1.0', 'gsdview ==\n1.0'):
            m = VERSION_CHECK_RE.match(s)
            self.assertFalse(m)

    def test_op(self):
        for op in ('==', '!=', '>', '>=', '<', '<='):
            s = 'gsdview%s1.0' % op
            m = VERSION_CHECK_RE.match(s)
            self.assertEqual(m.group('op'), op)

    def test_invalid_op(self):
        for op in ('=', '===', '!!=', '!==', '>>', '>>=', '>==', '<<', '<<=',
                   '<=='):
            s = 'gsdview%s1.0' % op
            m = VERSION_CHECK_RE.match(s)
            self.assertFalse(m)

    def test_simple_version(self):
        for version in ('1', '1.0', '1.0.1'):
            s = 'gsdview==%s' % version
            m = VERSION_CHECK_RE.match(s)
            self.assertEqual(m.group('version'), version)

    def test_decorated_version(self):
        for version in ('1', '1.0', '1.0.1'):
            for separator in ('', '-', '_', '+'):
                for decoration in ('b', 'b3', 'beta', 'beta3'):
                    s = 'gsdview==%s%s%s' % (version, separator, decoration)
                    m = VERSION_CHECK_RE.match(s)
                    self.assertEqual(m.group('version'), version)

    #~ def test_date_decorated_version(self):
        #~ decoration = '20091130'
        #~ for version in ('1', '1.0', '1.0.1'):
            #~ for separator in ('-', '_', '+'):
                #~ s = 'gsdview==%s%s%s' % (version, separator, decoration)
                #~ m = VERSION_CHECK_RE.match(s)
                #~ self.assertEqual(m.group('version'), version)

    def test_invalid_version1(self):
        for version in ('1.', '1.0.', '1.0.1-', '1.0.1a-', '1.0.1-b-',
                        '1.0.1beta-', '1.0.1-beta-', '1..0', '.0', '1.0.0.0'):
            s = 'gsdview==%s' % version
            m = VERSION_CHECK_RE.match(s)
            self.assertFalse(m)

    def test_invalid_version2(self):
        for version in ('1,0', '1 0', '-1 0'):
            s = 'gsdview==%s' % version
            m = VERSION_CHECK_RE.match(s)
            self.assertFalse(m)


if __name__ == '__main__':
    unittest.main()
