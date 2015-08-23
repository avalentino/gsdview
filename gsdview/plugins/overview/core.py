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


'''Overview pannel for GDAL raster bands.'''


from qtsix import QtCore, QtWidgets, QtGui

from gsdview.qtsupport import overrideCursor
from gsdview.gdalbackend import gdalsupport


class NavigationGraphicsView(QtWidgets.QGraphicsView):
    '''Graphics view for dataset navigation.

    The view usually displays an auto-scalled low resolution overview
    of the scene with a red box indicating the area currently displayed
    in the high resolution view.

    :SIGNALS:

        * :attr:`mousePressed`
        * :attr:`mouseMoved`

    '''

    BOXCOLOR = QtGui.QColor(QtCore.Qt.red)
    BOXWIDTH = 50

    #: SIGNAL: it is emitted when a mouse button is presses on the view
    #:
    #: :param point:
    #:     the scene position
    #: :param mousebutton:
    #:     the ID of the pressed button
    #: :param dragmode:
    #:     current darg mode
    #:
    #: :C++ signature: `void mousePressed(QPointF, Qt::MouseButtons,
    #:                                    QGraphicsView::DragMode)`
    mousePressed = QtCore.Signal(QtCore.QPointF, QtCore.Qt.MouseButtons,
                                 QtWidgets.QGraphicsView.DragMode)

    #: SIGNAL: it is emitted when the mouse is moved on the view
    #:
    #: :param point:
    #:     the scene position
    #: :param mousebutton:
    #:     the ID of the pressed button
    #: :param dragmode:
    #:     current darg mode
    #:
    #: :C++ signature: `void mouseMoved(QPointF, Qt::MouseButtons,
    #:                                    QGraphicsView::DragMode)`
    mouseMoved = QtCore.Signal(QtCore.QPointF, QtCore.Qt.MouseButtons,
                               QtWidgets.QGraphicsView.DragMode)

    def __init__(self, parent=None, **kwargs):
        super(NavigationGraphicsView, self).__init__(parent, **kwargs)
        self._viewbox = None
        self._autoscale = True
        self.setMouseTracking(True)

        # default pen
        self._pen = QtGui.QPen()
        self._pen.setColor(self.BOXCOLOR)
        self._pen.setWidth(self.BOXWIDTH)

    @property
    def viewbox(self):
        '''Viewport box in scene coordinates'''
        return self._viewbox

    @viewbox.setter
    def viewbox(self, box):
        '''Set the viewport box in scene coordinates'''
        assert isinstance(box, (QtCore.QRect, QtCore.QRectF))
        self._viewbox = box
        if self.isVisible():
            # @WARNING: calling "update" on the scene causes a repaint of
            #           *all* attached views and for each view the entire
            #           exposedRect is updated.
            #           Using QGraphicsView.invalidateScene with the
            #           QtWidgets.QGraphicsScene.ForegroundLayer parameter
            #           should be faster and repaint only one layer of the
            #           current view.

            # @TODO: check
            #self.invalidateScene(self.sceneRect(),
            #                     QtWidgets.QGraphicsScene.ForegroundLayer)
            self.scene().update()

    def drawForeground(self, painter, rect):
        if not self.viewbox:
            return

        pen = painter.pen()
        try:
            box = self.viewbox.intersected(self.sceneRect())
            painter.setPen(self._pen)
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
        QtWidgets.QGraphicsView.fitInView(self, rect, aspectRatioMode)

    @property
    def autoscale(self):
        return self._autoscale

    @autoscale.setter
    def autoscale(self, flag):
        self._autoscale = bool(flag)
        if self._autoscale:
            self.fitInView()
        else:
            self.setTransform(QtGui.QTransform())
            self.update()

    def resizeEvent(self, event):
        if self.autoscale:
            self.fitInView()
        return QtWidgets.QGraphicsView.resizeEvent(self, event)

    # @TODO: use event filters
    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.mousePressed.emit(pos, event.buttons(), self.dragMode())
        return QtWidgets.QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.mouseMoved.emit(pos, event.buttons(), self.dragMode())
        return QtWidgets.QGraphicsView.mouseMoveEvent(self, event)


