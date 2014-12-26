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


'''Utility functions and classes for Qt4 applicaions.'''


import os
import csv
import logging
from io import StringIO

try:
    from configparser import ConfigParser
except ImportError:
    # @COMPATIBILITY: python 2.x
    from ConfigParser import ConfigParser

from qt import QtCore, QtWidgets, QtGui, QtSvg, QtPrintSupport, uic

from gsdview import utils


intToWinState = {
    int(QtCore.Qt.WindowNoState): QtCore.Qt.WindowNoState,
    int(QtCore.Qt.WindowMinimized): QtCore.Qt.WindowMinimized,
    int(QtCore.Qt.WindowMaximized): QtCore.Qt.WindowMaximized,
    int(QtCore.Qt.WindowFullScreen): QtCore.Qt.WindowFullScreen,
    int(QtCore.Qt.WindowActive): QtCore.Qt.WindowActive,
}


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
    '''Remove contents from a table widget preserving labels. '''

    labels = [
        str(tablewidget.horizontalHeaderItem(col).text())
        for col in range(tablewidget.columnCount())
    ]
    tablewidget.clear()
    tablewidget.setHorizontalHeaderLabels(labels)
    tablewidget.setRowCount(0)


def selectAllItems(itemview):
    '''Select all items in an QAbstractItemView.'''

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


#@QtCore.Slot(QtWidgets.QWidget) # @TODO: check
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
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(data, QtGui.QClipboard.Clipboard)
        clipboard.setText(data, QtGui.QClipboard.Selection)

    # @TODO: check
    #data = QtCore.QByteArray()
    #data.append('\n'.join(lines))

    #mimedata = QtCore.QMimeData()
    #mimedata.setData('text/csv', data)

    #clipboard = QtWidgets.QApplication.clipboard()
    #clipboard.setMimeData(mimedata, QtGui.QClipboard.Clipboard)
    #clipboard.setMimeData(mimedata, QtGui.QClipboard.Selection)

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

    format = QtGui.QTextTableFormat()
    format.setCellPadding(5)
    format.setCellSpacing(0)
    format.setBorderStyle(QtGui.QTextFrameFormat.BorderStyle_Solid)
    format.setHeaderRowCount(1)

    nrows = model.rowCount()
    try:
        ncols = model.columnCount()
    except TypeError:
        # columnCount is a private method in QAbstractListModel
        ncols = 1
    table = cursor.insertTable(nrows, ncols, format)

    #textformat = QtWidgets.QTextFormat()

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
    #if widget.contextMenuPolicy() != QtCore.Qt.ActionsContextMenu:
    #    widget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

    icon = geticon('copy.svg', __name__)
    action = QtWidgets.QAction(
        icon, widget.tr('&Copy'), widget,
        objectName='copyAction',
        shortcut=widget.tr('Ctrl+C'),
        toolTip=widget.tr('Copy selected items'),
        triggered=lambda: copySelectedItems(widget))
    widget.addAction(action)

    #':/trolltech/dialogs/qprintpreviewdialog/images/view-page-multi-32.png'
    icon = QtGui.QIcon(
        ':/trolltech/styles/commonstyle/images/viewlist-128.png')
    action = QtWidgets.QAction(
        icon, widget.tr('Select &All'), widget,
        objectName='selectAllAction',
        #shortcut=widget.tr('Ctrl+A'),
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

    #~ icon = QtGui.QIcon(
        #~ ':/trolltech/styles/commonstyle/images/filecontents-128.png')
    #~ action = QtWidgets.QAction(icon, widget.tr('Print Preview'), widget,
                           #~ objectName='printPreviewAction',
                           #~ statusTip=widget.tr('Print Preview'))#,
                           #~ #triggered=tablePrintPreview)
                           #~ # @TODO: tablePrintPreview
    #~ widget.addAction(action)


# Printing helpers ##########################################################
def coreprint(obj, printer):
    painter = QtWidgets.QPainter(printer)
    painter.setRenderHint(QtWidgets.QPainter.Antialiasing)
    obj.render(painter)
    painter.end()


def printObject(obj, printer=None, parent=None):
    if printer is None:
        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.PrinterResolution)
        #printer.setOutputFile(os.path.join(utils.default_workdir().
        #                                   'filename.pdf'))

    # @TODO: check
    if parent is None:
        try:
            parent = obj.window()
        except AttributeError:
            parent = None

    #dialog = QtPrintSupport.QPrintDialog(printer)
    #try:
    #    window = obj.window()
    #except AttributeError:
    #    window = = None
    #preview = QtWidgets.QPrintPreviewWidget(printer, window)
    #preview.paintRequested.connect(coreprint)
    #dialog.setOptionTabs([preview])
    #ret = d.exec_()

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
        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.PrinterResolution)

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
#from PyQt4.Qwt5 import toQImage as _toQImage
#def numpy2qimage(data):
#    # @NOTE: for Qwt5 < 5.2.0
#    # return toQImage(data.transpose())
#    return _toQImage(data)

