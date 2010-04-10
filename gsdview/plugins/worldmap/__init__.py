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


'''World map component for GSDView.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'

__all__ = ['init', 'close', 'WorldmapPanel',
           'name','version', 'short_description','description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label',
]


from worldmap.info import *
from worldmap.info import __version__, __requires__


def init(app):
    from PyQt4 import QtCore
    from worldmap.core import WorldmapPanel

    worldmapPanel = WorldmapPanel(app)
    worldmapPanel.setObjectName('worldmapPanel') # @TODO: check
    app.addDockWidget(QtCore.Qt.BottomDockWidgetArea, worldmapPanel)

    # @TODO: move to core module - controller
    def setItemFootprint(item, worldmapPanel=worldmapPanel):
        try:
            footprint = item.footprint()
        except AttributeError:
            footprint = None

        worldmapPanel.setFootprint(footprint)

    def onSubWindowActivated(subwindow):
        if not subwindow:
            return

        try:
            item = subwindow.item
        except AttributeError:
            # the window has not an associated item in the datamodel
            pass
        else:
            setItemFootprint(item)

    def onItemClicked(index, app=app):
        if not app.mdiarea.activeSubWindow():
            item = app.datamodel.itemFromIndex(index)
            setItemFootprint(item)

    app.connect(app.mdiarea, QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                onSubWindowActivated)

    app.connect(app.treeview, QtCore.SIGNAL('clicked(const QModelIndex&)'),
                onItemClicked)

    def onModelChanged(index=None, start=None, stop=None, app=app):
        window = app.mdiarea.activeSubWindow()
        if window:
            onSubWindowActivated(window)
        else:
            item = app.currentItem()
            setItemFootprint(item)

    app.connect(app, QtCore.SIGNAL('subWindowClosed()'), onModelChanged)

    # @WARNING: rowsInserted/rowsRemoved don't work
    # @TODO: fix
    app.connect(app.datamodel,
                QtCore.SIGNAL('rowsInserted(const QModelIndex&,int,int)'),
                onModelChanged)

    app.connect(app.datamodel,
                QtCore.SIGNAL('rowsRemoved(const QModelIndex&,int,int)'),
                onModelChanged)

def close(app):
    saveSettings(app.settings)

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass
