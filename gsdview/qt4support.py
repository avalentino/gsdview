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


'''Utility functions and classes for Qt4 applicaions.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import os
import logging

from PyQt4 import QtCore, QtGui, uic

from gsdview import utils


intToWinState = {
    int(QtCore.Qt.WindowNoState):       QtCore.Qt.WindowNoState,
    int(QtCore.Qt.WindowMinimized):     QtCore.Qt.WindowMinimized,
    int(QtCore.Qt.WindowMaximized):     QtCore.Qt.WindowMaximized,
    int(QtCore.Qt.WindowFullScreen):    QtCore.Qt.WindowFullScreen,
    int(QtCore.Qt.WindowActive):        QtCore.Qt.WindowActive,
}


### Menus and toolbars helpers ###############################################
def actionGroupToMenu(actionGroup, label, mainwin):
    menu = QtGui.QMenu(label, mainwin)
    menu.addActions(actionGroup.actions())
    return menu


def actionGroupToToolbar(actionGroup, label, name=None):
    if name is None:
        # get camel case name
        parts = str(label).title().split()
        parts[0] = parts[0].lower()
        name = ''.join(parts)
    toolbar = QtGui.QToolBar(label)
    toolbar.addActions(actionGroup.actions())
    if name:
        toolbar.setObjectName(name)

    return toolbar

### Application cursor helpers ###############################################
def overrideCursor(func):
    def aux(*args, **kwargs):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            return func(*args, **kwargs)
        finally:
            QtGui.QApplication.restoreOverrideCursor()
    return aux


def callExpensiveFunc(func, *args, **kwargs):
    QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
    try:
        return func(*args, **kwargs)
    finally:
        QtGui.QApplication.restoreOverrideCursor()


### Table model/view hepers ##################################################
def clearTable(tablewidget):
    '''Remove contents from a table widget preserving labels. '''

    labels = [str(tablewidget.horizontalHeaderItem(col).text())
                            for col in range(tablewidget.columnCount())]
    tablewidget.clear()
    tablewidget.setHorizontalHeaderLabels(labels)
    tablewidget.setRowCount(0)


def selectAllItems(itemview):
    '''Select all items in an QAbstractItemView.'''

    model = itemview.model()
    topleft = model.index(0, 0)
    try:
        # Should work for tables: 'columnCount' is private in lists
        bottomright = model.index(model.rowCount()-1, model.columnCount()-1)
    except (TypeError, AttributeError):
        # Assume it is a list
        bottomright = model.index(model.rowCount()-1)

    selection = QtGui.QItemSelection(topleft, bottomright)
    itemview.selectionModel().select(selection,
                                     QtGui.QItemSelectionModel.Select)

#@QtCore.pyqtSlot(QtGui.QWidget) # @TODO: check
def copySelectedItems(itemview):
    '''Copy selected items of an QAbstractItemView to the clipboard and
    also return copied data.'''

    selection = itemview.selectionModel().selection()
    lines = []
    for itemrange in selection:
        model = itemrange.model()
        parent = itemrange.parent()
        for row in range(itemrange.top(), itemrange.bottom() + 1):
            parts = []
            for col in range(itemrange.left(), itemrange.right() + 1):
                index = model.index(row, col, parent)
                parts.append(str(model.data(index)))
            line = '\t'.join(parts)
            lines.append(line)

    data = '\n'.join(lines)

    if data:
        clipboard = QtGui.qApp.clipboard()
        clipboard.setText(data, QtGui.QClipboard.Clipboard)
        clipboard.setText(data, QtGui.QClipboard.Selection)

    # @TODO: check
    #data = QtCore.QByteArray()
    #data.append('\n'.join(lines))

    #mimedata = QtCore.QMimeData()
    #mimedata.setData('text/csv', data)

    #clipboard = QtGui.qApp.clipboard()
    #clipboard.setMimeData(mimedata, QtGui.QClipboard.Clipboard)
    #clipboard.setMimeData(mimedata, QtGui.QClipboard.Selection)

    return data


def setViewContextActions(widget):
    assert (widget.contextMenuPolicy() == QtCore.Qt.ActionsContextMenu), \
        'menu policy is not "QtCore.Qt.ActionsContextMenu"'
    #if widget.contextMenuPolicy() != QtCore.Qt.ActionsContextMenu:
    #    widget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

    icon = geticon('copy.svg', __name__)
    action = QtGui.QAction(icon, widget.tr('&Copy'), widget,
                           objectName='copy',
                           shortcut=widget.tr('Ctrl+C'),
                           toolTip=widget.tr('Copy selected items'),
                           triggered=lambda: copySelectedItems(widget))
    widget.addAction(action)

    #icon = geticon('selectall.svg', __name__)
    icon = QtGui.QIcon()
    action = QtGui.QAction(icon, widget.tr('Select &All'), widget,
                           objectName='selectall',
                           #shortcut=widget.tr('Ctrl+A'),
                           toolTip=widget.tr('Select all items'),
                           triggered=lambda: selectAllItems(widget))
    widget.addAction(action)


### QImage helpers ###########################################################
#from PyQt4.Qwt5 import toQImage as _toQImage
#def numpy2qimage(data):
#    # @NOTE: for Qwt5 < 5.2.0
#    # return toQImage(data.transpose())
#    return _toQImage(data)

import numpy
GRAY_COLORTABLE = [QtGui.QColor(i, i, i).rgb() for i in range(256)]

def _aligned(data, nbyes=4):
    h, w = data.shape

    fact = nbyes / data.itemsize
    shape = (h, numpy.ceil(w / float(fact)) * nbyes)
    if shape != data.shape:
        # build aligned matrix
        image = numpy.zeros(shape, data.dtype)
        image[:,:w] = data[:,:w]
    else:
        image = numpy.require(data, data.dtype, 'CO') # 'CAO'
    return image

def numpy2qimage(data):
    '''Convert a numpy array into a QImage.

    .. note:: requires sip >= 4.7.5.

    '''

    colortable = None

    if data.dtype in (numpy.uint8, numpy.ubyte, numpy.byte):
        if data.ndim == 2:
            h, w = data.shape
            image = _aligned(data)
            format_ = QtGui.QImage.Format_Indexed8
            colortable = GRAY_COLORTABLE

        elif data.ndim == 3 and data.shape[2] == 3:
            h, w = data.shape[:2]
            image = numpy.zeros((h,w,4), data.dtype)
            image[:,:,2::-1] = data
            image[...,-1] = 255
            format_ = QtGui.QImage.Format_RGB32

        elif data.ndim == 3 and data.shape[2] == 4:
            h, w = data.shape[:2]
            image = numpy.require(data, numpy.uint8, 'CO') # 'CAO'
            format_ = QtGui.QImage.Format_ARGB32

        else:
            raise ValueError('unable to convert data: shape=%s, '
                             'dtype="%s"' % (data.shape,
                                             numpy.dtype(data.dtype)))

    elif data.dtype == numpy.uint16 and data.ndim == 2:
        # @TODO: check
        h, w = data.shape
        image = _aligned(data)
        format_ = QtGui.QImage.Format_RGB16

    elif data.dtype == numpy.uint32 and data.ndim == 2:
        h, w = data.shape
        image = numpy.require(data, data.dtype, 'CO') # 'CAO'
        #format_ = QtGui.QImage.Format_ARGB32
        format_ = QtGui.QImage.Format_RGB32

    else:
        raise ValueError('unable to convert data: shape=%s, dtype="%s"' % (
                                        data.shape, numpy.dtype(data.dtype)))

    result = QtGui.QImage(image.data, w, h, format_)
    result.ndarray = image
    if colortable:
        result.setColorTable(colortable)

    return result


### Resources helpers #########################################################
def getuifile(name, package=None):
    '''Return the ui file path.

    It is assumed that Qt UI files are located in the "ui" subfolfer of
    the package.

    .. seealso:: :autolink:`gsdview.utils.getresource`

    '''

    return utils.getresource(os.path.join('ui', name), package)


def getuiform(name, package=None):
    '''Return the ui form class.

    If it is available a pre-build python module the form class is
    imported from it (assuming that the module contains a single UI
    class having a name that starts with `Ui_`).

    If no pre-build python module is available than the form call is
    loaded directly from the ui file usning the PyQt4.uic helper module.

    .. note:: like :autolink:`gsdview.qt4support.getuifile` this
              function assumes that pre-build form modules and Qt UI
              files are located in the "ui" subfolfer of the package.

    .. seealso:: :autolink:`gsdview.utils.getresource`,
                 :autolink:`gsdview.qt4support.getuifile`

    '''

    try:
        fromlist = package.rsplit('.')[:-1]
        fromlist.append('ui')
        modname = '.'.join(fromlist + [name])
        module = __import__(modname, fromlist=fromlist)
        formnames = [key for key in module.__dict__.keys()
                                                if key.startswith('Ui_')]
        formname = formnames[0]
        FormClass = getattr(module, formname)
        logging.debug('load "%s" form base class from pre-compiled python '
                      'module' % formname)
        return FormClass
    except ImportError:
        uifile = getuifile(name + '.ui', package)
        FormClass, QtBaseClass = uic.loadUiType(uifile)
        logging.debug('load "%s" form class from ui file' % FormClass.__name__)
        return FormClass


def geticonfile(name, package=None):
    '''Return the icon file path.

    It is assumed that icon files are located in the "images" subfolder
    of the package.

    .. seealso:: :autolink:`gsdview.utils.getresource`

    '''

    return utils.getresource(os.path.join('images', name), package)


def geticon(name, package=None):
    '''Build and return requested icon.

    It is assumed that icon files are located in the "images" subfolder
    of the package.

    .. seealso:: :autolink:`gsdview.utils.getresource`

    '''

    iconfile = utils.getresource(os.path.join('images', name), package)

    return QtGui.QIcon(iconfile)
