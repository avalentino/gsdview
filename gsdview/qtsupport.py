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


"""Utility functions and classes for Qt5 applications."""


import os
import csv
import math
import logging
from io import StringIO
from configparser import ConfigParser

from qtpy import QtCore, QtWidgets, QtGui, QtSvg, QtPrintSupport, uic

from gsdview import utils


_log = logging.getLogger(__name__)


# Menus and toolbars helpers ###############################################
def actionGroupToMenu(actionGroup, label, mainwin):
    menu = QtWidgets.QMenu(label, mainwin)
    menu.addActions(actionGroup.actions())
    return menu


def actionGroupToToolbar(actionGroup, label, name=None):
    if name is None:
        # get camel case name
        parts = str(label).title().split()
        parts[0] = parts[0].lower()
        name = ''.join(parts)

    toolbar = QtWidgets.QToolBar(label)
    toolbar.addActions(actionGroup.actions())
    if name:
        toolbar.setObjectName(name)

    return toolbar


# Application cursor helpers ###############################################
def overrideCursor(func):
    def aux(*args, **kwargs):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            return func(*args, **kwargs)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
    return aux


def callExpensiveFunc(func, *args, **kwargs):
    QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
    try:
        return func(*args, **kwargs)
    finally:
        QtWidgets.QApplication.restoreOverrideCursor()


# Table model/view helpers ##################################################
def clearTable(tablewidget):
    """Remove contents from a table widget preserving labels. """

    labels = [
        str(tablewidget.horizontalHeaderItem(col).text())
        for col in range(tablewidget.columnCount())
    ]
    tablewidget.clear()
    tablewidget.setHorizontalHeaderLabels(labels)
    tablewidget.setRowCount(0)


def selectAllItems(itemview):
    """Select all items in an QAbstractItemView."""

    model = itemview.model()
    topleft = model.index(0, 0)

    try:
        bottomright = model.index(model.rowCount() - 1,
                                  model.columnCount() - 1)
    except (TypeError, AttributeError):
        # columnCount is a private method in QAbstractListModel
        # assume it is a list
        bottomright = model.index(model.rowCount() - 1)

    selection = QtCore.QItemSelection(topleft, bottomright)
    itemview.selectionModel().select(selection,
                                     QtCore.QItemSelectionModel.Select)


# @QtCore.Slot(QtWidgets.QWidget)  # @TODO: check
def copySelectedItems(itemview):
    """Copy selected items of an QAbstractItemView to the clipboard and
    also return copied data."""

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
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(data, QtGui.QClipboard.Clipboard)
        clipboard.setText(data, QtGui.QClipboard.Selection)

    # @TODO: check
    # data = QtCore.QByteArray()
    # data.append('\n'.join(lines))

    # mimedata = QtCore.QMimeData()
    # mimedata.setData('text/csv', data)

    # clipboard = QtWidgets.QApplication.clipboard()
    # clipboard.setMimeData(mimedata, QtGui.QClipboard.Clipboard)
    # clipboard.setMimeData(mimedata, QtGui.QClipboard.Selection)

    return data


def modelToIni(model, section=None, cfg=None):
    assert model.columnCount() == 2

    if cfg is None:
        cfg = ConfigParser()

    for row in range(model.rowCount()):
        name = model.index(row, 0).data()
        value = model.index(row, 1).data()
        cfg.set(section, name, value)

    return cfg


def modelToCsv(model, dialect='excel'):
    fp = StringIO()
    writer = csv.writer(fp, dialect)

    try:
        ncols = model.columnCount()
    except TypeError:
        # columnCount is a private method in QAbstractListModel
        ncols = 1

    for row in range(model.rowCount()):
        line = []
        for col in range(ncols):
            line.append(model.index(row, col).data())
        writer.writerow(line)

    return fp.getvalue()


