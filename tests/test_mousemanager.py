#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2019 Antonio Valentino <antonio.valentino@tiscali.it>
#
# This module is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 2 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this module if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US


from __future__ import print_function

import os
import sys


# Fix sys path
GSDVIEWROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, GSDVIEWROOT)


from qtpy import QtCore, QtWidgets, QtGui

from gsdview.mousemanager import MouseManager


class MainWin(QtWidgets.QMainWindow):

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0)):
        super(MainWin, self).__init__(parent, flags)

        self.mousemanager = MouseManager(self)

        from gsdview.mousemanager import RubberBandMode
        rubberbandmode = RubberBandMode()
        self.mousemanager.addMode(rubberbandmode)

        def callback(rect):
            print('rect', rect)

        rubberbandmode.rubberBandSeclection.connect(callback)

        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphicsview = QtWidgets.QGraphicsView(self.scene, self)
        self.setCentralWidget(self.graphicsview)

        self.mousemanager.register(self.graphicsview)

        # File Actions
        self.fileactions = self._setupFileActions()

        menu = QtWidgets.QMenu('File', self)
        menu.addActions(self.fileactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtWidgets.QToolBar('File', self)
        toolbar.addActions(self.fileactions.actions())
        self.addToolBar(toolbar)

        # Mouse Actions
        menu = QtWidgets.QMenu('Mouse', self)
        menu.addActions(self.mousemanager.actions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtWidgets.QToolBar('Mouse')
        toolbar.addActions(self.mousemanager.actions.actions())
        self.addToolBar(toolbar)

        # Help action
        self.helpactions = self._setupHelpActions()

        menu = QtWidgets.QMenu('Help', self)
        menu.addActions(self.helpactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtWidgets.QToolBar('Help', self)
        toolbar.addActions(self.helpactions.actions())
        self.addToolBar(toolbar)

        self.resize(700, 500)

    def _setupFileActions(self):
        style = self.style()

        actions = QtWidgets.QActionGroup(self)

        icon = style.standardIcon(QtWidgets.QStyle.SP_DialogOpenButton)
        QtWidgets.QAction(icon, 'Open', actions, triggered=self.openfile)

        icon = style.standardIcon(QtWidgets.QStyle.SP_DialogCloseButton)
        QtWidgets.QAction(icon, 'Close', actions, triggered=self.scene.clear)

        QtWidgets.QAction(actions).setSeparator(True)

        icon = style.standardIcon(QtWidgets.QStyle.SP_DialogCancelButton)
        QtWidgets.QAction(icon, 'Exit', actions, triggered=self.close)

        return actions

    def _setupHelpActions(self):
        actions = QtWidgets.QActionGroup(self)

        icon = QtGui.QIcon(
            ':/trolltech/styles/commonstyle/images/fileinfo-32.png')
        QtWidgets.QAction(icon, 'About', actions, triggered=self.about)

        icon = QtGui.QIcon(':/trolltech/qmessagebox/images/qtlogo-64.png')
        QtWidgets.QAction(icon, 'About Qt', actions,
                          triggered=QtWidgets.QApplication.aboutQt)

        return actions

    @QtCore.Slot()
    def openfile(self):
        self.scene.clear()
        self.graphicsview.setTransform(QtGui.QTransform())
        filename = QtWidgets.QFileDialog.getOpenFileName()
        if filename:
            pixmap = QtGui.QPixmap(filename)
            item = self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(item.boundingRect())

    @QtCore.Slot()
    def about(self):
        title = self.tr('MouseManager Example')
        text = ['<h1>Mouse Manager</h1>'
                '<p>Example program for the Mouse manager component.</p>',
                '<p>Copyright (C): 2009-2019 '
                '<a href="mailto:antonio.valentino@tiscali.it">'
                'Antonio Valentino'
                '<a>.</p>']
        text = self.tr('\n'.join(text))
        QtWidgets.QMessageBox.about(self, title, text)


def test_mousemanager():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('MouseManager')
    mainwin = MainWin()
    mainwin.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    test_mousemanager()
