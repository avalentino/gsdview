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


'''Components for layers management.'''


import logging
import itertools

from qtsix import QtCore, QtWidgets, QtGui


SelectCurrentRows = (
    QtCore.QItemSelectionModel.SelectCurrent |
    QtCore.QItemSelectionModel.Rows
)


class BaseLayerManager(QtCore.QObject):
    def __init__(self, parent=None, **kargs):
        super(BaseLayerManager, self).__init__(parent, **kargs)
        self.actions = self._setupActions()

    def _setupActions(self):
        style = QtWidgets.QApplication.style()

        actions = QtWidgets.QActionGroup(self)

        icon = QtGui.QIcon(':/trolltech/styles/commonstyle/images/up-128.png')
        QtWidgets.QAction(
            icon, self.tr('Move to top'), actions,
            objectName='moveToTopAction',
            statusTip=self.tr('Move to top'),
            shortcut=self.tr('Ctrl+PgUp'))

        icon = style.standardIcon(QtWidgets.QStyle.SP_ArrowUp)
        QtWidgets.QAction(
            icon, self.tr('Move up'), actions,
            objectName='moveUpAction',
            statusTip=self.tr('Move up'),
            shortcut=self.tr('Ctrl+Up'))

        icon = style.standardIcon(QtWidgets.QStyle.SP_ArrowDown)
        QtWidgets.QAction(
            icon, self.tr('Move down'), actions,
            objectName='moveDownAction',
            statusTip=self.tr('Move down'),
            shortcut=self.tr('Ctrl+Down'))

        icon = QtGui.QIcon(
            ':/trolltech/styles/commonstyle/images/down-128.png')
        QtWidgets.QAction(
            icon, self.tr('Move to bottom'), actions,
            objectName='moveToBottomAction',
            statusTip=self.tr('Move to bottom'),
            shortcut=self.tr('Ctrl+PgDown'))

        #~ #'standardbutton-closetab-16.png'
        icon = QtGui.QIcon(':/trolltech/styles/commonstyle/images/'
                           'standardbutton-cancel-128.png')
        QtWidgets.QAction(
            icon, self.tr('Remove'), actions,
            objectName='removeLayerAction',
            statusTip=self.tr('Remove'),
            shortcut=self.tr('Del'))

        icon = QtGui.QIcon(
            ':/trolltech/styles/commonstyle/images/standardbutton-yes-128.png')
        QtWidgets.QAction(
            icon, self.tr('Show'), actions,
            objectName='showLayerAction',
            statusTip=self.tr('Show the layer'))

        icon = QtGui.QIcon(
            ':/trolltech/styles/commonstyle/images/standardbutton-no-128.png')
        QtWidgets.QAction(
            icon, self.tr('Hide'), actions,
            objectName='hideLayerAction',
            statusTip=self.tr('Hide the layer'))

        return actions

    def action(self, name):
        return self.actions.findChild(QtWidgets.QAction, name)

    def isLayer(self, item):
        # @TODO: complete
        return True

    @staticmethod
    def _selectionmap(selection):
        sortedselection = sorted(selection,
                                 key=QtCore.QItemSelectionRange.parent)

        selectionmap = {}  # collections.OrderedDict()
        for key, group in itertools.groupby(
                sortedselection, QtCore.QItemSelectionRange.parent):
            ranges = []
            for item in sorted(group, key=QtCore.QItemSelectionRange.top):
                if len(ranges) == 0:
                    ranges.append(item)
                    continue
                lastitem = ranges[-1]
                assert lastitem.parent() == item.parent()
                if lastitem.bottom() + 1 >= item.top():
                    model = lastitem.model()
                    topleft = model.index(
                        min(lastitem.top(), item.top()),
                        #min(lastitem.left(), item.left()),
                        0,
                        lastitem.parent())
                    bottomright = model.index(
                        max(lastitem.bottom(), item.bottom()),
                        #max(lastitem.right(), item.right()),
                        model.columnCount() - 1,
                        lastitem.parent())
                    ranges[-1] = QtCore.QItemSelectionRange(topleft,
                                                            bottomright)
                else:
                    ranges.append(item)
            selectionmap[key] = ranges

        return selectionmap

    @staticmethod
    def _parentitem(selectionrange):
        index = selectionrange.parent()
        if index.isValid():
            item = selectionrange.model().itemFromIndex(index)
        else:
            item = selectionrange.model().invisibleRootItem()

        return item

    @staticmethod
    def updateStackOrder(rootitem, offset=0):
        nrows = rootitem.rowCount()
        for row in range(nrows):
            qitem = rootitem.child(row).data()
            if qitem:
                qitem.setZValue(nrows + offset - row - 1)
            else:
                logging.warning('no graphics item associated to layer '
                                'n. %d' % row)

    # @TODO: beginMoveRows, endMoveRows
    def _takeRowsRange(self, selectionrange):
        parent = self._parentitem(selectionrange)

        rows = []
        for row in range(selectionrange.bottom(),
                         selectionrange.top() - 1, -1):
            # @TODO: check
            if not self.isLayer(parent.child(row)):
                #continue
                break
            items = parent.takeRow(row)
            rows.insert(0, items)

        return rows

    # @TODO: beginMoveRows, endMoveRows
    def _moveSelectionRange(self, selectionrange, dst):
        if selectionrange.top() == dst:
            return selectionrange

        model = selectionrange.model()
        parentindex = selectionrange.parent()
        parentitem = self._parentitem(selectionrange)
        nrows_selected = selectionrange.bottom() - selectionrange.top() + 1
        ncols = model.columnCount()

        if nrows_selected == parentitem.rowCount():
            return selectionrange

        if dst > parentitem.rowCount() - nrows_selected or dst < 0:
            return selectionrange

        selectedrows = self._takeRowsRange(selectionrange)
        for index, items in enumerate(selectedrows):
            parentitem.insertRow(dst + index, items)

        topleft = model.index(dst, 0, parentindex)
        bottomright = model.index(dst + nrows_selected - 1, ncols - 1,
                                  parentindex)

        return QtCore.QItemSelectionRange(topleft, bottomright)

    def moveSelectionToTop(self, selectionmodel):
        #assert selectionmodel.model() is self.model
        selection = selectionmodel.selection()
        selectionmap = self._selectionmap(selection)
        newselection = QtCore.QItemSelection()
        for parent, ranges in selectionmap.items():
            dst = 0
            for selectionrange in ranges:
                newrange = self._moveSelectionRange(selectionrange, dst)
                newselection.append(newrange)
                dst = newrange.bottom() + 1
        selectionmodel.select(newselection, SelectCurrentRows)

    def moveSelectionUp(self, selectionmodel):
        #assert selectionmodel.model() is self.model
        selection = selectionmodel.selection()
        selectionmap = self._selectionmap(selection)
        newselection = QtCore.QItemSelection()
        for parent, ranges in selectionmap.items():
            for selectionrange in ranges:
                dst = selectionrange.top() - 1
                newrange = self._moveSelectionRange(selectionrange, dst)
                newselection.append(newrange)
        selectionmodel.select(newselection, SelectCurrentRows)

    def moveSelectionDown(self, selectionmodel):
        #assert selectionmodel.model() is self.model
        selection = selectionmodel.selection()
        selectionmap = self._selectionmap(selection)
        newselection = QtCore.QItemSelection()
        for parent, ranges in selectionmap.items():
            ranges.reverse()
            for selectionrange in ranges:
                dst = selectionrange.top() + 1
                newrange = self._moveSelectionRange(selectionrange, dst)
                newselection.append(newrange)
        selectionmodel.select(newselection, SelectCurrentRows)

    def moveSelectionToBottom(self, selectionmodel):
        #assert selectionmodel.model() is self.model
        selection = selectionmodel.selection()
        selectionmap = self._selectionmap(selection)
        newselection = QtCore.QItemSelection()
        nrows = selectionmodel.model().rowCount()
        for parent, ranges in selectionmap.items():
            ranges.reverse()
            dst = nrows
            for selectionrange in ranges:
                dst -= selectionrange.height()
                newrange = self._moveSelectionRange(selectionrange, dst)
                newselection.append(newrange)
        selectionmodel.select(newselection, SelectCurrentRows)

    def removeSelectedLayers(self, selectionmodel):
        selection = selectionmodel.selection()
        selectionmap = self._selectionmap(selection)
        for parentindex, ranges in selectionmap.items():
            ranges.reverse()
            parentitem = self._parentitem(ranges[0])
            for selectionrange in ranges:
                for row in range(selectionrange.top(),
                                 selectionrange.bottom() + 1):
                    item = parentitem.child(row)
                    if not self.isLayer(item):
                        break
                    graphicsitem = item.data()
                    assert isinstance(graphicsitem, QtWidgets.QGraphicsItem)
                    scene = graphicsitem.scene()
                    scene.removeItem(graphicsitem)
                else:
                    parentitem.removeRows(selectionrange.top(),
                                          selectionrange.height())

        # @TODO: check
        #self.updateStackOrder(parent)

    def _updateActions(self, selectionmodel):
        model = selectionmodel.model()
        enabled = selectionmodel.hasSelection()
        for action in self.actions.actions():
            if action.objectName() == 'selectAllAction':
                selectedrows = selectionmodel.selectedRows()
                nselected = len(selectedrows)
                nlayers = model.rowCount()
                allselected = bool(nselected == nlayers)
                action.setEnabled(nlayers and not allselected)

            elif action.objectName() in ('showLayerAction', 'hideLayerAction'):
                selectedrows = selectionmodel.selectedRows()
                nselected = len(selectedrows)
                if nselected == 0:
                    action.setEnabled(False)
                else:
                    items = [
                        model.itemFromIndex(index) for index in selectedrows
                    ]
                    activerows = [
                        item.row() for item in items
                        if item.checkState() == QtCore.Qt.Checked
                    ]

                    if action.objectName() == 'showLayerAction':
                        action.setEnabled(len(activerows) != nselected)
                    elif action.objectName() == 'hideLayerAction':
                        action.setEnabled(len(activerows) != 0)
            else:
                action.setEnabled(enabled)

    @QtCore.Slot(QtCore.QModelIndex)
    #@QtCore.Slot(QtGui.QStandardItem)
    @QtCore.Slot('QStandardItem*')  # @TODO: fix
    def updateVisibility(self, index):
        if isinstance(index, QtCore.QModelIndex):
            if index.column() != 0:
                return
            item = index.model().itemFromIndex(index)

        elif isinstance(index, QtGui.QStandardItem):
            item = index
            index = item.index()
            if index.column() != 0:
                return
        else:
            raise TypeError(
                'unexpected type for index parameter: "%s"' % type(index))

        checked = bool(item.checkState() == QtCore.Qt.Checked)
        qlayer = item.data()  # index.data(QtCore.Qt.UserRole + 1)
        qlayer.setVisible(checked)

    def checkSelectedItems(self, selectionmodel, checked=True):
        model = selectionmodel.model()
        #assert model is self.model

        if checked:
            newstate = QtCore.Qt.Checked
        else:
            newstate = QtCore.Qt.Unchecked

        update = False
        for index in selectionmodel.selectedRows():
            item = model.itemFromIndex(index)

            if item.checkState() != newstate:
                item.setCheckState(newstate)
                self.updateVisibility(index)
                update = True

        if update:
            self._updateActions(selectionmodel)

    def toggleSelectedItems(self, selectionmodel):
        model = selectionmodel.model()
        #assert model is self.model

        update = False
        for index in selectionmodel.selectedRows():
            item = model.itemFromIndex(index)
            state = item.checkState()

            if state == QtCore.Qt.Checked:
                item.setCheckState(QtCore.Qt.Unchecked)
                update = True
            elif state == QtCore.Qt.Unchecked:
                item.setCheckState(QtCore.Qt.Checked)
                update = True
            else:
                logging.debug('unexpected check state: "%s"' % state)
                continue

            self.updateVisibility(index)

        if update:
            self._updateActions(selectionmodel)


class LayerManager(BaseLayerManager):
    def __init__(self, view, parent=None, **kargs):
        self.view = view
        super(LayerManager, self).__init__(parent, **kargs)

        view.addActions(self.actions.actions())
        view.installEventFilter(self)   # spacebar

        # connect signals
        model = self.view.model()
        model.layoutChanged.connect(self.updateStackOrder)
        model.rowsInserted.connect(self.updateStackOrder)
        model.rowsInserted.connect(self._updateActions)
        model.rowsRemoved.connect(self.updateStackOrder)
        model.rowsRemoved.connect(self._updateActions)
        model.itemChanged.connect(self.updateVisibility)

        view.clicked.connect(self.updateVisibility)
        view.activated.connect(self.toggleSelectedItems)

        view.selectionModel().selectionChanged.connect(self._updateActions)

        self._updateActions()

    @property
    def model(self):
        return self.view.model()

    @property
    def selectionmodel(self):
        return self.view.selectionModel()

    def _setupActions(self):
        actions = super(LayerManager, self)._setupActions()

        icon = QtGui.QIcon(
            ':/trolltech/styles/commonstyle/images/viewdetailed-128.png')
        QtWidgets.QAction(
            icon, self.tr('Select all'), actions,
            objectName='selectAllAction',
            statusTip=self.tr('Select all'),
            shortcut=self.tr('Ctrl-A'),
            triggered=self.view.selectAll)

        # connect actions
        action = actions.findChild(QtWidgets.QAction, 'moveToTopAction')
        action.triggered.connect(self.moveSelectionToTop)
        action = actions.findChild(QtWidgets.QAction, 'moveUpAction')
        action.triggered.connect(self.moveSelectionUp)
        action = actions.findChild(QtWidgets.QAction, 'moveDownAction')
        action.triggered.connect(self.moveSelectionDown)
        action = actions.findChild(QtWidgets.QAction, 'moveToBottomAction')
        action.triggered.connect(self.moveSelectionToBottom)
        action = actions.findChild(QtWidgets.QAction, 'removeLayerAction')
        action.triggered.connect(self.removeSelectedLayers)
        action = actions.findChild(QtWidgets.QAction, 'showLayerAction')
        action.triggered.connect(self.checkSelectedItems)
        action = actions.findChild(QtWidgets.QAction, 'hideLayerAction')
        action.triggered.connect(self.uncheckSelectedItems)

        return actions

    def eventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.KeyPress and
                event.key() == QtCore.Qt.Key_Space):
            self.toggleSelectedItems()
            return True
        else:
            return super(LayerManager, self).eventFilter(obj, event)

    @QtCore.Slot()
    def moveSelectionToTop(self, selectionmodel=None):
        if selectionmodel is None:
            selectionmodel = self.selectionmodel
        super(LayerManager, self).moveSelectionToTop(selectionmodel)

    @QtCore.Slot()
    def moveSelectionUp(self, selectionmodel=None):
        if selectionmodel is None:
            selectionmodel = self.selectionmodel
        super(LayerManager, self).moveSelectionUp(selectionmodel)

    @QtCore.Slot()
    def moveSelectionDown(self, selectionmodel=None):
        if selectionmodel is None:
            selectionmodel = self.selectionmodel
        super(LayerManager, self).moveSelectionDown(selectionmodel)

    @QtCore.Slot()
    def moveSelectionToBottom(self, selectionmodel=None):
        if selectionmodel is None:
            selectionmodel = self.selectionmodel
        super(LayerManager, self).moveSelectionToBottom(selectionmodel)

    @QtCore.Slot()
    def removeSelectedLayers(self, selectionmodel=None):
        if selectionmodel is None:
            selectionmodel = self.selectionmodel
        super(LayerManager, self).removeSelectedLayers(selectionmodel)

    @QtCore.Slot()
    def checkSelectedItems(self, selectionmodel=None, checked=True):
        if selectionmodel is None:
            selectionmodel = self.selectionmodel
        super(LayerManager, self).checkSelectedItems(selectionmodel, checked)

    @QtCore.Slot()
    def uncheckSelectedItems(self, selectionmodel=None):
        self.checkSelectedItems(selectionmodel, False)

    @QtCore.Slot()
    def toggleSelectedItems(self, selectionmodel=None):
        if selectionmodel is None:
            selectionmodel = self.selectionmodel
        super(LayerManager, self).toggleSelectedItems(selectionmodel)

    @QtCore.Slot()
    def _updateActions(self, selectionmodel=None):
        if selectionmodel is None:
            selectionmodel = self.selectionmodel
        super(LayerManager, self)._updateActions(selectionmodel)

    @QtCore.Slot()
    def updateStackOrder(self, rootitem=None):
        if rootitem is None:
            rootitem = self.model.invisibleRootItem()
        super(LayerManager, self).updateStackOrder(rootitem)
