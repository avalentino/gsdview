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


"""Drawing components for Qt5."""


from qtpy import QtCore, QtWidgets, QtGui

from gsdview.mousemanager import MouseMode  # , RubberBandMode


# Graphics Items ############################################################
def _highlightSelectedGraphicsItem(item, painter, option, boundingrect=None):
    """Highlights item as selected.

    .. note:: This function is a duplicate of
              qt_graphicsItem_highlightSelected() in
              qgraphicssvgitem.cpp!

    """

    murect = painter.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
    if abs(max(murect.width(), murect.height())) <= 0.000000000001:
        return

    if boundingrect is None:
        boundingrect = item.boundingRect()

    mbrect = painter.transform().mapRect(boundingrect)
    if min(mbrect.width(), mbrect.height()) < 1.0:
        return

    try:
        # if item.type() in (QGraphicsEllipseItem.Type,
        #                    QGraphicsPathItem.Type,
        #                    QGraphicsPolygonItem.Type,
        #                    QGraphicsRectItem.Type,
        #                    QGraphicsSimpleTextItem.Type,
        #                    QGraphicsLineItem.Type):
        itemPenWidth = item.pen().widthF()
    except AttributeError:
        itemPenWidth = 1.0

    pad = itemPenWidth / 2
    penWidth = 0            # cosmetic pen

    fgcolor = option.palette.windowText().color()
    # ensure good contrast against fgcolor
    bgcolor = QtGui.QColor(
        0 if fgcolor.red() > 127 else 255,
        0 if fgcolor.green() > 127 else 255,
        0 if fgcolor.blue() > 127 else 255)

    painter.setPen(QtGui.QPen(bgcolor, penWidth, QtCore.Qt.SolidLine))
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.drawRect(boundingrect.adjusted(pad, pad, -pad, -pad))

    painter.setPen(
        QtGui.QPen(option.palette.windowText(), 0, QtCore.Qt.DashLine))
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.drawRect(boundingrect.adjusted(pad, pad, -pad, -pad))


class GraphicsPointItem(QtWidgets.QAbstractGraphicsShapeItem):
    """Qt graphics item for point merkers.

    Draw a symbol that scales its size according to the zoom level in
    order to keep approximatively constant size.
    Original size and maximum scaling factor are configurable.

    .. note:: currently the only symbol supported is a filled circle
              (pen and brush are configurable).

    .. note:: this class don't depends on OGR so it can be moved in a
              module out of the gdalbackend.

    """

    Type = QtWidgets.QGraphicsItem.UserType + 100

    def __init__(self, x=None, y=None, radius=None, parent=None, scene=None,
                 **kargs):
        super(GraphicsPointItem, self).__init__(parent, scene, **kargs)
        self.setFlag(QtWidgets.QGraphicsItem.ItemUsesExtendedStyleOption)

        if None not in (x, y):
            self.setPos(x, y)

        self._radius = 1
        if radius is not None:
            self._radius = radius

        self._maxfact = 10

        brush = self.brush()
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.setBrush(brush)

    def radius(self):
        return self._radius

    def setRadius(self, radius):
        if radius < 0:
            raise ValueError('invalid radius: "%s"' % radius)
        self._radius = float(radius)

    def maxFactor(self):
        return self._maxfact

    def setMaxFactor(self, maxfact):
        if maxfact < 0:
            raise ValueError('invalid scaling factor: "%s"' % maxfact)
        self._maxfact = float(maxfact)

    def type(self):
        return self.Type

    def boundingRect(self):
        penwidth = self.pen().widthF()
        radius = self._maxfact * self._radius
        diameter = 2. * radius
        return QtCore.QRectF(-radius - penwidth / 2, -radius - penwidth / 2,
                             diameter + penwidth, diameter + penwidth)

    def paint(self, painter, option, widget):
        levelOfDetail = option.levelOfDetailFromTransform(painter.transform())

        painter.setPen(self.pen())
        painter.setBrush(self.brush())

        radius = min(self._radius / levelOfDetail,
                     self._radius * self._maxfact)
        painter.drawEllipse(QtCore.QPointF(0, 0), radius, radius)

        if option.state & QtWidgets.QStyle.State_Selected:
            penwidth = self.pen().widthF()
            diameter = 2. * radius
            rect = QtCore.QRectF(-radius - penwidth / 2,
                                 -radius - penwidth / 2,
                                 diameter + penwidth, diameter + penwidth)

            _highlightSelectedGraphicsItem(self, painter, option, rect)