def modelToTextDocument(model, doc=None):
    if doc is None:
        doc = QtGui.QTextDocument()

    cursor = QtGui.QTextCursor(doc)
    cursor.movePosition(QtGui.QTextCursor.End)
    cursor.beginEditBlock()

    format_ = QtGui.QTextTableFormat()
    format_.setCellPadding(5)
    format_.setCellSpacing(0)
    format_.setBorderStyle(QtGui.QTextFrameFormat.BorderStyle_Solid)
    format_.setHeaderRowCount(1)

    nrows = model.rowCount()
    try:
        ncols = model.columnCount()
    except TypeError:
        # columnCount is a private method in QAbstractListModel
        ncols = 1
    table = cursor.insertTable(nrows, ncols, format_)

    # textformat = QtWidgets.QTextFormat()

    for row in range(nrows):
        for col in range(ncols):
            text = model.index(row, col).data()
            if text is None:
                text = ''
            else:
                text = str(text)

            cell = table.cellAt(row, col)
            cellCursor = cell.firstCursorPosition()
            cellCursor.insertText(text)  # , textformat)

    # headers style
    headerformat = QtGui.QTextCharFormat()
    headerformat.setFontWeight(QtGui.QFont.Bold)
    brush = headerformat.background()
    brush.setColor(QtCore.Qt.lightGray)
    brush.setStyle(QtCore.Qt.SolidPattern)
    headerformat.setBackground(brush)

    # horizontal header
    headers = [
        model.headerData(col, QtCore.Qt.Horizontal) for col in range(ncols)
    ]
    if any(headers):
        table.insertRows(0, 1)
        for col, text in enumerate(headers):
            if text is None:
                text = ''
            else:
                text = str(text)

            cell = table.cellAt(0, col)
            cell.setFormat(headerformat)
            cellCursor = cell.firstCursorPosition()
            cellCursor.insertText(text)

    # vertical header
    headers = [
        model.headerData(row, QtCore.Qt.Vertical) for row in range(nrows)
    ]

    if any(headers):
        table.insertColumns(0, 1)
        for row, text in enumerate(headers):
            if text is None:
                text = ''
            else:
                text = str(text)

            cell = table.cellAt(row + 1, 0)
            cell.setFormat(headerformat)
            cellCursor = cell.firstCursorPosition()
            cellCursor.insertText(text, headerformat)

    cursor.endEditBlock()

    return doc


def exportTable(model, parent=None):
    filters = [
        'CSV file (*.csv)',
        'CSV TAB-delimited file (*.csv)',
        'HTML file (*.html)',
        'All files (*)',
    ]

    try:
        ncols = model.columnCount()
    except TypeError:
        # columnCount is a private method in QAbstractListModel
        ncols = 1

    if ncols == 1:
        filters.insert(0, 'Text file (*.txt)')
        target = os.path.join(utils.default_workdir(), 'data.txt')
    if ncols == 2:
        filters.insert(0, 'INI file format (*.ini)')
        target = os.path.join(utils.default_workdir(), 'data.ini')
    else:
        target = os.path.join(utils.default_workdir(), 'data.csv')

    # @TODO: check
    if parent is None:
        try:
            parent = model.window()
        except AttributeError:
            parent = None

    filename, filter_ = QtWidgets.QFileDialog.getSaveFileName(
        parent, model.tr('Save'), target, ';;'.join(filters))
    if filename:
        ext = os.path.splitext(filename)[-1]
        ext = ext.lower()
        if ext == '.csv' or ext == '.txt':
            if 'TAB' in filter_:
                dialect = 'excel-tab'
            else:
                dialect = 'excel'

            data = modelToCsv(model, dialect)
        elif ext == '.ini':
            cfg = modelToIni(model)
            fp = StringIO()
            cfg.write(fp)
            data = fp.getvalue()
        elif ext == '.html':
            doc = modelToTextDocument(model)
            data = doc.toHtml()
        else:
            # default
            data = modelToCsv(model, 'excel-tab')

        with open(filename, 'w') as fd:
            fd.write(data)


