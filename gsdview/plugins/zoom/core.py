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


'''Zoom tool.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import logging

from PyQt4 import QtCore, QtGui

from gsdview import qt4support


class ZoomTool(QtCore.QObject):
    def __init__(self, mainwin):
        QtCore.QObject.__init__(self, mainwin)
        self.mainwin = mainwin
        self.actions = self._setupActions()
        self.menu = qt4support.actionGroupToMenu(
                                    self.actions, self.tr('&Zoom'), mainwin)
        self.toolbar = qt4support.actionGroupToToolbar(self.actions,
                                                       self.tr('Zoom toolbar'))

    def _setupActions(self):
        actions = QtGui.QActionGroup(self)

        # Zoom in
        icon = qt4support.geticon('zoom-in.svg', 'gsdview')
        actionZoomIn = QtGui.QAction(icon, self.tr('Zoom In'), self)
        actionZoomIn.setStatusTip(self.tr('Zoom In'))
        actionZoomIn.setShortcut(QtGui.QKeySequence(self.tr('Ctrl++')))
        self.connect(actionZoomIn, QtCore.SIGNAL('triggered()'), self.zoomIn)
        actions.addAction(actionZoomIn)

        # Zoom out
        icon = qt4support.geticon('zoom-out.svg', 'gsdview')
        actionZoomOut = QtGui.QAction(icon, self.tr('Zoom Out'), self)
        actionZoomOut.setStatusTip(self.tr('Zoom Out'))
        actionZoomOut.setShortcut(QtGui.QKeySequence(self.tr('Ctrl+-')))
        self.connect(actionZoomOut, QtCore.SIGNAL('triggered()'), self.zoomOut)
        actions.addAction(actionZoomOut)

        # Zoom fit
        icon = qt4support.geticon('zoom-fit.svg', 'gsdview')
        actionZoomFit = QtGui.QAction(icon, self.tr('Zoom Fit'), self)
        actionZoomIn.setStatusTip(self.tr('Zoom to fit the window size'))
        self.connect(actionZoomFit, QtCore.SIGNAL('triggered()'), self.zoomFit)
        actions.addAction(actionZoomFit)

        # Zoom 100
        icon = qt4support.geticon('zoom-100.svg', 'gsdview')
        actionZoom100 = QtGui.QAction(icon, self.tr('Zoom 100%'), self)
        actionZoom100.setStatusTip(self.tr('Original size'))
        self.connect(actionZoom100, QtCore.SIGNAL('triggered()'), self.zoom100)
        actions.addAction(actionZoom100)

        return actions

    def currentview(self):
        subwin = self.mainwin.mdiarea.currentSubWindow()
        graphicsview = subwin.widget()
        if isinstance(graphicsview, QtGui.QGraphicsView):
            return graphicsview
        else:
            return None

    def zoomIn(self):
        factor = 1.2    # @TODO: make this configurable
        view = self.currentview()
        if view:
            view.scale(factor, factor)

    def zoomOut(self):
        factor = 1./1.2 # @TODO: make this configurable
        view = self.currentview()
        if view:
            view.scale(factor, factor)

    def zoomFit(self):
        subwin = self.mainwin.mdiarea.currentSubWindow()
        try:
            view = subwin.widget()
            view.fitInView(subwin.item.graphicsitem, QtCore.Qt.KeepAspectRatio)
        except AttributeError, e:
            logging.debug(str(e))

    def zoom100(self):
        view = self.currentview()
        if view:
            view.setMatrix(QtGui.QMatrix())
