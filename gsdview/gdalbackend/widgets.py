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


'''Widgets and dialogs for GSDView.'''

__author__   = '$Author$'
__date__     = '$Date$'
__revision__ = '$Revision$'

import os
import logging

import numpy
from osgeo import gdal
from PyQt4 import QtCore, QtGui

from gsdview import qt4support
from gsdview.widgets import get_filedialog, FileEntryWidget

from gsdview.gdalbackend import gdalsupport


GDALInfoWidgetBase = qt4support.getuiform('gdalinfo', __name__)
class GDALInfoWidget(QtGui.QWidget, GDALInfoWidgetBase):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(GDALInfoWidget, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

        # Context menu actions
        qt4support.setViewContextActions(self.gdalDriversTableWidget)

        # @TODO: check for available info in gdal 1.5 and above
        try:
            self.gdalReleaseNameValue.setText(gdal.VersionInfo('RELEASE_NAME'))
            self.gdalReleaseDateValue.setText(gdal.VersionInfo('RELEASE_DATE'))
        except AttributeError:
            self.gdalVersionGroupBox.hide()

        self.updateCacheInfo()
        self.setGdalDriversTab()

    def setGdalDriversTab(self):
        self.gdalDriversNumValue.setText(str(gdal.GetDriverCount()))

        tablewidget = self.gdalDriversTableWidget
        tablewidget.verticalHeader().hide()

        hheader = tablewidget.horizontalHeader()
        #hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)
        fontinfo = QtGui.QFontInfo(tablewidget.font())
        hheader.setDefaultSectionSize(10*fontinfo.pixelSize())

        sortingenabled = tablewidget.isSortingEnabled()
        tablewidget.setSortingEnabled(False)
        tablewidget.setRowCount(gdal.GetDriverCount())

        for row in range(gdal.GetDriverCount()):
            driver = gdal.GetDriver(row)
            # @TODO: check for available ingo in gdal 1.5 and above
            tablewidget.setItem(row, 0, QtGui.QTableWidgetItem(driver.ShortName))
            tablewidget.setItem(row, 1, QtGui.QTableWidgetItem(driver.LongName))
            tablewidget.setItem(row, 2, QtGui.QTableWidgetItem(driver.GetDescription()))
            tablewidget.setItem(row, 3, QtGui.QTableWidgetItem(str(driver.HelpTopic)))

            metadata = driver.GetMetadata()
            if metadata:
                tablewidget.setItem(row, 4, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_EXTENSION, ''))))
                tablewidget.setItem(row, 5, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_MIMETYPE, ''))))
                tablewidget.setItem(row, 6, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_CREATIONDATATYPES, ''))))

                data = metadata.pop(gdal.DMD_CREATIONOPTIONLIST, '')
                # @TODO: parse xml
                tableitem = QtGui.QTableWidgetItem(data)
                tableitem.setToolTip(data)
                tablewidget.setItem(row, 7, tableitem)

                metadata.pop(gdal.DMD_HELPTOPIC, '')
                metadata.pop(gdal.DMD_LONGNAME, '')

                metadatalist = ['%s=%s' % (k, v) for k, v in metadata.items()]
                tableitem = QtGui.QTableWidgetItem(', '.join(metadatalist))
                tableitem.setToolTip('\n'.join(metadatalist))
                tablewidget.setItem(row, 8, tableitem)

        tablewidget.setSortingEnabled(sortingenabled)
        tablewidget.sortItems(0, QtCore.Qt.AscendingOrder)

    def updateCacheInfo(self):
        self.gdalCacheMaxValue.setText('%.3f MB' % (gdal.GetCacheMax()/1024.**2))
        self.gdalCacheUsedValue.setText('%.3f MB' % (gdal.GetCacheUsed()/1024.**2))

    def showEvent(self, event):
        self.updateCacheInfo()
        QtGui.QWidget.showEvent(self, event)