def setViewContextActions(widget):
    assert (widget.contextMenuPolicy() == QtCore.Qt.ActionsContextMenu), \
        'menu policy is not "QtCore.Qt.ActionsContextMenu"'
    # if widget.contextMenuPolicy() != QtCore.Qt.ActionsContextMenu:
    #     widget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

    icon = geticon('copy.svg', __name__)
    action = QtWidgets.QAction(
        icon, widget.tr('&Copy'), widget,
        objectName='copyAction',
        shortcut=widget.tr('Ctrl+C'),
        toolTip=widget.tr('Copy selected items'),
        triggered=lambda: copySelectedItems(widget))
    widget.addAction(action)

    # ':/trolltech/dialogs/qprintpreviewdialog/images/view-page-multi-32.png'
    icon = QtGui.QIcon(
        ':/trolltech/styles/commonstyle/images/viewlist-128.png')
    action = QtWidgets.QAction(
        icon, widget.tr('Select &All'), widget,
        objectName='selectAllAction',
        # shortcut=widget.tr('Ctrl+A'),
        toolTip=widget.tr('Select all items'),
        triggered=lambda: selectAllItems(widget))
    widget.addAction(action)

    icon = widget.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton)
    action = QtWidgets.QAction(
        icon, widget.tr('&Save As'), widget,
        objectName='saveAsAction',
        shortcut=widget.tr('Ctrl+S'),
        statusTip=widget.tr('Save as'),
        triggered=lambda: exportTable(widget.model()))
    widget.addAction(action)

    icon = QtGui.QIcon(
        ':/trolltech/dialogs/qprintpreviewdialog/images/print-32.png')
    action = QtWidgets.QAction(
        icon, widget.tr('&Print'), widget,
        objectName='printAction',
        shortcut=widget.tr('Ctrl+P'),
        statusTip=widget.tr('Print'),
        triggered=lambda: printObject(widget))
    widget.addAction(action)

    # icon = QtGui.QIcon(
    #     ':/trolltech/styles/commonstyle/images/filecontents-128.png')
    # action = QtWidgets.QAction(icon, widget.tr('Print Preview'), widget,
    #                        objectName='printPreviewAction',
    #                        statusTip=widget.tr('Print Preview'))#,
    #                        #triggered=tablePrintPreview)
    #                        # @TODO: tablePrintPreview
    # widget.addAction(action)


# Printing helpers ##########################################################
def coreprint(obj, printer):
    painter = QtGui.QPainter(printer)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    obj.render(painter)
    painter.end()


def printObject(obj, printer=None, parent=None):
    if printer is None:
        printer = QtPrintSupport.QPrinter(
            QtPrintSupport.QPrinter.PrinterResolution)
        # printer.setOutputFile(os.path.join(utils.default_workdir().
        #                                    'filename.pdf'))

    # @TODO: check
    if parent is None:
        try:
            parent = obj.window()
        except AttributeError:
            parent = None

    # dialog = QtPrintSupport.QPrintDialog(printer)
    # try:
    #     window = obj.window()
    # except AttributeError:
    #     window = = None
    # preview = QtWidgets.QPrintPreviewWidget(printer, window)
    # preview.paintRequested.connect(coreprint)
    # dialog.setOptionTabs([preview])
    # ret = d.exec_()

    ret = QtPrintSupport.QPrintDialog(printer, parent).exec_()
    if ret == QtWidgets.QDialog.Accepted:
        if isinstance(obj, (QtGui.QTextDocument, QtWidgets.QTextEdit)):
            obj.print_(printer)
        elif hasattr(obj, 'model'):
            model = obj.model()
            doc = modelToTextDocument(model)
            doc.print_(printer)
        elif isinstance(obj, QtCore.QAbstractItemModel):
            doc = modelToTextDocument(obj)
            doc.print_(printer)
        else:
            coreprint(obj, printer)


