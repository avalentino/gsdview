#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Copyright (C) 2008-2011 Antonio Valentino <a_valentino@users.sf.net>

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


class TestLinearStretcher(unittest.TestCase):
    def test_noclip(self):
        stretch = LinearStretcher()
        data = np.arange(256)
        output = stretch(data)
        refout = data
        self.assert_(np.all(output == refout))

    def test_clipping1(self):
        stretch = LinearStretcher()
        data = np.arange(512)
        output = stretch(data)
        refout = data
        refout[256:] = 255
        self.assert_(np.all(output == refout))

    def test_clipping2(self):
        stretch = LinearStretcher()
        data = np.arange(512) - 10
        output = stretch(data)
        refout = data
        refout[:10] = 0
        refout[266:] = 255
        self.assert_(np.all(output == refout))

    def test_offset(self):
        stretch = LinearStretcher(offset=10)
        data = np.arange(256) + 10
        output = stretch(data)
        refout = data - 10
        self.assert_(np.all(output == refout))

    def test_scale1(self):
        stretch = LinearStretcher(scale=0.5)
        data = np.arange(512)
        output = stretch(data)
        refout = np.clip(data / 2, 0, 255)
        self.assert_(np.all(output == refout))

    def test_scale2(self):
        stretch = LinearStretcher(scale=0.5, dtype='float')
        data = np.arange(512)
        output = stretch(data)
        refout = np.clip(data / 2., 0, 255)
        self.assert_(np.all(output == refout))

    def test_offset_and_scale(self):
        stretch = LinearStretcher(scale=0.5, offset=10)
        data = np.arange(512) + 10
        output = stretch(data)
        refout = np.clip((data - 10) / 2, 0, 255)
        self.assert_(np.all(output == refout))

    def test_set_imput_range1(self):
        stretch = LinearStretcher()
        stretch.set_range(10, 265)

        self.assertEqual(stretch.offset, 10)
        self.assertEqual(stretch.scale, 1)

        data = np.arange(512) + 10
        output = stretch(data)
        refout = np.clip(data - 10, 0, 255)

        self.assert_(np.all(output == refout))

    def test_set_imput_range2(self):
        stretch = LinearStretcher()
        stretch.set_range(10, 521)

        scale = 255. / 511  # (omax - omin) / (imax - imin)
        self.assertEqual(stretch.scale, scale)
        self.assertEqual(stretch.offset, 10)

        data = np.arange(512) + 10
        output = stretch(data)
        refout = (scale * (data - 10)).astype('uint8')

        self.assert_(np.all(output == refout))

        self.assertEqual(output.max(), 255)


class TestLUTStretcher(unittest.TestCase):
    def test_clipping(self):
        stretch = LUTStretcher()
        indata = np.arange(-10, 299)
        outdata = stretch(indata)
        self.assertTrue(np.all(outdata[:11] == 0))
        self.assertTrue(np.all(outdata[10:266] == indata[10:266]))
        self.assertTrue(np.all(outdata[266:] == 255))

    def test_input_range(self):
        stretch = LUTStretcher(vmin=10, vmax=20)
        stretch.set_range(10, 20)
        indata = np.arange(30)
        outdata = stretch(indata)
        self.assertTrue(np.all(outdata[:10] == 10))
        self.assertTrue(np.all(outdata[10:20] == indata[10:20]))
        self.assertTrue(np.all(outdata[20:] == 20))

    def test_negative_offset(self):
        stretch = LUTStretcher(vmax=20)
        stretch.set_range(-10, 10)
        outdata = stretch(np.arange(-20, 20))
        self.assertTrue(np.all(outdata[:10] == 0))
        self.assertTrue(np.all(outdata[10:-10] == np.arange(20)))
        self.assertTrue(np.all(outdata[-10:] == 20))

if __name__ == '__main__':
    unittest.main()
