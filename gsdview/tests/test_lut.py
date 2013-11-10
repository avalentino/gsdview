#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Copyright (C) 2008-2013 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of exectools.

### This module is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### This module is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with this module; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US

import os
import sys
import unittest

# Fix sys path
from os.path import abspath, dirname
GSDVIEWROOT = abspath(os.path.join(dirname(__file__), os.pardir, os.pardir))
sys.path.insert(0, GSDVIEWROOT)


import numpy as np
from gsdview.imgutils import *


class TestLinearLUT(unittest.TestCase):
    def test_all_defaults(self):
        lut = linear_lut()
        self.assertEqual(lut.dtype, np.uint8)
        self.assertTrue(np.all(lut == np.arange(2 ** 8, dtype='uint8')))

    def test_dtype_uint8(self):
        lut = linear_lut(dtype='uint8')
        self.assertEqual(lut.dtype, np.uint8)
        self.assertTrue(np.all(lut == np.arange(2 ** 8, dtype='uint8')))

    def test_dtype_uint16(self):
        lut = linear_lut(dtype='uint16')
        self.assertEqual(lut.dtype, np.uint16)
        self.assertTrue(np.all(lut == np.arange(2 ** 16, dtype='uint16')))

    def test_dtype_invalid(self):
        self.assertRaises(TypeError, linear_lut, dtype=0)

    def test_dtype_out_of_range(self):
        invalid_types = [
            v for k, v in np.typeDict.iteritems() if isinstance(k, int)
        ]
        invalid_types.remove(np.uint8)
        invalid_types.remove(np.uint16)
        for type_ in invalid_types:
            self.assertRaises(ValueError, linear_lut, dtype=type_)

    def test_fill_false1(self):
        lut = linear_lut(100, 199)
        self.assertEqual(len(lut), 200)

    def test_fill_false2(self):
        lut = linear_lut(100, 3000)
        self.assertEqual(len(lut), 3001)

    def test_fill_true1(self):
        lut = linear_lut(100, 199, fill=True)
        self.assertEqual(len(lut), 256)

    def test_fill_true2(self):
        lut = linear_lut(100, 3000, fill=True)
        self.assertEqual(len(lut), 3001)

    def test_fill1(self):
        lut = linear_lut(100, 199, fill=500)
        self.assertEqual(len(lut), 500)

    def test_fill2(self):
        lut = linear_lut(100, 3000, fill=500)
        self.assertEqual(len(lut), 3001)

    def test_offset(self):
        lut = linear_lut(10, 265, fill=True)
        expected_lut = np.zeros(266, dtype='uint8')
        expected_lut[:10] = 0
        expected_lut[10:] = np.linspace(0, 255, 256)
        self.assertEqual(len(lut), len(expected_lut))
        self.assertTrue(np.all(lut == expected_lut))

    def test_scale(self):
        lut = linear_lut(0, 511)
        expected_lut = np.arange(256)
        expected_lut = np.repeat(expected_lut, 2)
        self.assertEqual(len(lut), len(expected_lut))
        self.assertTrue(np.all(lut == expected_lut))

    def test_omax(self):
        lut = linear_lut(0, 399, omax=199)
        expected_lut = np.arange(200)
        expected_lut = np.repeat(expected_lut, 2)
        self.assertEqual(len(lut), len(expected_lut))
        self.assertTrue(np.all(lut == expected_lut))

    def test_omin(self):
        lut = linear_lut(0, 399, omin=10, omax=209)
        expected_lut = np.arange(200)
        expected_lut = np.repeat(expected_lut, 2) + 10
        self.assertEqual(len(lut), len(expected_lut))
        self.assertTrue(np.all(lut == expected_lut))

    def test_vmin_omin(self):
        lut = linear_lut(10, 209, omin=10, omax=209)
        expected_lut = np.arange(210)
        expected_lut[:10] = 10
        self.assertEqual(len(lut), len(expected_lut))
        self.assertTrue(np.all(lut == expected_lut))

#~ class TestHistogramEqualizedLUT(unittest.TestCase):
    #~ def test_(self):
        #~ pass


if __name__ == '__main__':
    unittest.main()
