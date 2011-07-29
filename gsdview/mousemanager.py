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

'''Mouse manager for the Qt4 graphics framework.

Mouse management for the Qt4 graphics framework is implemented by a set
of MouseMode objects, that provide specific event handlers and behave
like a descriptor, and a manager object that catches mouse events and
dispatch them to the appropriate hendler.

The MouseManager provides methods for eddeing/removing mouse modes,
making the system expandible, and also methods to register objects
(QGraphicsScene and QGraphicsView) to be controlled.

'''


__author__ = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__ = '$Date$'
__revision__ = '$Revision$'


from PyQt4 import QtCore, QtGui

from gsdview import qt4support


class MouseMode(QtCore.QObject):
    '''Base class for mouse mode desctiptors.

    Qt Graphics Framework mouse mode descriptors define some basic
    property for mouse related matters:

    - cursor
    - dragmode
    - eventFilter
    - name
    - label
    - icon

    The first three properties (not to be intender as python progremming
    language property) are strongly characterizing of the way the mouse
    works.

    In particular the eventFilter method is used to filter all events
    coming from graphics scenes an graphics views.

    .. note:: in order to work properly the eventFilter should be installed
              on both graphics scene and view and also on the scrollbars of
              the graphics view.
              So please always use the register method of MouseManager for
              a proper installaton of al event filters.

    '''

    dragmode = QtGui.QGraphicsView.NoDrag
    cursor = None
    icon = QtGui.QIcon()
    label = ''
    name = ''

    def eventFilter(self, obj, event):
        '''Basic implementation of the eventFilter method.

        The dafault implementation makes some basic operation such setting
        the mouse cursor anc dispatch the event to specific methods:

        - sceneEventFilter
        - viewEventFilter
        - scrollbarEventFilter

        In most of the cases derived classes only need to specialize one or
        more of this specific methods.

        '''

        if isinstance(obj, QtGui.QGraphicsScene):
            return self.sceneEventFilter(obj, event)
        elif isinstance(obj, QtGui.QGraphicsView):
            if event.type() == QtCore.QEvent.Enter:
                obj.setDragMode(self.dragmode)
                if self.cursor:
                    obj.setCursor(self.cursor)
                else:
                    obj.unsetCursor()
            return self.viewEventFilter(obj, event)
        elif isinstance(obj, QtGui.QScrollBar):
            return self.scrollbarEventFilter(obj, event)
        else:
            return False

    def sceneEventFilter(self, obj, event):
        return False

    def viewEventFilter(self, obj, event):
        return False

    def scrollbarEventFilter(self, obj, event):
        return False


class PointerMode(MouseMode):
    dragmode = QtGui.QGraphicsView.NoDrag
    cursor = None
    icon = qt4support.geticon('arrow.svg', __name__)
    label = 'Pointer'
    name = 'pointer'


class ScrollHandMode(MouseMode):
    dragmode = QtGui.QGraphicsView.ScrollHandDrag
    cursor = None
    icon = qt4support.geticon('hand.svg', __name__)
    label = 'Scroll hand'
    name = 'hand'

    def viewEventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Wheel:

            # Delta is expressed in 1/8 degree
            delta = event.delta() / 8.  # degree

            # Conversion from degrees to zoom factor:
            # a factor of 1.1 every 15 degrees
            k = 1.1 / 15.

            if delta >= 0:
                factor = k * delta
            else:
                factor = -1 / (k * delta)

            obj.scale(factor, factor)
            event.accept()

            return True

        return False

    def scrollbarEventFilter(self, obj, event):
        # ignore wheel events
        if event.type() == QtCore.QEvent.Wheel:
            return True
        else:
            return False