class BandOverviewDock(QtWidgets.QDockWidget):
    OVRMAXSIZE = 10 * 1024 ** 2  # 10MB

    def __init__(self, app, flags=QtCore.Qt.WindowFlags(0), **kwargs):
        #title = self.tr('Dataset Browser')
        super(BandOverviewDock, self).__init__('Band Overview', app, flags,
                                               **kwargs)
        #self.setObjectName('datasetBroeserPanel') # @TODO: check

        self.app = app  # @TODO: check
        self.graphicsview = NavigationGraphicsView(self)
        self.setWidget(self.graphicsview)

    @property
    def _logger(self):
        return self.app.logger

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
    def setItem(self, item):
        assert item.backend == 'gdalbackend'

        self.graphicsview.setUpdatesEnabled(False)
        try:
            self.reset()

            try:
                level = gdalsupport.ovrLevelForSize(item, self.OVRMAXSIZE)
                # @NOTE: use GREATER for overview level to ensure an overview
                #        size smaller than OVRMAXSIZE
                ovrindex = gdalsupport.ovrBestIndex(item, level, 'GREATER')
            except gdalsupport.MissingOvrError:
                self._logger.info(
                    'no overview available or available overviews are too '
                    'large')
                return

            scene = item.scene
            self.graphicsview.setScene(scene)
            self.graphicsview.setSceneRect(scene.sceneRect())

            if not self.graphicsview.autoscale:
                ovrlevel = gdalsupport.ovrLevels(item)[ovrindex]
                matrix = QtCore.QMatirx(ovrlevel, 0, 0, ovrlevel, 0, 0)
                self.graphicsview.setMatrix(matrix)
            else:
                self.graphicsview.fitInView()

            self.updateMainViewBox()
        finally:
            self.graphicsview.setUpdatesEnabled(True)
            self.graphicsview.update()

    def centerMainViewOn(self, scenepos):
        view = self.app.currentGraphicsView()
        if view:
            if self.graphicsview.scene():
                # @TODO: check
                assert view.scene() == self.graphicsview.scene()
            view.centerOn(scenepos)

    @QtCore.Slot()
    @QtCore.Slot(QtWidgets.QGraphicsView)
    def updateMainViewBox(self, srcview=None):
        if not self.graphicsview.scene():
            return

        if not srcview:
            # @TODO: check API
            srcview = self.app.currentGraphicsView()
        elif srcview is not self.app.currentGraphicsView():
            # current view not yet updated: do nothing
            return

        if srcview:
            assert srcview.scene() == self.graphicsview.scene()  # @TODO: check
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


class OverviewController(QtCore.QObject):
    def __init__(self, app, **kwargs):
        super(OverviewController, self).__init__(app, **kwargs)
        self.app = app

        self.panel = BandOverviewDock(app)
        self.panel.setObjectName('bandOverviewPanel')   # @TODO: check
        app.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.panel)

        # Connect signals
        app.mdiarea.subWindowActivated.connect(self.onSubWindowChanged)
        app.subWindowClosed.connect(self.onWindowClosed)
        app.datamodel.itemChanged.connect(self.onItemChanged)

        app.monitor.scrolled.connect(self.panel.updateMainViewBox)
        app.monitor.viewportResized.connect(self.panel.updateMainViewBox)
        app.monitor.resized.connect(self.panel.updateMainViewBox)

        self.panel.graphicsview.mousePressed.connect(self.onNewPos)
        self.panel.graphicsview.mouseMoved.connect(self.onNewPos)

    @QtCore.Slot()
    @QtCore.Slot(QtWidgets.QMdiSubWindow)
    def onSubWindowChanged(self, subwin=None):
        if subwin is None:
            subwin = self.app.mdiarea.activeSubWindow()

        try:
            item = subwin.item
        except AttributeError:
            self.panel.reset()
        else:
            self.panel.setItem(item)

    @QtCore.Slot()
    def onWindowClosed(self):
        if len(self.app.mdiarea.subWindowList()) == 0:
            self.panel.reset()

    #@QtCore.Slot(QtGui.QStandardItem)
    @QtCore.Slot('QStandardItem*')  # @TODO:check
    def onItemChanged(self, item):
        if hasattr(item, 'scene'):
            srcview = self.app.currentGraphicsView()
            if (srcview and srcview.scene() is item.scene and
                    not self.panel.graphicsview.scene()):
                self.panel.setItem(item)

    # @TODO: translate into an event handler
    @QtCore.Slot(QtCore.QPointF, QtCore.Qt.MouseButtons,
                 QtWidgets.QGraphicsView.DragMode)
    def onNewPos(self, pos, buttons, dragmode):
        if buttons & QtCore.Qt.LeftButton:
            self.panel.centerMainViewOn(pos)