def printPreview(obj, printer=None, parent=None):
    if printer is None:
        printer = QtPrintSupport.QPrinter(
            QtPrintSupport.QPrinter.PrinterResolution)

    # @TODO: check
    if parent is None:
        try:
            parent = obj.window()
        except AttributeError:
            parent = None

    dialog = QtWidgets.QPrintPreviewDialog(printer, parent)
    dialog.paintRequested.connect(coreprint)
    ret = dialog.exec_()

    # @WARNING: duplicate code
    ret = QtPrintSupport.QPrintDialog(printer, parent).exec_()
    if ret == QtWidgets.QDialog.Accepted:
        if isinstance(obj, (QtGui.QTextDocument, QtWidgets.QTextEdit)):
            obj.print_(printer)
        elif hasattr(object, 'model'):
            model = obj.model()
            doc = modelToTextDocument(model)
            obj.print_(printer)
        elif isinstance(obj, QtCore.QAbstractItemModel):
            doc = modelToTextDocument(obj)
            doc.print_(printer)
        else:
            coreprint(obj, printer)


# QImage helpers ###########################################################
import numpy as np
GRAY_COLORTABLE = [QtGui.QColor(i, i, i).rgba() for i in range(256)]
RED_COLORTABLE = [QtGui.QColor(i, 0, 0).rgba() for i in range(256)]
GREEN_COLORTABLE = [QtGui.QColor(0, i, 0).rgba() for i in range(256)]
BLUE_COLORTABLE = [QtGui.QColor(0, 0, i).rgba() for i in range(256)]
JET_COLORTABLE = [QtGui.QColor(r, g, b).rgba() for r, g, b in [
    [  0,   0, 128],
    [  0,   0, 132],
    [  0,   0, 137],
    [  0,   0, 141],
    [  0,   0, 146],
    [  0,   0, 150],
    [  0,   0, 155],
    [  0,   0, 159],
    [  0,   0, 164],
    [  0,   0, 168],
    [  0,   0, 173],
    [  0,   0, 178],
    [  0,   0, 182],
    [  0,   0, 187],
    [  0,   0, 191],
    [  0,   0, 196],
    [  0,   0, 200],
    [  0,   0, 205],
    [  0,   0, 209],
    [  0,   0, 214],
    [  0,   0, 218],
    [  0,   0, 223],
    [  0,   0, 227],
    [  0,   0, 232],
    [  0,   0, 237],
    [  0,   0, 241],
    [  0,   0, 246],
    [  0,   0, 250],
    [  0,   0, 255],
    [  0,   0, 255],
    [  0,   0, 255],
    [  0,   0, 255],
    [  0,   0, 255],
    [  0,   4, 255],
    [  0,   8, 255],
    [  0,  12, 255],
    [  0,  16, 255],
    [  0,  20, 255],
    [  0,  24, 255],
    [  0,  28, 255],
    [  0,  32, 255],
    [  0,  36, 255],
    [  0,  40, 255],
    [  0,  44, 255],
    [  0,  48, 255],
    [  0,  52, 255],
    [  0,  56, 255],
    [  0,  60, 255],
    [  0,  64, 255],
    [  0,  68, 255],
    [  0,  72, 255],
    [  0,  76, 255],
    [  0,  80, 255],
    [  0,  84, 255],
    [  0,  88, 255],
    [  0,  92, 255],
    [  0,  96, 255],
    [  0, 100, 255],
    [  0, 104, 255],
    [  0, 108, 255],
    [  0, 112, 255],
    [  0, 116, 255],
    [  0, 120, 255],
    [  0, 124, 255],
    [  0, 128, 255],
    [  0, 132, 255],
    [  0, 136, 255],
    [  0, 140, 255],
    [  0, 144, 255],
    [  0, 148, 255],
    [  0, 152, 255],
    [  0, 156, 255],
    [  0, 160, 255],
    [  0, 164, 255],
    [  0, 168, 255],
    [  0, 172, 255],
    [  0, 176, 255],
    [  0, 180, 255],
    [  0, 184, 255],
    [  0, 188, 255],
    [  0, 192, 255],
    [  0, 196, 255],
    [  0, 200, 255],
    [  0, 204, 255],
    [  0, 208, 255],
    [  0, 212, 255],
    [  0, 216, 255],
    [  0, 220, 254],
    [  0, 224, 251],
    [  0, 228, 248],
    [  2, 232, 244],
    [  6, 236, 241],
    [  9, 240, 238],
    [ 12, 244, 235],
    [ 15, 248, 231],
    [ 19, 252, 228],
    [ 22, 255, 225],
    [ 25, 255, 222],
    [ 28, 255, 219],
    [ 31, 255, 215],
    [ 35, 255, 212],
    [ 38, 255, 209],
    [ 41, 255, 206],
    [ 44, 255, 202],
    [ 48, 255, 199],
    [ 51, 255, 196],
    [ 54, 255, 193],
    [ 57, 255, 190],
    [ 60, 255, 186],
    [ 64, 255, 183],
    [ 67, 255, 180],
    [ 70, 255, 177],
    [ 73, 255, 173],
    [ 77, 255, 170],
    [ 80, 255, 167],
    [ 83, 255, 164],
    [ 86, 255, 160],
    [ 90, 255, 157],
    [ 93, 255, 154],
    [ 96, 255, 151],
    [ 99, 255, 148],
    [102, 255, 144],
    [106, 255, 141],
    [109, 255, 138],
    [112, 255, 135],
    [115, 255, 131],
    [119, 255, 128],
    [122, 255, 125],
    [125, 255, 122],
    [128, 255, 119],
    [131, 255, 115],
    [135, 255, 112],
    [138, 255, 109],
    [141, 255, 106],
    [144, 255, 102],
    [148, 255,  99],
    [151, 255,  96],
    [154, 255,  93],
    [157, 255,  90],
    [160, 255,  86],
    [164, 255,  83],
    [167, 255,  80],
    [170, 255,  77],
    [173, 255,  73],
    [177, 255,  70],
    [180, 255,  67],
    [183, 255,  64],
    [186, 255,  60],
    [190, 255,  57],
    [193, 255,  54],
    [196, 255,  51],
    [199, 255,  48],
    [202, 255,  44],
    [206, 255,  41],
    [209, 255,  38],
    [212, 255,  35],
    [215, 255,  31],
    [219, 255,  28],
    [222, 255,  25],
    [225, 255,  22],
    [228, 255,  19],
    [231, 255,  15],
    [235, 255,  12],
    [238, 255,   9],
    [241, 252,   6],
    [244, 248,   2],
    [248, 245,   0],
    [251, 241,   0],
    [254, 237,   0],
    [255, 234,   0],
    [255, 230,   0],
    [255, 226,   0],
    [255, 222,   0],
    [255, 219,   0],
    [255, 215,   0],
    [255, 211,   0],
    [255, 208,   0],
    [255, 204,   0],
    [255, 200,   0],
    [255, 196,   0],
    [255, 193,   0],
    [255, 189,   0],
    [255, 185,   0],
    [255, 182,   0],
    [255, 178,   0],
    [255, 174,   0],
    [255, 171,   0],
    [255, 167,   0],
    [255, 163,   0],
    [255, 159,   0],
    [255, 156,   0],
    [255, 152,   0],
    [255, 148,   0],
    [255, 145,   0],
    [255, 141,   0],
    [255, 137,   0],
    [255, 134,   0],
    [255, 130,   0],
    [255, 126,   0],
    [255, 122,   0],
    [255, 119,   0],
    [255, 115,   0],
    [255, 111,   0],
    [255, 108,   0],
    [255, 104,   0],
    [255, 100,   0],
    [255,  96,   0],
    [255,  93,   0],
    [255,  89,   0],
    [255,  85,   0],
    [255,  82,   0],
    [255,  78,   0],
    [255,  74,   0],
    [255,  71,   0],
    [255,  67,   0],
    [255,  63,   0],
    [255,  59,   0],
    [255,  56,   0],
    [255,  52,   0],
    [255,  48,   0],
    [255,  45,   0],
    [255,  41,   0],
    [255,  37,   0],
    [255,  34,   0],
    [255,  30,   0],
    [255,  26,   0],
    [255,  22,   0],
    [255,  19,   0],
    [250,  15,   0],
    [246,  11,   0],
    [241,   8,   0],
    [237,   4,   0],
    [232,   0,   0],
    [228,   0,   0],
    [223,   0,   0],
    [218,   0,   0],
    [214,   0,   0],
    [209,   0,   0],
    [205,   0,   0],
    [200,   0,   0],
    [196,   0,   0],
    [191,   0,   0],
    [187,   0,   0],
    [182,   0,   0],
    [178,   0,   0],
    [173,   0,   0],
    [168,   0,   0],
    [164,   0,   0],
    [159,   0,   0],
    [155,   0,   0],
    [150,   0,   0],
    [146,   0,   0],
    [141,   0,   0],
    [137,   0,   0],
    [132,   0,   0],
    [128,   0,   0],
]]


def _aligned(data, nbyes=4):
    h, w = data.shape

    fact = nbyes / data.itemsize
    # math.ceil return int
    shape = (h, math.ceil(w / fact) * nbyes)
    if shape != data.shape:
        # build aligned matrix
        image = np.zeros(shape, data.dtype)
        image[:, 0:w] = data[:, 0:w]
    else:
        image = np.require(data, data.dtype, 'CO')  # 'CAO'
    return image


def numpy2qimage(data, colortable=GRAY_COLORTABLE):
    """Convert a numpy array into a QImage.

    .. note:: requires sip >= 4.7.5.

    """

    has_colortable = False

    if data.dtype in (np.uint8, np.ubyte, np.byte):
        if data.ndim == 2:
            h, w = data.shape
            image = _aligned(data)
            format_ = QtGui.QImage.Format_Indexed8
            has_colortable = True

        elif data.ndim == 3 and data.shape[2] == 3:
            h, w = data.shape[:2]
            image = np.zeros((h, w, 4), data.dtype)
            image[:, :, 2::-1] = data
            image[..., -1] = 255
            format_ = QtGui.QImage.Format_RGB32

        elif data.ndim == 3 and data.shape[2] == 4:
            h, w = data.shape[:2]
            image = np.require(data, np.uint8, 'CO')  # 'CAO'
            format_ = QtGui.QImage.Format_ARGB32

        else:
            raise ValueError('unable to convert data: shape=%s, '
                             'dtype="%s"' % (data.shape,
                                             np.dtype(data.dtype)))

    elif data.dtype == np.uint16 and data.ndim == 2:
        # @TODO: check
        h, w = data.shape
        image = _aligned(data)
        format_ = QtGui.QImage.Format_RGB16

    elif data.dtype == np.uint32 and data.ndim == 2:
        h, w = data.shape
        image = np.require(data, data.dtype, 'CO')  # 'CAO'
        # format_ = QtGui.QImage.Format_ARGB32
        format_ = QtGui.QImage.Format_RGB32

    else:
        raise ValueError(
            'unable to convert data: shape=%s, dtype="%s"' % (
                data.shape, np.dtype(data.dtype)))

    result = QtGui.QImage(image.data, w, h, format_)
    result.ndarray = image
    if has_colortable:
        result.setColorTable(colortable)

    return result


