# -*- coding: utf-8 -*-

### Copyright (C) 2008-2010 Antonio Valentino <a_valentino@users.sf.net>

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

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


from PyQt4 import QtCore, QtGui


# @TODO: move to gdalqt4.py
# @TODO: maybe this is not the best solution. Maybe a custom GraphicsItem
#        would be better
# @TODO: use event filters instead
class GraphicsView(QtGui.QGraphicsView):
    pass

    # @TODO: check
    #~ def __init__(self, *args, **kwargs):
        #~ super(GraphicsView, self).__init__(*args, **kwargs)
        #~ graphicsview.setMouseTracking(True)

    # @TODO: move to GraphicsViewMonitor
    #~ def enterEvent(self, event):
        #~ self.emit(QtCore.SIGNAL('enter()'))
        #~ return QtGui.QGraphicsView.enterEvent(self, event)

    # @TODO: move to GraphicsViewMonitor
    #~ def leaveEvent(self, event):
        #~ self.emit(QtCore.SIGNAL('leave()'))
        #~ return QtGui.QGraphicsView.leaveEvent(self, event)

    # @TODO: move to GraphicsViewMonitor
    # @TODO: use GraphicsSceneMouseMove
    #~ def mouseMoveEvent(self, event):
        #~ #if self.dragMode() == QtGui.QGraphicsView.NoDrag:
        #~ self.emit(QtCore.SIGNAL('mousePositionUpdated(QPoint)'),
                  #~ event.pos())
        #~ if event.buttons() & QtCore.Qt.LeftButton:
            #~ self.emit(QtCore.SIGNAL('posMarked(QPoint)'), event.pos())
        #~ #event.accept()
        #~ return QtGui.QGraphicsView.mouseMoveEvent(self, event)

    # @TODO: move to GraphicsViewMonitor
    # @TODO: use GraphicsSceneMousePress
    #~ def mousePressEvent(self, event):
        #~ if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            #~ if event.buttons() & QtCore.Qt.LeftButton:
                #~ self.emit(QtCore.SIGNAL('posMarked(QPoint)'), event.pos())
            #~ #event.accept()
        #~ return QtGui.QGraphicsView.mousePressEvent(self, event)

    # @TODO: move to GraphicsViewMonitor
    #~ def resizeEvent(self, event):
        #~ self.emit(QtCore.SIGNAL('newSize(QSize)'), event.size())
        #~ return QtGui.QGraphicsView.resizeEvent(self, event)

    ### Emit signals on transform modifications ###############################
    #~ def scale(self, sx, sy):
        #~ QtGui.QGraphicsView.scale(self, sx, sy)
        #~ self.emit(QtCore.SIGNAL('scaled()'))

    #~ def resetMatrix(self):
        #~ if not self.matrix().isIdentity():
            #~ QtGui.QGraphicsView.resetMatrix(self)
            #~ self.emit(QtCore.SIGNAL('scaled()'))

    # @TODO: remove
    #~ def clearScene(self):
        #~ scene = self.scene()
        #~ for item in scene.items():
            #~ scene.removeItem(item)

        #~ scene.setSceneRect(0, 0, 1, 1)
        #~ self.setSceneRect(scene.sceneRect())
        #~ self.resetTransform()

