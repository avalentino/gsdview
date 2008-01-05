### Copyright (C) 2007 Antonio Valentino <a_valentino@users.sf.net>

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

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date: 2007-12-02 20:30:11 +0100 (dom, 02 dic 2007) $'
__revision__ = '$Revision: 47 $'

import os

# @TODO: remove
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

from PyQt4 import QtCore, QtGui

from graphicsview import GraphicsView

import resources


class WorldmapPanel(QtGui.QDockWidget):
    # @TODO: use zoom plugin

    bigBoxSize = 40

    def __init__(self, parent=None): #, flags=0):
        #title = self.tr('Worldmap Panel')
        QtGui.QDockWidget.__init__(self, 'World Map Panel', parent) #, flags)
        #self.setObjectName('worldmapPanel') # @TODO: check

        scene = QtGui.QGraphicsScene(self)
        scene.setSceneRect(-180, -90, 360, 180)
        self.graphicsview = GraphicsView(scene)
        self.graphicsview.scale(2., -2.)

        self.worldmapitem = None
        self.setWorldmapItem('high')

        # Zoom in
        self.actionZoomIn = QtGui.QAction(QtGui.QIcon(':/images/zoom-in.svg'),
                                          self.tr('Zoom In'), self)
        self.actionZoomIn.setStatusTip(self.tr('Zoom In'))
        self.actionZoomIn.setShortcut(QtGui.QKeySequence(self.tr('Ctrl++')))
        self.actionZoomIn.setEnabled(False)
        self.connect(self.actionZoomIn, QtCore.SIGNAL('triggered()'),
                     lambda: self._zoom(+1))

        # Zoom out
        self.actionZoomOut = QtGui.QAction(QtGui.QIcon(':/images/zoom-out.svg'),
                                           self.tr('Zoom Out'), self)
        self.actionZoomOut.setStatusTip(self.tr('Zoom Out'))
        self.actionZoomOut.setShortcut(QtGui.QKeySequence(self.tr('Ctrl+-')))
        self.actionZoomOut.setEnabled(False)
        self.connect(self.actionZoomOut, QtCore.SIGNAL('triggered()'),
                     lambda: self._zoom(-1))

        toolbar = QtGui.QToolBar(self.tr('Zoom'))
        toolbar.setOrientation(QtCore.Qt.Vertical)
        toolbar.addAction(self.actionZoomIn)
        toolbar.addAction(self.actionZoomOut)

        mainlayout = QtGui.QHBoxLayout()
        mainlayout.addWidget(self.graphicsview)
        mainlayout.addWidget(toolbar)

        mainwidget = QtGui.QWidget()
        mainwidget.setLayout(mainlayout)
        self.setWidget(mainwidget)

        self.bigbox = None
        self.box = None
        self.fitItem = self.worldmapitem
        self._fitInView()
        self.connect(self.graphicsview, QtCore.SIGNAL('newSize(const QSize&)'),
                     self._fitInView)

    def setWorldmapItem(self, resolution='low'):
        scene = self.graphicsview.scene()
        if self.worldmapitem is not None:
            scene.removeItem(self.worldmapitem)

        resMap = {
            'low':  'WorldmapLowRes.jpg',
            'high': 'WorldmapHighRes.jpg',
        }

        filename = resMap.get(resolution, 'WorldmapLowRes.jpg')

        # @TODO: improve resources handling
        basedir = os.path.dirname(__file__)

        worldmap = QtGui.QPixmap(os.path.join(basedir, 'images', filename))
        worldmapitem = scene.addPixmap(worldmap)
        worldmapitem.setTransformationMode(QtCore.Qt.SmoothTransformation)
        # @NOTE: reverse the y axis
        worldmapitem.scale(360./worldmap.width(), -180./worldmap.height())
        worldmapitem.setOffset(-worldmap.width()/2.+0.5,
                               -worldmap.height()/2.+0.5)
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

    def plot(self, points):
        poly = QtGui.QPolygonF()
        for p in points:
            poly.append(QtCore.QPointF(p[0], p[1]))
        if points[0] != points[-1]:
            poly.append(poly[0])

        # View box on the overview
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setColor(QtGui.QColor(QtCore.Qt.red))

        item = self.graphicsview.scene().addPolygon(poly, pen)
        item.setZValue(1)

        return item

    def setDataset(self, dataset):
        # @TODO: move
        import osr
        import numpy
        from scipy import interpolate

        ngcp = dataset.GetGCPCount()
        if ngcp > 0:
            rcMatrix = numpy.zeros((ngcp, 2), dtype=numpy.float64)
            llMatrix = numpy.zeros((ngcp, 2), dtype=numpy.float64)

            sref_wgs84 = osr.SpatialReference()
            sref_wgs84.SetWellKnownGeogCS('WGS84')
            sref = osr.SpatialReference(dataset.GetGCPProjection())
            if sref.IsSame(sref_wgs84):
                ct = osr.CoordinateTransformation(sref, sref_wgs84)
                for row, gcp in enumerate(dataset.GetGCPs()):
                    rcMatrix[row] = gcp.GCPLine, gcp.GCPPixel
                    point = ct.TransformPoint(gcp.GCPX, gcp.GCPY, gcp.GCPZ)
                    llMatrix[row] = point[0:2]
                    # discard gcp.GCPZ
            else:
                for row, gcp in enumerate(dataset.GetGCPs()):
                    rcMatrix[row] = gcp.GCPLine, gcp.GCPPixel
                    llMatrix[row] = gcp.GCPX, gcp.GCPY
                    # discard gcp.GCPZ
            intLat = interpolate.interp2d(rcMatrix[:,0], rcMatrix[:,1], llMatrix[:,1])
            intLon = interpolate.interp2d(rcMatrix[:,0], rcMatrix[:,1], llMatrix[:,0])

            px = [0, dataset.RasterXSize-1]
            py = [0, dataset.RasterYSize-1]
            lat = intLat(px, py)
            lon = intLon(px, py)
            points = [
                (lon[0][0], lat[0][0]),
                (lon[0][1], lat[0][1]),
                (lon[1][1], lat[1][1]),
                (lon[1][0], lat[1][0]),
            ]
        else:
            pass

        self.box = self.plot(points)

        centLon = lon.mean()
        centLat = lat.mean()
        points = [
            (centLon - self.bigBoxSize/2, centLat - self.bigBoxSize/2),
            (centLon + self.bigBoxSize/2, centLat - self.bigBoxSize/2),
            (centLon + self.bigBoxSize/2, centLat + self.bigBoxSize/2),
            (centLon - self.bigBoxSize/2, centLat + self.bigBoxSize/2),
        ]
        self.bigbox = self.plot(points)

        self.actionZoomIn.setEnabled(True)

    def clear(self):
        scene = self.graphicsview.scene()
        for item in scene.items():
            if item is not self.worldmapitem:
                scene.removeItem(item)
        self.actionZoomIn.setEnabled(False)
        self.actionZoomOut.setEnabled(False)

if __name__ == '__main__':
    import sys
    import gdal

    app = QtGui.QApplication(sys.argv)
    mainWin = QtGui.QMainWindow()
    mainWin.setCentralWidget(QtGui.QTextEdit())

    dataset = gdal.Open('/home/antonio/projects/gsdview/data/ENVISAT/ASA_APM_1PNIPA20031105_172352_000000182021_00227_08798_0001.N1')
    panel = WorldmapPanel()
    panel.setDataset(dataset)

    mainWin.addDockWidget(QtCore.Qt.LeftDockWidgetArea, panel)
    #~ mainWin.showMaximized()
    mainWin.show()
    sys.exit(app.exec_())