class RubberBandMode(MouseMode):
    '''Mouse mode for rubber band selection.

    :SIGNALS:

        * :attr:`rubberBandSeclection`

    '''

    dragmode = QtGui.QGraphicsView.RubberBandDrag
    cursor = QtCore.Qt.CrossCursor
    icon = qt4support.geticon('area.svg', __name__)
    label = 'Rubber band'
    name = 'rubberband'

    #: SIGNAL: it is emitted when a rectangular area is selected
    #:
    #: :C++ signature: `void rubberBandSeclection(const QRectF&)`
    rubberBandSeclection = QtCore.pyqtSignal(QtCore.QRectF)

    def sceneEventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.GraphicsSceneMouseRelease:
            p0 = event.buttonDownScenePos(QtCore.Qt.LeftButton)
            p1 = event.scenePos()
            rect = QtCore.QRectF(p0, p1).normalized()
            self.rubberBandSeclection.emit(rect)
            return True

        #return obj.eventFilter(obj, event)   # @TODO: check
        #return QtGui.QGraphicsScene.eventFilter(self, obj, event)
        return False

    def scrollbarEventFilter(self, obj, event):
        # ignore wheel events if some button is pressed
        if ((event.type() == QtCore.QEvent.Wheel)
                                and (event.buttons() != QtCore.Qt.NoButton)):
            return True
        else:
            return False


class MouseManager(QtCore.QObject):

    #: SIGNAL: it is emitted when the mouse mode is changed
    #:
    #: :C++ signature: `void modeChanged(const QString&)`
    modeChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, stdmodes=True, **kwargs):
        QtCore.QObject.__init__(self, parent, **kwargs)

        self._moderegistry = []
        self.actions = QtGui.QActionGroup(self)
        self.actions.setExclusive(True)

        if stdmodes:
            self.registerStandardModes()

    def registerStandardModes(self):
        for mode in (PointerMode, ScrollHandMode):  # , RubberBandMode):
            self.addMode(mode)
        if len(self._moderegistry) and not self.actions.checkedAction():
            self.actions.actions()[0].setChecked(True)

    def _newModeAction(self, mode, parent):
        if isinstance(mode.icon, basestring):
            icon = QtGui.QIcon(mode.icon)
        elif isinstance(mode.icon, QtGui.QStyle.StandardPixmap):
            style = QtGui.QApplication.style()
            icon = style.standardIcon(mode.icon)
        else:
            icon = mode.icon

        action = QtGui.QAction(icon, self.tr(mode.label), parent,
                               statusTip=self.tr(mode.label),
                               checkable=True)
        action.triggered.connect(lambda: self.modeChanged.emit(self.mode))
        return action

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

    def addMode(self, mode):
        if isinstance(mode, type):
            mode = mode(self)

        action = self._newModeAction(mode, self.actions)
        self.actions.addAction(action)
        self._moderegistry.append(mode)

    def getModeDescriptor(self, name=None):
        '''Return the mouse mode object'''

        try:
            if name is None:
                action = self.actions.checkedAction()
                index = self.actions.actions().index(action)
            else:
                names = self.modes()
                index = names.index(name)
            return self._moderegistry[index]
        except IndexError:
            # @TODO: check
            #raise ValueError('invalid mde nema: "%s"' % mode)
            return None

    def eventFilter(self, obj, event):
        '''Events dispatcher'''

        return self.getModeDescriptor().eventFilter(obj, event)

    def register(self, obj):
        '''Register a Qt graphics object to be monitored by the mouse manager.

        QGraphicsScene and QGrapgicsViews (and descending classes) objects
        can be registered to be monitored by the mouse manager.

        Scene objects associated to views (passes as argument) are
        automatically registered.

        '''

        obj.installEventFilter(self)

        try:
            obj.verticalScrollBar().installEventFilter(self)
        except AttributeError:
            # it is a QGraphicsScene
            scene = obj
        else:
            scene = obj.scene()

        # Avoid event filter duplication
        scene.removeEventFilter(self)
        scene.installEventFilter(self)

    def unregister(self, obj):
        '''Unregister monitored objects.

        If the object passed as argument is not a registered object
        nothing happens.

        .. note:: this method never tries to unregister scene objects
                  associated to the view passed as argument.

        '''

        obj.removeEventFilter(self)
