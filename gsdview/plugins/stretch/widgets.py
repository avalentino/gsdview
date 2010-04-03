# -*- coding: utf-8 -*-

### Copyright (C) 2008-2010 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of GSDView.

### GSDView is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### GSDView is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with GSDView; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA.


'''Widgets and dialogs for GSDView.'''

__author__   = '$Author: a_valentino $'
__date__     = '$Date: 2010/02/14 12:21:23 $'
__revision__ = '$Revision: 003973572867 $'

import logging

from PyQt4 import QtCore, QtGui

from gsdview import qt4support

StretchWidgetBase = qt4support.getuiform('doubleslider', __name__)
class StretchWidget(QtGui.QWidget, StretchWidgetBase):

    # SIGNALS:
    # valueChanged()
    ##valueChanged(double vmin, double vmax)

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        super(StretchWidget, self).__init__(parent, flags)
        self.setupUi(self)
        self._floatmode = False
        self.connect(self.minSpinBox, QtCore.SIGNAL('valueChanged(double)'),
                     self._onMinimumChanged)
        self.connect(self.maxSpinBox, QtCore.SIGNAL('valueChanged(double)'),
                     self._onMaximumChanged)
        self.connect(self.lowSlider, QtCore.SIGNAL('valueChanged(int)'),
                     self._onLowSliderChanged)
        self.connect(self.highSlider, QtCore.SIGNAL('valueChanged(int)'),
                     self._onHighSliderChanged)
        self.connect(self.lowSpinBox, QtCore.SIGNAL('valueChanged(double)'),
                     self.setLow)
        self.connect(self.highSpinBox, QtCore.SIGNAL('valueChanged(double)'),
                     self.setHigh)

        self.connect(self.lowSpinBox, QtCore.SIGNAL('valueChanged(double)'),
                     lambda value: self.emit(QtCore.SIGNAL('valueChanged()')))
        self.connect(self.highSpinBox, QtCore.SIGNAL('valueChanged(double)'),
                     lambda value: self.emit(QtCore.SIGNAL('valueChanged()')))

    def _getFloatMode(self):
        return self._floatmode

    def _setFloatMode(self, floatmode=True):
        floatmode = bool(floatmode)
        if floatmode == self._floatmode:
            return
        self._floatmode = floatmode
        if self._floatmode:
            self.lowSlider.setRange(0, 1000)
            self.highSlider.setRange(0, 1000)
            self.lowSlider.setValue(self._pos(self.lowSpinBox.value()))
            self.highSlider.setValue(self._pos(self.highSpinBox.value()))
        else:
            vmin = self.minSpinBox.value()
            vmax = self.minSpinBox.value()
            self.lowSlider.setRange(vmin, vmax)
            self.highSlider.setRange(vmin, vmax)
            self.lowSlider.setValue(self.lowSpinBox.value())
            self.highSlider.setValue(self.highSpinBox.value())

    floatmode = property(_getFloatMode, _setFloatMode,
                         doc='Set the tretch widget in floating point mode.')

    def _pos(self, value):
        N = self.highSlider.maximum() - self.lowSlider.minimum()
        k = (self.maxSpinBox.value() - self.minSpinBox.value()) / float(N)
        if k == 0:
            return 0
        return (value - self.minSpinBox.value()) / k

    def _value(self, pos):
        N = self.highSlider.maximum() - self.lowSlider.minimum()
        k = (self.maxSpinBox.value() - self.minSpinBox.value()) / float(N)
        return k * pos + self.minSpinBox.value()

    def _setValue(self, value, spinbox, slider):
        spinbox.setValue(value)
        if self.floatmode:
            value = self._pos(spinbox.value())
        slider.setValue(value)

    def low(self):
        return self.lowSpinBox.value()

    def setLow(self, value):
        self._setValue(value, self.lowSpinBox, self.lowSlider)
        if self.lowSpinBox.value() > self.highSpinBox.value():
            self.highSpinBox.setValue(self.lowSpinBox.value())

    def high(self):
        return self.highSpinBox.value()

    def setHigh(self, value):
        self._setValue(value, self.highSpinBox, self.highSlider)
        if self.lowSpinBox.value() > self.highSpinBox.value():
            self.lowSpinBox.setValue(self.highSpinBox.value())

    def _onLowSliderChanged(self, value):
        if self.floatmode:
            value = self._value(value)
            N = max(self.maxStretchSpinBox.decimals(), 1)
            if abs(value - self.maxStretchSpinBox.value()) < 1./N:
                return
        self.setLow(value)

    def _onHighSliderChanged(self, value):
        if self.floatmode:
            value = self._value(value)
            N = max(self.maxStretchSpinBox.decimals(), 1)
            if abs(value - self.maxStretchSpinBox.value()) < 1./N:
                return
        self.setHigh(value)

    def values(self):
        return self.low(), self.high()

    def minimum(self):
        return self.minSpinBox.value()

    def setMinimum(self, value):
        self.minSpinBox.setValue(value)

    def _onMinimumChanged(self, value):
        if self.minSpinBox.value() > self.maxSpinBox.value():
            self.maxSpinBox.setValue(self.minSpinBox.value())

        self.lowSpinBox.setMinimum(value)
        self.highSpinBox.setMinimum(value)

        if self.floatmode:
            vmin = self._pos(self.lowSpinBox.value())
            self.lowSlider.setValue(vmin)
            vmax = self._pos(self.highSpinBox.value())
            self.highSlider.setValue(vmax)
        else:
            self.lowSlider.setMinimum(value)
            self.highSlider.setMinimum(value)

        if self.lowSpinBox.value() > self.highSpinBox.value():
            self.highSpinBox.setValue(self.lowSpinBox.value())

    def maximum(self):
        return self.maxSpinBox.value()

    def setMaximum(self, value):
        self.maxSpinBox.setValue(value)

    def _onMaximumChanged(self, value):
        if self.minSpinBox.value() > self.maxSpinBox.value():
            self.minSpinBox.setValue(self.maxSpinBox.value())

        self.lowSpinBox.setMaximum(value)
        self.highSpinBox.setMaximum(value)

        if self.floatmode:
            vmin = self._pos(self.lowSpinBox.value())
            self.lowSlider.setValue(vmin)
            vmax = self._pos(self.highSpinBox.value())
            self.highSlider.setValue(vmax)
        else:
            self.lowSlider.setMaximum(value)
            self.highSlider.setMaximum(value)

        if self.lowSpinBox.value() > self.highSpinBox.value():
            self.lowSpinBox.setValue(self.highSpinBox.value())

    def setState(self, d):
        self.minSpinBox.setMinimum(d['minSpinBox.minimum'])
        self.minSpinBox.setMaximum(d['minSpinBox.maximum'])
        self.maxSpinBox.setMinimum(d['maxSpinBox.minimum'])
        self.maxSpinBox.setMaximum(d['maxSpinBox.maximum'])

        self.floatmode = d['floatmode']
        self.setMinimum(d['minimum'])
        self.setMaximum(d['maximum'])
        self.setLow(d['low'])
        self.setHigh(d['high'])

    def state(self, d=None):
        if d is None:
            d = dict()

        d['floatmode'] = self.floatmode
        d['minimum'] = self.minimum()
        d['maximum'] = self.maximum()
        d['low'] = self.low()
        d['high'] = self.high()

        d['minSpinBox.minimum'] = self.minSpinBox.minimum()
        d['minSpinBox.maximum'] = self.minSpinBox.maximum()

        d['maxSpinBox.minimum'] = self.maxSpinBox.minimum()
        d['maxSpinBox.maximum'] = self.maxSpinBox.maximum()

        return d


