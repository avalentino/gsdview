# -*- coding: UTF8 -*-

### Copyright (C) 2008-2009 Antonio Valentino <a_valentino@users.sf.net>

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

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        super(GDALInfoWidget, self).__init__(parent, flags)
        self.setupUi(self)

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
        hheader.setStretchLastSection(True)

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

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        super(GDALPreferencesPage, self).__init__(parent, flags)
        self.setupUi(self)

        self.infoButton.setIcon(qt4support.geticon('info.svg', 'gsdview'))

        # Avoid promoted widgets
        DirectoryOnly = QtGui.QFileDialog.DirectoryOnly
        self.gdalDataDirEntryWidget = FileEntryWidget(mode=DirectoryOnly)
        self.optionsGridLayout.addWidget(self.gdalDataDirEntryWidget, 1, 1)
        self.gdalDataDirEntryWidget.setEnabled(False)
        self.connect(self.gdalDataCheckBox,
                     QtCore.SIGNAL('toggled(bool)'),
                     self.gdalDataDirEntryWidget,
                     QtCore.SLOT('setEnabled(bool)'))

        self.gdalDriverPathEntryWidget = FileEntryWidget(mode=DirectoryOnly)
        self.optionsGridLayout.addWidget(self.gdalDriverPathEntryWidget, 3, 1)
        self.gdalDriverPathEntryWidget.setEnabled(False)
        self.connect(self.gdalDriverPathCheckBox,
                     QtCore.SIGNAL('toggled(bool)'),
                     self.gdalDriverPathEntryWidget,
                     QtCore.SLOT('setEnabled(bool)'))

        self.ogrDriverPathEntryWidget = FileEntryWidget(mode=DirectoryOnly)
        self.optionsGridLayout.addWidget(self.ogrDriverPathEntryWidget, 4, 1)
        self.ogrDriverPathEntryWidget.setEnabled(False)
        self.connect(self.ogrDriverPathCheckBox,
                     QtCore.SIGNAL('toggled(bool)'),
                     self.ogrDriverPathEntryWidget,
                     QtCore.SLOT('setEnabled(bool)'))

        # info button
        self.connect(self.infoButton, QtCore.SIGNAL('clicked()'), self.showinfo)

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
        #hheader.hide()
        hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)
        hheader.setStretchLastSection(True)

    def showinfo(self):
        dialog = QtGui.QDialog(self)
        dialog.setWindowTitle(self.tr('GDAL info'))
        layout = QtGui.QVBoxLayout()
        layout.addWidget(GDALInfoWidget())

        buttonbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        dialog.connect(buttonbox, QtCore.SIGNAL('accepted()'),
                       dialog, QtCore.SLOT('accept()'))
        dialog.connect(buttonbox, QtCore.SIGNAL('rejected()'),
                       dialog, QtCore.SLOT('reject()'))
        layout.addWidget(buttonbox)

        dialog.setLayout(layout)
        buttonbox.setFocus()
        dialog.exec_()

    def load(self, settings):
        settings.beginGroup('gdal')
        try:

            # cache size
            cachesize = settings.value('GDAL_CACHEMAX')
            if not cachesize.isNull():
                cachesize, ok = cachesize.toULongLong()
                if ok:
                    self.cacheCheckBox.setChecked(True)
                    self.cacheSpinBox.setValue(cachesize/1024**2)
            else:
                # show the current value and disable the control
                cachesize = gdal.GetCacheMax()
                self.cacheSpinBox.setValue(cachesize/1024**2)
                self.cacheCheckBox.setChecked(False)

            # GDAL data dir
            datadir = settings.value('GDAL_DATA').toString()
            if datadir:
                self.gdalDataCheckBox.setChecked(True)
                self.gdalDataDirEntryWidget.setText(datadir)
            else:
                # show the current value and disable the control
                datadir = gdal.GetConfigOption('GDAL_DATA', '')
                self.gdalDataDirEntryWidget.setText(datadir)
                self.gdalDataCheckBox.setChecked(False)

            # GDAL_SKIP
            gdalskip = settings.value('GDAL_SKIP').toString()
            if gdalskip:
                self.skipCheckBox.setChecked(True)
                self.skipLineEdit.setText(gdalskip)
            else:
                # show the current value and disable the control
                gdalskip = gdal.GetConfigOption('GDAL_SKIP', '')
                self.skipLineEdit.setText(gdalskip)
                self.skipCheckBox.setChecked(False)

            # GDAL driver path
            gdaldriverpath = settings.value('GDAL_DRIVER_PATH').toString()
            if gdaldriverpath:
                self.gdalDriverPathCheckBox.setChecked(True)
                self.gdalDriverPathEntryWidget.setText(gdaldriverpath)
            else:
                # show the current value and disable the control
                gdaldriverpath = gdal.GetConfigOption('GDAL_DRIVER_PATH', '')
                self.gdalDriverPathEntryWidget.setText(gdaldriverpath)
                self.gdalDriverPathCheckBox.setChecked(False)

            # OGR driver path
            ogrdriverpath = settings.value('OGR_DRIVER_PATH').toString()
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
                settings.setValue('GDAL_CACHEMAX', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_CACHEMAX')

            # GDAL data dir
            if self.gdalDataCheckBox.isChecked():
                value = self.gdalDataDirEntryWidget.text()
                settings.setValue('GDAL_DATA', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_DATA')

            # GDAL_SKIP
            if self.skipCheckBox.isChecked():
                value = self.skipLineEdit.text()
                settings.setValue('GDAL_SKIP', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_SKIP')

            # GDAL driver path
            if self.gdalDriverPathCheckBox.isChecked():
                value = self.gdalDriverPathEntryWidget.text()
                settings.setValue('GDAL_DRIVER_PATH', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_DRIVER_PATH')

            # OGR driver path
            if self.ogrDriverPathCheckBox.isChecked():
                value = self.ogrDriverPathEntryWidget.text()
                settings.setValue('OGR_DRIVER_PATH', QtCore.QVariant(value))
            else:
                settings.remove('OGR_DRIVER_PATH')

            # @TODO: complete
            #~ gdal.GetConfigOption('CPL_DEBUG', 'OFF')
            #~ gdal.GetConfigOption('GDAL_PAM_ENABLED', "NULL")

            # extra options
            # @TODO
        finally:
            settings.endGroup()


class MajorObjectInfoDialog(QtGui.QDialog):
    def __init__(self, gdalobj, parent=None, flags=QtCore.Qt.Widget):
        super(MajorObjectInfoDialog, self).__init__(parent, flags)
        if hasattr(self, 'setupUi'):
            self.setupUi(self)

        self._obj = gdalobj

        # Contect menu
        self.actionCopy.setIcon(qt4support.geticon('copy.svg', __name__))
        #self.actionSelectAll.setIcon(qt4support.geticon('selectall.svg',
        #                                                __name__))
        self.connect(self.actionCopy, QtCore.SIGNAL('triggered()'),
                     self.copySelectedItems)
        self.connect(self.actionSelectAll, QtCore.SIGNAL('triggered()'),
                     self.selectedAllItems)
        if hasattr(self, 'domainComboBox'):
            self.connect(self.domainComboBox,
                         QtCore.SIGNAL('activated(const QString&)'),
                         self.updateMetadata)

        # Context menu actions
        for action in (self.actionCopy, self.actionSelectAll):
            self.metadataTableWidget.addAction(action)

        # Init tabs
        self.updateMetadata()

    def updateMetadata(self, domain=''):
        domain = str(domain)    # it could be a QString
        metadatalist = self._obj.GetMetadata_List(domain)
        if metadatalist:
            self.metadataNumValue.setText(str(len(metadatalist)))
            self._setMetadata(self.metadataTableWidget, metadatalist)
        else:
            self.metadataNumValue.setText('0')
            self._cleartable(self.metadataTableWidget)

    @staticmethod
    def _setMetadata(tablewidget, metadatalist):
        MajorObjectInfoDialog._cleartable(tablewidget)
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
        header = tablewidget.horizontalHeader()
        #~ header.resizeSections(QtGui.QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        tablewidget.setSortingEnabled(sortingenabled)

    @staticmethod
    def _cleartable(tablewidget):
        labels = [str(tablewidget.horizontalHeaderItem(col).text())
                                for col in range(tablewidget.columnCount())]
        tablewidget.clear()
        tablewidget.setHorizontalHeaderLabels(labels)
        header = tablewidget.horizontalHeader()
        header.setStretchLastSection(True)
        #tablewidget.setRowCount(0)

    @staticmethod
    def copySelectedItems():
        widget = QtGui.qApp.focusWidget()
        assert hasattr(widget, 'selectionModel')
        selection = widget.selectionModel().selection()
        qt4support.copyItemSelection(selection)

    @staticmethod
    def selectedAllItems():
        widget = QtGui.qApp.focusWidget()
        assert hasattr(widget, 'selectionModel')
        qt4support.selectAllItems(widget)


def _setupImageStructureInfo(widget, metadata):
    widget.compressionValue.setText(metadata.get('COMPRESSION', ''))
    widget.nbitsValue.setText(metadata.get('NBITS', ''))
    widget.interleaveValue.setText(metadata.get('INTERLEAVE', ''))
    widget.pixelTypeValue.setText(metadata.get('PIXELTYPE', ''))


HistogramConfigDialogBase = qt4support.getuiform('histoconfig', __name__)
class HistogramConfigDialog(QtGui.QDialog, HistogramConfigDialogBase):
    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        super(HistogramConfigDialog, self).__init__(parent, flags)
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

        self.connect(self.minSpinBox, QtCore.SIGNAL('editingFinished()'),
                     self.validate)
        self.connect(self.maxSpinBox, QtCore.SIGNAL('editingFinished()'),
                     self.validate)

    def validate(self):
        if self.minSpinBox.value() >= self.maxSpinBox.value():
            self.minSpinBox.lineEdit().setPalette(self._error_palette)
            self.maxSpinBox.lineEdit().setPalette(self._error_palette)
            return False
        self.minSpinBox.lineEdit().setPalette(self._default_palette)
        self.maxSpinBox.lineEdit().setPalette(self._default_palette)
        return True

    def setLimits(self, dtype):
        min_ = -2**15 - 0.5
        max_ = 2**16 - 0.5
        if dtype in (numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64):
            # Unsigned
            min_ = -0.5
            if dtype == numpy.uint8:
                max_ = 255.5
            else:
                max_ = 2**16 - 0.5
        elif dtype == numpy.int8:
            min_ = -128.5
            max_ = 127.5
        elif dtype == numpy.int16:
            max_ = 2**15 + 0.5

        self.minSpinBox.setMinimum(min_)
        self.minSpinBox.setMaximum(max_)
        self.maxSpinBox.setMinimum(min_)
        self.maxSpinBox.setMaximum(max_)


BandInfoDialogBase = qt4support.getuiform('banddialog', __name__)
class BandInfoDialog(MajorObjectInfoDialog, BandInfoDialogBase):

    def __init__(self, band, parent=None, flags=QtCore.Qt.Widget):
        assert band, 'a valid GDAL raster band expected'
        super(BandInfoDialog, self).__init__(band, parent, flags)

        self.connect(self.computeStatsButton, QtCore.SIGNAL('clicked()'),
                     self.computeStats)
        self.connect(self.computeHistogramButton, QtCore.SIGNAL('clicked()'),
                     self.computeHistogram)
        self.connect(self.approxStatsCheckBox, QtCore.SIGNAL('toggled(bool)'),
                     lambda chk: self.computeStatsButton.setEnabled(True))
        self.connect(self.customHistogramCheckBox,
                     QtCore.SIGNAL('toggled(bool)'),
                     lambda chk: self.computeHistogramButton.setEnabled(True))

        # Set tab icons
        geticon = qt4support.geticon
        self.tabWidget.setTabIcon(0, geticon('info.svg', 'gsdview'))
        self.tabWidget.setTabIcon(1, geticon('metadata.svg', __name__))
        self.tabWidget.setTabIcon(2, geticon('statistics.svg', __name__))
        self.tabWidget.setTabIcon(3, geticon('color.svg', __name__))

        # Context menu actions
        for action in (self.actionCopy, self.actionSelectAll):
            #self.metadataTableWidget.addAction(action) # set in parent class
            self.histogramTableWidget.addAction(action)
            self.colorTableWidget.addAction(action)

        # Tabs
        self._setupInfoTab(band)
        self._setupStatistics(band)
        self._setupHistogram(band)
        self._setupColorTable(band.GetRasterColorTable())

    def _setupInfoTab(self, band):
        # Color interpretaion
        colorint = band.GetRasterColorInterpretation()
        colorint = gdal.GetColorInterpretationName(colorint)

        # Info
        self.descriptionValue.setText(band.GetDescription().strip())
        # @COMPATIBILITY: GDAL 1.5.x doesn't support this API
        try:
            bandno = band.GetBand()
        except AttributeError:
            self.bandNumberLabel.hide()
            self.bandNumberValue.hide()
        else:
            self.bandNumberValue.setText(str(bandno))
        self.colorInterpretationValue.setText(colorint)
        self.overviewCountValue.setText(str(band.GetOverviewCount()))
        # @COMPATIBILITY: GDAL 1.5.x doesn't support this API
        try:
            hasArbitaryOvr = band.HasArbitraryOverviews()
        except AttributeError:
            self.hasArbitraryOverviewsLabel.hide()
            self.hasArbitraryOverviewsValue.hide()
        else:
            self.hasArbitraryOverviewsValue.setText(str(hasArbitaryOvr))

        # @TODO: checksum
        #~ band.Checksum                   ??

        # Data
        self.xSizeValue.setText(str(band.XSize))
        self.ySizeValue.setText(str(band.YSize))
        self.blockSizeValue.setText(str(band.GetBlockSize()))
        self.noDataValue.setText(str(band.GetNoDataValue()))

        self.dataTypeValue.setText(gdal.GetDataTypeName(band.DataType))
        # @COMPATIBILITY: GDAL 1.5.x doesn't support this API
        try:
            unitType = band.GetUnitType()
        except AttributeError:
            self.unitTypeLabel.hide()
            self.unitTypeValue.hide()
        else:
            self.unitTypeValue.setText(str(unitType))
        self.offsetValue.setText(str(band.GetOffset()))
        self.scaleValue.setText(str(band.GetScale()))

        _setupImageStructureInfo(self, band.GetMetadata('IMAGE_STRUCTURE'))

    @qt4support.overrideCursor
    def computeStats(self):
        logging.info('start statistics computation')
        # @TODO: use an external process (??)

        band = self._obj
        approx = self.approxStatsCheckBox.isChecked()
        # @COMPATIBILITY: GDAL 1.5.x doesn't support this API
        if hasattr(band, 'ComputeStatistics'):
            # New API
            # @TODO: use calback for progress reporting
            band.ComputeStatistics(approx)#, callback=None, callback_data=None)
        else:
            min_, max_, mean_, std_ = band.GetStatistics(approx, True)
            # @COMPATIBILITY: GDAL 1.5.x and 1.6.x (??)
            if gdal.VersionInfo() < '1700':
                band.SetStatistics(min_, max_, mean_, std_)
            if self.domainComboBox.currentText() == '':
                print 'self.updateMetadata()'
                self.updateMetadata()
        logging.debug('statistics computation completed')
        self._setupStatistics(band)

    def _setupStatistics(self, band):
        # @NOTE: it is not possible to use
        #
        #           band.GetStatistics(approx_ok=True, force=False)
        #
        #        thar ensure aquick computation, because currently python
        #        bindings don't provide any method to detect is result is
        #        valid or not.
        #        As a workaround check for statistics metadata
        #        (STATISTICS_MINIMUM, STATISTICS_MAXIMUM, STATISTICS_MEAN,
        #        STATISTICS_STDDEV)

        metadata = band.GetMetadata()
        if metadata.get('STATISTICS_STDDEV') is None:
            value = self.tr('Not computed')
            self.minimumValue.setText(value)
            self.maximumValue.setText(value)
            self.meanValue.setText(value)
            self.stdValue.setText(value)
        else:
            min_, max_, mean_, std_ = band.GetStatistics(True, True)
            self.minimumValue.setText(str(min_))
            self.maximumValue.setText(str(max_))
            self.meanValue.setText(str(mean_))
            self.stdValue.setText(str(std_))
            self.computeStatsButton.setEnabled(False)

    def computeHistogram(self):
        # @TODO: use an external process (??)

        band = self._obj
        approx = self.approxStatsCheckBox.isChecked()
        # @COMPATIBILITY: GDAL 1.5.x doesn't support this API
        if hasattr(band, 'GetHistogram'):
            if self.customHistogramCheckBox.isChecked():
                dialog = HistogramConfigDialog(self)

                # @COMPATIBILITY: bug in GDAL 1.6.x line
                # @WARNING: causes a crash in GDAL < 1.7.0 (r18405)
                # @SEEALSO: http://trac.osgeo.org/gdal/ticket/3304
                if gdal.VersionInfo() < '1700':
                    dialog.approxCheckBox.setChecked(True)
                    dialog.approxCheckBox.setEnabled(False)

                try:
                    dtype = gdalsupport.typemap[band.DataType]
                except KeyError:
                    pass
                else:
                    dialog.setLimits(dtype)

                done = False
                while not done:
                    ret = dialog.exec_()
                    if ret == QtGui.QDialog.Rejected:
                        return
                    if dialog.validate() is False:
                        msg = self.tr('The histogram minimum have been set to '
                                      'a value that is greater or equal of '
                                      'the histogram maximum.'
                                      '\n'
                                      'Please fix it.')
                        QtGui.QMessageBox.warning(self, self.tr('WARNING!'),
                                                  msg)
                    else:
                        done = True

                min_ = dialog.minSpinBox.value()
                max_ = dialog.maxSpinBox.value()
                nbuckets = dialog.nBucketsSpinBox.value()
                include_out_of_range = dialog.outOfRangeCheckBox.isChecked()
                approx = dialog.approxCheckBox.isChecked()

                # @TODO: use calback for progress reporting
                qt4support.callExpensiveFunc(
                                band.GetHistogram,
                                min_, max_, nbuckets,
                                include_out_of_range, approx)
                                #callback=None, callback_data=None)
            else:
                # @TODO: use calback for progress reporting
                qt4support.callExpensiveFunc(band.GetDefaultHistogram)
                                        #callback=None, callback_data=None)

            self._setupStatistics(band)
            self._setupHistogram(band)

    def _resetHistogram(self):
        tablewidget = self.histogramTableWidget
        self.numberOfClassesValue.setText('0')
        self._cleartable(tablewidget)

    def _setupHistogram(self, band):
        if not hasattr(band, 'GetDefaultHistogram'):
            self.histogramGroupBox.hide()
            self.statisticsVerticalLayout.addStretch()
            return

        if band.DataType in (gdal.GDT_CInt16, gdal.GDT_CInt32,
                             gdal.GDT_CFloat32, gdal.GDT_CFloat64):
            self.computeHistogramButton.setEnabled(False)
            return

        if gdal.VersionInfo() < '1700':
            if self.computeHistogramButton.enabled() == False:
                # Histogram already computed
                hist = band.GetDefaultHistogram()
        else:
            # @WARNING: causes a crash in GDAL < 1.7.0 (r18405)
            # @SEEALSO: http://trac.osgeo.org/gdal/ticket/3304
            hist = band.GetDefaultHistogram(force=False)

        if hist:
            histmin, histmax, bucketcount = hist[:3]
            hist = hist[3]
            w = (histmax - histmin) / bucketcount

            self.numberOfClassesValue.setText(str(bucketcount))

            tablewidget = self.histogramTableWidget
            tablewidget.setRowCount(bucketcount)

            for row in range(bucketcount):
                start = histmin + row
                stop = start + w
                tablewidget.setItem(row, 0,
                                    QtGui.QTableWidgetItem(str(start)))
                tablewidget.setItem(row, 1,
                                    QtGui.QTableWidgetItem(str(stop)))
                tablewidget.setItem(row, 2,
                                    QtGui.QTableWidgetItem(str(hist[row])))
            self.computeHistogramButton.setEnabled(False)   # @TODO: check

            # @TODO: plotting
        else:
            self._resetHistogram()

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

    def _setupColorTable(self, colortable):
        tablewidget = self.colorTableWidget

        if colortable is None:
            self.ctInterpretationValue.setText('')
            self.colorsNumberValue.setText('')
            self._cleartable(tablewidget)
            return

        ncolors = colortable.GetCount()
        colorint = colortable.GetPaletteInterpretation()

        label = gdalsupport.colorinterpretations[colorint]['label']
        self.ctInterpretationValue.setText(label)
        self.colorsNumberValue.setText(str(ncolors))

        mapping = gdalsupport.colorinterpretations[colorint]['inverse']
        labels = [mapping[k] for k in sorted(mapping.keys())]
        labels.append('Color')

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


DatasetInfoDialogBase = qt4support.getuiform('datasetdialog', __name__)
class DatasetInfoDialog(MajorObjectInfoDialog, DatasetInfoDialogBase):

    def __init__(self, dataset, parent=None, flags=QtCore.Qt.Widget):
        assert dataset, 'a valid GDAL dataset expected'
        super(DatasetInfoDialog, self).__init__(dataset, parent, flags)

        # Set icons
        geticon = qt4support.geticon
        self.tabWidget.setTabIcon(0, geticon('info.svg', 'gsdview'))
        self.tabWidget.setTabIcon(1, geticon('metadata.svg', __name__))
        self.tabWidget.setTabIcon(2, geticon('gcp.svg', __name__))
        self.tabWidget.setTabIcon(3, geticon('driver.svg', __name__))
        if hasattr(dataset, 'GetFileList'):
            self.tabWidget.setTabIcon(4, geticon('multiple-documents.svg',
                                                 __name__))
            for file_ in dataset.GetFileList():
                self.fileListWidget.addItem(file_)
        else:
            #self.tabWidget.setTabEnabled(4, False)
            self.tabWidget.removeTab(4)

        # Context menu actions
        for action in (self.actionCopy, self.actionSelectAll):
            #self.metadataTableWidget.addAction(action) # set in parent class
            self.gcpsTableWidget.addAction(action)
            self.driverMetadataTableWidget.addAction(action)
            self.fileListWidget.addAction(action)

        # Info Tab
        self._setupInfoTab(dataset)

        # Driver Tab
        self._setupDriverTab(dataset.GetDriver())

        # It seems there is a bug in GDAL that causes incorrect GCPs handling
        # when a subdatast is opened (a dataset is aready open)
        # @TODO: check and, if the case, fiel a ticket on http://www.gdal.org

        #~ self._setupGCPs(dataset.GetGCPs(), dataset.GetGCPProjection())
        # @TODO: report a bug on GDAL trac
        try:
            self._setupGCPs(dataset.GetGCPs(), dataset.GetGCPProjection())
        except SystemError:
            logging.debug('unable to read GCPs from dataset %s' %
                                    dataset.GetDescription())#, exc_info=True)

    def _setupInfoTab(self, dataset):
        description = os.path.basename(dataset.GetDescription())
        self.descriptionValue.setText(description)
        self.descriptionValue.setCursorPosition(0)
        self.rasterCountValue.setText(str(dataset.RasterCount))
        self.xSizeValue.setText(str(dataset.RasterXSize))
        self.ySizeValue.setText(str(dataset.RasterYSize))

        self.projectionValue.setText(dataset.GetProjection())
        self.projectionRefValue.setText(dataset.GetProjectionRef())

        _setupImageStructureInfo(self, dataset.GetMetadata('IMAGE_STRUCTURE'))

        xoffset, a11, a12, yoffset, a21, a22 = dataset.GetGeoTransform()
        self.xOffsetValue.setText(str(xoffset))
        self.yOffsetValue.setText(str(yoffset))
        self.a11Value.setText(str(a11))
        self.a12Value.setText(str(a12))
        self.a21Value.setText(str(a21))
        self.a22Value.setText(str(a22))

    def _setupDriverTab(self, driver):
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

    def _setupGCPs(self, gcplist, projection):
        # @TODO: improve
        self.gcpsProjectionValue.setText(projection)
        tablewidget = self.gcpsTableWidget

        self._cleartable(tablewidget)
        if not gcplist:
            header = tablewidget.horizontalHeader()
            header.setStretchLastSection(True)
            return

        self.gcpsNumValue.setText(str(len(gcplist)))

        tablewidget.setRowCount(len(gcplist))
        tablewidget.setVerticalHeaderLabels([str(gcp.Id) for gcp in gcplist])
        sortingenabled = tablewidget.isSortingEnabled()
        tablewidget.setSortingEnabled(False)

        for row, gcp in enumerate(gcplist):
            tablewidget.setItem(row, 0, QtGui.QTableWidgetItem(str(gcp.GCPPixel)))
            tablewidget.setItem(row, 1, QtGui.QTableWidgetItem(str(gcp.GCPLine)))
            tablewidget.setItem(row, 2, QtGui.QTableWidgetItem(str(gcp.GCPX)))
            tablewidget.setItem(row, 3, QtGui.QTableWidgetItem(str(gcp.GCPY)))
            tablewidget.setItem(row, 4, QtGui.QTableWidgetItem(str(gcp.GCPZ)))
            tablewidget.setItem(row, 5, QtGui.QTableWidgetItem(gcp.Info))
            #~ item.setToolTip(1, gcp.Info)

        # Fix table header behaviour
        header = tablewidget.horizontalHeader()
        #~ header.resizeSections(QtGui.QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        tablewidget.setSortingEnabled(sortingenabled)


#~ class SubDatasetInfoDialog(DatasetInfoDialog):

    #~ def __init__(self, subdataset, parent=None, flags=QtCore.Qt.Widget):
        #~ assert dataset, 'a valid GDAL dataset expected'
        #~ DatasetInfoDialog.__init__(self, subdataset, parent, flags)
