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
import sys
import logging
import unittest


# Fix sys path
GSDVIEWROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, GSDVIEWROOT)


from qtpy import QtWidgets
from qtpy.QtTest import QTest

from gsdview.plugins.stretch.widgets import StretchWidget, StretchDialog


class StretchWidgetTestCase(unittest.TestCase):
    app = QtWidgets.QApplication(sys.argv)
    FLOATMODE = False

    def setUp(self):
        self.stretch = StretchWidget(floatmode=self.FLOATMODE)
        self.stretch.setLow(10)

    def test_defaults(self):
        self.assertEqual(self.stretch.low(), 10)
        self.assertEqual(self.stretch.high(), 100)
        self.assertEqual(self.stretch.minimum(), 0)
        self.assertEqual(self.stretch.maximum(), 255)

    def test_floatmode_change(self):
        low = self.stretch.low()
        high = self.stretch.high()
        minimum = self.stretch.minimum()
        maximum = self.stretch.maximum()

        self.stretch.floatmode = not self.stretch.floatmode
        if not self.stretch.floatmode:
            low = int(low)
            high = int(high)

        self.assertAlmostEqual(self.stretch.low(), low)
        self.assertAlmostEqual(self.stretch.high(), high)
        self.assertAlmostEqual(self.stretch.minimum(), minimum)
        self.assertAlmostEqual(self.stretch.maximum(), maximum)

    def test_floatmode_change_and_back(self):
        low = self.stretch.low()
        high = self.stretch.high()
        minimum = self.stretch.minimum()
        maximum = self.stretch.maximum()

        self.stretch.floatmode = not self.stretch.floatmode
        if not self.stretch.floatmode:
            low = int(low)
            high = int(high)

        self.assertAlmostEqual(self.stretch.low(), low)
        self.assertAlmostEqual(self.stretch.high(), high)
        self.assertAlmostEqual(self.stretch.minimum(), minimum)
        self.assertAlmostEqual(self.stretch.maximum(), maximum)

        self.stretch.floatmode = not self.stretch.floatmode

        self.assertAlmostEqual(self.stretch.low(), low)
        self.assertAlmostEqual(self.stretch.high(), high)
        self.assertAlmostEqual(self.stretch.minimum(), minimum)
        self.assertAlmostEqual(self.stretch.maximum(), maximum)

    def test_decrease_minimum(self):
        low, high = self.stretch.values()
        minimum = self.stretch.minimum()
        delta = 1000 * max(abs(minimum), 1)
        self.stretch.setMinimum(minimum - delta)
        self.assertEqual(low, self.stretch.low())
        self.assertEqual(high, self.stretch.high())

    def test_increase_minimum(self):
        low, high = self.stretch.values()
        minimum = self.stretch.minimum()
        delta = low - minimum
        self.stretch.setMinimum(minimum + delta / 2)
        self.assertEqual(low, self.stretch.low())
        self.assertEqual(high, self.stretch.high())

    def test_increase_minimum_above_low(self):
        low, high = self.stretch.values()
        minimum = 0.5 * (low + high)
        self.assertGreater(minimum, low)
        self.assertLess(minimum, high)
        self.stretch.setMinimum(minimum)
        self.assertEqual(self.stretch.low(), minimum)
        self.assertEqual(high, self.stretch.high())

    def test_increase_minimum_above_high(self):
        low, high = self.stretch.values()
        delta = min(abs(low), abs(high))/2
        minimum = high + delta
        self.assertGreater(minimum, high)
        self.assertLess(minimum, self.stretch.maximum())
        self.stretch.setMinimum(minimum)
        self.assertAlmostEqual(self.stretch.low(), minimum)
        self.assertAlmostEqual(self.stretch.high(), minimum)
        # self.assertGreaterEqual(high, minimum)

    def test_increase_minimum_above_maximum(self):
        delta = max(abs(self.stretch.minimum()), abs(self.stretch.maximum()))
        minimum = self.stretch.maximum() + delta
        self.assertRaises(ValueError, self.stretch.setMinimum, minimum)

    def test_decrease_maximum_below_minimum(self):
        delta = max(abs(self.stretch.minimum()), abs(self.stretch.maximum()))
        maximum = self.stretch.minimum() - delta
        self.assertRaises(ValueError, self.stretch.setMaximum, maximum)

    def test_decrease_maximum_below_low(self):
        low, high = self.stretch.values()
        delta = min(abs(low), abs(high))/2
        maximum = low - delta
        self.assertLess(maximum, low)
        self.assertGreater(maximum, self.stretch.minimum())
        self.stretch.setMaximum(maximum)
        self.assertEqual(self.stretch.low(), maximum)
        self.assertEqual(self.stretch.high(), maximum)
        # self.assertLessEqual(low, maximum)

    def test_decrease_maximum_below_high(self):
        low, high = self.stretch.values()
        maximum = 0.5 * (low + high)
        self.assertGreater(maximum, low)
        self.assertLess(maximum, high)
        self.stretch.setMaximum(maximum)
        self.assertEqual(low, self.stretch.low())
        self.assertEqual(self.stretch.high(), maximum)

    def test_decrease_maximum(self):
        low, high = self.stretch.values()
        maximum = self.stretch.maximum()
        delta = maximum - high
        self.stretch.setMaximum(maximum + delta / 2)
        self.assertEqual(low, self.stretch.low())
        self.assertEqual(high, self.stretch.high())

    def test_increase_maximum(self):
        low, high = self.stretch.values()
        maximum = self.stretch.maximum()
        delta = 1000 * max(abs(maximum), 1)
        self.stretch.setMaximum(maximum + delta)
        self.assertEqual(low, self.stretch.low())
        self.assertEqual(high, self.stretch.high())

    # broken tests
    if False:
        def test_ui_decrease_minimum(self):
            low, high = self.stretch.values()
            minimum = self.stretch.minimum()
            delta = 1000 * max(abs(minimum), 1)
            value = minimum - delta
            QTest.keyClicks(self.stretch.minSpinBox, str(value))
            self.assertEqual(self.stretch.minimum(), value)
            self.assertEqual(low, self.stretch.low())
            self.assertEqual(high, self.stretch.high())

        def test_ui_increase_minimum(self):
            low, high = self.stretch.values()
            minimum = self.stretch.minimum()
            delta = low - minimum
            value = minimum + delta / 2
            QTest.keyClicks(self.stretch.minSpinBox, str(value))
            self.assertEqual(self.stretch.minimum(), value)
            self.assertEqual(low, self.stretch.low())
            self.assertEqual(high, self.stretch.high())

        def test_ui_increase_minimum_above_low(self):
            low, high = self.stretch.values()
            minimum = 0.5 * (low + high)
            self.assertGreater(minimum, low)
            self.assertLess(minimum, high)
            QTest.keyClicks(self.stretch.minSpinBox, str(minimum))
            self.assertEqual(self.stretch.minimum(), minimum)
            self.assertEqual(self.stretch.low(), minimum)
            self.assertEqual(high, self.stretch.high())

        def test_ui_increase_minimum_above_high(self):
            low, high = self.stretch.values()
            delta = min(abs(low), abs(high))/2
            minimum = high + delta
            self.assertGreater(minimum, high)
            self.assertLess(minimum, self.stretch.maximum())
            QTest.keyClicks(self.stretch.minSpinBox, str(minimum))
            self.assertEqual(self.stretch.minimum(), minimum)
            self.assertEqual(self.stretch.low(), minimum)
            self.assertEqual(self.stretch.high(), minimum)
            # self.assertGreaterEqual(high, minimum)

        @unittest.skip('incomplete')
        def test_ui_increase_minimum_above_maximum(self):
            delta = max(abs(self.stretch.minimum()), abs(self.stretch.maximum()))
            minimum = self.stretch.maximum() + delta
            QTest.keyClicks(self.stretch.minSpinBox, str(minimum))
            self.assertEqual(self.stretch.minimum(), minimum)
            # self.assertRaises(ValueError, self.stretch.setMinimum, minimum)

        @unittest.skip('incomplete')
        def test_ui_decrease_maximum_below_minimum(self):
            delta = max(abs(self.stretch.minimum()), abs(self.stretch.maximum()))
            maximum = self.stretch.minimum() - delta
            QTest.keyClicks(self.stretch.maxSpinBox, str(maximum))
            self.assertEqual(self.stretch.maximum(), maximum)
            # self.assertRaises(ValueError, self.stretch.setMaximum, maximum)

        def test_ui_decrease_maximum_below_low(self):
            low, high = self.stretch.values()
            delta = min(abs(low), abs(high))/2
            maximum = low - delta
            self.assertLess(maximum, low)
            self.assertGreater(maximum, self.stretch.minimum())
            QTest.keyClicks(self.stretch.maxSpinBox, str(maximum))
            self.assertEqual(self.stretch.maximum(), maximum)
            self.assertEqual(self.stretch.low(), maximum)
            self.assertEqual(self.stretch.high(), maximum)
            # self.assertLessEqual(low, maximum)

        def test_ui_decrease_maximum_below_high(self):
            low, high = self.stretch.values()
            maximum = 0.5 * (low + high)
            self.assertGreater(maximum, low)
            self.assertLess(maximum, high)
            QTest.keyClicks(self.stretch.maxSpinBox, str(maximum))
            self.assertEqual(self.stretch.maximum(), maximum)
            self.assertEqual(low, self.stretch.low())
            self.assertEqual(self.stretch.high(), maximum)

        def test_ui_decrease_maximum(self):
            low, high = self.stretch.values()
            maximum = self.stretch.maximum()
            delta = maximum - high
            value = maximum + delta / 2
            QTest.keyClicks(self.stretch.maxSpinBox, str(value))
            self.assertEqual(self.stretch.maximum(), value)
            self.assertEqual(low, self.stretch.low())
            self.assertEqual(high, self.stretch.high())

        def test_ui_increase_maximum(self):
            low, high = self.stretch.values()
            maximum = self.stretch.maximum()
            delta = 1000 * max(abs(maximum), 1)
            value = maximum + delta
            QTest.keyClicks(self.stretch.maxSpinBox, str(value))
            self.assertEqual(self.stretch.maximum(), value)
            self.assertEqual(low, self.stretch.low())
            self.assertEqual(high, self.stretch.high())


