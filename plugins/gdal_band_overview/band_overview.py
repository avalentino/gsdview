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

'''Overview pannel for GDAL raster bands.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date: 2007-12-02 20:30:11 +0100 (dom, 02 dic 2007) $'
__revision__ = '$Revision: 47 $'

#~ import os
#~ import gdal

#~ import os, sys
#~ path = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir
#~ sys.path.append(os.path.normpath(path))

import logging
import numpy

from PyQt4 import QtCore, QtGui
from PyQt4 import Qwt5 as Qwt

import gsdtools
from graphicsview import GraphicsView
from qt4support import overrideCursor

#import resources

class GdalBandOverview(QtGui.QDockWidget):
    def __init__(self, parent=None): #, flags=0):
        #title = self.tr('Dataset Browser')
        QtGui.QDockWidget.__init__(self, 'GDAL Raster Band Overview', parent) #, flags)
        #self.setObjectName('datasetBroeserPanel') # @TODO: check

        self.band = None
        self.ovrlevel = None
        self.pixmapItem = None
        self.boxItem = None
        self.graphicsview = GraphicsView(QtGui.QGraphicsScene(self))
        # @TODO: check
        #graphicsview.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.setWidget(self.graphicsview)

    @overrideCursor
    def setBand(self, band):
        self.graphicsview.setUpdatesEnabled(False)
        try:
            self.reset()

            if band.lut is None:
                band.lut = gsdtools.compute_band_lut(band)

            ovrindex = band.best_ovr_index()
            ovrBand = band.GetOverview(ovrindex)
            data = ovrBand.ReadAsArray()

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
            self.updateBox()
        finally:
            self.graphicsview.setUpdatesEnabled(True)

    def centerOn(self, pos):
        if self.band:
            #qlfactor = float(self.band.XSize) / self.quicklook.width()
            pos = self.graphicsview.mapToScene(pos.x(), pos.y())
            x = pos.x() * self.ovrlevel
            y = pos.y() * self.ovrlevel

            # @TODO: check API
            view = self.parent().graphicsView
            view.centerOn(x, y)

    def updateBox(self):
        if self.band:
            # @TODO: check API
            view = self.parent().graphicsView
            hbar = view.horizontalScrollBar()
            vbar = view.verticalScrollBar()
            x = hbar.value()
            y = vbar.value()
            w = hbar.pageStep()
            h = vbar.pageStep()

            # @TODO: bug report: mapping to scene seems to introduce a
            #        spurious offset "x1 = 2*x0"; this doesn't happen for "w"
            #~ polygon = self.graphicsView.mapToScene(x, y, w, h)
            #~ rect = polygon.boundingRect()

            #qlfactor = float(self.band.XSize) / self.quicklook.width()
            #~ x = rect.x() / qlfactor
            #~ y = rect.y() / qlfactor
            #~ w = rect.width() / qlfactor
            #~ h = rect.height() / qlfactor

            # @NOTE: this is a workaround; mapToScene should be used instead
            factor = self.ovrlevel * self.graphicsView.matrix().m11()
            x /= factor
            y /= factor
            w /= factor
            h /= factor

            self.boxItem.setRect(x, y, w, h)

    def reset(self):
        scene = self.graphicsview.scene()

        if self.boxItem:
            scene.remove(self.boxItem)
            self.boxItem = None

        if self.pixmapItem:
            scene.remove(self.pixmapItem)
            self.pixmapItem = None

        self.ovrlevel = None
        self.band = None
