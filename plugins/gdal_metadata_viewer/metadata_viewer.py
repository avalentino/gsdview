### Copyright (C) 2007 Antonio Valentino <a_valentino@users.sf.net>

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

'''Browser component for GDAL datasets.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date$'
__revision__ = '$Revision$'

#import gdal
from PyQt4 import QtCore, QtGui

class MetadataViewer(QtGui.QDockWidget):
    def __init__(self, parent=None): #, flags=0):
        #title = self.tr('Dataset Browser')
        QtGui.QDockWidget.__init__(self, 'Metadata Viewer', parent) #, flags)
        #self.setObjectName('metadataViewerPanel') # @TODO: check

        self.infoTable = QtGui.QTableWidget(5, 2, self)
        self.infoTable.verticalHeader().hide()
        self.infoTable.setHorizontalHeaderLabels(['Name', 'Value'])
        self.infoTable.horizontalHeader().setStretchLastSection(True)
        #self.tableWidget.horizontalHeader().hide()
        self.setWidget(self.infoTable)

    def setMetadata(self, metadataList):
        self.clear()

        self.infoTable.setRowCount(len(metadataList))

        for row, data in enumerate(metadataList):
            name, value = data.split('=', 1)
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
