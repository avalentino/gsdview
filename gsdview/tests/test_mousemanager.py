#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Copyright (C) 2008-2010 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of exectools.

### This module is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### This module is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with this module; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US

import os
import sys

# Select the PyQt API 2
import sip
sip.setapi('QDate',       2)
sip.setapi('QDateTime',   2)
sip.setapi('QString',     2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime',       2)
sip.setapi('QUrl',        2)
sip.setapi('QVariant',    2)

from PyQt4 import QtCore, QtGui

# Fix sys path
from os.path import abspath, dirname
GSDVIEWROOT = abspath(os.path.join(dirname(__file__), os.pardir, os.pardir))
sys.path.insert(0, GSDVIEWROOT)


from gsdview.mousemanager import MouseManager


class MainWin(QtGui.QMainWindow):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QMainWindow.__init__(self, parent, flags)

        self.mousemanager = MouseManager(self)

        from gsdview.mousemanager import RubberBandMode
        rubberbandmode = RubberBandMode()
        self.mousemanager.addMode(rubberbandmode)
        def callback(rect):
            print 'rect', rect

        rubberbandmode.rubberBandSeclection.connect(callback)
                                    #lambda r: sys.stdout.write(str(r)+'\n'))

        self.scene = QtGui.QGraphicsScene(self)
        self.graphicsview = QtGui.QGraphicsView(self.scene, self)
        self.setCentralWidget(self.graphicsview)

        self.mousemanager.register(self.graphicsview)

        # File Actions
        self.fileactions = self._setupFileActions()

        menu = QtGui.QMenu('File', self)
        menu.addActions(self.fileactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('File', self)
        toolbar.addActions(self.fileactions.actions())
        self.addToolBar(toolbar)

        # Mouse Actions
        menu = QtGui.QMenu('Mouse')
        menu.addActions(self.mousemanager.actions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('Mouse')
        toolbar.addActions(self.mousemanager.actions.actions())
        self.addToolBar(toolbar)

        # Help action
        self.helpactions = self._setupHelsActions()

        menu = QtGui.QMenu('Help', self)
        menu.addActions(self.helpactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('Help', self)
        toolbar.addActions(self.helpactions.actions())
        self.addToolBar(toolbar)

        self.resize(700, 500)

    def _setupFileActions(self):
        style = self.style()

        actions = QtGui.QActionGroup(self)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogOpenButton)
        QtGui.QAction(icon, 'Open', actions, triggered=self.openfile)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogCloseButton)
        QtGui.QAction(icon, 'Close', actions,triggered=self.scene.clear)

        QtGui.QAction(actions).setSeparator(True)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogCancelButton)
        QtGui.QAction(icon, 'Exit', actions, triggered=self.close)

        return actions

    def _setupHelsActions(self):
        actions = QtGui.QActionGroup(self)

        icon = QtGui.QIcon(':/trolltech/styles/commonstyle/images/fileinfo-32.png')
        QtGui.QAction(icon, 'About', actions, triggered=self.about)

        icon = QtGui.QIcon(':/trolltech/qmessagebox/images/qtlogo-64.png')
        QtGui.QAction(icon, 'About Qt', actions,
                      triggered=QtGui.QApplication.aboutQt)

        return actions

    @QtCore.pyqtSlot()
    def openfile(self):
        self.scene.clear()
        self.graphicsview.setMatrix(QtGui.QMatrix())
        filename = QtGui.QFileDialog.getOpenFileName()
        if filename:
            pixmap = QtGui.QPixmap(filename)
            item = self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(item.boundingRect())

    @QtCore.pyqtSlot()
    def about(self):
        title = self.tr('MouseManager Example')
        text = ['<h1>Mouse Manager</h1>'
                '<p>Example program for the Mouse manager component.</p>',
                '<p>Copyright (C): 2009-2010 '
                '<a href="mailto:a_valentino@users.sf.net">'
                    'Antonio Valentino'
                '<a>.</p>']
        text = self.tr('\n'.join(text))
        QtGui.QMessageBox.about(self, title, text)


def test_mousemanager():
    import sys
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('MouseManager')
    mainwin = MainWin()
    mainwin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    test_mousemanager()