import numpy as np
GRAY_COLORTABLE = [QtGui.QColor(i, i, i).rgb() for i in range(256)]


def _aligned(data, nbyes=4):
    h, w = data.shape

    fact = nbyes / data.itemsize
    shape = (h, np.ceil(w / float(fact)) * nbyes)
    if shape != data.shape:
        # build aligned matrix
        image = np.zeros(shape, data.dtype)
        image[:, 0:w] = data[:, 0:w]
    else:
        image = np.require(data, data.dtype, 'CO')  # 'CAO'
    return image


def numpy2qimage(data):
    '''Convert a numpy array into a QImage.

    .. note:: requires sip >= 4.7.5.

    '''

    colortable = None

    if data.dtype in (np.uint8, np.ubyte, np.byte):
        if data.ndim == 2:
            h, w = data.shape
            image = _aligned(data)
            format_ = QtGui.QImage.Format_Indexed8
            colortable = GRAY_COLORTABLE

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
        #format_ = QtGui.QImage.Format_ARGB32
        format_ = QtGui.QImage.Format_RGB32

    else:
        raise ValueError(
            'unable to convert data: shape=%s, dtype="%s"' % (
                data.shape, np.dtype(data.dtype)))

    result = QtGui.QImage(image.data, w, h, format_)
    result.ndarray = image
    if colortable:
        result.setColorTable(colortable)

    return result


# Resources helpers #########################################################
def getuifile(name, package=None):
    '''Return the ui file path.

    It is assumed that Qt UI files are located in the "ui" subfolfer of
    the package.

    .. seealso:: :func:`gsdview.utils.getresource`

    '''

    return utils.getresource(os.path.join('ui', name), package)


def getuiform(name, package=None):
    '''Return the ui form class.

    If it is available a pre-built python module the form class is
    imported from it (assuming that the module contains a single UI
    class having a name that starts with `Ui_`).

    If no pre-build python module is available than the form call is
    loaded directly from the ui file using the PyQt4.uic helper module.

    .. note:: in the pyside packege is used to provide bindings for Qt4
              then the uic module is not available and only pre-built
              modules are searched.
              When pyside is used an :exc:`ImportError` is raised
              if pre-built forms are not available.

    .. note:: like :func:`gsdview.qt4support.getuifile` this
              function assumes that pre-build form modules and Qt UI
              files are located in the "ui" subfolfer of the package.

    .. seealso:: :func:`gsdview.utils.getresource`,
                 :func:`gsdview.qt4support.getuifile`

    '''

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
        logging.debug('load "%s" form base class from pre-compiled python '
                      'module' % formname)
    except ImportError:
        uifile = getuifile(name + '.ui', package)
        FormClass, QtBaseClass = uic.loadUiType(uifile)
        logging.debug('load "%s" form class from ui file' % FormClass.__name__)

    return FormClass


def geticonfile(name, package=None):
    '''Return the icon file path.

    It is assumed that icon files are located in the "images" subfolder
    of the package.

    .. seealso:: :func:`gsdview.utils.getresource`

    '''

    return utils.getresource(os.path.join('images', name), package)


def geticon(name, package=None):
    '''Build and return requested icon.

    It is assumed that icon files are located in the "images" subfolder
    of the package.

    .. seealso:: :func:`gsdview.utils.getresource`

    '''

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
    #titleformat.setPointSze(12)

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

        #textformat = QtWidgets.QTextFormat()

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
            # QGraphicsViews alsa has a viewport method so they should be
            # trapped by the previous check
            srcsize = obj.sceneRect().toRect().size()
        else:
            srcsize = QtWidgets.QSize(800, 600)

        if ext in ('pdf', 'ps'):
            device = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
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
            #device.setViewBox(obj.sceneRect().toRect())
            #device.setTitle(obj.tr('Graphics Draw'))
            #device.setDescription(obj.tr('Qt SVG drawing.'))
        else:
            device = QtGui.QPixmap(srcsize)
            # @TODO: check
            device.fill(QtCore.Qt.white)

        painter = QtWidgets.QPainter()
        if painter.begin(device):
            #painter.setRenderHint(QtWidgets.QPainter.Antialiasing)
            obj.render(painter)
            painter.end()
            if hasattr(device, 'save'):
                device.save(filename)
        else:
            QtWidgets.QMessageBox.warning(
                parent,
                obj.tr('Warning'),
                obj.tr('Unable initialize painting device.'))
