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


class SnapshotTool(QtCore.QObject):
    def __init__(self, app, **kwargs):
        super(SnapshotTool, self).__init__(app, **kwargs)
        self.app = app

        self.actions = self._setupActions()
        self.actions.setEnabled(False)

        self.app.mdiarea.subWindowActivated.connect(self.onSubWindowChanged)

    def _setupActions(self):
        actions = QtGui.QActionGroup(self)

        # Save to file
        icon = qt4support.geticon('camera.svg', __name__)
        QtGui.QAction(icon, self.tr('Export'), actions,
                      objectName='exportAction',
                      statusTip=self.tr('Export a snapshot of the current '
                                        'view to file'),
                      shortcut=QtGui.QKeySequence(self.tr('Ctrl+S')),
                      triggered=self.exportToFile)

        # Copy to clipboard
        icon = qt4support.geticon('copy.svg', 'gsdview')
        QtGui.QAction(icon, self.tr('Copy'), actions,
                      objectName='copyToClipboarsAction',
                      statusTip=self.tr('Copy to clipboard'),
                      shortcut=QtGui.QKeySequence(self.tr('Ctrl+C')),
                      triggered=self.copyToClipboard)

        return actions

    def _graphicsview(self, subwin=None):
        if subwin is None:
            subwin = self.app.mdiarea.activeSubWindow()

        try:
            view = subwin.widget()
        except AttributeError:
            view = None
        else:
            if not isinstance(view, QtGui.QGraphicsView):
                view = None

        return view

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(QtGui.QMdiSubWindow)
    def onSubWindowChanged(self, subwin=None):
        view = self._graphicsview()
        enabled = bool(view is not None)
        self.actions.setEnabled(enabled)

    @QtCore.pyqtSlot()
    def exportToFile(self):
        print 'exportToFile'

        view = self._graphicsview()
        if view is None:
            #self.actions.setEnabled(False)
            return

        qt4support.imgexport(view, self.app)

    @QtCore.pyqtSlot()
    def copyToClipboard(self):
        print 'copyToClipboard'

        view = self._graphicsview()
        if view is None:
            #self.actions.setEnabled(False)
            return

        srcsize = view.viewport().rect().size()
        image = QtGui.QImage(srcsize, QtGui.QImage.Format_RGB32)
        #color = view.backgroundBrush().color()
        #color = QtCore.Qt.white
        #image.fill(color.rgb())

        painter = QtGui.QPainter()
        if painter.begin(image):
            view.render(painter)
            painter.end()

            clipboard = QtGui.qApp.clipboard()
            clipboard.setImage(image)
        else:
            QtGui.QMessageBox.warning(self.app, self.tr('Warning'),
                                self.tr('Unable initialize painting device.'))

