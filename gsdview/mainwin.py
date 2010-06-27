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

    :ivar mdiarea:       QMdiArea
    :ivar windowactions: sub-windows actions
    :ivar windowmenu:    sub-windows menu

    :signals:

    - subWindowClosed()     # @TODO: should this signal be emitted by mdiarea?

    '''
    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QMainWindow.__init__(self, parent, flags)

        self.mdiarea = QtGui.QMdiArea()
        self.setCentralWidget(self.mdiarea)
        self.mdiarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.windowmenu = QtWindowListMenu(self.menuBar())
        self.windowmenu.attachToMdiArea(self.mdiarea)

    ### SIGNALS ###############################################################
    def subWindowClosed(self):
        self.emit(QtCore.SIGNAL('subWindowClosed()'))


class ItemSubWindow(QtGui.QMdiSubWindow):

    def __init__(self, item, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QMdiSubWindow.__init__(self, parent, flags)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.item = item


class ItemModelMainWindow(MdiMainWindow):

    def __init__(self, parent=None):
        super(ItemModelMainWindow, self).__init__(parent)

        self.datamodel = QtGui.QStandardItemModel(self)

        # @TODO: custom treeview with "currentChanged" slot re-implemented
        self.treeview = QtGui.QTreeView()
        # @TODO self.treeview.setSelectionMode(QtGui.QTreeView.SingleSelection)
        self.treeview.setModel(self.datamodel)
        self.treeview.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.treeview.header().hide()

        self.connect(self.treeview,
                     QtCore.SIGNAL('clicked(const QModelIndex&)'),
                     self.setActiveWinFromIndex)
        self.connect(self.mdiarea,
                     QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                     self.setActiveIndexFromWin)
        self.connect(self.datamodel,
                     QtCore.SIGNAL('rowsAboutToBeRemoved(const QModelIndex&, '
                                   'int, int)'),
                     self.onItemsClosed)

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

    def setActiveWinFromIndex(self, index):
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

    def setActiveIndexFromWin(self, window):
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

    def onItemsClosed(self, modelindex, start, end):
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
