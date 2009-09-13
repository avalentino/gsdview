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


'''Position tracker.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'
__requires__ = []       # @TODO: move to the info file

__all__ = ['CoordinateView', 'init', 'close',
           'name','version', 'short_description','description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label',
]


import info
from info import *

from PyQt4 import QtCore

from coordinateview import CoordinateView, GeoCoordinateView

__version__ = info.__version__

_controller = None

def init(mainwin):
    statusbar = mainwin.statusBar()

    # image coordinates
    coorview = CoordinateView()
    statusbar.addPermanentWidget(coorview)
    coorview.hide()
    QtCore.QObject.connect(mainwin.monitor,
                           QtCore.SIGNAL('leave(QGraphicsScene*)'),
                           coorview.hide)

    # geographic coordinates
    geocoorview = GeoCoordinateView()
    statusbar.addPermanentWidget(geocoorview)
    geocoorview.hide()
    QtCore.QObject.connect(mainwin.monitor,
                           QtCore.SIGNAL('leave(QGraphicsScene*)'),
                           geocoorview.hide)

    # @TODO: move to core.py (??)
    class Controller(QtCore.QObject):
        def __init__(self, mainwin, coorview, geocoorview):
            QtCore.QObject.__init__(self, mainwin)

            self.coorview = coorview
            self.geocoorview = geocoorview

            mainwin.progressbar.installEventFilter(self)

            self.connect(mainwin.monitor,
                         QtCore.SIGNAL('mouseMoved(QGraphicsScene*, '
                                       'QPointF, Qt::MouseButtons)'),
                         self.onMouseMoved)

        def eventFilter(self, obj, event):
            if event.type() == QtCore.QEvent.Show:
                self.coorview.hide()
                self.geocoorview.hide()
            return obj.eventFilter(obj, event)

        def onMouseMoved(self, scene, pos, buttons):
            mainwin = self.parent() # @TODO: fix

            if mainwin.progressbar.isVisible():
                return

            coorview.updatePos(pos)

            item = mainwin.currentItem()
            try:
                cmapper = item.cmapper
            except AttributeError:
                cmapper = None
            geocoorview.updatePos(pos, cmapper)

    # Keep alive the controller object after function exit
    # @TODO: avoid the use of "global"
    global _controller
    _controller = Controller(mainwin, coorview, geocoorview)

def close(mainwin):
    saveSettings(mainwin.settings)

    # @TODO: avoid the use of "global"
    global _controller
    _controller = None

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass
