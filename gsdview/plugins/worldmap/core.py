# -*- coding: utf-8 -*-

### Copyright (C) 2008-2011 Antonio Valentino <a_valentino@users.sf.net>

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


'''World map component for GSDView.'''


import numpy as np

from qt import QtCore, QtGui

from gsdview import utils
from gsdview import qt4support


__author__ = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__ = '$Date$'
__revision__ = '$Revision$'


class WorldmapPanel(QtGui.QDockWidget):
    # @TODO: use zoom plugin

    bigBoxSize = 40

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0), **kwargs):
        #title = self.tr('Worldmap Panel')
        super(WorldmapPanel, self).__init__('World Map Panel', parent, flags,
                                            **kwargs)
        #self.setObjectName('worldmapPanel') # @TODO: check

        scene = QtGui.QGraphicsScene(self)
        scene.setSceneRect(-180, -90, 360, 180)
        self.graphicsview = QtGui.QGraphicsView(scene)
        self.graphicsview.scale(2., -2.)

        self.worldmapitem = None
        self.setWorldmapItem()

        self.actions = self._setupActions()
        self.actionZoomIn, self.actionZoomOut = self.actions.actions()

        toolbar = qt4support.actionGroupToToolbar(self.actions,
                                                  self.tr('Zoom toolbar'))
        toolbar.setOrientation(QtCore.Qt.Vertical)

        mainlayout = QtGui.QHBoxLayout()
        mainlayout.addWidget(self.graphicsview)
        mainlayout.addWidget(toolbar)

        mainwidget = QtGui.QWidget()
        mainwidget.setLayout(mainlayout)
        self.setWidget(mainwidget)

        self.bigbox = None
        self.box = None
        self.fitItem = self.worldmapitem

        self.graphicsview.installEventFilter(self)

    def _setupActions(self):
        actions = QtGui.QActionGroup(self)

        # Zoom in
        icon = qt4support.geticon('zoom-in.svg', 'gsdview')
        QtGui.QAction(icon, self.tr('Zoom In'), actions,
                      objectName='zoomOutAction',
                      statusTip=self.tr('Zoom In'),
                      shortcut=QtGui.QKeySequence(self.tr('Ctrl++')),
                      enabled=False,
                      triggered=lambda: self._zoom(+1))

        # Zoom out
        icon = qt4support.geticon('zoom-out.svg', 'gsdview')
        QtGui.QAction(icon, self.tr('Zoom Out'), actions,
                      objectName='zoomOutAction',
                      statusTip=self.tr('Zoom Out'),
                      shortcut=QtGui.QKeySequence(self.tr('Ctrl+-')),
                      enabled=False,
                      triggered=lambda: self._zoom(-1))

        return actions

    def eventFilter(self, obj, event):
        if event.type() in (QtCore.QEvent.Resize, QtCore.QEvent.Show):
            self._fitInView()
        return obj.eventFilter(obj, event)

    def setWorldmapItem(self, resolution='low'):
        scene = self.graphicsview.scene()
        if self.worldmapitem is not None:
            scene.removeItem(self.worldmapitem)

        #~ imgfile = qt4support.geticonfile('world_2160x1080.jpg', __name__)
        imgfile = qt4support.geticonfile('world_4320x2160.jpg', __name__)
        #~ imgfile = qt4support.geticonfile('world_5400x2700.jpg', __name__)
        worldmap = QtGui.QPixmap(imgfile)

        worldmapitem = scene.addPixmap(worldmap)
        worldmapitem.setTransformationMode(QtCore.Qt.SmoothTransformation)
        # @NOTE: reverse the y axis
        worldmapitem.scale(360. / worldmap.width(), -180. / worldmap.height())
        worldmapitem.setOffset(-worldmap.width() / 2. + 0.5,
                               -worldmap.height() / 2. + 0.5)
        #~ transform = QtGui.QTransform(360./worldmap.width(),
                                     #~ 0,
                                     #~ 0,
                                     #~ 180./worldmap.height(),
                                     #~ -worldmap.width()/2.+0.5,
                                     #~ -worldmap.height()/2.+0.5)
        #~ worldmapitem.setTransform(transform)
        #~ worldmapitem.update()
        self.worldmapitem = worldmapitem
        #~ return worldmapitem

    def _zoom(self, increment):
        items = (self.worldmapitem, self.bigbox, self.box)
        items = [item for item in items if item is not None]
        index = items.index(self.fitItem)
        newindex = index + increment
        if 0 <= newindex < len(items):
            self.fitItem = items[newindex]
            self.graphicsview.fitInView(self.fitItem,
                                        QtCore.Qt.KeepAspectRatio)
            if increment > 0:
                self.actionZoomOut.setEnabled(True)
            else:
                self.actionZoomIn.setEnabled(True)
        if (increment > 0) and (self.fitItem == items[-1]):
            self.actionZoomIn.setEnabled(False)
        elif (increment < 0) and (self.fitItem == items[0]):
            self.actionZoomOut.setEnabled(False)

    def _fitInView(self):
        self.graphicsview.fitInView(self.fitItem,
                                    QtCore.Qt.KeepAspectRatio)

    def plot(self, polygon):
        #~ if points[0] != points[-1]:
            #~ poly.append(poly[0])

        # View box on the overview
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setColor(QtGui.QColor(QtCore.Qt.red))

        item = self.graphicsview.scene().addPolygon(polygon, pen)
        item.setZValue(1)

        return item

    def setFootprint(self, polygon):
        self.clear()
        if not polygon:
            return

        lon = np.asarray([p.x() for p in polygon])
        lat = np.asarray([p.y() for p in polygon])

        mlon = lon.mean()
        mlat = lat.mean()

        delta = mlon - utils.geonormalize(mlon)
        if delta:
            lon -= delta
            mlon -= delta
            polygon.translate(-delta, 0)

        self.box = self.plot(polygon)

        points = QtGui.QPolygonF([
            QtCore.QPointF(mlon - self.bigBoxSize / 2,
                           mlat - self.bigBoxSize / 2),
            QtCore.QPointF(mlon + self.bigBoxSize / 2,
                           mlat - self.bigBoxSize / 2),
            QtCore.QPointF(mlon + self.bigBoxSize / 2,
                           mlat + self.bigBoxSize / 2),
            QtCore.QPointF(mlon - self.bigBoxSize / 2,
                           mlat + self.bigBoxSize / 2),
        ])
        self.bigbox = self.plot(points)

        self.actionZoomIn.setEnabled(True)

    def clear(self):
        scene = self.graphicsview.scene()
        for item in scene.items():
            if item is not self.worldmapitem:
                scene.removeItem(item)
        self.actionZoomIn.setEnabled(False)
        self.actionZoomOut.setEnabled(False)
        self.fitItem = self.worldmapitem
        self._fitInView()


