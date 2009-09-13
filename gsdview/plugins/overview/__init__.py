# -*- coding: UTF8 -*-

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


'''Overview pannel for GDAL raster bands.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'
__requires__ = []

__all__ = ['BandOverviewDock', 'init', 'close',
           'name','version', 'short_description','description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label',
]

import info
from info import *

from PyQt4 import QtCore

from core import BandOverviewDock


__version__ = info.__version__


def init(mainwin):
    overviewPanel = BandOverviewDock(mainwin)
    overviewPanel.setObjectName('bandOverviewPanel') # @TODO: check
    mainwin.addDockWidget(QtCore.Qt.LeftDockWidgetArea, overviewPanel)

    def onWindowMapped(subwin, overviewPanel=overviewPanel, mainwin=mainwin):
        try:
            item = subwin.item
        except AttributeError:
            overviewPanel.reset()
        else:
            overviewPanel.setItem(item)

    def onWindowClosed(overviewPanel=overviewPanel, mainwin=mainwin):
        if len(mainwin.mdiarea.subWindowList()) == 0:
            overviewPanel.reset()

    mainwin.connect(mainwin.mdiarea,
                    QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                    onWindowMapped)
    mainwin.connect(mainwin, QtCore.SIGNAL('subWindowClosed()'),
                    onWindowClosed)

    def onItemChanged(item, mainwin=mainwin, overviewPanel=overviewPanel):
        if hasattr(item, 'scene'):
            srcview = mainwin.currentGraphicsView()
            if (srcview and srcview.scene() is item.scene
                                and not overviewPanel.graphicsview.scene()):
                overviewPanel.setItem(item)

    mainwin.connect(mainwin.datamodel,
                    QtCore.SIGNAL('itemChanged(QStandardItem*)'),
                    onItemChanged)

    QtCore.QObject.connect(mainwin.monitor,
                           QtCore.SIGNAL('scrolled(QGraphicsView*)'),
                           overviewPanel.updateMainViewBox)
    QtCore.QObject.connect(mainwin.monitor,
                           QtCore.SIGNAL('viewportResized(QGraphicsView*)'),
                           overviewPanel.updateMainViewBox)
    QtCore.QObject.connect(mainwin.monitor,
                           QtCore.SIGNAL('resized(QGraphicsView*, QSize)'),
                           overviewPanel.updateMainViewBox)

    # @TODO: translate into an event handler
    def onNewPos(pos, buttons, dragmode, overviewPanel=overviewPanel):
        if buttons & QtCore.Qt.LeftButton:
            overviewPanel.centerMainViewOn(pos)

    QtCore.QObject.connect(overviewPanel.graphicsview,
                           QtCore.SIGNAL('mousePressed(QPointF,Qt::MouseButtons,'
                                         'QGraphicsView::DragMode)'),
                           onNewPos)
    QtCore.QObject.connect(overviewPanel.graphicsview,
                           QtCore.SIGNAL('mouseMoved(QPointF,Qt::MouseButtons,'
                                         'QGraphicsView::DragMode)'),
                           onNewPos)


def close(mainwin):
    saveSettings(mainwin.settings)

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass

