#!/usr/bin/env python

from PyQt4 import QtCore, QtGui

from gsdview import qt4support

class MouseMode(QtCore.QObject):
    dragmode = QtGui.QGraphicsView.NoDrag
    cursor = None
    icon = QtGui.QIcon()
    label = ''
    name = ''

    def eventFilter(self, object, event):
        if isinstance(object, QtGui.QGraphicsScene):
            return self.sceneEventFilter(object, event)
        elif isinstance(object, QtGui.QGraphicsView):
            if event.type() == QtCore.QEvent.Enter:
                object.setDragMode(self.dragmode)
                if self.cursor:
                    object.setCursor(self.cursor)
                else:
                    object.unsetCursor()
            return self.viewEventFilter(object, event)
        elif isinstance(object, QtGui.QScrollBar):
            return self.scrollbarEventFilter(object, event)
        else:
            return False

    def sceneEventFilter(self, object, event):
        return False

    def viewEventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Enter:
            object.setDragMode(self.dragmode)
            if self.cursor:
                object.setCursor(self.cursor)
            else:
                object.unsetCursor()

        return False

    def scrollbarEventFilter(self, object, event):
        return False

class PointerMode(MouseMode):
    dragmode = QtGui.QGraphicsView.NoDrag
    cursor = None
    icon = qt4support.geticon('arrow.svg', __name__)
    label = 'Pointer'
    name = 'pointer'

class ScrollHandMouseMode(MouseMode):
    dragmode = QtGui.QGraphicsView.ScrollHandDrag
    cursor = None
    icon = qt4support.geticon('hand.svg', __name__)
    label = 'Scroll hand'
    name = 'hand'

    def viewEventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Wheel:

            # Delta is expressed in 1/8 degree
            delta = event.delta() / 8.  # degree

            # Conversion from degrees to zoom factor:
            # a factor of 1.1 every 15 degrees
            k = 1.1/15.

            if delta >= 0:
                factor = k * delta
            else:
                factor = -1/(k * delta)

            object.scale(factor, factor)
            event.accept()

            return True

        return False

    def scrollbarEventFilter(self, object, event):
        # ignore wheel events
        if event.type() == QtCore.QEvent.Wheel:
            return True
        else:
            return False

class RubberBandMouseMode(MouseMode):
    dragmode = QtGui.QGraphicsView.RubberBandDrag
    cursor = QtCore.Qt.CrossCursor
    icon = qt4support.geticon('area.svg', __name__)
    label = 'Rubber band'
    name = 'rubberband'

    def sceneEventFilter(self, object, event):
        if event.type() == QtCore.QEvent.GraphicsSceneMouseRelease:
            p0 = event.buttonDownScenePos(QtCore.Qt.LeftButton)
            p1 = event.scenePos()
            rect = QtCore.QRectF(p0, p1).normalized()
            self.emit(QtCore.SIGNAL('rubberBandSeclection(const QRectF&)'),
                      rect)
            return True

        #return object.eventFilter(object, event)   # @TODO: check
        #return QtGui.QGraphicsScene.eventFilter(self, object, event)
        return False

    def scrollbarEventFilter(self, object, event):
        # ignore wheel events if some button is pressed
        if ((event.type() == QtCore.QEvent.Wheel)
                                and (event.buttons() != QtCore.Qt.NoButton)):
            return True
        else:
            return False

class MouseManager(QtCore.QObject):

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)

        self._moderegistry = [
            PointerMode(),
            ScrollHandMouseMode(),
            RubberBandMouseMode(),
        ]

        self.actions = self._setupActions()

        self.toolbar = QtGui.QToolBar('Mouse')
        self.toolbar.addActions(self.actions.actions())

        self.menu = QtGui.QMenu('Mouse')
        self.menu.addActions(self.actions.actions())

    def _newModeAction(self, mode, parent=None):
        action = QtGui.QAction(mode.icon, self.tr(mode.label), parent)
        action.setCheckable(True)
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self._emitModeChanged)

        return action

    def _setupActions(self):
        actions = QtGui.QActionGroup(self)
        actions.setExclusive(True)

        for index, mode in enumerate(self._moderegistry):
            action = self._newModeAction(mode, actions)
            action.setData(QtGui.QGraphicsView.NoDrag)

        actions.actions()[0].setChecked(True)

        return actions

    def _getMode(self):
        action = self.actions.checkedAction()
        index = self.actions.actions().index(action)
        return self._moderegistry[index].name

    def _setMode(self, name):
        names = self.modes()
        index = names.index(name)
        action = self.actions.actions()[index]
        action.setChecked(True)

    def _delMode(self, name):
        names = [m.name for m in self._moderegistry]
        index = names.index(name)
        action = self.actions.actions()[index]
        self.actions.removeAction(action)
        del self._moderegistry[index]
        #~ if actin.checked() and self._moderegistry:
            #~ self.actions.actions()[0].setChecked(True)

    mode = property(_getMode, _setMode, _delMode, 'mouse mode name')

    def modes(self):
        return tuple(m.name for m in self._moderegistry)

    def register(self, mode):
        action = self._newModeAction(mode, self.actions)
        self.actions.addAction(action)
        self._moderegistry.append(mode)

    def _modeIndex(self, name):
        names = self.modes()
        return names.index(name)

    def getMode(self, name=None):
        '''Return the mouse mode object'''

        if name is None:
            action = self.actions.checkedAction()
            index = self.actions.actions().index(action)
        else:
            index = self._modeIndex(name)
        return self._moderegistry[index]

    def _emitModeChanged(self, name=None):
        if name is None:
            name = self.mode
        self.emit(QtCore.SIGNAL('modeChanged(PyQt_PyObject)'), name)

    def eventFilter(self, object, event):
        '''Events dispatcher'''

        return self.getMode().eventFilter(object, event)