GDALPreferencesPageBase = qt4support.getuiform('gdalpage', __name__)
class GDALPreferencesPage(QtGui.QWidget, GDALPreferencesPageBase):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(GDALPreferencesPage, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

        self.infoButton.setIcon(qt4support.geticon('info.svg', 'gsdview'))

        # Avoid promoted widgets
        DirectoryOnly = QtGui.QFileDialog.DirectoryOnly
        self.gdalDataDirEntryWidget = FileEntryWidget(mode=DirectoryOnly,
                                                      enabled=False)
        self.optionsGridLayout.addWidget(self.gdalDataDirEntryWidget, 1, 1)
        self.gdalDataCheckBox.toggled.connect(
                                    self.gdalDataDirEntryWidget.setEnabled)

        self.gdalDriverPathEntryWidget = FileEntryWidget(mode=DirectoryOnly,
                                                         enabled=False)
        self.optionsGridLayout.addWidget(self.gdalDriverPathEntryWidget, 3, 1)
        self.gdalDriverPathCheckBox.toggled.connect(
                                    self.gdalDriverPathEntryWidget.setEnabled)

        self.ogrDriverPathEntryWidget = FileEntryWidget(mode=DirectoryOnly,
                                                        enabled=False)
        self.optionsGridLayout.addWidget(self.ogrDriverPathEntryWidget, 4, 1)
        self.ogrDriverPathCheckBox.toggled.connect(
                                    self.ogrDriverPathEntryWidget.setEnabled)

        # info button
        self.infoButton.clicked.connect(self.showinfo)

        # Context menu actions
        qt4support.setViewContextActions(self.extraOptTableWidget)

        # standard options
        cachesize = gdal.GetCacheMax()
        self.cacheSpinBox.setValue(cachesize/1024**2)
        dialog = get_filedialog(self)
        for name in ('gdalDataDir', 'gdalDriverPath', 'ogrDriverPath'):
            widget = getattr(self, name + 'EntryWidget')
            widget.dialog = dialog
            widget.mode = QtGui.QFileDialog.Directory

        # extra options
        self._extraoptions = {}
        stdoptions = set(('GDAL_DATA', 'GDAL_SKIP', 'GDAL_DRIVER_PATH',
                          'OGR_DRIVER_PATH', 'GDAL_CACHEMAX', ''))

        extraoptions = gdalsupport.GDAL_CONFIG_OPTIONS.splitlines()
        extraoptions = [opt for opt in extraoptions if opt not in stdoptions]
        self.extraOptTableWidget.setRowCount(len(extraoptions))

        for row, key in enumerate(extraoptions):
            item = QtGui.QTableWidgetItem(key)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.extraOptTableWidget.setItem(row, 0, item)
            value = gdal.GetConfigOption(key, '')
            item = QtGui.QTableWidgetItem(value)
            self.extraOptTableWidget.setItem(row, 1, item)
            if value:
                self._extraoptions[key] = value

        hheader = self.extraOptTableWidget.horizontalHeader()
        hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)

    @QtCore.pyqtSlot()
    def showinfo(self):
        dialog = QtGui.QDialog(self)
        dialog.setWindowTitle(self.tr('GDAL info'))
        layout = QtGui.QVBoxLayout()
        layout.addWidget(GDALInfoWidget())

        buttonbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close,
                                           accepted=dialog.accept,
                                           rejected=dialog.reject)
        layout.addWidget(buttonbox)

        dialog.setLayout(layout)
        buttonbox.setFocus()
        dialog.exec_()

    def load(self, settings):
        settings.beginGroup('gdal')
        try:

            # cache size
            cachesize = settings.value('GDAL_CACHEMAX')
            if cachesize is not None:
                self.cacheCheckBox.setChecked(True)
                self.cacheSpinBox.setValue(int(cachesize)/1024**2)
            else:
                # show the current value and disable the control
                cachesize = gdal.GetCacheMax()
                self.cacheSpinBox.setValue(cachesize/1024**2)
                self.cacheCheckBox.setChecked(False)

            # GDAL data dir
            datadir = settings.value('GDAL_DATA')
            if datadir:
                self.gdalDataCheckBox.setChecked(True)
                self.gdalDataDirEntryWidget.setText(datadir)
            else:
                # show the current value and disable the control
                datadir = gdal.GetConfigOption('GDAL_DATA', '')
                self.gdalDataDirEntryWidget.setText(datadir)
                self.gdalDataCheckBox.setChecked(False)

            # GDAL_SKIP
            gdalskip = settings.value('GDAL_SKIP')
            if gdalskip:
                self.skipCheckBox.setChecked(True)
                self.skipLineEdit.setText(gdalskip)
            else:
                # show the current value and disable the control
                gdalskip = gdal.GetConfigOption('GDAL_SKIP', '')
                self.skipLineEdit.setText(gdalskip)
                self.skipCheckBox.setChecked(False)

            # GDAL driver path
            gdaldriverpath = settings.value('GDAL_DRIVER_PATH')
            if gdaldriverpath:
                self.gdalDriverPathCheckBox.setChecked(True)
                self.gdalDriverPathEntryWidget.setText(gdaldriverpath)
            else:
                # show the current value and disable the control
                gdaldriverpath = gdal.GetConfigOption('GDAL_DRIVER_PATH', '')
                self.gdalDriverPathEntryWidget.setText(gdaldriverpath)
                self.gdalDriverPathCheckBox.setChecked(False)

            # OGR driver path
            ogrdriverpath = settings.value('OGR_DRIVER_PATH')
            if ogrdriverpath:
                self.ogrDriverPathCheckBox.setChecked(True)
                self.ogrDriverPathEntryWidget.setText(ogrdriverpath)
            else:
                # show the current value and disable the control
                ogrdriverpath = gdal.GetConfigOption('OGR_DRIVER_PATH', '')
                self.ogrDriverPathEntryWidget.setText(ogrdriverpath)
                self.ogrDriverPathCheckBox.setChecked(False)

            # @TODO: complete
            #~ gdal.GetConfigOption('CPL_DEBUG', 'OFF')
            #~ gdal.GetConfigOption('GDAL_PAM_ENABLED', "NULL")

            # extra options
            # @TODO

        finally:
            settings.endGroup()

    def save(self, settings):
        settings.beginGroup('gdal')
        try:

            # cache
            if self.cacheCheckBox.isChecked():
                value = self.cacheSpinBox.value() * 1024**2
                settings.setValue('GDAL_CACHEMAX', value)
            else:
                settings.remove('GDAL_CACHEMAX')

            # GDAL data dir
            if self.gdalDataCheckBox.isChecked():
                value = self.gdalDataDirEntryWidget.text()
                settings.setValue('GDAL_DATA', value)
            else:
                settings.remove('GDAL_DATA')

            # GDAL_SKIP
            if self.skipCheckBox.isChecked():
                settings.setValue('GDAL_SKIP', self.skipLineEdit.text())
            else:
                settings.remove('GDAL_SKIP')

            # GDAL driver path
            if self.gdalDriverPathCheckBox.isChecked():
                value = self.gdalDriverPathEntryWidget.text()
                settings.setValue('GDAL_DRIVER_PATH', value)
            else:
                settings.remove('GDAL_DRIVER_PATH')

            # OGR driver path
            if self.ogrDriverPathCheckBox.isChecked():
                value = self.ogrDriverPathEntryWidget.text()
                settings.setValue('OGR_DRIVER_PATH', value)
            else:
                settings.remove('OGR_DRIVER_PATH')

            # @TODO: complete
            #~ gdal.GetConfigOption('CPL_DEBUG', 'OFF')
            #~ gdal.GetConfigOption('GDAL_PAM_ENABLED', "NULL")

            # extra options
            # @TODO
        finally:
            settings.endGroup()


class BackendPreferencesPage(GDALPreferencesPage):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(BackendPreferencesPage, self).__init__(parent, flags, **kwargs)
        #self.setupUi(self)

        # GDAL backend
        msg = 'Show overview items in the tree view.'
        tip = msg + "\nNOTE: this setting doesn't affects items already open."
        checkbox = QtGui.QCheckBox(self.tr(msg), toolTip=self.tr(tip))
        self.showOverviewCheckbox = checkbox

        layout = QtGui.QVBoxLayout()
        layout.addWidget(checkbox)
        #~ layout.addSpacerItem(QtGui.QSpacerItem(0, 20))

        self.groupbox = QtGui.QGroupBox(self.tr('GDAL Backend Preferences'))
        self.groupbox.setLayout(layout)
        self.verticalLayout.insertWidget(1, self.groupbox)

    def load(self, settings):
        settings.beginGroup('gdalbackend')
        try:
            # show overviews in the treeview
            value = settings.value('visible_overview_items')
            if value is not None:
                # @COMPATIBILITY: presumably a bug in PyQt4 (4.7.2)
                if isinstance(value, basestring):
                    value = True if value in ('true', 'True') else False

                self.showOverviewCheckbox.setChecked(value)
        finally:
            settings.endGroup()

        super(BackendPreferencesPage, self).load(settings)

    def save(self, settings):
        settings.beginGroup('gdalbackend')
        try:
            # show overviews in the treeview
            value = self.showOverviewCheckbox.isChecked()
            settings.setValue('visible_overview_items', bool(value))
        finally:
            settings.endGroup()

        super(BackendPreferencesPage, self).save(settings)


