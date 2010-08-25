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


'''Specialized MainWindow classes and mixins.'''

# @TODO: move this to widgets sub-package or qt4freesolutions subpackage

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


from PyQt4 import QtCore, QtGui

from gsdview.qtwindowlistmenu import QtWindowListMenu


class MdiMainWindow(QtGui.QMainWindow):
    '''Base class for MDI applications.

    :SIGNALS:

        * :attr:`subWindowClosed`

    '''

    # @TODO: should the subWindowClosed signal be emitted by mdiarea?
    #: SIGNAL: it is emitted when an MDI subwindow is closed
    #:
    #: :C++ signature: `void subWindowClosed()`
    subWindowClosed = QtCore.pyqtSignal()

    def __init__(self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(MdiMainWindow, self).__init__(parent, flags, **kwargs)

        #: MDI area instance (QMdiArea)
        self.mdiarea = QtGui.QMdiArea()
        self.setCentralWidget(self.mdiarea)
        self.mdiarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        #: sub-windows menu
        self.windowmenu = QtWindowListMenu(self.menuBar())
        self.windowmenu.attachToMdiArea(self.mdiarea)


class ItemSubWindow(QtGui.QMdiSubWindow):

    def __init__(self, item, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(ItemSubWindow, self).__init__(parent, flags, **kwargs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        #: datamodel item associated to the MDI sub-window
        self.item = item


class ItemModelMainWindow(MdiMainWindow):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(ItemModelMainWindow, self).__init__(parent, flags, **kwargs)

        #: main application datamodel (QStandardItemModel)
        self.datamodel = QtGui.QStandardItemModel(self)

        # @TODO: custom treeview with "currentChanged" slot re-implemented
        #: tree view for the main application data model
        self.treeview = QtGui.QTreeView()
        # @TODO self.treeview.setSelectionMode(QtGui.QTreeView.SingleSelection)
        self.treeview.setModel(self.datamodel)
        self.treeview.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.treeview.header().hide()

        self.treeview.clicked.connect(self.setActiveWinFromIndex)
        self.mdiarea.subWindowActivated.connect(self.setActiveIndexFromWin)
        self.datamodel.rowsAboutToBeRemoved.connect(self.onItemsClosed)

        # setup the treeview dock
        treeviewdock = QtGui.QDockWidget(self.tr('Data Browser'), self)
        treeviewdock.setWidget(self.treeview)
        treeviewdock.setObjectName('TreeViewPanel')
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, treeviewdock)

    def currentItem(self):
        modelindex = self.treeview.currentIndex()
        if not modelindex.isValid():
            return None
        return self.datamodel.itemFromIndex(modelindex)

    #@QtCore.pyqtSlot(QtCore.QModelIndex) # @TODO: check
    def setActiveWinFromIndex(self, index):
        '''Set the active sub-window from index.

        :C++ signature: `void setActiveWinFromIndex(const QModelIndex&)`

        '''

        # @TODO: find a better name
        item = self.datamodel.itemFromIndex(index)
        windowlist = self.mdiarea.subWindowList()
        window = self.mdiarea.activeSubWindow()
        if window:
            windowlist.remove(window)
            windowlist.insert(0, window)

        for window in windowlist:
            try:
                if window.item == item:
                    self.mdiarea.setActiveSubWindow(window)
            except AttributeError:
                # the window has not an associated item in the datamodel
                pass

    @QtCore.pyqtSlot(QtGui.QMdiSubWindow)
    def setActiveIndexFromWin(self, window):
        '''Set the active sub-window.

        :C++ signature: `void setActiveIndexFromWin(QMdiSubWindow*)`

        '''

        # @TODO: find a better name
        # @TODO: check and, if the case, remove
        if not window:
            return

        try:
            index = window.item.index()
        except AttributeError:
            # the window has not an associated item in the datamodel
            pass
        else:
            self.treeview.setCurrentIndex(index)

    #@QtCore.pyqtSlot(QtCore.QModelIndex, int, int) # @TODO: check
    def onItemsClosed(self, modelindex, start, end):
        '''Closes sub-windows associated to the closed model items.

        :C++ signature: `void onItemsClosed(const QModelIndex&, int, int)`

        '''

        if not modelindex.isValid():
            return
        parentitem = modelindex.model().itemFromIndex(modelindex)
        for row in range(start, end+1):
            item = parentitem.child(row)
            for subwin in self.mdiarea.subWindowList():
                if subwin.item == item:
                    subwin.close()
                    # just une window per run (??)
                    break
        for subwin in self.mdiarea.subWindowList():
            if subwin.item == parentitem:
                subwin.close()
                # just une window per run (??)
                break