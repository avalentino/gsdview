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


'''Core modue for image stretch control.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date: 2010/02/14 22:02:21 $'
__revision__ = '$Revision: 36b7b35ff3b6 $'

from PyQt4 import QtCore, QtGui

from gsdview import qt4support

from stretch.widgets import StretchDialog

class StretchController(QtCore.QObject):
    def __init__(self, app):
        super(StretchController, self).__init__()
        self.app = app
        self.dialog = StretchDialog(parent=app)
        self.dialog.hide()

        self.action = self._setupAction()
        self.action.setEnabled(False)

        self.connect(self.dialog, QtCore.SIGNAL('finished(int)'),
                     lambda result: self.action.setChecked(False))
        self.connect(self.app.mdiarea,
                     QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                     self.onSubWindowActivated)
        #~ self.connect(self.app.treeview,
                     #~ QtCore.SIGNAL('clicked(const QModelIndex&)'),
                     #~ self.onItemClicked)
        #~ self.connect(self.app, QtCore.SIGNAL('subWindowClosed()'),
                     #~ self.onModelChanged)
        self.connect(self.dialog,
                     QtCore.SIGNAL('valueChanged()'),
                     self.onStretchChanged)

    def _setupAction(self):
        icon = qt4support.geticon('stretching.svg', __name__)
        action = QtGui.QAction(icon, self.tr('Stretch'), self)
        action.setStatusTip(self.tr('Stretch'))
        action.setCheckable(True)
        self.connect(action, QtCore.SIGNAL('triggered(bool)'),
                     self.onButtonToggled)

        return action

    def onButtonToggled(self, checked=True):
        if checked:
            self.reset()
            self.dialog.show()
            #self.action.setChecked(True)
        else:
            self.dialog.hide()
            self.action.setChecked(False)

    def reset(self, item=None):
        if item is None:
            item = self.currentGraphicsItem()
        if item is None or not hasattr(item,'stretch'):
            self.dialog.setEnabled(False)
            return

        self.dialog.setEnabled(True)

        imin, imax = item.stretch.range
        minimum, maximum = item.dataRange()

        # @TODO: remove this
        #minimum = None

        if minimum is not None:
            self.dialog.stretchwidget.setMinimum(minimum)
        else:
            self.dialog.stretchwidget.setMinimum(min(imin, 0))

        if maximum is not None:
            self.dialog.stretchwidget.setMaximum(maximum)
        else:
            self.dialog.stretchwidget.setMaximum(max(imax, 2*imax))

        self.dialog.stretchwidget.setLow(imin)
        self.dialog.stretchwidget.setHigh(imax)
        self.dialog.saveState()

    # @TODO: move to main app (??)
    def currentGraphicsItem(self, window=None):
        if window is None:
            window = self.app.mdiarea.activeSubWindow()
        try:
            return window.item.graphicsitem
        except AttributeError, e:
            return None

    def onSubWindowActivated(self, subwindow):
        if not subwindow:
            self.action.setEnabled(self.dialog.isVisible())
            self.dialog.setEnabled(False)
            return

        item = self.currentGraphicsItem(subwindow)
        try:
            stretchable = item.stretch is not None
        except AttributeError:
            stretchable = False

        if stretchable:
            self.action.setEnabled(True)
            if self.dialog.isVisible():
                self.dialog.setEnabled(True)
                self.reset(item)
        else:
            if self.dialog.isVisible():
                self.action.setEnabled(True)
                self.dialog.setEnabled(False)
            else:
                self.action.setEnabled(False)


    # @TODO: remove
    #~ def onItemClicked(self, index):
        #~ if not self.app.mdiarea.activeSubWindow():
            #~ item = mainwin.datamodel.itemFromIndex(index)
            #~ self.reset(item)

    #~ def onModelChanged(self, index=None, start=None, stop=None):
        #~ item = self.app.currentGraphicsItem()
        #~ self.reset(item)

    def onStretchChanged(self):
        item = self.currentGraphicsItem()
        try:
            stretch = item.stretch
        except AttributeError:
            #self.dialog.hide()
            pass
        else:
            vmin, vmax = self.dialog.values()
            stretch.set_range(vmin, vmax)
            item.update()