class GraphicsItemGroup(QtWidgets.QGraphicsItemGroup):
    """Qt graphics item group with common style."""

    Type = QtWidgets.QGraphicsItem.UserType + 101

    def __init__(self, parent=None, scene=None, **kargs):
        super(GraphicsItemGroup, self).__init__(parent, scene, **kargs)

        self._pen = QtGui.QPen()
        self._brush = QtGui.QBrush()

    def addToGroup(self, item):
        super(GraphicsItemGroup, self).addToGroup(item)
        try:
            item.setPen(self._pen)
            item.setBrusH(self._brush)
        except AttributeError:
            pass

    # @TODO: check pyqtProperty
    def pen(self):
        return self._pen

    def setPen(self, pen):
        if not isinstance(pen, QtGui.QPen):
            raise TypeError('invalid pen object: %s' % pen)
        self._pen = pen

        for item in self.childItems():
            try:
                item.setPen(pen)
            except AttributeError:
                pass

    def brush(self):
        return self._brush

    def setBrush(self, brush):
        if not isinstance(brush, QtWidgets.QBrush):
            raise TypeError('invalid brush object: %s' % brush)
        self._brush = brush

        for item in self.childItems():
            try:
                item.setBrush(brush)
            except AttributeError:
                pass


# Drawing tools #############################################################
class DrawPointMode(MouseMode):
    dragmode = QtWidgets.QGraphicsView.NoDrag
    cursor = QtCore.Qt.CrossCursor
    icon = ':/trolltech/styles/commonstyle/images/standardbutton-yes-128.png'
    label = 'Draw Point'
    name = 'drawPoint'

    def sceneEventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.GraphicsSceneMousePress and
                event.button() == QtCore.Qt.LeftButton):
            return True

        elif (event.type() == QtCore.QEvent.GraphicsSceneMouseRelease and
                event.button() == QtCore.Qt.LeftButton):
            pen = QtGui.QPen()
            pen.setColor(QtCore.Qt.red)

            brush = QtGui.QBrush()
            brush.setColor(QtCore.Qt.red)
            brush.setStyle(QtCore.Qt.SolidPattern)

            RADIUS = 3
            point = event.scenePos()
            item = GraphicsPointItem(point.x(), point.y(), RADIUS)
            item.setPen(pen)
            item.setBrush(brush)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
            obj.addItem(item)
            return True

        return False


class DrawLineMode(MouseMode):
    dragmode = QtWidgets.QGraphicsView.NoDrag
    cursor = QtCore.Qt.CrossCursor
    icon = ':/trolltech/dialogs/qprintpreviewdialog/images/fit-width-24.png'
    label = 'Draw Line'
    name = 'drawLine'

    def __init__(self, parent=None):
        super(DrawLineMode, self).__init__(parent)
        self.rubberband = None
        self.pen = QtGui.QPen()
        self.pen.setWidth(1)
        self.pen.setColor(QtCore.Qt.red)

    def sceneEventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.GraphicsSceneMousePress and
                event.button() == QtCore.Qt.LeftButton):
            assert(self.rubberband is None)
            self.rubberband = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Line)
            self.rubberband.setGeometry(
                QtCore.QRect(event.screenPos(), QtCore.QSize()))
            self.rubberband.show()
            return True

        if (event.type() == QtCore.QEvent.GraphicsSceneMouseRelease and
                event.button() == QtCore.Qt.LeftButton):
            assert(self.rubberband is not None)
            self.rubberband.hide()
            self.rubberband = None
            line = QtCore.QLineF(
                event.buttonDownScenePos(QtCore.Qt.LeftButton),
                event.scenePos())
            item = obj.addLine(line, self.pen)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
            return True

        elif (event.type() == QtCore.QEvent.GraphicsSceneMouseMove and
                bool(event.buttons() & QtCore.Qt.LeftButton)):
            assert(self.rubberband is not None)
            rect = QtCore.QRect(
                event.buttonDownScreenPos(QtCore.Qt.LeftButton),
                event.screenPos()).normalized()
            self.rubberband.setGeometry(rect)
            return True

        return False


# class DrawPolygonMode(MouseMode):
#     dragmode = QtWidgets.QGraphicsView.NoDrag
#     cursor = QtCore.Qt.CrossCursor
#     icon = ':/trolltech/dialogs/qprintpreviewdialog/images/fit-width-24.png'
#     label = 'Draw Line'
#     name = 'drawLine'
#
#     def __init__(self, parent=None):
#         super(DrawPolygonMode, self).__init__(parent)
#         self.rubberband = None
#         self.pen = QtGui.QPen()
#         self.pen.setWidth(1)
#         self.pen.setColor(QtCore.Qt.red)
#         self.brush = QtWidgets.QBrush()
#         #self.brush.setStyle(QtCore.Qt.SolidPattern)
#         #self.brush.setColor(QtCore.Qt.red)
#
#     def sceneEventFilter(self, obj, event):
#         if (event.type() == QtCore.QEvent.GraphicsSceneMousePress and
#                                     event.button() == QtCore.Qt.LeftButton):
#             assert(self.rubberband is None)
#             self.rubberband = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Line)
#             self.rubberband.setGeometry(QtCore.QRect(event.screenPos(),
#                                                      QtCore.QSize()))
#             self.rubberband.show()
#             return True
#
#         if (event.type() == QtCore.QEvent.GraphicsSceneMouseRelease and
#                                     event.button() == QtCore.Qt.LeftButton):
#             assert(self.rubberband is not None)
#             self.rubberband.hide()
#             self.rubberband = None
#             line = QtCore.QLineF(
#                             event.buttonDownScenePos(QtCore.Qt.LeftButton),
#                             event.scenePos())
#             item = obj.addLine(line, self.pen)
#             item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
#             item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
#             return True
#
#         elif (event.type() == QtCore.QEvent.GraphicsSceneMouseMove and
#                     bool(event.buttons() & QtCore.Qt.LeftButton)):
#             assert(self.rubberband is not None)
#             rect = QtCore.QRect(
#                             event.buttonDownScreenPos(QtCore.Qt.LeftButton),
#                             event.screenPos()).normalized()
#             self.rubberband.setGeometry(rect)
#             return True
#
#         return False


