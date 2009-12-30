# -*- coding: utf-8 -*-

### Copyright (C) 2008-2009 Antonio Valentino <a_valentino@users.sf.net>

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


'''Browser component for geo-datasets metadata.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


from PyQt4 import QtCore, QtGui


class MetadataViewer(QtGui.QDockWidget):
    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        #title = self.tr('Dataset Browser')
        QtGui.QDockWidget.__init__(self, 'Metadata Viewer', parent, flags)
        #self.setObjectName('metadataViewerPanel') # @TODO: check

        self.infoTable = QtGui.QTableWidget(5, 2, self)
        self.infoTable.verticalHeader().hide()
        self.infoTable.setHorizontalHeaderLabels(['Name', 'Value'])
        self.infoTable.horizontalHeader().setStretchLastSection(True)
        #self.tableWidget.horizontalHeader().hide()
        # @TODO: comment if you want allow the uset to edit items
        self.infoTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setWidget(self.infoTable)

    def setMetadata(self, metadatalist):
        self.clear()
        if not metadatalist:
            return

        self.infoTable.setRowCount(len(metadatalist))

        for row, data in enumerate(metadatalist):
            name, value = data.split('=', 1)
            #item = QtGui.QTableWidgetItem(name)
            #item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.infoTable.setItem(row, 0, QtGui.QTableWidgetItem(name))
            self.infoTable.setItem(row, 1, QtGui.QTableWidgetItem(value))

        # Fix table header behaviour
        header = self.infoTable.horizontalHeader()
        header.resizeSections(QtGui.QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

    def clear(self):
        self.infoTable.clear()
        self.infoTable.setHorizontalHeaderLabels(['Name', 'Value'])
        self.infoTable.setRowCount(0)
