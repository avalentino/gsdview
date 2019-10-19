#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2015 Antonio Valentino <antonio.valentino@tiscali.it>
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


import os
import sys
import logging

from osgeo import ogr


# Fix sys path
GSDVIEWROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, GSDVIEWROOT)


from qtpy import QtCore, QtWidgets, QtGui

from gsdview.mousemanager import MouseManager
from gsdview.layermanager import LayerManager
from gsdview.gdalbackend import ogrqt


class VectorGraphicsApp(QtWidgets.QMainWindow):
    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0)):
        QtWidgets.QMainWindow.__init__(self, parent, flags)
        self.statusBar().show()

        self.model = QtGui.QStandardItemModel(self)
        self.model.setColumnCount(2)

        self.treeview = QtWidgets.QTreeView()
        self.treeview.setModel(self.model)
        self.treeview.setHeaderHidden(True)
        self.treeview.setIndentation(0)
        self.treeview.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)
        self.treeview.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.treeview.header().setStretchLastSection(True)

        self.treedock = QtWidgets.QDockWidget(self.tr('Layers View'), self)
        self.treedock.setWidget(self.treeview)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.treedock)

        self.scene = QtWidgets.QGraphicsScene(self)
        self.graphicsview = QtWidgets.QGraphicsView(self.scene, self)
        self.setCentralWidget(self.graphicsview)

        self.mousemanager = MouseManager(self)
        self.mousemanager.register(self.graphicsview)
        self.mousemanager.mode = 'hand'

        self.layermanager = LayerManager(self.treeview, self)

        # File Actions
        self.fileactions = self._setupFileActions()

        menu = QtWidgets.QMenu('File', self)
        menu.addActions(self.fileactions.actions())
        self.menuBar().addMenu(menu)
        self._filemenu = menu

        toolbar = QtWidgets.QToolBar('File toolbar', self)
        toolbar.addActions(self.fileactions.actions())
        self.addToolBar(toolbar)

        # Mouse Actions
        menu = QtWidgets.QMenu('Mouse', self)
        menu.addActions(self.mousemanager.actions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtWidgets.QToolBar('Mouse toolbar')
        toolbar.addActions(self.mousemanager.actions.actions())
        self.addToolBar(toolbar)

        # View Actions
        self.viewactions = self._setupViewActions()

        menu = QtWidgets.QMenu('View', self)
        menu.addActions(self.viewactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtWidgets.QToolBar('View toolbar')
        toolbar.addActions(self.viewactions.actions())
        self.addToolBar(toolbar)

        # Layer Actions
        layeractions = self.layermanager.actions

        menu = QtWidgets.QMenu('Layer', self)
        menu.addActions(layeractions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtWidgets.QToolBar('Layer toolbar')
        toolbar.addActions(layeractions.actions())
        self.addToolBar(toolbar)

        # Help action
        self.helpactions = self._setupHelpActions()

        menu = QtWidgets.QMenu('Help', self)
        menu.addActions(self.helpactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtWidgets.QToolBar('Help toolbar', self)
        toolbar.addActions(self.helpactions.actions())
        self.addToolBar(toolbar)

        self.resize(900, 500)
        self.reset()
        self.statusBar().showMessage('Ready')

    def _setupFileActions(self):
        style = self.style()

        actions = QtWidgets.QActionGroup(self)

        icon = style.standardIcon(QtWidgets.QStyle.SP_DialogOpenButton)
        QtWidgets.QAction(
            icon, self.tr('Open Vector'), actions,
            objectName='openVectorAction',
            statusTip=self.tr('Open Vector'),
            triggered=self.onOpenVector)

        icon = style.standardIcon(QtWidgets.QStyle.SP_DialogResetButton)
        QtWidgets.QAction(
            icon, self.tr('Close All'), actions,
            objectName='claseAllAction',
            statusTip=self.tr('Close All'),
            triggered=self.reset)

        QtWidgets.QAction(actions).setSeparator(True)

        icon = style.standardIcon(QtWidgets.QStyle.SP_DialogCancelButton)
        QtWidgets.QAction(
            icon, self.tr('Exit'), actions,
            objectName='exitAction',
            statusTip=self.tr('Exit'),
            triggered=self.close)

        return actions

    def _setupViewActions(self):
        actions = QtWidgets.QActionGroup(self)

        icon = QtGui.QIcon(
            ':/trolltech/dialogs/qprintpreviewdialog/images/zoom-in-32.png')
        QtWidgets.QAction(
            icon, self.tr('Zoom In'), actions,
            objectName='zoomInAction',
            statusTip=self.tr('Zoom In'),
            shortcut=self.tr('Ctrl++'),
            triggered=lambda: self.graphicsview.scale(1.2, 1.2))

        icon = QtGui.QIcon(
            ':/trolltech/dialogs/qprintpreviewdialog/images/zoom-out-32.png')
        QtWidgets.QAction(
            icon, self.tr('Zoom Out'), actions,
            objectName='zoomOutAction',
            statusTip=self.tr('Zoom Out'),
            shortcut=self.tr('Ctrl+-'),
            triggered=lambda: self.graphicsview.scale(1 / 1.2, 1 / 1.2))

        icon = QtGui.QIcon(
            ':/trolltech/dialogs/qprintpreviewdialog/images/page-setup-24.png')
        QtWidgets.QAction(
            icon, self.tr('Zoom 1:1'), actions,
            objectName='zoomResetAction',
            statusTip=self.tr('Zoom 1:1'),
            triggered=lambda: self.graphicsview.setTransform(
                QtGui.QTransform(1, 0, 0, -1, 0, 0)))

        icon = QtGui.QIcon(
            ':/trolltech/dialogs/qprintpreviewdialog/images/fit-page-32.png')
        QtWidgets.QAction(
            icon, self.tr('Zoom Fit'), actions,
            objectName='zoomFitAction',
            statusTip=self.tr('Zoom Fit'),
            #checkable=True,
            triggered=lambda: self.graphicsview.fitInView(
                self.graphicsview.sceneRect(),
                QtCore.Qt.KeepAspectRatio))

        return actions

    def _setupHelpActions(self):
        actions = QtWidgets.QActionGroup(self)

        icon = QtGui.QIcon(
            ':/trolltech/styles/commonstyle/images/fileinfo-32.png')
        QtWidgets.QAction(
            icon, self.tr('About'), actions,
            objectName='aboutAction',
            statusTip=self.tr('About'),
            triggered=self.about)

        icon = QtGui.QIcon(':/trolltech/qmessagebox/images/qtlogo-64.png')
        QtWidgets.QAction(
            icon, self.tr('About Qt'), actions,
            objectName='aboutQtAction',
            statusTip=self.tr('About Qt'),
            triggered=QtWidgets.QApplication.aboutQt)

        return actions

    @QtCore.Slot()
    def about(self):
        title = self.tr('MouseManager Example')
        text = [
            '<h1>Mouse Manager</h1>'
            '<p>Example program for the OGR proxy components.</p>',
            '<p>Copyright (C): 2009-2015 '
            '<a href="mailto:antonio.valentino@tiscali.it">Antonio Valentino<a>.'
            '</p>'
        ]
        text = self.tr('\n'.join(text))
        QtWidgets.QMessageBox.about(self, title, text)

    @QtCore.Slot()
    def reset(self):
        self.scene.clear()
        self.graphicsview.resetTransform()
        self.graphicsview.scale(1., -1.)
        self.model.clear()

    @QtCore.Slot()
    def onOpenVector(self):
        ogrFilters = [
            'All files (*)',
            'ESRI Shapefiles (*.shp)',
            'KML (*.kml, *.kmz)',
        ]
        filenames, filter_ = QtWidgets.QFileDialog.getOpenFileNamesAndFilter(
            self,
            self.tr('Open Vector'),
            QtCore.QDir.home().absolutePath(),
            ';;'.join(ogrFilters),
            ogrFilters[1])

        for filename in filenames:
            filename = str(filename)    # unicode --> str
            # @TODO: check if it is already open
            self.openvector(filename)

    def openvector(self, filename):
        # @TODO: check limits
        MAX_LAYER_COUNT = 10

        srs = None
        transform = None
        affine_transform = None

        # @TODO: remove
        #srs = osr.SpatialReference()
        #srs.SetLCC(20, 20, 20, 0, 0, 0)
        ##srs.SetUTM(33)

        # @TODO: remove
        #~ from math import sin, cos, radians
        #~ a = radians(-45)
        #~ qtransform = QtGui.QTransform(
            #~ cos(a), -sin(a), sin(a), cos(a), 0, 0)
        #~ #affine_transform = qtransform
        #~ transform = lambda x, y, z: qtransform.map(x, y)

        ds = ogr.Open(filename)
        if ds is None:
            raise ValueError('unable to open "$s"' % filename)

        if ds.GetLayerCount() > MAX_LAYER_COUNT:
            raise RuntimeError('too many layers: %d' % ds.GetLayerCount())

        for index, layer in enumerate(ds):
            qlayer = ogrqt.layerToGraphicsItem(layer, srs, transform)
            #qlayer.datasource = ds.GetName()
            #qlayer.index = index
            qlayer.setData(ogrqt.DATAKEY['datasource'], ds.GetName())
            qlayer.setData(ogrqt.DATAKEY['index'], index)

            if affine_transform:
                qlayer.setTransform(affine_transform)

            if qlayer.childItems():
                self.scene.addItem(qlayer)

                item = QtGui.QStandardItem(layer.GetName())
                item.setCheckable(True)
                item.setCheckState(QtCore.Qt.Checked)
                item.setData(qlayer)
                item.setToolTip(
                    self.tr('Layer "%s": %d features.' % (
                        layer.GetName(),
                        len(qlayer.childItems()))))

                self.model.appendRow(item)

        self.treeview.resizeColumnToContents(0)

    def _autocolor(self):
        COLORS = (
            #QtCore.Qt.white,
            QtCore.Qt.black,
            QtCore.Qt.red,
            QtCore.Qt.darkRed,
            QtCore.Qt.green,
            QtCore.Qt.darkGreen,
            QtCore.Qt.blue,
            QtCore.Qt.darkBlue,
            QtCore.Qt.cyan,
            QtCore.Qt.darkCyan,
            QtCore.Qt.magenta,
            QtCore.Qt.darkMagenta,
            QtCore.Qt.yellow,
            QtCore.Qt.darkYellow,
            QtCore.Qt.gray,
            QtCore.Qt.darkGray,
            QtCore.Qt.lightGray,
            #QtCore.Qt.transparent,
            #QtCore.Qt.color0,
            #QtCore.Qt.color1,
        )

        ncolors = len(COLORS)
        nrows = self.model.rowCount()
        for row in range(nrows):
            color = COLORS[row % ncolors]

            qlayer = self.model.item(row).data()

            #~ pen = qlayer.pen()
            #~ pen.setColor(color)
            #~ #pen.setWidth(1)
            #~ qlayer.setPen(pen)

            brush = qlayer.brush()
            brush.setColor(color)
            brush.setStyle(QtCore.Qt.SolidPattern)
            qlayer.setBrush(brush)


def main(*argv):
    # @NOTE: basic config doesn't work since other modules (e.g. sip)
    #        use it before this line
    #logging.basicConfig(level=logging.DEBUG,
    #                    format='%(levelname): %(message)s')
    logging.getLogger().setLevel(logging.DEBUG)

    if not argv:
        argv = sys.argv
    else:
        argv = list(argv)

    app = QtWidgets.QApplication(argv)
    app.setApplicationName('VectorGraphicsApp')
    w = VectorGraphicsApp()
    w.show()
    for filename in argv[1:]:
        w.openvector(filename)

    w._autocolor()

    sys.exit(app.exec_())


if __name__ == '__main__':
    import glob
    datadir = os.path.expanduser('~/Immagini/naturalearth_small_scale')
    shapefiles = glob.glob(os.path.join(datadir, '110m_physical', '*.shp'))
    argv = sys.argv + sorted(shapefiles)
    main(*argv)