class StretchWidgetFloatModeTestCase(StretchWidgetTestCase):
    FLOATMODE = True


class StretchWidgetSmallFloatModeTestCase(StretchWidgetTestCase):
    FLOATMODE = True
    LOW = -0.02
    HIGH = +0.01
    MINIMUM = -0.7
    MAXIMUM = +0.3

    def setUp(self):
        super(StretchWidgetSmallFloatModeTestCase, self).setUp()
        self.stretch.setMinimum(self.MINIMUM)
        self.stretch.setMaximum(self.MAXIMUM)
        self.stretch.setLow(self.LOW)
        self.stretch.setHigh(self.HIGH)

    def test_defaults(self):
        self.assertEqual(self.stretch.low(), self.LOW)
        self.assertEqual(self.stretch.high(), self.HIGH)
        self.assertEqual(self.stretch.minimum(), self.MINIMUM)
        self.assertEqual(self.stretch.maximum(), self.MAXIMUM)


def _test_stretchingdialog(floatmode=False):
    app = QtWidgets.QApplication(sys.argv)
    d = StretchDialog(floatmode=floatmode)
    # state = d.stretchwidget.state()
    d.show()
    app.exec_()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # _test_stretchingdialog()
    # _test_stretchingdialog(True)
    unittest.main()
