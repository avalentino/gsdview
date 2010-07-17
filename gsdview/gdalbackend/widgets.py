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
from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode
from PyQt4 import QtCore, QtGui

from gsdview import qt4support
from gsdview.widgets import get_filedialog, FileEntryWidget

from gsdview.gdalbackend import gdalsupport


GDALInfoWidgetBase = qt4support.getuiform('gdalinfo', __name__)
class GDALInfoWidget(QtGui.QWidget, GDALInfoWidgetBase):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        super(GDALInfoWidget, self).__init__(parent, flags)
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

        if hasattr(self, 'domainComboBox'):
            self.connect(self.domainComboBox,
                         QtCore.SIGNAL('activated(const QString&)'),
                         self.updateMetadata)

        # Contect menu
        qt4support.setViewContextActions(self.metadataTableWidget)

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
            qt4support.clearTable(self.metadataTableWidget)

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
        qt4support.setViewContextActions(self.histogramTableWidget)
        qt4support.setViewContextActions(self.colorTableWidget)

        # @TODO: improve method names
        # Tabs
        self._setupInfoTab(band)
        self._setupStatisticsBox(band)
        self._setupHistogramBox(band)
        self._setupColorTableTab(band.GetRasterColorTable())

    def _setupInfoTab(self, band):
        # Color interpretaion
        colorint = band.GetRasterColorInterpretation()
        colorint = gdal.GetColorInterpretationName(colorint)

        # Info
        self.descriptionValue.setText(band.GetDescription().strip())
        bandno = band.GetBand()
        self.bandNumberValue.setText(str(bandno))
        self.colorInterpretationValue.setText(colorint)
        self.overviewCountValue.setText(str(band.GetOverviewCount()))

        hasArbitaryOvr = band.HasArbitraryOverviews()
        self.hasArbitraryOverviewsValue.setText(str(hasArbitaryOvr))

        # @TODO: checksum
        #~ band.Checksum                   ??

        # Data
        self.xSizeValue.setText(str(band.XSize))
        self.ySizeValue.setText(str(band.YSize))
        self.blockSizeValue.setText(str(band.GetBlockSize()))
        self.noDataValue.setText(str(band.GetNoDataValue()))

        self.dataTypeValue.setText(gdal.GetDataTypeName(band.DataType))
        unitType = band.GetUnitType()
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
        # @TODO: use callback for progress reporting
        band.ComputeStatistics(approx)#, callback=None, callback_data=None)

        # @COMPATIBILITY: workaround fo flagging statistics as computed
        # @SEALSO: ticket #3572 on GDAL Trac
        stats = band.GetStatistics(True, True)
        for name, value in zip(gdalsupport.GDAL_STATS_KEYS, stats):
            band.SetMetadataItem(name, str(value))

        # @TODO: check
        #if self.domainComboBox.currentText() == '':
        #    self.updateMetadata()
        logging.debug('statistics computation completed')
        self._setupStatisticsBox(band)

    def _resetStatisticsBox(self):
        '''Reset statistics.'''

        value = self.tr('Not computed')
        self.minimumValue.setText(value)
        self.maximumValue.setText(value)
        self.meanValue.setText(value)
        self.stdValue.setText(value)

    def _setupStatisticsBox(self, band):
        # @NOTE: the band.GetStatistics method called with the second argument
        #        set to False (no image rescanning) has been fixed in
        #        r19666_ (1.6 branch) and r19665_ (1.7 branch)
        #        see `ticket #3572` on `GDAL Trac`_.
        #
        # .. _r19666: http://trac.osgeo.org/gdal/changeset/19666
        # .. _r19665: http://trac.osgeo.org/gdal/changeset/19665
        # .. _`ticket #3572`: http://trac.osgeo.org/gdal/ticket/3572
        # .. _`GDAL Trac`: http://trac.osgeo.org/gdal

        if gdalsupport.hasFastStats(band):
            vmin, vmax, mean, stddev = band.GetStatistics(True, True)
            self.minimumValue.setText(str(vmin))
            self.maximumValue.setText(str(vmax))
            self.meanValue.setText(str(mean))
            self.stdValue.setText(str(stddev))
            self.computeStatsButton.setEnabled(False)
        else:
            self._resetStatisticsBox()

    def computeHistogram(self):
        # @TODO: use an external process (??)

        band = self._obj
        approx = self.approxStatsCheckBox.isChecked()
        if self.customHistogramCheckBox.isChecked():
            dialog = HistogramConfigDialog(self)

            # @COMPATIBILITY: bug in GDAL 1.6.x line
            # @WARNING: causes a crash in GDAL < 1.6.4 (r18405)
            # @SEEALSO: http://trac.osgeo.org/gdal/ticket/3304
            if gdal.VersionInfo() < '1640':
                dialog.approxCheckBox.setChecked(True)
                dialog.approxCheckBox.setEnabled(False)

            try:
                dtype = GDALTypeCodeToNumericTypeCode(band.DataType)
            except KeyError:
                pass
            else:
                dialog.setLimits(dtype)

            tablewidget = self.histogramTableWidget
            if tablewidget.rowCount() > 0:
                item = tablewidget.item(0, 0)
                vmin = float(item.text())
                item = tablewidget.item(tablewidget.rowCount() - 1 , 1)
                vmax = float(item.text())

                dialog.minSpinBox.setValue(vmin)
                dialog.maxSpinBox.setValue(vmax)
                dialog.nBucketsSpinBox.setValue(tablewidget.rowCount())

            done = False
            while not done:
                ret = dialog.exec_()
                if ret == QtGui.QDialog.Rejected:
                    return
                if dialog.validate() is False:
                    msg = self.tr('The histogram minimum have been set to a '
                                  'value that is greater or equal of the '
                                  'histogram maximum.\n'
                                  'Please fix it.')
                    QtGui.QMessageBox.warning(self, self.tr('WARNING!'), msg)
                else:
                    done = True

            vmin = dialog.minSpinBox.value()
            vmax = dialog.maxSpinBox.value()
            nbuckets = dialog.nBucketsSpinBox.value()
            include_out_of_range = dialog.outOfRangeCheckBox.isChecked()
            approx = dialog.approxCheckBox.isChecked()

            # @TODO: use callback for progress reporting
            hist = qt4support.callExpensiveFunc(
                                band.GetHistogram,
                                vmin, vmax, nbuckets,
                                include_out_of_range, approx)
                                #callback=None, callback_data=None)

        else:
            # @TODO: use callback for progress reporting
            hist = qt4support.callExpensiveFunc(band.GetDefaultHistogram)
                                                #callback=None,
                                                #callback_data=None)
            vmin, vmax, nbuckets, hist = hist

        self.computeHistogramButton.setEnabled(False)
        self._setupStatisticsBox(band) # @TODO: check
        self._setHistogram(vmin, vmax, nbuckets, hist)

    def _setHistogram(self, vmin, vmax, nbuckets, hist):
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

    def _resetHistogramBox(self):
        tablewidget = self.histogramTableWidget
        self.numberOfClassesValue.setText('0')
        qt4support.clearTable(tablewidget)

    def _setupHistogramBox(self, band):
        if not hasattr(band, 'GetDefaultHistogram'):
            self.histogramGroupBox.hide()
            self.statisticsVerticalLayout.addStretch()
            return

        if band.DataType in (gdal.GDT_CInt16, gdal.GDT_CInt32,
                             gdal.GDT_CFloat32, gdal.GDT_CFloat64):
            self.computeHistogramButton.setEnabled(False)
            return

        if gdal.VersionInfo() < '1700':
            if self.computeHistogramButton.isEnabled() == False:
                # Histogram already computed
                hist = band.GetDefaultHistogram()
            else:
                hist = None
        else:
            # @WARNING: causes a crash in GDAL < 1.7.0 (r18405)
            # @SEEALSO: http://trac.osgeo.org/gdal/ticket/3304
            hist = band.GetDefaultHistogram(force=False)

        if hist:
            self._setHistogram(*hist)
            self.computeHistogramButton.setEnabled(False)
        else:
            self._resetHistogramBox()

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

    def _setupColorTableTab(self, colortable):
        tablewidget = self.colorTableWidget

        if colortable is None:
            self.ctInterpretationValue.setText('')
            self.colorsNumberValue.setText('')
            qt4support.clearTable(tablewidget)
            # Disable the color table tab
            self.tabWidget.setTabEnabled(3, False)
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
        qt4support.setViewContextActions(self.gcpsTableWidget)
        qt4support.setViewContextActions(self.driverMetadataTableWidget)
        qt4support.setViewContextActions(self.fileListWidget)

        # Setup Tabs
        self._setupInfoTab(dataset)
        self._setupDriverTab(dataset.GetDriver())

        # It seems there is a bug in GDAL that causes incorrect GCPs handling
        # when a subdatast is opened (a dataset is aready open)
        # @TODO: check and, if the case, file a ticket on http://www.gdal.org

        #~ self._setupGCPs(dataset.GetGCPs(), dataset.GetGCPProjection())
        try:
            gcplist = dataset.GetGCPs()
        except SystemError:
            logging.debug('unable to read GCPs from dataset %s' %
                                    dataset.GetDescription())#, exc_info=True)
        else:
            self._setupGCPs(gcplist, dataset.GetGCPProjection())

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

    def _resetGCPs(self):
        tablewidget = self.gcpsTableWidget
        qt4support.clearTable(tablewidget)
        self.gcpsNumValue.setText('')
        self.gcpsProjectionValue.setText('')

    def _setupGCPs(self, gcplist, projection):
        self._resetGCPs()
        if not gcplist:
            # Disable the GCPs tab
            self.tabWidget.setTabEnabled(2, False)

        tablewidget = self.gcpsTableWidget

        self.gcpsProjectionValue.setText(projection)
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
        tablewidget.setSortingEnabled(sortingenabled)


#~ class SubDatasetInfoDialog(DatasetInfoDialog):

    #~ def __init__(self, subdataset, parent=None, flags=QtCore.Qt.Widget):
        #~ assert dataset, 'a valid GDAL dataset expected'
        #~ DatasetInfoDialog.__init__(self, subdataset, parent, flags)
