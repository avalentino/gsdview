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


'''Core modue for position tracker plugin.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'

from PyQt4 import QtCore


class Controller(QtCore.QObject):
    def __init__(self, app, coorview, geocoorview):
        QtCore.QObject.__init__(self, app)

        self.app = app
        self.coorview = coorview
        self.geocoorview = geocoorview

        app.progressbar.installEventFilter(self)

        self.connect(self.app.monitor,
                     QtCore.SIGNAL('mouseMoved(QGraphicsScene*, '
                                   'QPointF, Qt::MouseButtons)'),
                     self.onMouseMoved)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Show:
            self.coorview.hide()
            self.geocoorview.hide()
        return obj.eventFilter(obj, event)

    def onMouseMoved(self, scene, pos, buttons):
        if self.app.progressbar.isVisible():
            return

        self.coorview.updatePos(pos)

        item = self.app.currentItem()
        try:
            cmapper = item.cmapper
        except AttributeError:
            cmapper = None
        self.geocoorview.updatePos(pos, cmapper)
