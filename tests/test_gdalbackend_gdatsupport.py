# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2015 Antonio Valentino <antonio.valentino@tiscali.it>
#
# This module is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 2 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this module if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US

import os
import sys
import shutil
import tempfile
import unittest
from xml.etree import ElementTree as etree

import numpy as np
from osgeo import gdal
from osgeo.gdal_array import NumericTypeCodeToGDALTypeCode

# Fix sys path
GSDVIEWROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, GSDVIEWROOT)

from gsdview.gdalbackend import gdalsupport


class SafeVrtCopyTestCase01(unittest.TestCase):
    SRCFILENAME = 'dataset.vrt'
    DSTFILENAME = 'dataset-copy.vrt'
    XSIZE = 12
    YSIZE = 4
    DTYPE = np.float
    RELATIVE_TO_VRT = 0

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix=self.__class__.__name__ + '_')
        self.srcfilename = os.path.join(self.root, self.SRCFILENAME)
        self.dstfilename = os.path.join(self.root, self.DSTFILENAME)
        self.data = self._make_tmp_data()
        self._make_tmp_vrt(self.srcfilename, self.data,
                           relativeToVRT=self.RELATIVE_TO_VRT)
        os.makedirs(os.path.dirname(self.dstfilename), exist_ok=True)

    def _make_tmp_data(self):
        data = np.arange(self.YSIZE * self.XSIZE, dtype=self.DTYPE)
        data.shape = (self.YSIZE, self.XSIZE)
        return data

    def _make_tmp_vrt(self, filename, data=None, relativeToVRT=False):
        dirname = os.path.dirname(filename)
        os.makedirs(dirname, exist_ok=True)

        old_dirname = os.getcwd()

        if relativeToVRT:
            filename = os.path.basename(filename)
            os.chdir(dirname)

        try:
            driver = gdal.GetDriverByName('VRT')
            ds = driver.Create(filename, self.XSIZE, self.YSIZE, 0)

            if relativeToVRT:
                srcpath = os.path.basename(filename) + '.raw'
            else:
                srcpath = filename + '.raw'

            if self.data is not None:
                gdtype = NumericTypeCodeToGDALTypeCode(data.dtype)
            else:
                gdtype = gdal.GDT_Byte

            pixel_offset = gdal.GetDataTypeSize(gdtype) // 8

            options = {
                'subClass': 'VRTRawRasterBand',
                'SourceFilename': srcpath,
                'ImageOffset': 0,
                'PixelOffset': pixel_offset,
                'LineOffset': pixel_offset * self.XSIZE,
                'relativeToVRT': int(relativeToVRT),
            }
            options = ['{}={}'.format(k, v) for k, v in options.items()]

            ds.AddBand(gdtype, options)

            if self.data is not None:
                b = ds.GetRasterBand(1)
                b.WriteArray(data)
            ds.FlushCache()
        finally:
            os.chdir(old_dirname)

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_copy_file(self):
        self.assertFalse(os.path.exists(self.dstfilename))
        gdalsupport.safe_vrt_copy(self.srcfilename, self.dstfilename)
        self.assertTrue(os.path.exists(self.dstfilename))

    def test_copy_ds(self):
        self.assertFalse(os.path.exists(self.dstfilename))
        ds = gdal.Open(self.srcfilename)
        self.assertTrue(ds is not None)
        gdalsupport.safe_vrt_copy(ds, self.dstfilename)
        self.assertTrue(os.path.exists(self.dstfilename))

    def test_copy_open(self):
        gdalsupport.safe_vrt_copy(self.srcfilename, self.dstfilename)
        ds = gdal.Open(self.dstfilename)
        self.assertTrue(ds is not None)

    def test_relative_to_vrt(self):
        gdalsupport.safe_vrt_copy(self.srcfilename, self.dstfilename)

        xml = etree.parse(self.dstfilename)
        sources = list(xml.iter('SourceFilename'))
        self.assertGreater(len(sources), 0)
        for element in sources:
            # with self.subTest( XXX )
            relativeToVRT = element.get('relativeToVRT')
            self.assertTrue(relativeToVRT is not None)
            self.assertEqual(relativeToVRT, '0')


class SafeVrtCopyTestCase02(SafeVrtCopyTestCase01):
    RELATIVE_TO_VRT = 1


class SafeVrtCopyTestCase03(SafeVrtCopyTestCase01):
    SRCFILENAME = 'data/dataset.vrt'
    DSTFILENAME = 'dataset-copy.vrt'
    RELATIVE_TO_VRT = 0


class SafeVrtCopyTestCase04(SafeVrtCopyTestCase03):
    RELATIVE_TO_VRT = 1


class SafeVrtCopyTestCase05(SafeVrtCopyTestCase01):
    SRCFILENAME = 'data/dataset.vrt'
    DSTFILENAME = 'out/dataset-copy.vrt'
    RELATIVE_TO_VRT = 0


class SafeVrtCopyTestCase06(SafeVrtCopyTestCase05):
    RELATIVE_TO_VRT = 1


if __name__ == '__main__':
    unittest.main()
