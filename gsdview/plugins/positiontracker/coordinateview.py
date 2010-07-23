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


'''Position tool.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


from PyQt4 import QtCore, QtGui


class CoordinateView(QtGui.QWidget):
    def __init__ (self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(CoordinateView, self).__init__(parent, flags, **kwargs)

        layout = QtGui.QHBoxLayout()

        self.xlabel = QtGui.QLabel('x:')
        layout.addWidget(self.xlabel)

        self.xedit = QtGui.QLineEdit()
        self.xedit.setMaxLength(6)
        self.xedit.setReadOnly(True)
        layout.addWidget(self.xedit)

        self.ylabel = QtGui.QLabel('y:')
        layout.addWidget(self.ylabel)

        self.yedit = QtGui.QLineEdit()
        self.yedit.setMaxLength(6)
        self.yedit.setReadOnly(True)
        layout.addWidget(self.yedit)

        self.setLayout(layout)

    def updatePos(self, scenepos, cmapper=None):
        self.show()
        self.xedit.setText(str(scenepos.x()))
        self.yedit.setText(str(scenepos.y()))

class GeoCoordinateView(CoordinateView):
    def __init__ (self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(GeoCoordinateView, self).__init__(parent, flags, **kwargs)

        self.xlabel.setText('lon:')
        self.ylabel.setText('lat:')
        self.xedit.setMaxLength(12)
        self.yedit.setMaxLength(12)

    def updatePos(self, scenepos, cmapper=None):
        if not cmapper:
            self.hide()
            return

        self.show()

        # @TODO: the imgToGeoPoints method should return the same type
        vlon, vlat = cmapper.imgToGeoPoints(scenepos.x(), scenepos.y())
        lon, lat = vlon[0], vlat[0]    # @TODO: fix

        self.xedit.setText(str(lon))
        self.yedit.setText(str(lat))