class WorldmapController(QtCore.QObject):
    def __init__(self, app, **kwargs):
        super(WorldmapController, self).__init__(app, **kwargs)
        self.app = app

        self.panel = WorldmapPanel(app)
        self.panel.setObjectName('worldmapPanel')   # @TODO: check

        app.mdiarea.subWindowActivated.connect(self.onSubWindowChanged)
        app.treeview.clicked.connect(self.onItemClicked)
        app.subWindowClosed.connect(self.onModelChanged)

        # @WARNING: rowsInserted/rowsRemoved don't work
        # @TODO: fix
        app.datamodel.rowsInserted.connect(self.onModelChanged)
        app.datamodel.rowsRemoved.connect(self.onModelChanged)

    def setItemFootprint(self, item):
        try:
            footprint = item.footprint()
        except AttributeError:
            footprint = None

        self.panel.setFootprint(footprint)

    @QtCore.Slot()
    @QtCore.Slot(QtGui.QMdiSubWindow)
    def onSubWindowChanged(self, subwin=None):
        if subwin is None:
            subwin = self.app.mdiarea.activeSubWindow()

        if subwin is None:
            return

        try:
            item = subwin.item
        except AttributeError:
            # the window has not an associated item in the datamodel
            pass
        else:
            self.setItemFootprint(item)

    @QtCore.Slot(QtCore.QModelIndex)
    def onItemClicked(self, index):
        if not self.app.mdiarea.activeSubWindow():
            item = self.app.datamodel.itemFromIndex(index)
            self.setItemFootprint(item)

    @QtCore.Slot()
    @QtCore.Slot(QtCore.QModelIndex, int, int)
    def onModelChanged(self, index=None, start=None, stop=None):
        subwin = self.app.mdiarea.activeSubWindow()
        if subwin:
            self.onSubWindowChanged(subwin)
        else:
            item = self.app.currentItem()
            self.setItemFootprint(item)


if __name__ == '__main__':
    import os
    import sys

    from osgeo import gdal

    app = QtGui.QApplication(sys.argv)
    mainwin = QtGui.QMainWindow()
    mainwin.setCentralWidget(QtGui.QTextEdit())

    dataset = gdal.Open(os.path.expanduser('~/projects/gsdview/data/ENVISAT/'
        'ASA_APM_1PNIPA20031105_172352_000000182021_00227_08798_0001.N1'))
    panel = WorldmapPanel()
    panel.setDataset(dataset)

    mainwin.addDockWidget(QtCore.Qt.LeftDockWidgetArea, panel)
    #~ mainWin.showMaximized()
    mainwin.show()
    sys.exit(app.exec_())
