# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2015 Antonio Valentino <antonio.valentino@tiscali.it>
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


'''Widgets and dialogs for GSDView.'''


import logging
import contextlib

import numpy as np
from qtpy import QtCore, QtWidgets, QtGui

from gsdview import qtsupport


_log = logging.getLevelName(__name__)

StretchWidgetBase = qtsupport.getuiform('doubleslider', __name__)


class StretchWidget(QtWidgets.QWidget, StretchWidgetBase):
    '''Stretch widget.

    :SIGNALS:

        * :attr:`valueChanged`

    '''

    #: SIGNAL: it is emitted when the stretch value changes
    #:
    #: :C++ signature: `void valueChanged()`
    valueChanged = QtCore.Signal()

    #: SIGNAL: it is emitted when the stretch range changes
    #:
    #: :C++ signature: `void rangeChanged(int, int)`
    #rangeChanged = QtCore.Signal(int, int)

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0),
                 floatmode=True, **kwargs):
        super(StretchWidget, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)
        self._floatmode = False
        self._kslider = self._computeKSlider()

        self._connectSignals()

        self.floatmode = floatmode

    def _connectSignals(self):
        self.lowSlider.valueChanged.connect(self._onLowSliderChanged)
        self.highSlider.valueChanged.connect(self._onHighSliderChanged)

        #self.rangeChanged.connect(self._onRangeChanged)

        self.minSpinBox.valueChanged[float].connect(self._onMinimumChanged)
        self.maxSpinBox.valueChanged[float].connect(self._onMaximumChanged)
        self.lowSpinBox.valueChanged[float].connect(self._onLowSpinBoxChanged)
        self.highSpinBox.valueChanged[float].connect(self._onHighSpinBoxChanged)

        self.lowSpinBox.valueChanged.connect(self.valueChanged)
        self.highSpinBox.valueChanged.connect(self.valueChanged)

    def _disconnectSignals(self):
        self.lowSlider.valueChanged.disconnect(self._onLowSliderChanged)
        self.highSlider.valueChanged.disconnect(self._onHighSliderChanged)

        #self.rangeChanged.disconnect(self._onRangeChanged)

        self.minSpinBox.valueChanged[float].disconnect(self._onMinimumChanged)
        self.maxSpinBox.valueChanged[float].disconnect(self._onMaximumChanged)
        self.lowSpinBox.valueChanged[float].disconnect(self._onLowSpinBoxChanged)
        self.highSpinBox.valueChanged[float].disconnect(self._onHighSpinBoxChanged)

        self.lowSpinBox.valueChanged.disconnect(self.valueChanged)
        self.highSpinBox.valueChanged.disconnect(self.valueChanged)

    @contextlib.contextmanager
    def _disconnectedSignals(self):
        self._disconnectSignals()
        yield
        self._connectSignals()

    @QtCore.Property(bool)
    def floatmode(self):
        return self._floatmode

    @floatmode.setter
    def floatmode(self, floatmode=True):
        '''Set the stretch widget in floating point mode.'''

        floatmode = bool(floatmode)
        if floatmode == self._floatmode:
            return

        vmin = self.minSpinBox.value()
        vmax = self.maxSpinBox.value()

        self._floatmode = floatmode
        if self._floatmode:
            self.lowSlider.setRange(0, 1000)
            self.highSlider.setRange(0, 1000)
        else:
            self.lowSlider.setRange(vmin, vmax)
            self.highSlider.setRange(vmin, vmax)

        self.setRange(vmin, vmax)

    def setRange(self, vmin, vmax):
        if vmin >= vmax:
            raise ValueError('vmin (%f) >= vmax (%f)' % (vmin, vmax))

        low = self.lowSpinBox.value()
        if low < vmin:
            low = vmin
        elif low > vmax:
            low = vmax
        high = self.highSpinBox.value()
        if high < vmin:
            high = vmin
        elif high > vmax:
            high = vmax

        with self._disconnectedSignals():
            self.minSpinBox.setValue(vmin)
            self.maxSpinBox.setValue(vmax)

            self._kslider = self._computeKSlider(vmin, vmax)

            if not self._floatmode:
                self.lowSlider.setRange(vmin, vmax)
                self.highSlider.setRange(vmin, vmax)

                self.lowSlider.setValue(low)
                self.highSlider.setValue(high)
            else:
                self.lowSlider.setValue(self._pos(low))
                self.highSlider.setValue(self._pos(high))

        self._updateSteps(self.maximum(), self.minimum())

    def _computeSteps(self, vmin, vmax):
        vmax = max(abs(vmax), abs(vmin))
        if vmax == 0:
            # @TODO: check
            return 1, 10

        if not self._floatmode and vmax < 32:
            return 1, min(5, vmax)

        kmax = np.log10(vmax)
        singleStep = 10**(np.round(kmax) - 2)
        pageStep = 10 * singleStep

        return singleStep, pageStep

    def _updateSteps(self, vmin, vmax):
        singleStep, pageStep = self._computeSteps(vmin, vmax)

        self.lowSpinBox.setSingleStep(singleStep)
        self.highSpinBox.setSingleStep(singleStep)

        if self._floatmode:
            decimals = 7
            self.lowSpinBox.setDecimals(decimals)
            self.highSpinBox.setDecimals(decimals)

            step = np.round(singleStep * self._kslider)
            self.lowSlider.setSingleStep(step)
            self.highSlider.setSingleStep(step)

            step = np.round(pageStep * self._kslider)
            self.lowSlider.setSingleStep(step)
            self.highSlider.setSingleStep(step)

        else:
            self.lowSpinBox.setDecimals(0)
            self.highSpinBox.setDecimals(0)

            self.lowSlider.setSingleStep(singleStep)
            self.highSlider.setSingleStep(singleStep)

            self.lowSlider.setSingleStep(pageStep)
            self.highSlider.setSingleStep(pageStep)

        # @TODO: update all steps
        self.maxSpinBox.setSingleStep(pageStep)
        if self.minimum() != 0:
            step = 10**(np.round(np.log10(abs(self.minimum()))))
        else:
            step = singleStep
        self.minSpinBox.setSingleStep(step)

    def _computeKSlider(self, vmin=None, vmax=None):
        if not self._floatmode:
            return 1

        if vmin is None:
            vmin = self.lowSlider.minimum()

        if vmax is None:
            vmax = self.highSlider.maximum()

        vrange = float(self.maxSpinBox.value() - self.minSpinBox.value())
        srange = float(vmax - vmin)

        if srange == 0:
            return 0
        else:
            return np.round(vrange / srange)

    def _pos(self, value):
        if self._kslider == 0:
            return self.minSpinBox.value()

        return (value - self.minSpinBox.value()) / self._kslider

    def _value(self, pos):
        return self.minSpinBox.value() + self._kslider * pos

    def low(self):
        return self.lowSpinBox.value()

    @QtCore.Slot(float)
    def setLow(self, value):
        self.lowSpinBox.setValue(value)
        if self.lowSpinBox.value() > self.highSpinBox.value():
            self.highSpinBox.setValue(self.lowSpinBox.value())

    def high(self):
        return self.highSpinBox.value()

    @QtCore.Slot(float)
    def setHigh(self, value):
        self.highSpinBox.setValue(value)
        if self.lowSpinBox.value() > self.highSpinBox.value():
            self.lowSpinBox.setValue(self.highSpinBox.value())

    @QtCore.Slot(float)
    def _onLowSpinBoxChanged(self, value):
        if self.floatmode:
            pos = self._pos(value)
        else:
            pos = value
        self.lowSlider.setValue(pos)

    @QtCore.Slot(float)
    def _onHighSpinBoxChanged(self, value):
        if self.floatmode:
            pos = self._pos(value)
        else:
            pos = value
        self.highSlider.setValue(pos)

    @QtCore.Slot(int)
    def _onLowSliderChanged(self, value):
        if value > self.highSlider.value():
            self.highSlider.setValue(value)

        if self.floatmode:
            value = self._value(value)
        self.lowSpinBox.setValue(value)

    @QtCore.Slot(int)
    def _onHighSliderChanged(self, value):
        if value < self.lowSlider.value():
            self.lowSlider.setValue(value)

        if self.floatmode:
            value = self._value(value)
        self.highSpinBox.setValue(value)

    def values(self):
        return self.low(), self.high()

    def singleStep(self):
        #assert self.lowSlider.singleStep() == self.highSlider.singleStep()
        #assert self.lowSlider.singleStep() == self.lowSpinBox.singleStep()
        #assert self.lowSlider.singleStep() == self.highSpinBox.singleStep()
        return self.highSpinBox.singleStep()

    def setSingleStep(self, step):
        k = self._kslider if self._kslider else 1
        self.lowSlider.setSingleStep(step / k)
        self.highSlider.setSingleStep(step / k)
        self.lowSpinBox.setSingleStep(step)
        self.highSpinBox.setSingleStep(step)

    def pageStep(self):
        #assert self.lowSlider.pageStep() == self.highSlider.pageStep()
        return self.highSlider.pageStep() * self._kslider

    def setPageStep(self, step):
        k = self._kslider if self._kslider else 1
        self.lowSlider.setPageStep(step / k)
        self.highSlider.setPageStep(step / k)

    def minimum(self):
        return self.minSpinBox.value()

    def setMinimum(self, value):
        if value >= self.maximum():
            raise ValueError("can't set a minimum value greater that maximum")
        self.minSpinBox.setValue(value)

    @QtCore.Slot(float)
    def _onMinimumChanged(self, value):
        if value >= self.maxSpinBox.value():
            value = self.maxSpinBox.value() - self.singleStep()
            self.minSpinBox.setValue(value)
            return

        stretch_changed = False

        with self._disconnectedSignals():
            self.maxSpinBox.setMinimum(value)
            self.lowSpinBox.setMinimum(value)
            self.highSpinBox.setMinimum(value)

            if self.floatmode:
                self._kslider = self._computeKSlider()

                vmin = self._pos(self.lowSpinBox.value())
                vmax = self._pos(self.highSpinBox.value())

                self.lowSlider.setValue(vmin)
                self.highSlider.setValue(vmax)
            else:
                self.lowSlider.setMinimum(value)
                self.highSlider.setMinimum(value)

            if self.lowSpinBox.value() < self.minSpinBox.value():
                self.lowSpinBox.setValue(self.minSpinBox.value())
                stretch_changed = True

            if self.highSpinBox.value() < self.minSpinBox.value():
                high = self.minSpinBox.value() + self.lowSpinBox.singleStep()
                high = min(high, self.maxSpinBox.value())
                self.highSpinBox.setValue(high)
                stretch_changed = True

        self._updateSteps(self.minimum(), self.maximum())

        if stretch_changed:
            self.valueChanged.emit()

    def maximum(self):
        return self.maxSpinBox.value()

    def setMaximum(self, value):
        if value <= self.minimum():
            raise ValueError("can't set a maximum value smaller that minimum")
        self.maxSpinBox.setValue(value)

    @QtCore.Slot(float)
    def _onMaximumChanged(self, value):
        if value <= self.minSpinBox.value():
            value = self.minSpinBox.value() + self.singleStep()
            self.maxSpinBox.setValue(value)
            return

        stretch_changed = False

        with self._disconnectedSignals():
            self.minSpinBox.setMaximum(value)
            self.lowSpinBox.setMaximum(value)
            self.highSpinBox.setMaximum(value)

            if self.floatmode:
                self._kslider = self._computeKSlider()

                vmin = self._pos(self.lowSpinBox.value())
                vmax = self._pos(self.highSpinBox.value())

                self.lowSlider.setValue(vmin)
                self.highSlider.setValue(vmax)
            else:
                self.lowSlider.setMaximum(value)
                self.highSlider.setMaximum(value)

            if self.lowSpinBox.value() > self.maxSpinBox.value():
                low = self.maxSpinBox.value() + self.highSpinBox.singleStep()
                low = max(low, self.minSpinBox.value())
                self.lowSpinBox.setValue(low)
                stretch_changed = True

            if self.highSpinBox.value() > self.maxSpinBox.value():
                self.highSpinBox.setValue(self.maxSpinBox.value())
                stretch_changed = True

        self._updateSteps(self.minimum(), self.maximum())

        if stretch_changed:
            self.valueChanged.emit()

    def setState(self, d):
        self.minSpinBox.setMinimum(d['minSpinBox.minimum'])
        self.minSpinBox.setMaximum(d['minSpinBox.maximum'])
        self.minSpinBox.setSingleStep(d['minSpinBox.singleStep'])
        self.maxSpinBox.setMinimum(d['maxSpinBox.minimum'])
        self.maxSpinBox.setMaximum(d['maxSpinBox.maximum'])
        self.maxSpinBox.setSingleStep(d['maxSpinBox.singleStep'])

        self.floatmode = d['floatmode']
        self.setMinimum(d['minimum'])
        self.setMaximum(d['maximum'])
        self.setLow(d['low'])
        self.setHigh(d['high'])
        self.setSingleStep(d['singleStep'])
        self.setPageStep(d['pageStep'])

    def state(self, d=None):
        if d is None:
            d = dict()

        d['floatmode'] = self.floatmode
        d['minimum'] = self.minimum()
        d['maximum'] = self.maximum()
        d['low'] = self.low()
        d['high'] = self.high()
        d['singleStep'] = self.singleStep()
        d['pageStep'] = self.pageStep()

        d['minSpinBox.minimum'] = self.minSpinBox.minimum()
        d['minSpinBox.maximum'] = self.minSpinBox.maximum()
        d['minSpinBox.singleStep'] = self.minSpinBox.singleStep()
        d['maxSpinBox.minimum'] = self.maxSpinBox.minimum()
        d['maxSpinBox.maximum'] = self.maxSpinBox.maximum()
        d['maxSpinBox.singleStep'] = self.maxSpinBox.singleStep()

        return d


