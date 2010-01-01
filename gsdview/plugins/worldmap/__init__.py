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
__requires__ = []       # @TODO: move to the info file

__all__ = ['init', 'close', 'WorldmapPanel',
           'name','version', 'short_description','description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label',
]


from worldmap import info
from worldmap.info import *

from PyQt4 import QtCore

from worldmap.core import WorldmapPanel


__version__ = info.__version__


def init(mainwin):
    worldmapPanel = WorldmapPanel(mainwin)
    worldmapPanel.setObjectName('worldmapPanel') # @TODO: check
    mainwin.addDockWidget(QtCore.Qt.BottomDockWidgetArea, worldmapPanel)


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

    def onItemClicked(index, mainwin=mainwin):
        if not mainwin.mdiarea.activeSubWindow():
            item = mainwin.datamodel.itemFromIndex(index)
            setItemFootprint(item)

    mainwin.connect(mainwin.mdiarea,
                    QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                    onSubWindowActivated)

    mainwin.connect(mainwin.treeview,
                    QtCore.SIGNAL('clicked(const QModelIndex&)'),
                    onItemClicked)

    def onModelChanged(index=None, start=None, stop=None, mainwin=mainwin):
        window = mainwin.mdiarea.activeSubWindow()
        if window:
            onSubWindowActivated(window)
        else:
            item = mainwin.currentItem()
            setItemFootprint(item)

    mainwin.connect(mainwin, QtCore.SIGNAL('subWindowClosed()'),
                    onModelChanged)

    # @WARNING: rowsInserted/rowsRemoved don't work
    # @TODO: fix
    mainwin.connect(mainwin.datamodel,
                    QtCore.SIGNAL('rowsInserted(const QModelIndex&,int,int)'),
                    onModelChanged)

    mainwin.connect(mainwin.datamodel,
                    QtCore.SIGNAL('rowsRemoved(const QModelIndex&,int,int)'),
                    onModelChanged)

def close(mainwin):
    saveSettings(mainwin.settings)

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass
