#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>
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
import logging
import unittest


# Fix sys path
GSDVIEWROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, GSDVIEWROOT)


from qt import QtGui

from gsdview.plugins.stretch.widgets import StretchWidget, StretchDialog


class StretchWidgetTestCase(unittest.TestCase):
    FLOATMODE = True
    app = QtGui.QApplication(sys.argv)

    def setUp(self):
        #self.app = QtGui.QApplication(sys.argv)
        self.stretch = StretchWidget(floatmode=self.FLOATMODE)

    def test_defaults(self):
        self.assertEqual(self.stretch.low(), 0)
        self.assertEqual(self.stretch.high(), 100)
        self.assertEqual(self.stretch.minimum(), 0)
        self.assertEqual(self.stretch.maximum(), 255)

    def test_floatmode_change_to_false(self):
        self.stretch.floatmode = True

        low = self.stretch.low()
        high = self.stretch.high()
        minimum = self.stretch.minimum()
        maximum = self.stretch.maximum()

        self.stretch.floatmode = not self.stretch.floatmode

        self.assertAlmostEqual(self.stretch.low(), low, 2)
        self.assertAlmostEqual(self.stretch.high(), high, 2)
        self.assertAlmostEqual(self.stretch.minimum(), minimum, 2)
        self.assertAlmostEqual(self.stretch.maximum(), maximum, 2)

    def test_floatmode_change_to_true(self):
        self.stretch.floatmode = False

        low = self.stretch.low()
        high = self.stretch.high()
        minimum = self.stretch.minimum()
        maximum = self.stretch.maximum()

        self.stretch.floatmode = not self.stretch.floatmode

        self.assertAlmostEqual(self.stretch.low(), low, 2)
        self.assertAlmostEqual(self.stretch.high(), high, 2)
        self.assertAlmostEqual(self.stretch.minimum(), minimum, 2)
        self.assertAlmostEqual(self.stretch.maximum(), maximum, 2)

    def test_floatmode_change_and_back(self):
        low = self.stretch.low()
        high = self.stretch.high()
        minimum = self.stretch.minimum()
        maximum = self.stretch.maximum()

        self.stretch.floatmode = not self.stretch.floatmode

        self.assertAlmostEqual(self.stretch.low(), low, 2)
        self.assertAlmostEqual(self.stretch.high(), high, 2)
        self.assertAlmostEqual(self.stretch.minimum(), minimum, 2)
        self.assertAlmostEqual(self.stretch.maximum(), maximum, 2)

        self.stretch.floatmode = not self.stretch.floatmode

        self.assertAlmostEqual(self.stretch.low(), low, 2)
        self.assertAlmostEqual(self.stretch.high(), high, 2)
        self.assertAlmostEqual(self.stretch.minimum(), minimum, 2)
        self.assertAlmostEqual(self.stretch.maximum(), maximum, 2)


def _test_stretchingdialog(floatmode=False):
    app = QtGui.QApplication(sys.argv)
    d = StretchDialog(floatmode=floatmode)
    #state = d.stretchwidget.state()
    d.show()
    app.exec_()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #_test_stretchingdialog()
    #_test_stretchingdialog(True)
    unittest.main()