OverviewWidgetBase = qt4support.getuiform('overview', __name__)
class OverviewWidget(QtGui.QWidget, OverviewWidgetBase):
    '''Widget for overview management.

    Display existing overview levels and allow to to sibmit overview
    compitation requests.

    :SIGNALS:

        * :attr:`overviewComputationRequest`

    '''

    #: SIGNAL: it is emitted when a time expensive computation of overviews
    #: is required
    #:
    #: :C++ signature: `void overviewComputationRequest()`
    overviewComputationRequest = QtCore.pyqtSignal()

    def __init__(self, item=None, parent=None, flags=QtCore.Qt.Widget,
                 **kwargs):
        super(OverviewWidget, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

        # @COMPATIBILITY: GDAL >= 1.7.0
        if gdal.VersionInfo() < '1700':
            index = self.resamplingMethodComboBox.findText('cubic')
            self.resamplingMethodComboBox.removeItem(index)

        # @COMPATIBILITY: GDAL >= 1.7.0
        if not hasattr(gdal.Band, 'HasArbitraryOverviews'):
            self.hasArbitraryOverviewsLabel.hide()
            self.hasArbitraryOverviewsValue.hide()

        model = QtGui.QStandardItemModel(self)
        model.setColumnCount(3)
        model.itemChanged.connect(self._updateStartButton)
        self.ovrTreeView.setModel(model)

        self._readonly = False
        self._item = None

        self.recomputeCheckBox.toggled.connect(self._updateStartButton)
        self.startButton.clicked.connect(self.overviewComputationRequest)

        if item:
            self.setItem(item)
        else:
            self.reset()

    def readOnly(self):
        return self._readonly

    def setReadOnly(self, readonly=True):
        self._readonly = readonly
        visible = bool(not readonly)
        self.optionsGroupBox.setVisible(visible)
        self.addLevelButton.setVisible(visible)
        self.addLevelSpinBox.setVisible(visible)
        self.ovrTreeView.setEnabled(visible)

    def reset(self):
        self.ovrTreeView.model().clear()

        self.overviewCountValue.setText('0')
        self.hasArbitraryOverviewsValue.setText('')
        self.fullSizeValue.setText('')

        self.resamplingMethodComboBox.setCurrentIndex(2)
        self.compressionComboBox.setCurrentIndex(0)
        self.photointComboBox.setCurrentIndex(0)
        self.interleavingComboBox.setCurrentIndex(0)
        self.bigtiffComboBox.setCurrentIndex(0)

        self.readonlyCheckBox.setChecked(False)
        self.rrdCheckBox.setChecked(False)
        self.recomputeCheckBox.setChecked(False)

        self.startButton.setEnabled(False)
        self.addLevelSpinBox.setEnabled(False)
        self.addLevelButton.setEnabled(False)

        if self._item:
            self.addLevelButton.clicked.disconnect(self.addLevel)

        self._item = None

    def _addLevel(self, level, xsize, ysize, checked=QtCore.Qt.Unchecked,
                  locked=False):
        model = self.ovrTreeView.model()

        check = QtGui.QStandardItem()
        check.setCheckable(True)
        check.setCheckState(checked)

        ovrfact = QtGui.QStandardItem()
        ovrfact.setData(level, QtCore.Qt.DisplayRole)

        size = QtGui.QStandardItem('%dx%d' % (ysize, xsize))

        model.appendRow([check, ovrfact, size])

        if locked:
            #model.item(row, 0).setEnabled(False)
            #model.item(row, 0).setEditable(False) # doesn't work
            check.setEnabled(False)
            font = ovrfact.font()
            font.setBold(True)
            check.setFont(font)
            ovrfact.setFont(font)
            size.setFont(font)

    def setItem(self, item):
        self.reset()
        if item is None:
            return

        assert hasattr(item, 'GetOverviewCount')

        if gdal.DataTypeIsComplex(item.DataType):
            index = self.resamplingMethodComboBox.findText('average_magphase')
            print 'index', index
            if index >= 0:
                self.resamplingMethodComboBox.setCurrentIndex(index)

        ovrcount = item.GetOverviewCount()

        self.overviewCountValue.setText(str(ovrcount))
        self.fullSizeValue.setText('%dx%d' % (item.YSize, item.XSize))
        # @COMPATIBILITY: GDAL >= 1.7.0
        if hasattr(gdal.Band, 'HasArbitraryOverviews'):
            self.hasArbitraryOverviewsValue.setText(
                                            str(item.HasArbitraryOverviews()))

        view = self.ovrTreeView

        # Add existing overviews
        levels = gdalsupport.ovrLevels(item)
        for index in range(ovrcount):
            ovr = item.GetOverview(index)
            self._addLevel(levels[index], ovr.XSize, ovr.YSize,
                           QtCore.Qt.Checked, True)

        if not self._readonly:
            # Add powers of two
            xexp = int(numpy.log2(item.XSize))
            yexp = int(numpy.log2(item.YSize))
            mexexp = min(xexp, yexp)
            mexexp = max(mexexp-4, 1)
            for exp_ in range(1, mexexp):
                level = 2**exp_
                if level in levels:
                    continue
                xsize = int(item.XSize + level - 1) // level
                ysize = int(item.YSize + level - 1) // level
                self._addLevel(level, xsize, ysize)

        view.header().resizeSections(QtGui.QHeaderView.ResizeToContents)
        view.sortByColumn(1, QtCore.Qt.AscendingOrder)

        self.addLevelSpinBox.setEnabled(True)
        self.addLevelButton.setEnabled(True)

        self.addLevelButton.clicked.connect(self.addLevel)

        self._item = item

        self._updateStartButton()

    def _listedLevels(self):
        model = self.ovrTreeView.model()
        levels = []
        for index in range(model.rowCount()):
            item = model.item(index, 1)
            levels.append(int(item.text()))

        return levels

    def _checkedLevels(self):
        model = self.ovrTreeView.model()
        levels = []
        for index in range(model.rowCount()):
            checkitem = model.item(index, 0)
            if checkitem.checkState() == QtCore.Qt.Checked:
                item = model.item(index, 1)
                levels.append(int(item.text()))

        return levels

    def _newLevels(self):
        model = self.ovrTreeView.model()
        levels = []
        for index in range(model.rowCount()):
            checkitem = model.item(index, 0)
            if (checkitem.checkState() == QtCore.Qt.Checked and
                                                        checkitem.isEnabled()):
                item = model.item(index, 1)
                levels.append(int(item.text()))

        return levels

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(int)
    def addLevel(self, level=None, xsize=None, ysize=None, checked=False):
        if level is None:
            level = self.addLevelSpinBox.value()

        if level in self._listedLevels():
            return

        if xsize is None:
            if self._item is None:
                raise ValueError('no reference band is set: '
                                 'xsize and ysize have to be provided.')
            xsize = int(self._item.XSize + level - 1) // level

        if ysize is None:
            if self._item is None:
                raise ValueError('no reference band is set: '
                                 'xsize and ysize have to be provided.')
            ysize = int(self._item.YSize + level - 1) // level

        if checked:
            checked = QtCore.Qt.Checked
        else:
            checked = QtCore.Qt.Unchecked

        self._addLevel(level, xsize, ysize, checked)

        view = self.ovrTreeView
        view.header().resizeSections(QtGui.QHeaderView.ResizeToContents)
        view.sortByColumn(1, QtCore.Qt.AscendingOrder)

        self._updateStartButton()

    @QtCore.pyqtSlot()
    def _updateStartButton(self):
        if self.recomputeCheckBox.isChecked() or self._newLevels():
            self.startButton.setEnabled(True)
        else:
            self.startButton.setEnabled(False)

    def optionlist(self):
        args = []

        if self.rrdCheckBox.isChecked():
            args.extend(('--config', 'USE_RRD', 'YES'))
        else:
            if self.compressionComboBox.currentText() not in ('DEFAULT', 'None'):
                args.extend(('--config', 'COMPRESS_OVERVIEW',
                             self.compressionComboBox.currentText()))

            if self.photointComboBox.currentText() not in ('DEFAULT', ''):
                args.extend(('--config', 'PHOTOMETRIC_OVERVIEW',
                             self.photointComboBox.currentText()))

            if self.interleavingComboBox.currentText() != 'DEFAULT':
                args.extend(('--config', 'INTERLEAVE_OVERVIEW',
                             self.interleavingComboBox.currentText()))

            if self.bigtiffComboBox.currentText() != 'DEFAULT':
                args.extend(('--config', 'BIGTIFF_OVERVIEW',
                             self.bigtiffComboBox.currentText()))

        if self.readonlyCheckBox.isChecked():
            args.append('-ro')
        if self.resamplingMethodComboBox.currentText() != 'DEFAULT':
            args.extend(('-r', self.resamplingMethodComboBox.currentText()))

        args = map(str, args)

        return args

    def levels(self):
        if self.recomputeCheckBox.isChecked():
            levels = self._checkedLevels()
        else:
            levels = self._newLevels()

        return levels


class SpecialOverviewWidget(OverviewWidget):
    '''An overview widget that always performs overview recomputation.

    .. seealso:: :class:`OverviewWidget`

    '''

    def reset(self):
        super(SpecialOverviewWidget, self).reset()
        self.recomputeCheckBox.setChecked(True)
        self.recomputeCheckBox.hide()
        self.recomputeLabel.hide()

    def levels(self):
        if self._newLevels():
            levels = self._checkedLevels()
        else:
            levels = []

        return levels

    @QtCore.pyqtSlot()
    def _updateStartButton(self):
        if self._newLevels():
            self.startButton.setEnabled(True)
        else:
            self.startButton.setEnabled(False)


class OverviewDialog(QtGui.QDialog):
    '''Dialog for overview management.

    Display existing overview levels and allow to to sibmit overview
    compitation requests.

    :SIGNALS:

        * :attr:`overviewComputationRequest`

    '''

    #: SIGNAL: it is emitted when a time expensive computation of overviews
    #: is required
    #:
    #: :C++ signature: `void overviewComputationRequest(PyQt_PyObject)`
    overviewComputationRequest = QtCore.pyqtSignal('PyQt_PyObject')


    def __init__(self, item=None, parent=None, flags=QtCore.Qt.Widget, **kargs):
        super(OverviewDialog, self).__init__(parent, flags)
        self.setWindowTitle(self.tr('Overview computation'))

        label = QtGui.QLabel(self.tr('Dataset:'))

        #: dataset label
        self.description = QtGui.QLineEdit()
        self.description.setReadOnly(True)

        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(label)
        hlayout.addWidget(self.description)

        #: overview widget
        self.overviewWidget = SpecialOverviewWidget()

        buttonbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        buttonbox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(hlayout)
        layout.addWidget(self.overviewWidget)
        layout.addWidget(buttonbox)

        self.setLayout(layout)

        self._item = None
        if item:
            self.setItem(item)
        else:
            self.reset()

    def _emitComputationRequest(self):
        assert self._item, 'item not set'
        self.overviewComputationRequest.emit(self._item)

    def reset(self):
        self.overviewWidget.reset()
        self.description.setText('')
        if self._item:
            self.overviewWidget.overviewComputationRequest.disconnect(
                                                self._emitComputationRequest)
        self._item = None

    def setItem(self, item):
        if item:
            if not hasattr(item, 'GetRasterBand'):
                band = item
                while not hasattr(item, 'GetRasterBand'):
                    band = item
                    item = item.parent()
            else:
                band = item.GetRasterBand(1)
            self.overviewWidget.setItem(band)
            self._item = item
            self.description.setText(self._item.GetDescription())
            self.description.setCursorPosition(0)
            self.overviewWidget.overviewComputationRequest.connect(
                                                self._emitComputationRequest)
        else:
            self.reset()

    def updateOverviewInfo(self):
        if self._item:
            self.setItem(self._item)
        else:
            self.reset()


class MajorObjectInfoDialog(QtGui.QDialog):
    def __init__(self, gdalobj, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(MajorObjectInfoDialog, self).__init__(parent, flags, **kwargs)
        if hasattr(self, 'setupUi'):
            self.setupUi(self)

        self._obj = gdalobj

        if hasattr(self, 'domainComboBox'):
            self.domainComboBox.activated[str].connect(self.updateMetadata)

        # Contect menu
        qt4support.setViewContextActions(self.metadataTableWidget)

        # Init tabs
        self.updateMetadata()

    def _checkgdalobj(self):
        if not self._obj:
            raise ValueError('no GDAL object attached (self._obj is None).')

    @staticmethod
    def _setMetadata(tablewidget, metadatalist):
        qt4support.clearTable(tablewidget)
        if not metadatalist:
            return

        tablewidget.setRowCount(len(metadatalist))
        sortingenabled = tablewidget.isSortingEnabled()
        tablewidget.setSortingEnabled(False)

        for row, data in enumerate(metadatalist):
            name, value = data.split('=', 1)
            tablewidget.setItem(row, 0, QtGui.QTableWidgetItem(name))
            tablewidget.setItem(row, 1, QtGui.QTableWidgetItem(value))

        # Fix table header behaviour
        tablewidget.setSortingEnabled(sortingenabled)

    def resetMetadata(self, domain=''):
        self.metadataNumValue.setText('0')
        qt4support.clearTable(self.metadataTableWidget)

    def setMetadata(self, metadatalist):
        self.metadataNumValue.setText(str(len(metadatalist)))
        self._setMetadata(self.metadataTableWidget, metadatalist)

    @QtCore.pyqtSlot(str)
    def updateMetadata(self, domain=''):
        if self._obj is not None:
            # @COMPATIBILITY: presumably a bug in PyQt4 4.7.2
            domain = str(domain)    # it could be a "char const *"
            metadatalist = self._obj.GetMetadata_List(domain)

        if metadatalist:
            self.setMetadata(metadatalist)
        else:
            self.resetMetadata()

    def reset(self):
        self.resetMetadata()

    def update(self):
        if self._obj is not None:
            self.updateMetadata()
        else:
            self.reset()


def _setupImageStructureInfo(widget, metadata):
    widget.compressionValue.setText(metadata.get('COMPRESSION', ''))
    widget.nbitsValue.setText(metadata.get('NBITS', ''))
    widget.interleaveValue.setText(metadata.get('INTERLEAVE', ''))
    widget.pixelTypeValue.setText(metadata.get('PIXELTYPE', ''))


HistogramConfigDialogBase = qt4support.getuiform('histoconfig', __name__)
class HistogramConfigDialog(QtGui.QDialog, HistogramConfigDialogBase):
    def __init__(self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(HistogramConfigDialog, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

        # Make it not resizable
        w = self.maximumSize().width()
        h = self.size().height()
        self.setMaximumSize(w, h)

        # Colors
        self._default_palette = self.minSpinBox.palette()
        self._error_palette = QtGui.QPalette(self._default_palette)

        color = QtGui.QColor(QtCore.Qt.red)
        self._error_palette.setColor(QtGui.QPalette.Text, color)
        color.setAlpha(50)
        self._error_palette.setColor(QtGui.QPalette.Base, color)

        self.minSpinBox.editingFinished.connect(self.validate)
        self.maxSpinBox.editingFinished.connect(self.validate)

    @QtCore.pyqtSlot()
    def validate(self):
        if self.minSpinBox.value() >= self.maxSpinBox.value():
            self.minSpinBox.lineEdit().setPalette(self._error_palette)
            self.maxSpinBox.lineEdit().setPalette(self._error_palette)
            return False
        self.minSpinBox.lineEdit().setPalette(self._default_palette)
        self.maxSpinBox.lineEdit().setPalette(self._default_palette)
        return True

    def setLimits(self, dtype):
        vmin = -2**15 - 0.5
        vmax = 2**16 - 0.5
        if dtype in (numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64):
            # Unsigned
            vmin = -0.5
            if dtype == numpy.uint8:
                vmax = 255.5
            else:
                vmax = 2**16 - 0.5
        elif dtype == numpy.int8:
            vmin = -128.5
            vmax = 127.5
        elif dtype == numpy.int16:
            vmax = 2**15 + 0.5

        self.minSpinBox.setMinimum(vmin)
        self.minSpinBox.setMaximum(vmax)
        self.maxSpinBox.setMinimum(vmin)
        self.maxSpinBox.setMaximum(vmax)


BandInfoDialogBase = qt4support.getuiform('banddialog', __name__)
class BandInfoDialog(MajorObjectInfoDialog, BandInfoDialogBase):
    '''Info dialog for GDAL raster bands.

    :SIGNALS:

        * :attr:`statsComputationRequest`
        * :attr:`histogramComputationRequest`
        * :attr:`overviewComputationRequest`

    '''

    #: SIGNAL: it is emitted when a time expensive computation of statistics
    #: is required
    #:
    #: :C++ signature: `void statsComputationRequest(PyQt_PyObject)`
    statsComputationRequest = QtCore.pyqtSignal('PyQt_PyObject')

    #: SIGNAL: it is emitted when a time expensive computation of an histogram
    #: is required
    #:
    #: :C++ signature: `void histogramComputationRequest(PyQt_PyObject)`
    histogramComputationRequest = QtCore.pyqtSignal('PyQt_PyObject')
    # @TODO: check
    #self.emit(QtCore.SIGNAL(
    #                'histogramComputationRequest(PyQt_PyObject, int, int, int)'),
    #                band, hmin, nmax, nbuckets)

    #: SIGNAL: it is emitted when overview computation is required
    #:
    #: :C++ signature: `void overviewComputationRequest()`
    overviewComputationRequest = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self, band=None, parent=None, flags=QtCore.Qt.Widget,
                 **kwargs):
        super(BandInfoDialog, self).__init__(band, parent, flags, **kwargs)

        # Set tab icons
        geticon = qt4support.geticon
        self.tabWidget.setTabIcon(0, geticon('info.svg', 'gsdview'))
        self.tabWidget.setTabIcon(1, geticon('metadata.svg', __name__))
        self.tabWidget.setTabIcon(2, geticon('statistics.svg', __name__))
        self.tabWidget.setTabIcon(3, geticon('color.svg', __name__))

        # Overview page

        #: overview widget
        self.overviewWidget = SpecialOverviewWidget(parent=self)
        self.overviewWidget.addLevelButton.setIcon(geticon('add.svg', 'gsdview'))
        self.tabWidget.addTab(self.overviewWidget,
                              geticon('overview.svg', __name__),
                              self.tr('Overviews'))

        # Context menu actions
        qt4support.setViewContextActions(self.histogramTableWidget)
        qt4support.setViewContextActions(self.colorTableWidget)

        if not hasattr(gdal.Band, 'GetDefaultHistogram'):
            self.histogramGroupBox.hide()
            self.statisticsVerticalLayout.addStretch()

        # @TODO: remove.
        # Tempoorary disable the button for custom histogram configuration
        self.customHistogramCheckBox.setEnabled(False)

        # Tabs
        if band:
            self._connect_signals()
            self.update()

    def _connect_signals(self):
        # @TODO: check
        self.computeStatsButton.clicked.connect(self._computeStats)
        self.approxStatsCheckBox.toggled.connect(
                                        self.computeStatsButton.setEnabled)
        # @TODO: check
        self.computeHistogramButton.clicked.connect(self._computeHistogram)
        self.customHistogramCheckBox.toggled.connect(
                                        self.computeHistogramButton.setEnabled)

        self.overviewWidget.overviewComputationRequest.connect(
                                                        self._computeOverviews)

    def _disconnect_signals(self):
        # @TODO: check
        self.computeStatsButton.clicked.disconnect(self._computeStats)
        self.approxStatsCheckBox.toggled.disconnect(
                                        self.computeStatsButton.setEnabled)
        # @TODO: check
        self.computeHistogramButton.clicked.dosconnect(self._computeHistogram)
        self.customHistogramCheckBox.toggled.disconnect(
                                        self.computeHistogramButton.setEnabled)

        self.overviewWidget.overviewComputationRequest.disconnect(
                                                        self._computeOverviews)

    @property
    def band(self):
        return self._obj

    def setBand(self, band):
        self._obj = band
        if band is not None:
            # @TODO: check type
            self._connect_signals()
            self.update()
        else:
            self._disconnect_signals()
            self.reset()

    def reset(self):
        super(BandInfoDialog, self).reset()

        self.resetInfoTab()
        self.resetStatistics()
        self.resetHistogram()
        self.resetColorTable()
        self.overviewWidget.reset()

    def update(self):
        super(BandInfoDialog, self).update()

        self.updateInfoTab()
        self.updateStatistics()
        self.updateHistogram()
        self.updateColorTable()
        self.updateOverviewInfo()

    def resetImageStructure(self):
        _setupImageStructureInfo(self, {})

    def setImageStructure(self, metadata):
        if metadata is None:
            self.resetImageStructure()

        _setupImageStructureInfo(self, metadata)

    def updateImageStructure(self):
        if self.band is not None:
            metadata = self.band.GetMetadata('IMAGE_STRUCTURE')
        else:
            metadata = {}

        self.setImageStructure(metadata)

    def resetInfoTab(self):
        # Info
        self.descriptionValue.setText('')
        self.bandNumberValue.setText('')
        self.colorInterpretationValue.setText('')
        self.overviewCountValue.setText('0')
        self.hasArbitraryOverviewsValue.setText('')

        # @TODO: checksum
        #~ band.Checksum                   ??

        # Data
        self.xSizeValue.setText('0')
        self.ySizeValue.setText('0')
        self.blockSizeValue.setText('0')
        self.noDataValue.setText('')

        self.dataTypeValue.setText('')
        self.unitTypeValue.setText('')
        self.offsetValue.setText('0')
        self.scaleValue.setText('1')

        self.resetImageStructure()

    def updateInfoTab(self):
        if self.band is None:
            self.resetInfoTab()
            return

        band = self.band

        # Color interpretaion
        colorint = band.GetRasterColorInterpretation()
        colorint = gdal.GetColorInterpretationName(colorint)

        # Info
        self.descriptionValue.setText(band.GetDescription().strip())
        bandno = band.GetBand()
        self.bandNumberValue.setText(str(bandno))
        self.colorInterpretationValue.setText(colorint)
        self.overviewCountValue.setText(str(band.GetOverviewCount()))

        # @COMPATIBILITY: HasArbitraryOverviews requires GDAL >= 1.7
        if hasattr(gdal.Band, 'HasArbitraryOverviews'):
            hasArbitaryOvr = band.HasArbitraryOverviews()
            self.hasArbitraryOverviewsValue.setText(str(hasArbitaryOvr))
        else:
            self.hasArbitraryOverviewsValue.setText('')

        # @TODO: checksum
        #~ band.Checksum                   ??

        # Data
        self.xSizeValue.setText(str(band.XSize))
        self.ySizeValue.setText(str(band.YSize))
        self.blockSizeValue.setText(str(band.GetBlockSize()))
        self.noDataValue.setText(str(band.GetNoDataValue()))

        self.dataTypeValue.setText(gdal.GetDataTypeName(band.DataType))

        # @COMPATIBILITY: GetUnitType requires GDAL >= 1.7
        if hasattr(gdal.Band, 'GetUnitType'):
            unitType = band.GetUnitType()
            self.unitTypeValue.setText(str(unitType))
        else:
            self.unitTypeValue.setText('')
        self.offsetValue.setText(str(band.GetOffset()))
        self.scaleValue.setText(str(band.GetScale()))

        self.updateImageStructure()

    def resetStatistics(self):
        '''Reset statistics.'''

        value = self.tr('Not computed')
        self.minimumValue.setText(value)
        self.maximumValue.setText(value)
        self.meanValue.setText(value)
        self.stdValue.setText(value)

    def setStatistics(self, vmin, vmax, mean, stddev):
        self.minimumValue.setText(str(vmin))
        self.maximumValue.setText(str(vmax))
        self.meanValue.setText(str(mean))
        self.stdValue.setText(str(stddev))

    @QtCore.pyqtSlot()
    @qt4support.overrideCursor
    def updateStatistics(self):
        if self.band is None:
            self.resetStatistics()
            return

        # @NOTE: the band.GetStatistics method called with the second argument
        #        set to False (no image rescanning) has been fixed in
        #        r19666_ (1.6 branch) and r19665_ (1.7 branch)
        #        see `ticket #3572` on `GDAL Trac`_.
        #
        # .. _r19666: http://trac.osgeo.org/gdal/changeset/19666
        # .. _r19665: http://trac.osgeo.org/gdal/changeset/19665
        # .. _`ticket #3572`: http://trac.osgeo.org/gdal/ticket/3572
        # .. _`GDAL Trac`: http://trac.osgeo.org/gdal

        if gdalsupport.hasFastStats(self.band):
            vmin, vmax, mean, stddev = self.band.GetStatistics(True, True)
            self.setStatistics(vmin, vmax, mean, stddev)
            self.computeStatsButton.setEnabled(False)
        else:
            self.resetStatistics()

    def resetHistogram(self):
        tablewidget = self.histogramTableWidget
        self.numberOfClassesValue.setText('0')
        qt4support.clearTable(tablewidget)

    def setHistogram(self, vmin, vmax, nbuckets, hist):
        self.numberOfClassesValue.setText(str(nbuckets))

        w = (vmax - vmin) / nbuckets

        tablewidget = self.histogramTableWidget
        tablewidget.setRowCount(nbuckets)

        for row in range(nbuckets):
            start = vmin + row * w
            stop = start + w
            tablewidget.setItem(row, 0,
                                QtGui.QTableWidgetItem(str(start)))
            tablewidget.setItem(row, 1,
                                QtGui.QTableWidgetItem(str(stop)))
            tablewidget.setItem(row, 2,
                                QtGui.QTableWidgetItem(str(hist[row])))

        # @TODO: plotting

    def updateHistogram(self):
        if self.band is None:
            self.resetHistogram()

        if gdal.DataTypeIsComplex(self.band.DataType):
            self.computeHistogramButton.setEnabled(False)
            return
        else:
            self.computeHistogramButton.setEnabled(True)

        if gdal.VersionInfo() < '1700':
            # @TODO: check
            if self.computeHistogramButton.isEnabled() == False:
                # Histogram already computed
                hist = self.band.GetDefaultHistogram()
            else:
                hist = None
        else:
            # @WARNING: causes a crash in GDAL < 1.7.0 (r18405)
            # @SEEALSO: http://trac.osgeo.org/gdal/ticket/3304
            hist = self.band.GetDefaultHistogram(force=False)

        if hist:
            self.setHistogram(*hist)
            self.computeHistogramButton.setEnabled(False)
        else:
            self.resetHistogram()

    @staticmethod
    def _rgb2qcolor(red, green, blue, alpha=255):
        qcolor = QtGui.QColor()
        qcolor.setRgb(red, green, blue, alpha)
        return qcolor

    @staticmethod
    def _gray2qcolor(gray):
        qcolor = QtGui.QColor()
        qcolor.setRgb(gray, gray, gray)
        return qcolor

    @staticmethod
    def _cmyk2qcolor(cyan, magenta, yellow, black=255):
        qcolor = QtGui.QColor()
        qcolor.setCmyk(cyan, magenta, yellow, black)
        return qcolor

    @staticmethod
    def _hsv2qcolor(hue, lightness, saturation, a=0):
        qcolor = QtGui.QColor()
        qcolor.setHsv(hue, lightness, saturation, a)
        return qcolor

    def resetColorTable(self):
        self.ctInterpretationValue.setText('')
        self.colorsNumberValue.setText('')
        qt4support.clearTable(self.colorTableWidget)

    def setColorTable(self, colortable):
        if colortable is None:
            self.resetColorTable()
            return

        ncolors = colortable.GetCount()
        colorint = colortable.GetPaletteInterpretation()

        label = gdalsupport.colorinterpretations[colorint]['label']
        self.ctInterpretationValue.setText(label)
        self.colorsNumberValue.setText(str(ncolors))

        mapping = gdalsupport.colorinterpretations[colorint]['inverse']
        labels = [mapping[k] for k in sorted(mapping.keys())]
        labels.append('Color')

        tablewidget = self.colorTableWidget

        tablewidget.setRowCount(ncolors)
        tablewidget.setColumnCount(len(labels))

        tablewidget.setHorizontalHeaderLabels(labels)
        tablewidget.setVerticalHeaderLabels([str(i) for i in range(ncolors)])

        colors = gdalsupport.colortable2numpy(colortable)

        if colorint == gdal.GPI_RGB:
            func = BandInfoDialog._rgb2qcolor
        elif colorint == gdal.GPI_Gray:
            func = BandInfoDialog._gray2qcolor
        elif colorint == gdal.GPI_CMYK:
            func = BandInfoDialog._cmyk2qcolor
        elif colorint == gdal.GPI_HLS:
            func = BandInfoDialog._hsv2qcolor
        else:
            raise ValueError('invalid color intepretatin: "%s"' % colorint)

        brush = QtGui.QBrush()
        brush.setStyle(QtCore.Qt.SolidPattern)

        for row, color in enumerate(colors):
            for chan, value in enumerate(color):
                tablewidget.setItem(row, chan,
                                    QtGui.QTableWidgetItem(str(value)))
            qcolor = func(*color)
            brush.setColor(qcolor)
            item = QtGui.QTableWidgetItem()
            item.setBackground(brush)
            tablewidget.setItem(row, chan+1, item)

        hheader = tablewidget.horizontalHeader()
        hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)

    def updateColorTable(self):
        if self.band is None:
            self.resetColorTable()
        else:
            colortable = self.band.GetRasterColorTable()

            if colortable is None:
                # Disable the color table tab
                self.tabWidget.setTabEnabled(3, False)
            else:
                self.tabWidget.setTabEnabled(3, True)
                self.setColorTable(colortable)

    def updateOverviewInfo(self):
        if self.band is not None:
            self.overviewWidget.setItem(self.band)
        else:
            self.overviewWidget.reset()

    # @TODO: check
    @QtCore.pyqtSlot()
    def _computeStats(self):
        self._checkgdalobj()
        self.statsComputationRequest.emit(self.band)

        #~ logging.info('start statistics computation')

        #~ band = self.band
        #~ approx = self.approxStatsCheckBox.isChecked()
        #~ band.ComputeStatistics(approx)#, callback=None, callback_data=None)

        #~ # @COMPATIBILITY: workaround fo flagging statistics as computed
        #~ # @SEALSO: ticket #3572 on GDAL Trac
        #~ stats = band.GetStatistics(True, True)
        #~ for name, value in zip(gdalsupport.GDAL_STATS_KEYS, stats):
            #~ band.SetMetadataItem(name, str(value))

        #~ # @TODO: check
        #~ #if self.domainComboBox.currentText() == '':
        #~ #    self.updateMetadata()
        #~ logging.debug('statistics computation completed')
        #~ self.updateStatistics()

    # @TODO: check
    @QtCore.pyqtSlot()
    def _computeHistogram(self):
        self._checkgdalobj()
        self.histogramComputationRequest.emit(self.band)

        #~ band = self.band
        #~ approx = self.approxStatsCheckBox.isChecked()
        #~ if self.customHistogramCheckBox.isChecked():
            #~ dialog = HistogramConfigDialog(self)

            #~ # @COMPATIBILITY: bug in GDAL 1.6.x line
            #~ # @WARNING: causes a crash in GDAL < 1.6.4 (r18405)
            #~ # @SEEALSO: http://trac.osgeo.org/gdal/ticket/3304
            #~ if gdal.VersionInfo() < '1640':
                #~ dialog.approxCheckBox.setChecked(True)
                #~ dialog.approxCheckBox.setEnabled(False)

            #~ from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode
            #~ try:
                #~ dtype = GDALTypeCodeToNumericTypeCode(band.DataType)
            #~ except KeyError:
                #~ pass
            #~ else:
                #~ dialog.setLimits(dtype)

            #~ tablewidget = self.histogramTableWidget
            #~ if tablewidget.rowCount() > 0:
                #~ item = tablewidget.item(0, 0)
                #~ vmin = float(item.text())
                #~ item = tablewidget.item(tablewidget.rowCount() - 1 , 1)
                #~ vmax = float(item.text())

                #~ dialog.minSpinBox.setValue(vmin)
                #~ dialog.maxSpinBox.setValue(vmax)
                #~ dialog.nBucketsSpinBox.setValue(tablewidget.rowCount())

            #~ done = False
            #~ while not done:
                #~ ret = dialog.exec_()
                #~ if ret == QtGui.QDialog.Rejected:
                    #~ return
                #~ if dialog.validate() is False:
                    #~ msg = self.tr('The histogram minimum have been set to a '
                                  #~ 'value that is greater or equal of the '
                                  #~ 'histogram maximum.\n'
                                  #~ 'Please fix it.')
                    #~ QtGui.QMessageBox.warning(self, self.tr('WARNING!'), msg)
                #~ else:
                    #~ done = True

            #~ vmin = dialog.minSpinBox.value()
            #~ vmax = dialog.maxSpinBox.value()
            #~ nbuckets = dialog.nBucketsSpinBox.value()
            #~ include_out_of_range = dialog.outOfRangeCheckBox.isChecked()
            #~ approx = dialog.approxCheckBox.isChecked()

            #~ # @TODO: use callback for progress reporting
            #~ hist = qt4support.callExpensiveFunc(
                                #~ band.GetHistogram,
                                #~ vmin, vmax, nbuckets,
                                #~ include_out_of_range, approx)
                                #~ #callback=None, callback_data=None)

        #~ else:
            #~ # @TODO: use callback for progress reporting
            #~ hist = qt4support.callExpensiveFunc(band.GetDefaultHistogram)
                                                #~ #callback=None,
                                                #~ #callback_data=None)
            #~ vmin, vmax, nbuckets, hist = hist

        #~ self.computeHistogramButton.setEnabled(False)
        #~ self.setHistogram(vmin, vmax, nbuckets, hist)
        #~ self.updateStatistics() # @TODO: check

    @QtCore.pyqtSlot()
    def _computeOverviews(self):
        self._checkgdalobj()
        self.overviewComputationRequest.emit(self.band)


DatasetInfoDialogBase = qt4support.getuiform('datasetdialog', __name__)
class DatasetInfoDialog(MajorObjectInfoDialog, DatasetInfoDialogBase):

    def __init__(self, dataset=None, parent=None, flags=QtCore.Qt.Widget,
                 **kwargs):
        super(DatasetInfoDialog, self).__init__(dataset, parent, flags,
                                                **kwargs)

        # Set icons
        geticon = qt4support.geticon
        self.tabWidget.setTabIcon(0, geticon('info.svg', 'gsdview'))
        self.tabWidget.setTabIcon(1, geticon('metadata.svg', __name__))
        self.tabWidget.setTabIcon(2, geticon('gcp.svg', __name__))
        self.tabWidget.setTabIcon(3, geticon('driver.svg', __name__))
        self.tabWidget.setTabIcon(4, geticon('multiple-documents.svg',
                                  __name__))

        # Context menu actions
        qt4support.setViewContextActions(self.gcpsTableWidget)
        qt4support.setViewContextActions(self.driverMetadataTableWidget)
        qt4support.setViewContextActions(self.fileListWidget)

        if not hasattr(gdal.Dataset, 'GetFileList'):
            self.tabWidget.setTabEnabled(4, False)

        # Setup Tabs
        if dataset:
            self.update()

    @property
    def dataset(self):
        return self._obj

    def setDataset(self, dataset):
        self._obj = dataset
        if dataset is not None:
            # @TODO: check type
            self.update()
        else:
            self.reset()

    def reset(self):
        super(DatasetInfoDialog, self).reset()

        self.resetInfoTab()
        self.resetDriverTab()
        self.resetGCPs()
        self.resetFilesTab()

    def update(self):
        super(DatasetInfoDialog, self).update()

        self.updateInfoTab()
        self.updateDriverTab()
        self.updateGCPs()
        self.updateFilesTab()

    def resetImageStructure(self):
        _setupImageStructureInfo(self, {})

    def setImageStructure(self, metadata):
        if metadata is None:
            self.resetImageStructure()

        _setupImageStructureInfo(self, metadata)

    def updateImageStructure(self):
        if self.dataset is not None:
            metadata = self.dataset.GetMetadata('IMAGE_STRUCTURE')
        else:
            metadata = {}

        self.setImageStructure(metadata)

    def resetInfoTab(self):
        self.descriptionValue.setText('')
        self.rasterCountValue.setText('0')
        self.xSizeValue.setText('0')
        self.ySizeValue.setText('0')

        self.projectionValue.setText('')
        self.projectionRefValue.setText('')

        self.resetImageStructure()

        self.xOffsetValue.setText('0')
        self.yOffsetValue.setText('0')
        self.a11Value.setText('1')
        self.a12Value.setText('0')
        self.a21Value.setText('0')
        self.a22Value.setText('1')

    def updateInfoTab(self):
        if self.dataset is None:
            self.resetInfoTab()
            return

        dataset = self.dataset
        description = os.path.basename(dataset.GetDescription())
        self.descriptionValue.setText(description)
        self.descriptionValue.setCursorPosition(0)
        self.rasterCountValue.setText(str(dataset.RasterCount))
        self.xSizeValue.setText(str(dataset.RasterXSize))
        self.ySizeValue.setText(str(dataset.RasterYSize))

        self.projectionValue.setText(dataset.GetProjection())
        self.projectionRefValue.setText(dataset.GetProjectionRef())

        self.updateImageStructure()

        xoffset, a11, a12, yoffset, a21, a22 = dataset.GetGeoTransform()
        self.xOffsetValue.setText(str(xoffset))
        self.yOffsetValue.setText(str(yoffset))
        self.a11Value.setText(str(a11))
        self.a12Value.setText(str(a12))
        self.a21Value.setText(str(a21))
        self.a22Value.setText(str(a22))

    def resetDriverTab(self):
        self.driverShortNameValue.setText('')
        self.driverLongNameValue.setText('')
        self.driverDescriptionValue.setText('')
        self.driverHelpTopicValue.setText('')
        self.driverMetadataNumValue.setText('0')
        qt4support.clearTable(self.driverMetadataTableWidget)

    def setDriverTab(self, driver):
        self.resetDriverTab()

        self.driverShortNameValue.setText(driver.ShortName)
        self.driverLongNameValue.setText(driver.LongName)
        self.driverDescriptionValue.setText(driver.GetDescription())

        if driver.HelpTopic:
            link = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'DejaVu Sans'; font-size:10pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a href="http://www.gdal.org/%s"><span style=" text-decoration: underline; color:#0000ff;">%s</span></a></p></body></html>''' % (driver.HelpTopic, driver.HelpTopic)
        else:
            link = str(driver.HelpTopic)

        self.driverHelpTopicValue.setText(link)

        metadatalist = driver.GetMetadata_List()
        if metadatalist:
            self.driverMetadataNumValue.setText(str(len(metadatalist)))
            self._setMetadata(self.driverMetadataTableWidget, metadatalist)

    def updateDriverTab(self):
        if self.dataset is None:
            self.resetDriverTab()
            return

        driver = self.dataset.GetDriver()
        self.setDriverTab(driver)

    def resetGCPs(self):
        tablewidget = self.gcpsTableWidget
        qt4support.clearTable(tablewidget)
        self.gcpsNumValue.setText('')
        self.gcpsProjectionValue.setText('')

    def setGCPs(self, gcplist, projection):
        self.resetGCPs()

        tablewidget = self.gcpsTableWidget

        self.gcpsProjectionValue.setText(projection)
        self.gcpsNumValue.setText(str(len(gcplist)))

        tablewidget.setRowCount(len(gcplist))
        tablewidget.setVerticalHeaderLabels([str(gcp.Id) for gcp in gcplist])
        sortingenabled = tablewidget.isSortingEnabled()
        tablewidget.setSortingEnabled(False)

        Item = QtGui.QTableWidgetItem
        for row, gcp in enumerate(gcplist):
            tablewidget.setItem(row, 0, Item(str(gcp.GCPPixel)))
            tablewidget.setItem(row, 1, Item(str(gcp.GCPLine)))
            tablewidget.setItem(row, 2, Item(str(gcp.GCPX)))
            tablewidget.setItem(row, 3, Item(str(gcp.GCPY)))
            tablewidget.setItem(row, 4, Item(str(gcp.GCPZ)))
            tablewidget.setItem(row, 5, Item(gcp.Info))
            #~ item.setToolTip(1, gcp.Info)

        # Fix table header behaviour
        tablewidget.setSortingEnabled(sortingenabled)

    def updateGCPs(self):
        if self.dataset is None:
            self.resetGCPs()
        else:
            # It seems there is a bug in GDAL that causes incorrect GCPs
            # handling when a subdatast is opened (a dataset is aready open)
            # @TODO: check and, if the case, file a ticket on
            #        http://www.gdal.org

            #self.setGCPs(dataset.GetGCPs(), dataset.GetGCPProjection())
            try:
                gcplist = self.dataset.GetGCPs()
            except SystemError:
                logging.debug('unable to read GCPs from dataset %s' %
                                    self.dataset.GetDescription())
                                    #, exc_info=True)
            else:
                if not gcplist:
                    # Disable the GCPs tab
                    self.tabWidget.setTabEnabled(2, False)
                else:
                    self.tabWidget.setTabEnabled(2, True)
                    self.setGCPs(gcplist, self.dataset.GetGCPProjection())

    def resetFilesTab(self):
        #qt4support.clearTable(self.fileListWidget) # @TODO: check
        self.fileListWidget.clear()

    def setFiles(self, files):
        self.tabWidget.setTabEnabled(4, True)

        for filename in files:
            self.fileListWidget.addItem(filename)

    def updateFilesTab(self):
        if self.dataset is not None:
            self.tabWidget.setTabEnabled(4, True)
            self.setFiles(self.dataset.GetFileList())
        else:
            self.resetFilesTab()
            self.tabWidget.setTabEnabled(4, False)

#~ class SubDatasetInfoDialog(DatasetInfoDialog):

    #~ def __init__(self, subdataset, parent=None, flags=QtCore.Qt.Widget):
        #~ assert dataset, 'a valid GDAL dataset expected'
        #~ DatasetInfoDialog.__init__(self, subdataset, parent, flags)
