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


'''Widgets and dialogs for GSDView.'''


import logging

from qt import QtCore, QtWidgets

from gsdview import qtsupport


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

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0),
                 floatmode=True, **kwargs):
        super(StretchWidget, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)
        self._floatmode = floatmode

        self.lowSlider.valueChanged.connect(self._onLowSliderChanged)
        self.highSlider.valueChanged.connect(self._onHighSliderChanged)
        self.minSpinBox.valueChanged[float].connect(self._onMinimumChanged)
        self.maxSpinBox.valueChanged[float].connect(self._onMaximumChanged)
        self.lowSpinBox.valueChanged[float].connect(self.setLow)
        self.highSpinBox.valueChanged[float].connect(self.setHigh)

        self.lowSpinBox.valueChanged.connect(self.valueChanged)
        self.highSpinBox.valueChanged.connect(self.valueChanged)

    @QtCore.Property(bool)
    def floatmode(self):
        return self._floatmode

    @floatmode.setter
    def floatmode(self, floatmode=True):
        '''Set the stretch widget in floating point mode.'''

        floatmode = bool(floatmode)
        if floatmode == self._floatmode:
            return

        self._floatmode = floatmode
        if self._floatmode:
            self.lowSlider.setRange(0, 1000000)
            self.highSlider.setRange(0, 1000000)
            self.lowSlider.setValue(self._pos(self.lowSpinBox.value()))
            self.highSlider.setValue(self._pos(self.highSpinBox.value()))
        else:
            vmin = self.minSpinBox.value()
            vmax = self.maxSpinBox.value()
            self.lowSlider.setRange(vmin, vmax)
            self.highSlider.setRange(vmin, vmax)
            self.lowSlider.setValue(self.lowSpinBox.value())
            self.highSlider.setValue(self.highSpinBox.value())

    @property
    def _scale(self):
        if not self._floatmode:
            return 1

        N = self.highSlider.maximum() - self.lowSlider.minimum()
        k = (self.maxSpinBox.value() - self.minSpinBox.value()) / float(N)

        return k

    def _pos(self, value):
        k = self._scale
        if k == 0:
            return self.minSpinBox.value()

        return (value - self.minSpinBox.value()) / k

    def _value(self, pos):
        return self.minSpinBox.value() + self._scale * pos

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

    def singleStep(self):
        #assert self.lowSlider.singleStep() == self.highSlider.singleStep()
        #assert self.lowSlider.singleStep() == self.lowSpinBox.singleStep()
        #assert self.lowSlider.singleStep() == self.highSpinBox.singleStep()
        return self.highSpinBox.singleStep()

    def setSingleStep(self, step):
        k = self._scale if self._scale else 1
        self.lowSlider.setSingleStep(step / k)
        self.highSlider.setSingleStep(step / k)
        self.lowSpinBox.setSingleStep(step)
        self.highSpinBox.setSingleStep(step)

    def pageStep(self):
        #assert self.lowSlider.pageStep() == self.highSlider.pageStep()
        return self.highSlider.pageStep() * self._scale

    def setPageStep(self, step):
        k = self._scale if self._scale else 1
        self.lowSlider.setPageStep(step / k)
        self.highSlider.setPageStep(step / k)

    @staticmethod
    def _fixSpinBoxStep(spinbox):
        newstep = abs(spinbox.value()) / 10
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

        self._fixSpinBoxStep(self.minSpinBox)

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

        self._fixSpinBoxStep(self.maxSpinBox)

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
        d['pageSTep'] = self.pageStep()

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
            logging.info('unable to set state: %s' % str(e))

    def values(self):
        return self.stretchwidget.values()
        # @TODO: working on linux
        #return 0, self.stretchwidget.maxStretch()
