#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2020 Antonio Valentino <antonio.valentino@tiscali.it>
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
import shutil
import tempfile
import unittest


from gsdview import utils


class TestDirectorySize(unittest.TestCase):
    DATASIZE = 1024     # 1 kbyte

    def setUp(self):
        self.dirname = tempfile.mkdtemp(prefix='gsdview_test_utils_')

    def _popuate_test_dir(self):
        data = b'0' * self.DATASIZE

        with open(os.path.join(self.dirname, 'test.dat'), 'wb') as fd:
            fd.write(data)

        subdir = os.path.join(self.dirname, 'testdir')
        os.makedirs(subdir)

        with open(os.path.join(subdir, 'test.dat'), 'wb') as fd:
            fd.write(data)

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_directory_size(self):
        self._popuate_test_dir()
        dirsize = utils.get_tree_size(self.dirname)
        self.assertEqual(dirsize, 2*self.DATASIZE)

    def test_empty_directory_size(self):
        dirsize = utils.get_tree_size(self.dirname)
        self.assertEqual(dirsize, 0)


class TestDataUuid(unittest.TestCase):
    DATASIZE = 1024     # 1 kbyte

    def setUp(self):
        self.fd = tempfile.NamedTemporaryFile(
                prefix='gsdview_test_utils_', suffix='.dat')
        data = b'0' * self.DATASIZE
        self.fd.write(data)
        self.fd.flush()

    def test_data_uuid_type(self):
        data_uuid = utils.data_uuid(self.fd.name)
        self.assertTrue(isinstance(data_uuid, str))

    def test_data_uuid_len(self):
        data_uuid = utils.data_uuid(self.fd.name)
        self.assertEqual(len(data_uuid), 60)

    def test_data_uuid_consistency(self):
        data_uuid1 = utils.data_uuid(self.fd.name)
        self.fd.seek(0)
        data = self.fd.read()
        data_uuid2 = utils.data_uuid(self.fd.name)
        self.assertEqual(data_uuid1, data_uuid2)

    def test_data_uuid_filename(self):
        data_uuid1 = utils.data_uuid(self.fd.name)

        self.fd.seek(0)
        data = self.fd.read()
        with tempfile.NamedTemporaryFile(
                prefix='gsdview_test_utils_', suffix='.dat') as fd:
            data_uuid2 = utils.data_uuid(fd.name)
        self.assertNotEqual(data_uuid1, data_uuid2)

    def test_data_uuid_newfile(self):
        data_uuid1 = utils.data_uuid(self.fd.name)

        self.fd.seek(0)
        data = self.fd.read()
        filename = self.fd.name
        self.fd.file.close()

        with open(filename, 'w+b') as fd:
            fd.write(data)
            data_uuid2 = utils.data_uuid(filename)
        # filename is unlinked by NamedTemporaryFile __del__ method
        # os.remove(filename)
        self.assertNotEqual(data_uuid1, data_uuid2)

    def test_data_uuid_filechange(self):
        data_uuid1 = utils.data_uuid(self.fd.name)

        data = b'b' * self.DATASIZE
        self.fd.write(data)
        self.fd.flush()
        data_uuid2 = utils.data_uuid(self.fd.name)
        self.assertNotEqual(data_uuid1, data_uuid2)


if __name__ == '__main__':
    unittest.main()
