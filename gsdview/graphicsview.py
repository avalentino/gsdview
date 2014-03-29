# -*- coding: utf-8 -*-

### Copyright (C) 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>

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


'''Custom QtGui.QGraphicsView component.'''


from qt import QtCore, QtGui


# @TODO: move to gdalqt4.py
# @TODO: maybe this is not the best solution. Maybe a custom GraphicsItem
#        would be better
# @TODO: use event filters instead
class GraphicsView(QtGui.QGraphicsView):
    pass

    # @TODO: check
    #~ enter = QtCore.Signal()
    #~ leave = QtCore.Signal()
    #~ mousePositionUpdated = QtCore.Signal(QtCore.QPoint)
    #~ posMarked = QtCore.Signal(QtCore.QPoint)
    #~ newSize = QtCore.Signal(QtCore.QSize)
    #~ scaled = QtCore.Signal()

    #~ def __init__(self, *args, **kwargs):
        #~ super(GraphicsView, self).__init__(*args, **kwargs)
        #~ graphicsview.setMouseTracking(True)

    # @TODO: move to GraphicsViewMonitor
    #~ def enterEvent(self, event):
        #~ self.enter.emit()
        #~ return QtGui.QGraphicsView.enterEvent(self, event)

    # @TODO: move to GraphicsViewMonitor
    #~ def leaveEvent(self, event):
        #~ self.leave.emit()
        #~ return QtGui.QGraphicsView.leaveEvent(self, event)

    # @TODO: move to GraphicsViewMonitor
    # @TODO: use GraphicsSceneMouseMove
    #~ def mouseMoveEvent(self, event):
        #~ #if self.dragMode() == QtGui.QGraphicsView.NoDrag:
        #~ self.mousePositionUpdated.emit(event.pos())
        #~ if event.buttons() & QtCore.Qt.LeftButton:
            #~ self.posMarked.emit(event.pos())
        #~ #event.accept()
        #~ return QtGui.QGraphicsView.mouseMoveEvent(self, event)

    # @TODO: move to GraphicsViewMonitor
    # @TODO: use GraphicsSceneMousePress
    #~ def mousePressEvent(self, event):
        #~ if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            #~ if event.buttons() & QtCore.Qt.LeftButton:
                #~ self.posMarked.emit(event.pos())
            #~ #event.accept()
        #~ return QtGui.QGraphicsView.mousePressEvent(self, event)

    # @TODO: move to GraphicsViewMonitor
    #~ def resizeEvent(self, event):
        #~ self.newSize.emit(event.size())
        #~ return QtGui.QGraphicsView.resizeEvent(self, event)

    # Emit signals on transform modifications ###############################
    #~ def scale(self, sx, sy):
        #~ QtGui.QGraphicsView.scale(self, sx, sy)
        #~ self.scaled.emit()

    #~ def resetMatrix(self):
        #~ if not self.matrix().isIdentity():
            #~ QtGui.QGraphicsView.resetMatrix(self)
            #~ self.scaled.emit()

    # @TODO: remove
    #~ def clearScene(self):
        #~ scene = self.scene()
        #~ for item in scene.items():
            #~ scene.removeItem(item)

        #~ scene.setSceneRect(0, 0, 1, 1)
        #~ self.setSceneRect(scene.sceneRect())
        #~ self.resetTransform()