# Resources helpers #########################################################
def getuifile(name, package=None):
    """Return the ui file path.

    It is assumed that Qt UI files are located in the "ui" subfolfer of
    the package.

    .. seealso:: :func:`gsdview.utils.getresource`

    """

    return utils.getresource(os.path.join('ui', name), package)


def getuiform(name, package=None):
    """Return the ui form class.

    If it is available a pre-built python module the form class is
    imported from it (assuming that the module contains a single UI
    class having a name that starts with `Ui_`).

    If no pre-build python module is available than the form call is
    loaded directly from the ui file using the PyQt5.uic helper module.

    .. note:: in the pyside2 packege is used to provide bindings for Qt5
              then the uic module is not available and only pre-built
              modules are searched.
              When pyside2 is used an :exc:`ImportError` is raised
              if pre-built forms are not available.

    .. note:: like :func:`gsdview.qtsupport.getuifile` this
              function assumes that pre-build form modules and Qt UI
              files are located in the "ui" subfolder of the package.

    .. seealso:: :func:`gsdview.utils.getresource`,
                 :func:`gsdview.qtsupport.getuifile`

    """

    try:
        fromlist = package.rsplit('.')[:-1]
        fromlist.append('ui')
        modname = '.'.join(fromlist + [name])
        module = __import__(modname, fromlist=fromlist)
        formnames = [
            key for key in module.__dict__.keys() if key.startswith('Ui_')
        ]
        formname = formnames[0]
        FormClass = getattr(module, formname)
        _log.debug('load "%s" form base class from pre-compiled python module',
                   formname)
    except ImportError:
        uifile = getuifile(name + '.ui', package)
        FormClass, QtBaseClass = uic.loadUiType(uifile)
        _log.debug('load "%s" form class from ui file', FormClass.__name__)

    return FormClass