class DrawRectMode(MouseMode):
    dragmode = QtWidgets.QGraphicsView.NoDrag
    cursor = QtCore.Qt.CrossCursor
    icon = ':/trolltech/styles/commonstyle/images/media-stop-32.png'
    label = 'Draw Rect'
    name = 'drawRect'

    def __init__(self, parent=None):
        super(DrawRectMode, self).__init__(parent)
        self.rubberband = None
        self.pen = QtGui.QPen()
        self.pen.setWidth(1)
        self.pen.setColor(QtCore.Qt.red)
        self.brush = QtWidgets.QBrush()
        # self.brush.setStyle(QtCore.Qt.SolidPattern)
        # self.brush.setColor(QtCore.Qt.red)

    def sceneEventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.GraphicsSceneMousePress and
                event.button() == QtCore.Qt.LeftButton):
            assert(self.rubberband is None)
            self.rubberband = QtWidgets.QRubberBand(
                QtWidgets.QRubberBand.Rectangle)
            self.rubberband.setGeometry(
                QtCore.QRect(event.screenPos(), QtCore.QSize()))
            self.rubberband.show()
            return True

        if (event.type() == QtCore.QEvent.GraphicsSceneMouseRelease and
                event.button() == QtCore.Qt.LeftButton):
            assert(self.rubberband is not None)
            self.rubberband.hide()
            self.rubberband = None
            rect = QtCore.QRectF(
                event.buttonDownScenePos(QtCore.Qt.LeftButton),
                event.scenePos()).normalized()
            item = obj.addRect(rect, self.pen, self.brush)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
            return True

        elif (event.type() == QtCore.QEvent.GraphicsSceneMouseMove and
                bool(event.buttons() & QtCore.Qt.LeftButton)):
            assert(self.rubberband is not None)
            rect = QtCore.QRect(
                event.buttonDownScreenPos(QtCore.Qt.LeftButton),
                event.screenPos()).normalized()
            self.rubberband.setGeometry(rect)
            return True

        return False


class DrawEllipseMode(MouseMode):
    dragmode = QtWidgets.QGraphicsView.NoDrag
    cursor = QtCore.Qt.CrossCursor
    icon = ':/trolltech/styles/commonstyle/images/standardbutton-no-128.png'
    label = 'Draw Ellipse'
    name = 'drawEllipse'

    def __init__(self, parent=None):
        super(DrawEllipseMode, self).__init__(parent)
        self.rubberband = None
        self.pen = QtGui.QPen()
        self.pen.setWidth(1)
        self.pen.setColor(QtCore.Qt.red)
        self.brush = QtWidgets.QBrush()
        # self.brush.setStyle(QtCore.Qt.SolidPattern)
        # self.brush.setColor(QtCore.Qt.red)

    def sceneEventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.GraphicsSceneMousePress and
                event.button() == QtCore.Qt.LeftButton):
            assert(self.rubberband is None)
            self.rubberband = QtWidgets.QRubberBand(
                QtWidgets.QRubberBand.Rectangle)
            self.rubberband.setGeometry(
                QtCore.QRect(event.screenPos(), QtCore.QSize()))
            self.rubberband.show()
            return True

        if (event.type() == QtCore.QEvent.GraphicsSceneMouseRelease and
                event.button() == QtCore.Qt.LeftButton):
            assert(self.rubberband is not None)
            self.rubberband.hide()
            self.rubberband = None
            rect = QtCore.QRectF(
                event.buttonDownScenePos(QtCore.Qt.LeftButton),
                event.scenePos()).normalized()
            item = obj.addEllipse(rect, self.pen, self.brush)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
            return True

        elif (event.type() == QtCore.QEvent.GraphicsSceneMouseMove and
                bool(event.buttons() & QtCore.Qt.LeftButton)):
            assert(self.rubberband is not None)
            rect = QtCore.QRect(
                event.buttonDownScreenPos(QtCore.Qt.LeftButton),
                event.screenPos()).normalized()
            self.rubberband.setGeometry(rect)
            return True

        return False