StretchDialogBase = qt4support.getuiform('stretchdialog', __name__)
class StretchDialog(QtGui.QDialog, StretchDialogBase):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget): # QtCore.Qt.Dialog
        super(StretchDialog, self).__init__(parent, flags)
        self.setupUi(self)

        self.stretchwidget = StretchWidget(self)
        self.mainLayout.insertWidget(0, self.stretchwidget)

        if not self.checkBox.isChecked():
            self.setAdvanced(False)

        self.state = None
        self.saveState()

        self.connect(self.checkBox, QtCore.SIGNAL('toggled(bool)'),
                     self.setAdvanced)
        self.connect(self.resetButton, QtCore.SIGNAL('clicked()'),
                     self.reset)

        self.connect(self.stretchwidget,
                     QtCore.SIGNAL('valueChanged()'),
                     lambda: self.emit(QtCore.SIGNAL('valueChanged()')))

        #~ self.connect(self.stretchwidget.lowSpinBox,
                     #~ QtCore.SIGNAL('valueChanged(double)'),
                     #~ lambda value: self.emit(QtCore.SIGNAL('valueChanged()')))
        #~ self.connect(self.stretchwidget.highSpinBox,
                     #~ QtCore.SIGNAL('valueChanged(double)'),
                     #~ lambda value: self.emit(QtCore.SIGNAL('valueChanged()')))

    def advanced(self):
        return self.stretchwidget.lowSpinBox.isVisible()

    def setAdvanced(self, advmode=True):
        self.stretchwidget.lowSpinBox.setVisible(advmode)
        self.stretchwidget.lowSlider.setVisible(advmode)

    def _getFloatmode(self):
        return self.stretchwidget.floatmode

    def _setFloatmode(self, mode):
        self.stretchwidget.floatmode = mode

    floatmode = property(_getFloatmode, _setFloatmode)

    def saveState(self):
        self.state = self.stretchwidget.state()

    def reset(self, d=None):
        if d is None:
            d = self.state
        if d is None:
            return
        try:
            self.stretchwidget.setState(d)
        except KeyError, e:
            logging.info('unable to set state: %s' % str(e))

    def values(self):
        return self.stretchwidget.values()
        # @TODO: working on linux
        #return 0, self.stretchwidget.maxStretch()
