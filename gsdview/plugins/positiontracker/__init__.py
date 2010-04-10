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


'''Position tracker.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'

__all__ = ['CoordinateView', 'init', 'close',
           'name','version', 'short_description','description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label',
]


from positiontracker.info import *
from positiontracker.info import __version__, __requires__

# @TODO: check the name (use _instance instead)
_controller = None


def init(app):
    from PyQt4 import QtCore
    from positiontracker.core import Controller
    from positiontracker.coordinateview import CoordinateView, GeoCoordinateView

    statusbar = app.statusBar()

    # image coordinates
    coorview = CoordinateView()
    statusbar.addPermanentWidget(coorview)
    coorview.hide()
    QtCore.QObject.connect(app.monitor,
                           QtCore.SIGNAL('leave(QGraphicsScene*)'),
                           coorview.hide)

    # geographic coordinates
    geocoorview = GeoCoordinateView()
    statusbar.addPermanentWidget(geocoorview)
    geocoorview.hide()
    QtCore.QObject.connect(app.monitor,
                           QtCore.SIGNAL('leave(QGraphicsScene*)'),
                           geocoorview.hide)

    # Keep alive the controller object after function exit
    global _controller
    _controller = Controller(app, coorview, geocoorview)

def close(app):
    saveSettings(app.settings)

    global _controller
    _controller = None

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass
