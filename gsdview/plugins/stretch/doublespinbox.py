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


import re

from qt import QtWidgets, QtGui


class DoubleSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super(DoubleSpinBox, self).__init__(*args, **kwargs)
        self.lineEdit().setValidator(QtGui.QDoubleValidator(self))
        self.setDecimals(7)
        self.setRange(-1e50, 1e50)

    def validate(self, text, position):
        return self.lineEdit().validator().validate(text, position)

    def valueFromText(self, text):
        return float(text)

    def textFromValue(self, value):
        text = self.locale().toString(value, 'g', self.decimals())
        # @COMPATIBILITY: isGroupSeparatorShown is new in Qt 5.3
        if (not hasattr(self, 'isGroupSeparatorShown') or
                not self.isGroupSeparatorShown()):
            text = text.replace(self.locale().groupSeparator(), '')
        text = text.replace("e+", "e")
        return re.sub(r'e(-?)0*(\d+)', r'e\1\2', text)