class GraphicsViewMonitor(QtCore.QObject):
    '''Emit signals when a registered graphics view changes status.

    :SIGNALS:

        * :attr:`leave`
        * :attr:`scrolled`
        * :attr:`resized`
        * :attr:`viewportResized`
        * :attr:`mouseMoved`

    '''

    ##: SIGNAL: it is emitted when the mouse pointer enterss the scene
    ##:
    ##: :C++ signature: `void enter(QGraphicsView*)`
    ###enter = QtCore.Signal(QtGui.QGraphicsScene)
    ##enter = QtCore.Signal(QtCore.QObject) # @TODO: check

    #: SIGNAL: it is emitted when the mouse pointer leaves the scene
    #:
    #: :C++ signature: `void leave(QGraphicsView*)`
    leave = QtCore.Signal(QtGui.QGraphicsScene)

    #: SIGNAL: it is emitted when a graphics view is scrolled
    #:
    #: :C++ signature: `void scrolled(QGraphicsView*)`
    scrolled = QtCore.Signal(QtGui.QGraphicsView)

    #: SIGNAL: it is emitted when the graphicsview window is resized
    #:
    #: :C++ signature: `void resized(QGraphicsView*, QSize)`
    resized = QtCore.Signal(QtGui.QGraphicsView, QtCore.QSize)

    # @TODO: explain difference with previous
    #: SIGNAL:
    #:
    #: :C++ signature: `void viewportResized(QGraphicsView*)`
    viewportResized = QtCore.Signal(QtGui.QGraphicsView)

    #: SIGNAL: it is emitted when the mouse pointer is moved on the scene
    #:
    #: :C++ signature: `void mouseMoved(QtGui.QGraphicsScene, QtCore.QPointF,
    #:                                  QtCore.Qt.MuseButtons)`
    mouseMoved = QtCore.Signal(QtGui.QGraphicsScene, QtCore.QPointF,
                               QtCore.Qt.MouseButtons)

    ##: SIGNAL:
    ##:
    ##: :C++ signature: `newPos(QtCore.QObject, QPoint)`
    ###newPos = QtCore.Signal(QtGui.QGraphicsView, QtCore.QPoint)
    ##newPos = QtCore.Signal(QtCore.QObject, QtCore.QPoint) # @TODO: check

    # @TODO: use signal mappers
    #~ def __init__(self, parent=None, **kwargs):
        #~ super(GraphicsViewMonitor, self).__init__(parent, **kwargs)

        #~ self.mappers = {}
        #~ self.mappers['scroll'] = QtCore.QSignalMapper(self,
                                                      #~ mapped=self.scrolled)
        #~ #self.mappers['scroll'].mapped.connect(self.scrolled)

        #~ self.mappers['scale'] = QtCore.QSignalMapper(
        #~     self, mapped=self.scaled)
        #~ #self.mappers['scale'].mapped.connect(self.scaled)

    #~ def register(self, graphicsview):
        #~ graphicsview.horizontalScrollBar().valueChanged.connect(
                                                #~ self.mappers['scroll'].map)
        #~ graphicsview.verticalScrollBar().valueChanged.connect(
                                                #~ self.mappers['scroll'].map)
        #~ self.mappers['scroll'].setMapping(graphicsview, graphicsview)
        #~ graphicsview.viewportResized.connect(self.mappers['scale'].map)
        #~ self.mappers['scale'].setMapping(graphicsview, graphicsview)

    def register(self, graphicsview):
        graphicsview.horizontalScrollBar().valueChanged.connect(
            lambda: self.scrolled.emit(graphicsview))
        graphicsview.verticalScrollBar().valueChanged.connect(
            lambda: self.scrolled.emit(graphicsview))
        graphicsview.horizontalScrollBar().rangeChanged.connect(
            lambda: self.viewportResized.emit(graphicsview))
        graphicsview.verticalScrollBar().rangeChanged.connect(
            lambda: self.viewportResized.emit(graphicsview))
        graphicsview.installEventFilter(self)

        # Many views can refer to the same scene so before installing a new
        # event filter old ones are removed
        scene = graphicsview.scene()
        if scene:
            scene.removeEventFilter(self)
            scene.installEventFilter(self)

    def eventFilter(self, obj, event):
        # @TODO: use an event map (??)
        if event.type() == QtCore.QEvent.Resize:
            assert isinstance(obj, QtGui.QGraphicsView)
            self.resized.emit(obj, event.size())
        elif event.type() == QtCore.QEvent.GraphicsSceneMouseMove:
            assert isinstance(obj, QtGui.QGraphicsScene)
            self.mouseMoved.emit(obj, event.scenePos(), event.buttons())
        elif event.type() == QtCore.QEvent.Leave:
            # Discard events from graphicsviews
            if isinstance(obj, QtGui.QGraphicsScene):
                self.leave.emit(obj)

        return obj.eventFilter(obj, event)

    #~ def eventFilter(self, obj, event):
        #~ '''bool QObject.eventFilter (self, QObject, QEvent)'''

        #~ QEvent = QtCore.QEvent

        #~ eventmap = {
            #~ QEvent.Enter: self.enterEvent,
            #~ QEvent.Leave: self.leaveEvent,

            #~ #QEvent.GraphicsSceneMouseDoubleClick
            #~ QEvent.GraphicsSceneMouseMove: self.mouseMoveEvent,
            #~ QEvent.GraphicsSceneMousePress: self.mousePressEvent,
            #~ #QEvent.GraphicsSceneMouseRelease
            #~ #QEvent.GraphicsSceneWheel

            #~ #QEvent.MouseButtonDblClick
            #~ #QEvent.MouseButtonPress: self.mouseMoveEvent,
            #~ #QEvent.MouseButtonRelease
            #~ #QEvent.MouseMove: self.mousePressEvent,

            #~ QEvent.Resize: self.resizeEvent,
        #~ }

        #~ methd = eventmap[event.type()]
        #~ return method(object, event)
        #~ #return True # stop event

    # Mouse events ##########################################################
    #~ def enterEvent(self, obj, event):
        #~ self.enter.emit(obj)
        #~ return obj.eventFilter(obj, event)

    #~ def leaveEvent(self, obj, event):
        #~ self.leave.emit(obj)
        #~ return obj.eventFilter(obj, event)

    #~ def mouseMoveEvent(self, obj, event):
        #~ self.mouseMove.emit(obj, event.pos())
        #~ if event.buttons() & QtCore.Qt.LeftButton:
            #~ self.newPos.emit(obj, event.pos())
        #~ return obj.eventFilter(obj, event)

    #~ def mousePressEvent(self, obj, event):
        #~ if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            #~ if event.buttons() & QtCore.Qt.LeftButton:
                #~ self.newPos.emit(obj, event.pos())
            #~ #event.accept()
        #~ return obj.eventFilter(obj, event)