StretchDialogBase = qtsupport.getuiform('stretchdialog', __name__)


class StretchDialog(QtWidgets.QDialog, StretchDialogBase):
    '''Stretch dialog.

    :SIGNALS:

        * :attr:`valueChanged`

    '''

    #: SIGNAL: it is emitted when the stretch value changes
    #:
    #: :C++ signature: `void valueChanged()`
    valueChanged = QtCore.Signal()

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0),
                 floatmode=True, **kwargs):
        super(StretchDialog, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

        self.stretchwidget = StretchWidget(self, floatmode=floatmode)
        self.mainLayout.insertWidget(0, self.stretchwidget)

        if not self.checkBox.isChecked():
            self.setAdvanced(False)

        self.state = None
        self.saveState()

        self.checkBox.toggled.connect(self.setAdvanced)
        self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.reset)

        self.stretchwidget.valueChanged.connect(self.valueChanged)

        #~ self.stretchwidget.lowSpinBox.valueChanged.connect(
        #~     self.valueChanged)
        #~ self.stretchwidget.highSpinBox.valueChanged.connect(
        #~     self.valueChanged)

    def advanced(self):
        return self.stretchwidget.lowSpinBox.isVisible()

    @QtCore.Slot()
    @QtCore.Slot(bool)
    def setAdvanced(self, advmode=True):
        self.stretchwidget.lowSpinBox.setVisible(advmode)
        self.stretchwidget.lowSlider.setVisible(advmode)

    @QtCore.Property(bool)
    def floatmode(self):
        return self.stretchwidget.floatmode

    @floatmode.setter
    def floatmode(self, mode):
        self.stretchwidget.floatmode = mode

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
        except KeyError as e:
            _log.info('unable to set state: %s', e)

    def values(self):
        return self.stretchwidget.values()
        # @TODO: working on linux
        #return 0, self.stretchwidget.maxStretch()
