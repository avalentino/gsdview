### Copyright (C) 2008-2009 Antonio Valentino <a_valentino@users.sf.net>

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

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import logging
import numpy

from PyQt4 import QtCore, QtGui

import gsdtools
from qt4support import overrideCursor, numpy2qimage

class NavigationGraphicsView(QtGui.QGraphicsView):
    BOXCOLOR = QtGui.QColor(QtCore.Qt.red)

    def __init__(self, parent=None):    #, flags):
        super(NavigationGraphicsView, self).__init__(parent) #, flags)
        self._viewbox = None
        self._autoscale = True

    def getbox(self):
        return self._viewbox

    def setbox(self, box):
        assert isinstance(box, (QtCore.QRect, QtCore.QRectF))
        self._viewbox = box
        #self.update()
        self.scene().update()

    viewbox = property(getbox, setbox, doc='viewport box in scene coordinates')

    def drawForeground(self, painter, rect):
        if not self.viewbox:
            return

        pen = painter.pen()
        try:
            box = self.viewbox.intersected(self.sceneRect())
            painter.setPen(self.BOXCOLOR)
            painter.drawRect(box)
            #painter.drawConvexPolygon(self.viewbox) #@TODO: check
        finally:
            painter.setPen(pen)

    def fitInView(self, rect=None, aspectRatioMode=QtCore.Qt.KeepAspectRatio):
        if not rect:
            scene = self.scene()
            if scene:
                rect = scene.sceneRect()
            else:
                return
        QtGui.QGraphicsView.fitInView(self, rect, aspectRatioMode)

    def _getAutoscale(self):
        return self._autoscale

    def _setAutoscale(self, flag):
        self._autoscale = bool(flag)
        if self._autoscale:
            self.fitInView()
        else:
            self.setMatrix(QtGui.QMatrix())
            self.update()

    autoscale = property(_getAutoscale, _setAutoscale)

    def resizeEvent(self, event):
        if self.autoscale:
            self.fitInView()
        return QtGui.QGraphicsView.resizeEvent(self, event)

    # @TODO: use event filters
    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.emit(QtCore.SIGNAL('mousePressed(QPointF, Qt::MouseButtons, '
                                'QGraphicsView::DragMode)'),
                  pos, event.buttons(), self.dragMode())
        return QtGui.QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.emit(QtCore.SIGNAL('mouseMoved(QPointF, Qt::MouseButtons, '
                                'QGraphicsView::DragMode)'),
                  pos, event.buttons(), self.dragMode())
        return QtGui.QGraphicsView.mouseMoveEvent(self, event)


class BandOverviewDock(QtGui.QDockWidget):
    OVRMAXSIZE = 10 * 1024**2 # 10MB

    def __init__(self, mainwin): #, flags=0):
        #title = self.tr('Dataset Browser')
        QtGui.QDockWidget.__init__(self, 'Band Overview', mainwin) #, flags)
        #self.setObjectName('datasetBroeserPanel') # @TODO: check

        self.mainwin = mainwin  # @TODO: check
        self.graphicsview = NavigationGraphicsView(self)
        self.setWidget(self.graphicsview)

    # @TODO: understand why this doewn't work
    #
    #    self.graphicsview.installEventFilter(self)
    #
    #def eventFilter(self, obj, event):
    #    if obj.scene():
    #        if event.type() in (QtCore.QEvent.MouseButtonPress,
    #                            QtCore.QEvent.MouseMove):
    #            if event.buttons() & QtCore.Qt.LeftButton:
    #                pos = obj.mapToScene(event.pos())
    #                self.centerMainViewOn(pos)
    #    return obj.eventFilter(obj, event)

    @overrideCursor
    def setItem(self, banditem):
        # @TODO: fix
        # @WARNING: this method contains backend specific code
        if banditem.backend != 'gdalbackend':
            logging.warning('only "gdalbackend" is supported by "overview" '
                            'plugin')
            return

        self.graphicsview.setUpdatesEnabled(False)
        try:
            self.reset()

            # @TODO: fix
            from osgeo import gdal
            from gdalbackend import gdalsupport

            try:
                ovrindex = gdalsupport.best_ovr_index(banditem)
            except gdalsupport.MissingOvrError:
                logging.debug('no overview available')
                return

            ovrBand = banditem.GetOverview(ovrindex)
            datatypesize = gdal.GetDataTypeSize(ovrBand.DataType) / 8 # byte
            ovrsize = ovrBand.XSize * ovrBand.YSize * datatypesize
            if ovrsize > self.OVRMAXSIZE:
                return

            # @TODO: check
            scene = banditem.scene
            self.graphicsview.setScene(scene)
            self.graphicsview.setSceneRect(scene.sceneRect())

            if not self.graphicsview.autoscale:
                ovrlevel = gdalsupport.available_ovr_levels(banditem)[ovrindex]
                matrix = QtCore.QMatirx(ovrlevel, 0, 0, ovrlevel, 0, 0)
                self.graphicsview.setMatrix(matrix)

            self.updateMainViewBox()
        finally:
            self.graphicsview.setUpdatesEnabled(True)

    def centerMainViewOn(self, scenepos):
        view = self.mainwin.currentGraphicsView()
        if view:
            if self.graphicsview.scene():
                assert view.scene() == self.graphicsview.scene() # @TODO: check
            view.centerOn(scenepos)

    def updateMainViewBox(self, srcview=None):
        if not self.graphicsview.scene():
            return

        if not srcview:
            # @TODO: check API
            srcview = self.mainwin.currentGraphicsView()
        elif srcview is not self.mainwin.currentGraphicsView():
            # current view not yet updated: do nothing
            return

        if srcview:
            assert srcview.scene() == self.graphicsview.scene() # @TODO: check
            hbar = srcview.horizontalScrollBar()
            vbar = srcview.verticalScrollBar()

            # @TODO: bug report: mapping to scene seems to introduce a
            #        spurious offset "x1 = 2*x0" and y1 = 2*y0;
            #        this doesn't happen for "w" and "h"
            #polygon = srcview.mapToScene(hbar.value(), vbar.value(),
            #                             hbar.pageStep(), vbar.pageStep())
            #@TODO: in case of rotations it should be better keep using
            #       a polygon
            #self.graphicsview.viewbox = polygon.boundingRect()

            # @NOTE: this is a workaround; mapToScene should be used instead
            rect = QtCore.QRectF(hbar.value(), vbar.value(),
                                 hbar.pageStep(), vbar.pageStep())
            transform = srcview.transform().inverted()[0]
            self.graphicsview.viewbox = transform.mapRect(rect)

    def reset(self):
        self.graphicsview.setScene(None)
