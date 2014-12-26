# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>
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


'''Core modue for image stretch control.'''


from qt import QtCore, QtWidgets

from gsdview import qtsupport

from .widgets import StretchDialog


class StretchTool(QtCore.QObject):
    def __init__(self, app, **kwargs):
        super(StretchTool, self).__init__(app, **kwargs)
        self.app = app

        self.dialog = StretchDialog(parent=app)
        self.dialog.hide()

        # This should not be necessary since tha main window (app) is set
        # as parent of the StretchDialog
        QtWidgets.qApp.lastWindowClosed.connect(self.dialog.close)

        self.action = self._setupAction()
        self.action.setEnabled(False)

        self.dialog.finished.connect(lambda: self.action.setChecked(False))
        self.app.mdiarea.subWindowActivated.connect(self.onSubWindowChanged)
        self.dialog.valueChanged.connect(self.onStretchChanged)
        self.dialog.accepted.connect(self.saveDialogState)

        self.toolbar = QtWidgets.QToolBar(self.tr('Stretching Toolbar'))
        self.toolbar.setObjectName('stretchingToolbar')
        self.toolbar.addAction(self.action)

        self._state_registry = {}
        #self.app.subWindowClosed(self.onItemClosed)
        self.app.datamodel.rowsAboutToBeRemoved.connect(self.onItemClosed)

    def _setupAction(self):
        icon = qtsupport.geticon('stretching.svg', __name__)
        action = QtWidgets.QAction(
            icon, self.tr('Stretch'), self,
            objectName='stretchAction',
            statusTip=self.tr('Stretch'),
            checkable=True,
            triggered=self.onButtonToggled)

        return action

    @QtCore.Slot(QtCore.QModelIndex, int, int)
    def onItemClosed(self, index, start, end):
        for i in range(start, end+1):
            subindex = index.child(i, 0)
            item = self.app.datamodel.itemFromIndex(subindex)
            self._state_registry.pop(item.filename, None)

    @QtCore.Slot(bool)
    def onButtonToggled(self, checked=True):
        if checked:
            self.restoreDialogState()
            self.dialog.show()
            #self.action.setChecked(True)
        else:
            self.dialog.hide()
            self.saveDialogState()
            self.action.setChecked(False)

    @QtCore.Slot()
    def saveDialogState(self):
        item = self.currentGraphicsItem()
        if item:
            self.dialog.saveState()
            key = item.filename
            self._state_registry[key] = self.sialog.state
        #else:
        #    logging.debug('no item')

    def restoreDialogState(self, item=None):
        if item is None:
            item = self.currentGraphicsItem()
        if item is None or not hasattr(item, 'stretch'):
            self.dialog.setEnabled(False)
            return

        self.dialog.setEnabled(True)

        imin, imax = item.stretch.range

        itemId = item.path()
        if itemId in self._state_registry:
            state = self._data[itemId]
            state['low'] = imin
            state['high'] = imax
            self.dialog.setState(state)
        else:
            minimum, maximum = item.dataRange()
            self._setDialogState(imin, imax, minimum, maximum)

    def resetDialogState(self, item=None):
        if item is None:
            item = self.currentGraphicsItem()
        if item is None or not hasattr(item, 'stretch'):
            self.dialog.setEnabled(False)
            return

        self.dialog.setEnabled(True)

        imin, imax = item.stretch.range
        minimum, maximum = item.dataRange()

        self._setDialogState(imin, imax, minimum, maximum)

    def _setDialogState(self, imin, imax, minimum=None, maximum=None):
        if minimum is not None:
            self.dialog.stretchwidget.setMinimum(minimum)
        else:
            self.dialog.stretchwidget.setMinimum(min(imin, 0))

        if maximum is not None:
            self.dialog.stretchwidget.setMaximum(maximum)
        else:
            self.dialog.stretchwidget.setMaximum(max(imax, 2 * imax))

        self.dialog.stretchwidget.setLow(imin)
        self.dialog.stretchwidget.setHigh(imax)
        self.dialog.saveState()

    # @TODO: move to main app (??)
    def currentGraphicsItem(self, window=None):
        if window is None:
            window = self.app.mdiarea.activeSubWindow()
        try:
            return window.item.graphicsitem
        except AttributeError:
            return None

    @QtCore.Slot()
    @QtCore.Slot(QtWidgets.QMdiSubWindow)
    def onSubWindowChanged(self, subwin=None):
        if subwin is None:
            subwin = self.app.mdiarea.activeSubWindow()

        if subwin is None:
            self.action.setEnabled(self.dialog.isVisible())
            self.dialog.setEnabled(False)
            return

        item = self.currentGraphicsItem(subwin)
        try:
            stretchable = item.stretch is not None
        except AttributeError:
            stretchable = False

        if stretchable:
            self.action.setEnabled(True)
            if self.dialog.isVisible():
                self.dialog.setEnabled(True)
                self.restoreDialogtate(item)
        else:
            if self.dialog.isVisible():
                self.action.setEnabled(True)
                self.dialog.setEnabled(False)
            else:
                self.action.setEnabled(False)

    @QtCore.Slot()
    def onStretchChanged(self):
        item = self.currentGraphicsItem()
        try:
            stretch = item.stretch
        except AttributeError:
            #self.dialog.hide()
            pass
        else:
            vmin, vmax = self.dialog.values()
            if vmin < vmax:
                stretch.set_range(vmin, vmax)
                item.update()
            #else:
            #    logging.warning('vmin: %f, vmax: %f' % (vmin, vmax))
