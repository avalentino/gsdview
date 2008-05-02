### Copyright (C) 2008 Antonio Valentino <a_valentino@users.sf.net>

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

'''Overview pannel for GDAL raster bands.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date$'
__revision__ = '$Revision$'


import logging
import numpy

from PyQt4 import QtCore, QtGui
from PyQt4 import Qwt5 as Qwt

import gsdtools
from graphicsview import GraphicsView
from qt4support import overrideCursor


class GdalBandOverview(QtGui.QDockWidget):
    def __init__(self, parent=None): #, flags=0):
        #title = self.tr('Dataset Browser')
        QtGui.QDockWidget.__init__(self, 'GDAL Raster Band Overview', parent) #, flags)
        #self.setObjectName('datasetBroeserPanel') # @TODO: check

        self.band = None
        self._transform = None
        self.pixmapItem = None
        self.boxItem = None
        self.graphicsview = GraphicsView(QtGui.QGraphicsScene(self))
        # @TODO: check
        #graphicsview.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.setWidget(self.graphicsview)

        self.autoscale = True

    def fitInView(self):
        if self.pixmapItem is not None:
            self.graphicsview.fitInView(self.pixmapItem,
                                        QtCore.Qt.KeepAspectRatio)

    def _getAutoscale(self):
        return self._autoscale

    def _setAutoscale(self, flag):
        if self.graphicsview:
            if flag:
                self.connect(self.graphicsview,
                             QtCore.SIGNAL('newSize(const QSize&)'),
                             self.fitInView)
                self.fitInView()
            else:
                self.disconnect(self.graphicsview,
                                QtCore.SIGNAL('newSize(const QSize&)'),
                                self.fitInView)
                self.graphicsview.setMatrix(QtGui.QMatrix())
        self._autoscale = bool(flag)

    autoscale = property(_getAutoscale, _setAutoscale)

    def _getOvrLevel(self):
        if self._transform is not None:
            return self._transform.m11()
        else:
            return None

    def _setOvrLevel(self, ovrlevel):
        if ovrlevel is None:
            self._transform = None
        else:
            self._transform = QtGui.QTransform(ovrlevel, 0, 0, ovrlevel,
                                               ovrlevel/2., ovrlevel/2.)

    ovrlevel = property(_getOvrLevel, _setOvrLevel)

    @overrideCursor
    def setBand(self, band):
        self.graphicsview.setUpdatesEnabled(False)
        try:
            self.reset()
            self.band = band

            ovrindex = band.best_ovr_index()
            ovrBand = band.GetOverview(ovrindex)
            data = ovrBand.ReadAsArray()

            if numpy.iscomplexobj(data):
                data = numpy.abs(data)

            if band.lut is None:
                band.lut = gsdtools.ovr_lut(data)

            data = gsdtools.apply_LUT(data, band.lut)
            image = Qwt.toQImage(data.transpose())
            pixmap = QtGui.QPixmap.fromImage(image)

            #~ nSrcXOff = (int)(0.5 + (iDstPixel/(double)nOXSize) * nSrcWidth);
            #~ nSrcXOff2 = (int)(0.5 + ((iDstPixel+1)/(double)nOXSize) * nSrcWidth);
            #~ nSrcYOff = (int)(0.5 + (iDstLine/(double)nOYSize) * nSrcHeight);
            #~ nSrcYOff2 = (int)(0.5 + ((iDstLine+1)/(double)nOYSize) * nSrcHeight);
            #~ xwinsize = nSrcXOff2 - nSrcXOff # -1 (??)
            #~ ywinsize = nSrcYOff2 - nSrcYOff # -1 (??)

            self.ovrlevel = band.available_ovr_levels()[ovrindex]

            scene = self.graphicsview.scene()
            self.pixmapItem = scene.addPixmap(pixmap)
            rect = self.pixmapItem.boundingRect()
            scene.setSceneRect(rect.x(), rect.y(), rect.width(), rect.height())
            self.graphicsview.setSceneRect(scene.sceneRect())
            self.graphicsview.ensureVisible(rect.x(), rect.y(), 1, 1, 0, 0)

            # View box on the overview
            pen = QtGui.QPen(QtCore.Qt.SolidLine)
            pen.setColor(QtGui.QColor(QtCore.Qt.red))
            scene = self.graphicsview.scene()
            self.boxItem = scene.addRect(QtCore.QRectF(), pen)
            self.boxItem.setZValue(1)

            if self.autoscale:
                self.fitInView()
                self.connect(self.graphicsview,
                             QtCore.SIGNAL('newSize(const QSize&)'),
                             self.fitInView)

            self.updateBox()
        finally:
            self.graphicsview.setUpdatesEnabled(True)

    def centerOn(self, pos):
        if self.band:
            # @TODO: check API
            view = self.parent().graphicsView

            pos = self.graphicsview.mapToScene(pos.x(), pos.y())
            pos = self._transform.map(pos)
            view.centerOn(pos)

    def updateBox(self):
        if self.band:
            # @TODO: check API
            view = self.parent().graphicsView
            hbar = view.horizontalScrollBar()
            vbar = view.verticalScrollBar()

            # @TODO: bug report: mapping to scene seems to introduce a
            #        spurious offset "x1 = 2*x0"; this doesn't happen for "w"
            #polygon = view.mapToScene(hbar.value(), vbar.value(),
            #                          hbar.pageStep(), vbar.pageStep())
            #rect = polygon.boundingRect()

            # @NOTE: this is a workaround; mapToScene should be used instead
            rect = QtCore.QRectF(hbar.value(), vbar.value(),
                                 hbar.pageStep(), vbar.pageStep())
            transform = view.transform().inverted()[0]
            rect = transform.mapRect(rect)

            transform = self._transform.inverted()[0]
            rect = transform.mapRect(rect)

            self.boxItem.setRect(rect)

    def reset(self):
        if self.autoscale and self.graphicsview:
            self.disconnect(self.graphicsview,
                            QtCore.SIGNAL('newSize(const QSize&)'),
                            self.fitInView)
        self.graphicsview.clearScene()
        self.boxItem = None
        self.pixmapItem = None
        self.ovrlevel = None
        self.band = None
