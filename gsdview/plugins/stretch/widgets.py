# -*- coding: utf-8 -*-

### Copyright (C) 2008-2011 Antonio Valentino <a_valentino@users.sf.net>

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


import logging

from qt import QtCore, QtGui

from gsdview import qt4support


__author__ = '$Author: a_valentino $'
__date__ = '$Date: 2010/02/14 12:21:23 $'
__revision__ = '$Revision: 003973572867 $'


StretchWidgetBase = qt4support.getuiform('doubleslider', __name__)


class StretchWidget(QtGui.QWidget, StretchWidgetBase):
    '''Stretch widget.

    :SIGNALS:

        * :attr:`valueChanged`

    '''

    #: SIGNAL: it is emitted when the stretch value changes
    #:
    #: :C++ signature: `void valueChanged()`
    valueChanged = QtCore.Signal()

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0), **kwargs):
        super(StretchWidget, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)
        self._floatmode = False
        self.minSpinBox.valueChanged[float].connect(self._onMinimumChanged)
        self.maxSpinBox.valueChanged[float].connect(self._onMaximumChanged)
        self.lowSlider.valueChanged.connect(self._onLowSliderChanged)
        self.highSlider.valueChanged.connect(self._onHighSliderChanged)
        self.lowSpinBox.valueChanged[float].connect(self.setLow)
        self.highSpinBox.valueChanged[float].connect(self.setHigh)

        self.lowSpinBox.valueChanged.connect(self.valueChanged)
        self.highSpinBox.valueChanged.connect(self.valueChanged)

        self._fixStep(self.minSpinBox)
        self._fixStep(self.maxSpinBox)

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

    @QtCore.Slot(float)
    def setLow(self, value):
        self._setValue(value, self.lowSpinBox, self.lowSlider)
        if self.lowSpinBox.value() > self.highSpinBox.value():
            self.highSpinBox.setValue(self.lowSpinBox.value())

    def high(self):
        return self.highSpinBox.value()

    @QtCore.Slot(float)
    def setHigh(self, value):
        self._setValue(value, self.highSpinBox, self.highSlider)
        if self.lowSpinBox.value() > self.highSpinBox.value():
            self.lowSpinBox.setValue(self.highSpinBox.value())

    @QtCore.Slot(int)
    def _onLowSliderChanged(self, value):
        if self.floatmode:
            value = self._value(value)
            N = 10. ** self.lowSpinBox.decimals()
            if abs(value - self.lowSpinBox.value()) < 1. / N:
                return
        self.setLow(value)

    @QtCore.Slot(int)
    def _onHighSliderChanged(self, value):
        if self.floatmode:
            value = self._value(value)
            N = 10. ** self.highSpinBox.decimals()
            if abs(value - self.highSpinBox.value()) < 1. / N:
                return
        self.setHigh(value)

    def values(self):
        return self.low(), self.high()

    @staticmethod
    def _fixStep(spinbox):
        newstep = abs(spinbox.value()) / 20
        newstep = max(int(newstep), 1)
        spinbox.setSingleStep(newstep)

    def minimum(self):
        return self.minSpinBox.value()

    def setMinimum(self, value):
        self.minSpinBox.setValue(value)

    @QtCore.Slot(float)
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

        self._fixStep(self.minSpinBox)

    def maximum(self):
        return self.maxSpinBox.value()

    def setMaximum(self, value):
        self.maxSpinBox.setValue(value)

    @QtCore.Slot(float)
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

        self._fixStep(self.maxSpinBox)

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
    '''Stretch dialog.

    :SIGNALS:

        * :attr:`valueChanged`

    '''

    #: SIGNAL: it is emitted when the stretch value changes
    #:
    #: :C++ signature: `void valueChanged()`
    valueChanged = QtCore.Signal()

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0), **kwargs):
        super(StretchDialog, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

        self.stretchwidget = StretchWidget(self)
        self.mainLayout.insertWidget(0, self.stretchwidget)

        if not self.checkBox.isChecked():
            self.setAdvanced(False)

        self.state = None
        self.saveState()

        self.checkBox.toggled.connect(self.setAdvanced)
        self.resetButton.clicked.connect(self.reset)

        self.stretchwidget.valueChanged.connect(self.valueChanged)

        #~ self.stretchwidget.lowSpinBox.valueChanged.connect(self.valueChanged)
        #~ self.stretchwidget.highSpinBox.valueChanged.connect(self.valueChanged)

    def advanced(self):
        return self.stretchwidget.lowSpinBox.isVisible()

    @QtCore.Slot()
    @QtCore.Slot(bool)
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

    @QtCore.Slot()
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