def geticonfile(name, package=None):
    """Return the icon file path.

    It is assumed that icon files are located in the "images" subfolder
    of the package.

    .. seealso:: :func:`gsdview.utils.getresource`

    """

    return utils.getresource(os.path.join('images', name), package)


def geticon(name, package=None):
    """Build and return requested icon.

    It is assumed that icon files are located in the "images" subfolder
    of the package.

    .. seealso:: :func:`gsdview.utils.getresource`

    """

    iconfile = utils.getresource(os.path.join('images', name), package)

    return QtGui.QIcon(iconfile)


# Misc helpers ##############################################################
def cfgToTextDocument(cfg, doc=None):
    if doc is None:
        doc = QtGui.QTextDocument()

    cursor = QtGui.QTextCursor(doc)
    cursor.movePosition(QtGui.QTextCursor.End)

    # table style
    tableformat = QtGui.QTextTableFormat()
    tableformat.setTopMargin(10)
    tableformat.setBottomMargin(10)
    tableformat.setCellPadding(5)
    tableformat.setCellSpacing(0)
    tableformat.setBorderStyle(QtGui.QTextFrameFormat.BorderStyle_Solid)
    tableformat.setHeaderRowCount(1)

    # headers style
    titleblockformat = QtGui.QTextBlockFormat()
    titleblockformat.setTopMargin(20)
    titleblockformat.setBottomMargin(10)

    titleformat = QtGui.QTextCharFormat()
    titleformat.setFontWeight(QtGui.QFont.Bold)
    # titleformat.setPointSze(12)

    # headers style
    headerformat = QtGui.QTextCharFormat()
    headerformat.setFontWeight(QtGui.QFont.Bold)
    brush = headerformat.background()
    brush.setColor(QtCore.Qt.lightGray)
    brush.setStyle(QtCore.Qt.SolidPattern)
    headerformat.setBackground(brush)

    for section in cfg.sections():
        items = sorted(cfg.items(section))
        if not items:
            continue

        cursor.beginEditBlock()
        cursor.movePosition(QtGui.QTextCursor.End)

        # title
        cursor.insertBlock(titleblockformat)
        cursor.insertText(section, titleformat)

        nrows = len(items)
        ncols = 2
        table = cursor.insertTable(nrows, ncols, tableformat)

        # textformat = QtWidgets.QTextFormat()

        for index, (key, value) in enumerate(items):
            cell = table.cellAt(index, 0)
            cellCursor = cell.firstCursorPosition()
            cellCursor.insertText(key)

            cell = table.cellAt(index, 1)
            cellCursor = cell.firstCursorPosition()
            cellCursor.insertText(value)

        # horizontal header
        headers = [doc.tr('Key'), doc.tr('Value')]
        table.insertRows(0, 1)
        for col, text in enumerate(headers):
            cell = table.cellAt(0, col)
            cell.setFormat(headerformat)
            cellCursor = cell.firstCursorPosition()
            cellCursor.insertText(text)

        # vertical header
        table.insertColumns(0, 1)
        for row in range(1, nrows + 1):
            text = str(row)

            cell = table.cellAt(row, 0)
            cell.setFormat(headerformat)
            cellCursor = cell.firstCursorPosition()
            cellCursor.insertText(text, headerformat)

        cursor.endEditBlock()

    return doc


