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

from PyQt4 import QtCore, QtGui
from osgeo import ogr

# Fix sys path
from os.path import abspath, dirname
GSDVIEWROOT = abspath(os.path.join(dirname(__file__),
                                   os.pardir, os.pardir, os.pardir))
sys.path.insert(0, GSDVIEWROOT)

from gsdview.mousemanager import MouseManager
from gsdview.gdalbackend import ogrqt4


class VectorGraphicsApp(QtGui.QMainWindow):
    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QMainWindow.__init__(self, parent, flags)
        self.statusBar().show()

        self.model = QtGui.QStandardItemModel(self)
        self.model.setColumnCount(2)
        # @TODO: check
        self.model.layoutChanged.connect(self.onLayoutChanged)
        self.model.rowsInserted.connect(self.onLayoutChanged)
        self.model.rowsRemoved.connect(self.onLayoutChanged)

        self.treeview = QtGui.QTreeView()
        self.treeview.setModel(self.model)
        self.treeview.setHeaderHidden(True)
        self.treeview.setIndentation(0)
        self.treeview.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.treeview.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.treeview.header().setStretchLastSection(True)
        self.treeview.clicked.connect(self.onItemClicked)
        self.treeview.activated.connect(self.onItemActivated)

        self.treedock = QtGui.QDockWidget(self.tr('Layers View'), self)
        self.treedock.setWidget(self.treeview)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.treedock)

        self.scene = QtGui.QGraphicsScene(self)
        self.graphicsview = QtGui.QGraphicsView(self.scene, self)
        self.setCentralWidget(self.graphicsview)

        self.mousemanager = MouseManager(self)
        self.mousemanager.register(self.graphicsview)
        self.mousemanager.mode = 'hand'

        # File Actions
        self.fileactions = self._setupFileActions()

        menu = QtGui.QMenu('File', self)
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

        menu = QtGui.QMenu('View', self)
        menu.addActions(self.viewactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('View toolbar')
        toolbar.addActions(self.viewactions.actions())
        self.addToolBar(toolbar)

        # Layer Actions
        self.layeractions = self._setupLayerActions()
        self.treeview.addActions(self.layeractions.actions())
        self.model.rowsInserted.connect(self._updateLayerActions)
        self.model.rowsRemoved.connect(self._updateLayerActions)
        self.treeview.selectionModel().selectionChanged.connect(
                                                    self._updateLayerActions)

        menu = QtGui.QMenu('Layer', self)
        menu.addActions(self.layeractions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('Layer toolbar')
        toolbar.addActions(self.layeractions.actions())
        self.addToolBar(toolbar)

        self._updateLayerActions()

        # Help action
        self.helpactions = self._setupHelpActions()

        menu = QtGui.QMenu('Help', self)
        menu.addActions(self.helpactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('Help toolbar', self)
        toolbar.addActions(self.helpactions.actions())
        self.addToolBar(toolbar)

        self.resize(900, 500)
        self.reset()
        self.statusBar().showMessage('Ready')

    def _setupFileActions(self):
        style = self.style()

        actions = QtGui.QActionGroup(self)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogOpenButton)
        QtGui.QAction(icon, self.tr('Open Vector'), actions,
                      objectName='openVectorAction',
                      statusTip=self.tr('Open Vector'),
                      triggered=self.onOpenVector)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogResetButton)
        QtGui.QAction(icon, self.tr('Close All'), actions,
                      objectName='claseAllAction',
                      statusTip=self.tr('Close All'),
                      triggered=self.reset)

        QtGui.QAction(actions).setSeparator(True)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogCancelButton)
        QtGui.QAction(icon, self.tr('Exit'), actions,
                      objectName='exitAction',
                      statusTip=self.tr('Exit'),
                      triggered=self.close)

        return actions

    def _setupViewActions(self):
        actions = QtGui.QActionGroup(self)

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

    def _setupLayerActions(self):
        style = self.style()

        actions = QtGui.QActionGroup(self)

        icon = QtGui.QIcon(':/trolltech/styles/commonstyle/images/up-128.png')
        QtGui.QAction(icon, self.tr('Move to top'), actions,
                      objectName='moveToTopAction',
                      statusTip=self.tr('Move to top'),
                      shortcut=self.tr('Ctrl+PgUp'),
                      triggered=self.onMoveToTop)

        icon = style.standardIcon(QtGui.QStyle.SP_ArrowUp)
        QtGui.QAction(icon, self.tr('Move up'), actions,
                      objectName='moveUpAction',
                      statusTip=self.tr('Move up'),
                      shortcut=self.tr('Ctrl+Up'),
                      triggered=self.onMoveUp)

        icon = style.standardIcon(QtGui.QStyle.SP_ArrowDown)
        QtGui.QAction(icon, self.tr('Move down'), actions,
                      objectName='moveDownAction',
                      statusTip=self.tr('Move down'),
                      shortcut=self.tr('Ctrl+Down'),
                      triggered=self.onMoveDown)

        icon = QtGui.QIcon(':/trolltech/styles/commonstyle/images/down-128.png')
        QtGui.QAction(icon, self.tr('Move to bottom'), actions,
                      objectName='moveToBottomAction',
                      statusTip=self.tr('Move to bottom'),
                      shortcut=self.tr('Ctrl+PgDown'),
                      triggered=self.onMoveToBottom)

        #':/trolltech/styles/commonstyle/images/standardbutton-closetab-16.png'
        icon = QtGui.QIcon(
            ':/trolltech/styles/commonstyle/images/standardbutton-cancel-128.png')
        QtGui.QAction(icon, self.tr('Remove'), actions,
                      objectName='removeLayerAction',
                      statusTip=self.tr('Remove'),
                      shortcut=self.tr('Del'),
                      triggered=self.onRemoveLayer)

        icon = QtGui.QIcon(
            ':/trolltech/styles/commonstyle/images/standardbutton-yes-128.png')
        QtGui.QAction(icon, self.tr('Show'), actions,
                      objectName='showLayerAction',
                      statusTip=self.tr('Show the layer'),
                      triggered=self.checkSelectedItems)

        icon = QtGui.QIcon(
            ':/trolltech/styles/commonstyle/images/standardbutton-no-128.png')
        QtGui.QAction(icon, self.tr('Hide'), actions,
                      objectName='hideLayerAction',
                      statusTip=self.tr('Hide the layer'),
                      triggered=self.uncheckSelectedItems)

        icon = QtGui.QIcon(
                ':/trolltech/styles/commonstyle/images/viewdetailed-128.png')
        QtGui.QAction(icon, self.tr('Select all'), actions,
                      objectName='selectAllAction',
                      statusTip=self.tr('Select all'),
                      shortcut=self.tr('Ctrl-A'),
                      triggered=self.treeview.selectAll)

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
        title = self.tr('MouseManager Example')
        text = ['<h1>Mouse Manager</h1>'
                '<p>Example program for the OGR proxy components.</p>',
                '<p>Copyright (C): 2009-2010 '
                '<a href="mailto:a_valentino@users.sf.net">'
                    'Antonio Valentino'
                '<a>.</p>']
        text = self.tr('\n'.join(text))
        QtGui.QMessageBox.about(self, title, text)

    @QtCore.pyqtSlot()
    def reset(self):
        self.scene.clear()
        self.graphicsview.resetTransform()
        self.graphicsview.scale(1., -1.)
        self.model.clear()

    @QtCore.pyqtSlot()
    def onOpenVector(self):
        ogrFilters = [
            'All files (*)',
            'ESRI Shapefiles (*.shp)',
            'KML (*.kml, *.kmz)',
        ]
        filenames, filter_ = QtGui.QFileDialog.getOpenFileNamesAndFilter(
                                        self,
                                        self.tr('Open Vector'),
                                        QtCore.QDir.home().absolutePath(), #os.path.expanduser('~')
                                        ';;'.join(ogrFilters),
                                        ogrFilters[1])

        for filename in filenames:
            filename = str(filename) # unicode --> str
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
        #~ qtransform = QtGui.QTransform(cos(a), -sin(a), sin(a), cos(a), 0, 0)
        #~ #affine_transform = qtransform
        #~ transform = lambda x, y, z: qtransform.map(x, y)

        ds = ogr.Open(filename)
        if ds is None:
            raise ValueError('unable to open "$s"' % filename)

        if ds.GetLayerCount() > MAX_LAYER_COUNT:
            raise RuntimeError('too many layers: %d' % ds.GetLayerCount())

        for index, layer in enumerate(ds):
            qlayer = ogrqt4.layerToGraphicsItem(layer, srs, transform)
            #qlayer.datasource = ds.GetName()
            #qlayer.index = index
            qlayer.setData(ogrqt4.DATAKEY['datasource'], ds.GetName())
            qlayer.setData(ogrqt4.DATAKEY['index'], index)

            if affine_transform:
                qlayer.setTransform(affine_transform)

            if qlayer.childItems():
                self.scene.addItem(qlayer)

                item = QtGui.QStandardItem(layer.GetName())
                item.setCheckable(True)
                item.setCheckState(QtCore.Qt.Checked)
                item.setData(qlayer)
                item.setToolTip(self.tr('Layer "%s": %d features.' % (
                                                    layer.GetName(),
                                                    len(qlayer.childItems()))))

                self.model.appendRow(item)

                #~ # style settings
                #~ color = QtCore.Qt.red

                #~ pen = qlayer.pen()
                #~ pen.setColor(color)
                #~ #pen.setWidth(1)
                #~ qlayer.setPen(pen)

                #~ brush = qlayer.brush()
                #~ brush.setColor(color)
                #~ brush.setStyle(QtCore.Qt.SolidPattern)
                #~ qlayer.setBrush(brush)

        self.treeview.resizeColumnToContents(0)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def onItemClicked(self, index):
        if not index.column() == 0:
            return

        item = self.model.itemFromIndex(index)
        checked = bool(item.checkState() == QtCore.Qt.Checked)
        qlayer = item.data() # index.data(QtCore.Qt-UserRole+1)
        qlayer.setVisible(checked)

    @QtCore.pyqtSlot()
    def onItemActivated(self):
        selectionmodel = self.treeview.selectionModel()
        for index in selectionmodel.selectedRows():
            item = self.model.itemFromIndex(index)

            if item.checkState() == QtCore.Qt.Checked:
                item.setCheckState(QtCore.Qt.Unchecked)
            elif item.checkState() == QtCore.Qt.Unchecked:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                continue

            self.onItemClicked(index)

    @QtCore.pyqtSlot()
    def checkSelectedItems(self, check=True):
        selectionmodel = self.treeview.selectionModel()

        if check:
            state = QtCore.Qt.Checked
        else:
            state = QtCore.Qt.Unchecked

        update = False
        for index in selectionmodel.selectedRows():
            item = self.model.itemFromIndex(index)

            if item.checkState() != state:
                item.setCheckState(state)
                self.onItemClicked(index)
                update = True
        if update:
            self._updateLayerActions()

    @QtCore.pyqtSlot()
    def uncheckSelectedItems(self):
        self.checkSelectedItems(False)

    # @TODO: beginMoveRows, endMoveRows
    def _takeSelectedRows(self, selectedrows=None):
        if selectedrows is None:
            selectedrows = self.treeview.selectionModel().selectedRows()

        rows = []
        for index in reversed(selectedrows):
            row = index.row()
            items = self.model.takeRow(row)
            rows.insert(0, (row, items))

        return rows

    # @TODO: beginMoveRows, endMoveRows
    @QtCore.pyqtSlot()
    def onMoveToTop(self):
        selectionmodel = self.treeview.selectionModel()
        selectedrows = selectionmodel.selectedRows()

        if len(selectedrows) == self.model.rowCount():
            return

        rows = self._takeSelectedRows(selectedrows)
        rows.reverse()
        for row, items in rows:
            self.model.insertRow(0, items)
        selection = QtGui.QItemSelection(self.model.index(0, 0),
                                         self.model.index(len(rows) - 1, 0))
        selectionmodel.select(selection, QtGui.QItemSelectionModel.Select)

    # @TODO: beginMoveRows, endMoveRows
    @QtCore.pyqtSlot()
    def onMoveUp(self):
        selectionmodel = self.treeview.selectionModel()
        selectedrows = selectionmodel.selectedRows()

        firatitem = self.model.itemFromIndex(selectedrows[0])
        if firatitem and firatitem.row() == 0:
            return

        rows = self._takeSelectedRows(selectedrows)
        for row, items in rows:
            row = max(row-1, 0)
            self.model.insertRow(row, items)

            selection = QtGui.QItemSelection(self.model.index(row, 0),
                                             self.model.index(row, 0))
            selectionmodel.select(selection, QtGui.QItemSelectionModel.Select)

    # @TODO: beginMoveRows, endMoveRows
    @QtCore.pyqtSlot()
    def onMoveDown(self):
        selectionmodel = self.treeview.selectionModel()
        selectedrows = selectionmodel.selectedRows()

        lastitem = self.model.itemFromIndex(selectedrows[-1])
        if lastitem and lastitem.row() == self.model.rowCount() - 1:
            return

        rows = self._takeSelectedRows(selectedrows)
        for row, items in rows:
            row = min(row+1, self.model.rowCount())
            self.model.insertRow(row, items)
            selection = QtGui.QItemSelection(self.model.index(row, 0),
                                             self.model.index(row, 0))
            selectionmodel.select(selection, QtGui.QItemSelectionModel.Select)

    # @TODO: beginMoveRows, endMoveRows
    @QtCore.pyqtSlot()
    def onMoveToBottom(self):
        selectionmodel = self.treeview.selectionModel()
        selectedrows = selectionmodel.selectedRows()

        if len(selectedrows) == self.model.rowCount():
            return

        rows = self._takeSelectedRows(selectedrows)
        for row, items in rows:
            self.model.appendRow(items)

        start = self.model.rowCount() - len(rows)
        stop = self.model.rowCount() - 1
        selection = QtGui.QItemSelection(self.model.index(start, 0),
                                         self.model.index(stop, 0))
        selectionmodel.select(selection, QtGui.QItemSelectionModel.Select)

    @QtCore.pyqtSlot()
    def onRemoveLayer(self):
        selectionmodel = self.treeview.selectionModel()
        selection = selectionmodel.selection()
        while selection:
            selectionrange = selection[0]
            for row in range(selectionrange.top(), selectionrange.bottom()+1):
                item = self.model.item(row)
                self.scene.removeItem(item.data())
            self.model.removeRows(selectionrange.top(), selectionrange.height())
            selection = selectionmodel.selection()

    @QtCore.pyqtSlot()
    def _updateLayerActions(self):
        selectionmodel = self.treeview.selectionModel()
        enabled = selectionmodel.hasSelection()
        for action in self.layeractions.actions():
            if action.objectName() == 'selectAllAction':
                selectedrows = selectionmodel.selectedRows()
                nselected = len(selectedrows)
                nlayers = self.model.rowCount()
                allselected = bool(nselected == nlayers)
                action.setEnabled(nlayers and not allselected)

            elif action.objectName() in ('showLayerAction', 'hideLayerAction'):
                selectedrows = selectionmodel.selectedRows()
                nselected = len(selectedrows)
                if nselected == 0:
                    action.setEnabled(False)
                else:
                    items = [self.model.itemFromIndex(index)
                                                    for index in selectedrows]
                    activerows = [item.row() for item in items
                                    if item.checkState() == QtCore.Qt.Checked]

                    if action.objectName() in 'showLayerAction':
                        action.setEnabled(len(activerows) != nselected)

                    elif action.objectName() == 'hideLayerAction':
                        action.setEnabled(len(activerows) != 0)
            else:
                action.setEnabled(enabled)

    @QtCore.pyqtSlot()
    def onLayoutChanged(self, offset=0):
        nrows = self.model.rowCount()
        for row in range(nrows):
            qitem = self.model.item(row).data()
            if qitem:
                qitem.setZValue(nrows + offset - row - 1)
            else:
                logging.warning('no graphics item associated to layer n. %d: '
                                '%s' % (row, self.model.item(row, 1)))

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
    # @NOTE: basic config doesn't work since sip use it before this line
    #logging.basicConfig(level=logging.DEBUG, format='%(levelname): %(message)s')
    logging.getLogger().setLevel(logging.DEBUG)

    if not argv:
        argv = sys.argv
    else:
        argv = list(argv)

    app = QtGui.QApplication(argv)
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
