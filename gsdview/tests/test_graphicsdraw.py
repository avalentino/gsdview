#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Copyright (C) 2008-2010 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of exectools.

### This module is free software you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation either version 2 of the License, or
### (at your option) any later version.

### This module is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with this module if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US

import os
import sys
import logging

# Select the PyQt API 2
import sip
sip.setapi('QDate',       2)
sip.setapi('QDateTime',   2)
sip.setapi('QString',     2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime',       2)
sip.setapi('QUrl',        2)
sip.setapi('QVariant',    2)

from PyQt4 import QtCore, QtGui, QtSvg

# Fix sys path
from os.path import abspath, dirname
GSDVIEWROOT = abspath(os.path.join(dirname(__file__), os.pardir, os.pardir))
sys.path.insert(0, GSDVIEWROOT)

from gsdview import qt4support
from gsdview import qt4draw
from gsdview.mousemanager import MouseManager, RubberBandMode


### Main application ##########################################################
class GraphicsDrawApp(QtGui.QMainWindow):
    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0)):
        QtGui.QMainWindow.__init__(self, parent, flags)
        self.statusBar().show()

        self.scene = QtGui.QGraphicsScene(self)
        self.graphicsview = QtGui.QGraphicsView(self.scene, self)
        #~ self.graphicsview.setMouseTracking(True)    # @TODO: check
        self.setCentralWidget(self.graphicsview)

        self.mousemanager = MouseManager(self)
        self.mousemanager.register(self.graphicsview)
        self.mousemanager.addMode(RubberBandMode)
        self.mousemanager.addMode(qt4draw.DrawPointMode)
        self.mousemanager.addMode(qt4draw.DrawLineMode)
        #self.mousemanager.addMode(qt4draw.DrawPolygonMode)
        self.mousemanager.addMode(qt4draw.DrawRectMode)
        self.mousemanager.addMode(qt4draw.DrawEllipseMode)
        self.mousemanager.mode = 'hand'

        # File Actions
        self.fileactions = self._setupFileActions()

        menu = QtGui.QMenu('&File', self)
        menu.addActions(self.fileactions.actions())
        self.menuBar().addMenu(menu)
        self._filemenu = menu

        toolbar = QtGui.QToolBar('File toolbar', self)
        toolbar.addActions(self.fileactions.actions())
        self.addToolBar(toolbar)

        # Mouse Actions
        menu = QtGui.QMenu('Mouse', self)
        menu.addActions(self.mousemanager.actions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('Mouse toolbar')
        toolbar.addActions(self.mousemanager.actions.actions())
        self.addToolBar(toolbar)

        # View Actions
        self.viewactions = self._setupViewActions()

        menu = QtGui.QMenu('&View', self)
        menu.addActions(self.viewactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('View toolbar')
        toolbar.addActions(self.viewactions.actions())
        self.addToolBar(toolbar)

        # Help action
        self.helpactions = self._setupHelpActions()

        menu = QtGui.QMenu('&Help', self)
        menu.addActions(self.helpactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('Help toolbar', self)
        toolbar.addActions(self.helpactions.actions())
        self.addToolBar(toolbar)

        self.scene.setSceneRect(0, 0, 800, 600)
        self.statusBar().showMessage('Ready')

    def _setupFileActions(self):
        style = self.style()

        actions = QtGui.QActionGroup(self)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogOpenButton)
        QtGui.QAction(icon, self.tr('&Open'), actions,
                      objectName='openAction',
                      shortcut=self.tr('Ctrl+O'),
                      statusTip=self.tr('Open'),
                      triggered=self.onOpen)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogSaveButton)
        QtGui.QAction(icon, self.tr('&Save As'), actions,
                      objectName='saveAsAction',
                      shortcut=self.tr('Ctrl+S'),
                      statusTip=self.tr('Save as'),
                      triggered=self.onSave)

        icon = QtGui.QIcon(
                ':/trolltech/dialogs/qprintpreviewdialog/images/print-32.png')
        QtGui.QAction(icon, self.tr('&Print'), actions,
                      objectName='printAction',
                      shortcut=self.tr('Ctrl+P'),
                      statusTip=self.tr('Print'),
                      triggered=self.onPrint)

        QtGui.QAction(actions).setSeparator(True)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogCancelButton)
        QtGui.QAction(icon, self.tr('&Quit'), actions,
                      objectName='exitAction',
                      shortcut=self.tr('Ctrl+Q'),
                      statusTip=self.tr('Quit'),
                      triggered=self.close)

        return actions

    def _setupViewActions(self):
        style = self.style()
        actions = QtGui.QActionGroup(self)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogResetButton)
        QtGui.QAction(icon, self.tr('Reset'), actions,
                      objectName='resetAction',
                      statusTip=self.tr('Reset'),
                      triggered=self.onReset)

        QtGui.QAction(actions).setSeparator(True)

        icon = QtGui.QIcon(
            ':/trolltech/dialogs/qprintpreviewdialog/images/zoom-in-32.png')
        QtGui.QAction(icon, self.tr('Zoom In'), actions,
                      objectName='zoomInAction',
                      statusTip=self.tr('Zoom In'),
                      shortcut=self.tr('Ctrl++'),
                      triggered=lambda: self.graphicsview.scale(1.2, 1.2))

        icon = QtGui.QIcon(
            ':/trolltech/dialogs/qprintpreviewdialog/images/zoom-out-32.png')
        QtGui.QAction(icon, self.tr('Zoom Out'), actions,
                      objectName='zoomOutAction',
                      statusTip=self.tr('Zoom Out'),
                      shortcut=self.tr('Ctrl+-'),
                      triggered=lambda: self.graphicsview.scale(1/1.2, 1/1.2))

        icon = QtGui.QIcon(
            ':/trolltech/dialogs/qprintpreviewdialog/images/page-setup-24.png')
        QtGui.QAction(icon, self.tr('Zoom 1:1'), actions,
                      objectName='zoomResetAction',
                      statusTip=self.tr('Zoom 1:1'),
                      triggered=lambda: self.graphicsview.setMatrix(
                                            QtGui.QMatrix(1, 0, 0, -1, 0, 0)))

        icon = QtGui.QIcon(
            ':/trolltech/dialogs/qprintpreviewdialog/images/fit-page-32.png')
        QtGui.QAction(icon, self.tr('Zoom Fit'), actions,
                      objectName='zoomFitAction',
                      statusTip=self.tr('Zoom Fit'),
                      #checkable=True,
                      triggered=lambda: self.graphicsview.fitInView(
                                                self.graphicsview.sceneRect(),
                                                QtCore.Qt.KeepAspectRatio))

        return actions

    def _setupHelpActions(self):
        actions = QtGui.QActionGroup(self)

        icon = QtGui.QIcon(
                    ':/trolltech/styles/commonstyle/images/fileinfo-32.png')
        QtGui.QAction(icon, self.tr('About'), actions,
                      objectName='aboutAction',
                      statusTip=self.tr('About'),
                      triggered=self.about)

        icon = QtGui.QIcon(':/trolltech/qmessagebox/images/qtlogo-64.png')
        QtGui.QAction(icon, self.tr('About Qt'), actions,
                      objectName='aboutQtAction',
                      statusTip=self.tr('About Qt'),
                      triggered=QtGui.QApplication.aboutQt)

        return actions

    @QtCore.pyqtSlot()
    def about(self):
        title = self.tr('PyQt4 Graphics Draw Example')
        text = ['<h1>Graphics Draw</h1>'
                '<p>Example program for the basic PyQt4 graphics drawing.</p>',
                '<p>Copyright (C): 2010 '
                '<a href="mailto:a_valentino@users.sf.net">'
                    'Antonio Valentino<a>.</p>']
        text = self.tr('\n'.join(text))
        QtGui.QMessageBox.about(self, title, text)

    @QtCore.pyqtSlot()
    def reset(self):
        self.scene.clear()
        self.scene.setSceneRect(0, 0, 800, 600)
        self.graphicsview.setTransform(QtGui.QTransform())

    @QtCore.pyqtSlot()
    def onReset(self):
        ret = QtGui.QMessageBox.question(self,
                self.tr('Reset'),
                self.tr('Are you sure you want to reset the document?\n'
                        'All changes will be lost.'))
        if ret == QtGui.QMessageBox.Ok:
            self.reset()


    @QtCore.pyqtSlot()
    def onOpen(self):
        filters = [
            self.tr('All files (*)'),
        ]
        filters.extend('%s file (*.%s)' % (str(f).upper(), str(f))
                        for f in QtGui.QImageReader.supportedImageFormats())

        filename, filter_ = QtGui.QFileDialog.getOpenFileNameAndFilter(
                                        self,
                                        self.tr('Load picture'),
                                        QtCore.QDir.home().absolutePath(),
                                        ';;'.join(filters)) #, filters[1])
        if filename:
            if '.svg' in filename:
                item = QtSvg.QGraphicsSvgItem(filename)
            else:
                image = QtGui.QImage(filename)
                item = QtGui.QGraphicsPixmapItem(image)

            item.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
            item.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)

            self.scene.addItem(item)

    @QtCore.pyqtSlot()
    def onSave(self):
        qt4support.imgexport(self.scene, self)

    @QtCore.pyqtSlot()
    def onPrint(self):
        qt4support.printObject(self.scene, parent=self)


def main(*argv):
    # @NOTE: basic config doesn't work since sip use it before this line
    #logging.basicConfig(level=logging.DEBUG, format='%(levelname): %(message)s')
    logging.getLogger().setLevel(logging.DEBUG)

    if not argv:
        argv = sys.argv
    else:
        argv = list(argv)

    app = QtGui.QApplication(argv)
    app.setApplicationName('GraphicsDrawApp')
    w = GraphicsDrawApp()
    w.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