def imgexport(obj, parent=None):
    filters = [
        obj.tr('All files (*)'),
        obj.tr('Simple Vector Graphics file (*.svg)'),
        obj.tr('PDF file (*.pdf)'),
        obj.tr('PostScript file (*.ps)'),
    ]
    filters.extend('%s file (*.%s)' % (
        str(fmt).upper(), str(fmt))
        for fmt in QtGui.QImageWriter.supportedImageFormats())

    formats = set(
        str(fmt).lower()
        for fmt in QtGui.QImageWriter.supportedImageFormats())
    formats.update(('svg', 'pdf', 'ps'))

    # @TODO: check
    if parent is None:
        try:
            parent = obj.window()
        except AttributeError:
            parent = None

    target = os.path.join(utils.default_workdir(), 'image.jpeg')

    filename, filter_ = QtWidgets.QFileDialog.getSaveFileName(
        parent, obj.tr('Save picture'), target, ';;'.join(filters))
    ext = 'unknown'
    while filename and (ext not in formats):
        ext = os.path.splitext(filename)[1]
        if ext:
            ext = ext[1:].lower()
            if ext in formats:
                break
            else:
                QtWidgets.QMessageBox.information(
                    parent, obj.tr('Unknown file format'),
                    obj.tr('Unknown file format "%s".\nPlease retry.') % ext)

                filename, filter_ = QtWidgets.QFileDialog.getSaveFileName(
                    parent, obj.tr('Save draw'), filename, ';;'.join(filters),
                    filter_)
        else:
            ext = 'unknown'

    if filename:
        if hasattr(obj, 'viewport'):
            srcsize = obj.viewport().rect().size()
        elif hasattr(obj, 'sceneRect'):
            # QGraphicsViews also has a viewport method so they should be
            # trapped by the previous check
            srcsize = obj.sceneRect().toRect().size()
        else:
            srcsize = QtWidgets.QSize(800, 600)

        if ext in ('pdf', 'ps'):
            device = QtPrintSupport.QPrinter(
                QtPrintSupport.QPrinter.HighResolution)
            device.setOutputFileName(filename)
            if ext == 'pdf':
                device.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            else:
                # ext == 'ps'
                device.setOutputFormat(QtPrintSupport.QPrinter.PostScriptFormat)
        elif ext == 'svg':
            device = QtSvg.QSvgGenerator()
            device.setFileName(filename)
            device.setSize(srcsize)
            # device.setViewBox(obj.sceneRect().toRect())
            # device.setTitle(obj.tr('Graphics Draw'))
            # device.setDescription(obj.tr('Qt SVG drawing.'))
        else:
            device = QtGui.QPixmap(srcsize)
            # @TODO: check
            device.fill(QtCore.Qt.white)

        painter = QtGui.QPainter()
        if painter.begin(device):
            # painter.setRenderHint(QtGui.QPainter.Antialiasing)
            obj.render(painter)
            painter.end()
            if hasattr(device, 'save'):
                device.save(filename)
        else:
            QtWidgets.QMessageBox.warning(
                parent,
                obj.tr('Warning'),
                obj.tr('Unable initialize painting device.'))


# Qt info
def format_qt_info():
    qlocale = QtCore.QLocale()
    supported_image_formats = [
        bytes(fmt).decode('utf-8')
        for fmt in QtGui.QImageReader.supportedImageFormats()
    ]
    qt_info = [
        'Qt system locale: %s\n' % qlocale.system().name(),
        'Qt locale name: %s\n' % qlocale.name(),
        'Qt locale country: %s\n' % qlocale.countryToString(qlocale.country()),
        'Qt locale language: %s\n' % qlocale.languageToString(
            qlocale.language()),
        'Qt locale decimal point: "%s"\n' % qlocale.decimalPoint(),
        'Qt UI languages: %s\n' % qlocale.uiLanguages(),
        'Qt supported image formats: %s\n' % ', '.join(supported_image_formats),
    ]

    return qt_info