class GraphicsViewMonitor(QtCore.QObject):
    '''Emit signals when a registered graphcs view changes status.

    :signals:

    - scrolled(QGraphicsView*): scroll on graphicsview
    - resized(QGraphicsView*, QSize): emitted when the graphicsview
      window is resized
    - viewportResized(QGraphicsView*):
    - leave(QGraphicsView*):

    '''

    # @TODO: use signal mappers
    #~ def __init__(self, parent=None, **kwargs):
        #~ super(GraphicsViewMonitor, self).__init__(parent, **kwargs)

        #~ self.mappers = {}
        #~ self.mappers['scroll'] = QtCore.QSignalMapper(self)
        #~ self.connect(self.mappers['scroll'], QtCore.SIGNAL('mapped(QWidget*)'),
                     #~ self.scrolled)

        #~ self.mappers['scale'] = QtCore.QSignalMapper(self)
        #~ self.connect(self.mappers['scale'], QtCore.SIGNAL('mapped(QWidget*)'),
                     #~ self.scaled)

    #~ def register(self, graphicsview):
        #~ self.connect(graphicsview.horizontalScrollBar(),
                     #~ QtCore.SIGNAL('valueChanged(int)'),
                     #~ self.mappers['scroll'], QtCore.SLOT('map()'))
        #~ self.connect(graphicsview.verticalScrollBar(),
                     #~ QtCore.SIGNAL('valueChanged(int)'),
                     #~ self.mappers['scroll'], QtCore.SLOT('map()'))
        #~ self.mappers['scroll'].setMapping(graphicsview, graphicsview)
        #~ self.connect(graphicsview, QtCore.SIGNAL('viewportResized()'),
                     #~ self.mappers['scale'], QtCore.SLOT('map()'))
        #~ self.mappers['scale'].setMapping(graphicsview, graphicsview)

    def register(self, graphicsview):
        self.connect(graphicsview.horizontalScrollBar(),
                     QtCore.SIGNAL('valueChanged(int)'),
                     lambda x: self.scrolled(graphicsview))
        self.connect(graphicsview.verticalScrollBar(),
                     QtCore.SIGNAL('valueChanged(int)'),
                     lambda y: self.scrolled(graphicsview))
        self.connect(graphicsview.horizontalScrollBar(),
                     QtCore.SIGNAL('rangeChanged(int,int)'),
                     lambda x: self.viewportResized(graphicsview))
        self.connect(graphicsview.verticalScrollBar(),
                     QtCore.SIGNAL('rangeChanged(int,int)'),
                     lambda y: self.viewportResized(graphicsview))
        graphicsview.installEventFilter(self)

        # Many views can refer to the same scene so before installing a new
        # event filter old ones are removed
        scene = graphicsview.scene()
        if scene:
            scene.removeEventFilter(self)
            scene.installEventFilter(self)

    ### SIGNALS ###############################################################
    def scrolled(self, graphicsview):
        self.emit(QtCore.SIGNAL('scrolled(QGraphicsView*)'), graphicsview)

    def viewportResized(self, graphicsview):
        self.emit(QtCore.SIGNAL('viewportResized(QGraphicsView*)'),
                  graphicsview)

    def resized(self, graphcsview, size):
        '''GraphicsViw resized'''

        self.emit(QtCore.SIGNAL('resized(QGraphicsView*, QSize)'),
                  graphcsview, size)

    def mouseMoved(self, scene, pos, buttons):
        self.emit(QtCore.SIGNAL('mouseMoved(QGraphicsScene*, QPointF, '
                                'Qt::MouseButtons)'),
                  scene, pos, buttons)

    def leave(self, scene):
        self.emit(QtCore.SIGNAL('leave(QGraphicsScene*)'), scene)

    def eventFilter(self, obj, event):
        # @TODO: use an event map (??)
        if event.type() == QtCore.QEvent.Resize:
            assert isinstance(obj, QtGui.QGraphicsView)
            self.resized(obj, event.size())
        elif event.type() == QtCore.QEvent.GraphicsSceneMouseMove:
            assert isinstance(obj, QtGui.QGraphicsScene)
            self.mouseMoved(obj, event.scenePos(), event.buttons())
        elif event.type() == QtCore.QEvent.Leave:
            # Discard events from graphicsviews
            if isinstance(obj, QtGui.QGraphicsScene):
                self.leave(obj)

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

    ### Mouse events ##########################################################
    #~ def enterEvent(self, obj, event):
        #~ self.emit(QtCore.SIGNAL('enter(PyQt_PyObject)'), obj)
        #~ return obj.eventFilter(obj, event)

    #~ def leaveEvent(self, obj, event):
        #~ self.emit(QtCore.SIGNAL('leave(PyQt_PyObject)'))
        #~ return obj.eventFilter(obj, event)

    #~ def mouseMoveEvent(self, obj, event):
        #~ self.emit(QtCore.SIGNAL('mouseMove(PyQt_PyObject, QPoint)'),
                  #~ obj, event.pos())
        #~ if event.buttons() & QtCore.Qt.LeftButton:
            #~ self.emit(QtCore.SIGNAL('newPos(PyQt_PyObject, QPoint)'),
                      #~ obj, event.pos())
        #~ return obj.eventFilter(obj, event)

    #~ def mousePressEvent(self, obj, event):
        #~ if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            #~ if event.buttons() & QtCore.Qt.LeftButton:
                #~ self.emit(QtCore.SIGNAL('newPos(PyQt_PyObject, QPoint)'),
                          #~ obj, event.pos())
            #~ #event.accept()
        #~ return obj.eventFilter(obj, event)
