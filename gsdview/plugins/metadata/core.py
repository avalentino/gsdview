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


'''Browser component for geo-datasets metadata.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


from PyQt4 import QtCore, QtGui

from gsdview import qt4support


class MetadataViewer(QtGui.QDockWidget):
    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0), **kwargs):
        #title = self.tr('Dataset Browser')
        super(MetadataViewer, self).__init__('Metadata Viewer', parent, flags,
                                             **kwargs)
        #self.setObjectName('metadataViewerPanel') # @TODO: check

        self.infoTable = QtGui.QTableWidget(5, 2, self)
        self.infoTable.verticalHeader().hide()
        self.infoTable.setHorizontalHeaderLabels(['Name', 'Value'])
        self.infoTable.horizontalHeader().setStretchLastSection(True)
        #self.tableWidget.horizontalHeader().hide()
        # @TODO: comment if you want allow the uset to edit items
        self.infoTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.infoTable.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        qt4support.setViewContextActions(self.infoTable)

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


class MetadataController(QtCore.QObject):
    def __init__(self, app, **kwargs):
        super(MetadataController, self).__init__(app, **kwargs)
        self.app = app

        self.panel = MetadataViewer(app)
        self.panel.setObjectName('metadataViewerPanel') # @TODO: check

        # Connect signals
        app.treeview.clicked.connect(self.onItemClicked)
        app.mdiarea.subWindowActivated.connect(self.onSubWindowChanged)
        app.subWindowClosed.connect(self.onSubWindowChanged)

    def setItemMetadata(self, item):
        if not item:
            self.panel.clear()
            return

        # @TODO: fix
        # @WARNING: this method contains backend specific code
        if item.backend != 'gdalbackend':
            import logging
            logging.warning('only "gdalbackend" is supported by "overview" '
                            'plugin')
            return

        try:
            metadata = item.GetMetadata_List()
        except RuntimeError:
            # closed sub-dataset
            return
        self.panel.setMetadata(metadata)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def onItemClicked(self, index):
        #if not app.mdiarea.activeSubWindow():
        item = self.app.datamodel.itemFromIndex(index)
        self.setItemMetadata(item)

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(QtGui.QMdiSubWindow)
    def onSubWindowChanged(self, subwin=None):
        if not subwin:
            subwin = self.app.mdiarea.activeSubWindow()

        try:
            item = subwin.item
        except AttributeError:
            item = None
        else:
            item = self.app.currentItem()

        self.setItemMetadata(item)
