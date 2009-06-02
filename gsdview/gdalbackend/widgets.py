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

# -*- coding: UTF8 -*-

'''Widgets and dialogs for GSDView.'''

__author__   = '$Author$'
__date__     = '$Date$'
__revision__ = '$Revision$'

import os
import logging

from osgeo import gdal
from PyQt4 import QtCore, QtGui, uic

from gsdview.widgets import get_filedialog

import gdalsupport


class GDALInfoWidget(QtGui.QWidget):
    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'gdalinfo.ui')

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QWidget.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

        # @TODO: check for available info in gdal 1.5 and above
        try:
            self.gdalReleaseNameValue.setText(gdal.VersionInfo('RELEASE_NAME'))
            self.gdalReleaseDateValue.setText(gdal.VersionInfo('RELEASE_DATE'))
        except AttributeError:
            self.gdalVersionGroupBox.hide()

        self.updateCacheInfo()

        #~ gdal.GetConfigOption('CPL_DEBUG', 'OFF')
        #~ gdal.GetConfigOption('GDAL_PAM_ENABLED', "NULL")
        #~ gdal.GetConfigOption(GDAL_DATA) (path of the GDAL "data" directory)
        #~ #gdal.GetConfigOption(GDAL_CACHEMAX) (memory used internally for caching in megabytes)

        self.setGdalDriversTab()

    def setGdalDriversTab(self):
        self.gdalDriversNumValue.setText(str(gdal.GetDriverCount()))

        tableWidget = self.gdalDriversTableWidget
        #tableWidget.clear()
        #tableWidget.setHorizontalHeaderLabels(['Software', 'Version', 'Home Page'])
        tableWidget.verticalHeader().hide()
        hheader = tableWidget.horizontalHeader()
        hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)
        hheader.setStretchLastSection(True)
        tableWidget.setRowCount(gdal.GetDriverCount())
        sortingenabled = tableWidget.isSortingEnabled()
        tableWidget.setSortingEnabled(False)

        for row in range(gdal.GetDriverCount()):
            driver = gdal.GetDriver(row)
            # @TODO: check for available ingo in gdal 1.5 and above
            tableWidget.setItem(row, 0, QtGui.QTableWidgetItem(driver.ShortName))
            tableWidget.setItem(row, 1, QtGui.QTableWidgetItem(driver.LongName))
            tableWidget.setItem(row, 2, QtGui.QTableWidgetItem(driver.GetDescription()))
            tableWidget.setItem(row, 3, QtGui.QTableWidgetItem(str(driver.HelpTopic)))

            metadata = driver.GetMetadata()
            if metadata:
                tableWidget.setItem(row, 4, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_EXTENSION, ''))))
                tableWidget.setItem(row, 5, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_MIMETYPE, ''))))
                tableWidget.setItem(row, 6, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_CREATIONDATATYPES, ''))))

                data = metadata.pop(gdal.DMD_CREATIONOPTIONLIST, '')
                # @TODO: parse xml
                tableItem = QtGui.QTableWidgetItem(data)
                tableItem.setToolTip(data)
                tableWidget.setItem(row, 7, tableItem)

                metadata.pop(gdal.DMD_HELPTOPIC, '')
                metadata.pop(gdal.DMD_LONGNAME, '')

                metadatalist = ['%s=%s' % (k, v) for k, v in metadata.items()]
                tableItem = QtGui.QTableWidgetItem(', '.join(metadatalist))
                tableItem.setToolTip('\n'.join(metadatalist))
                tableWidget.setItem(row, 8, tableItem)

        tableWidget.setSortingEnabled(sortingenabled)
        tableWidget.sortItems(0, QtCore.Qt.AscendingOrder)

    def updateCacheInfo(self):
        self.gdalCacheMaxValue.setText('%.3f MB' % (gdal.GetCacheMax()/1024.**2))
        self.gdalCacheUsedValue.setText('%.3f MB' % (gdal.GetCacheUsed()/1024.**2))

    def showEvent(self, event):
        self.updateCacheInfo()
        QtGui.QWidget.showEvent(self, event)


class GDALPreferencesPage(QtGui.QWidget):
    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'gdal-page.ui')

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QWidget.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

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
        dialog.connect(buttonbox, QtCore.SIGNAL('rejected()'), dialog.reject)
        layout.addWidget(buttonbox)

        dialog.setLayout(layout)
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

            # extra options
            # @TODO
        finally:
            settings.endGroup()


class MajorObjectInfoDialog(QtGui.QDialog):
    def __init__(self, gdalobj, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QDialog.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

        # Metadata Tab
        metadatalist = gdalobj.GetMetadata_List()
        if metadatalist:
            self.metadataNumValue.setText(str(len(metadatalist)))
            self._setMetadata(self.metadataTableWidget, metadatalist)

    def _setMetadata(self, tablewidget, metadatalist):
        self._cleartable(tablewidget)

        if not metadatalist:
            header = tablewidget.horizontalHeader()
            header.setStretchLastSection(True)
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

    def _cleartable(self, tablewidget):
        labels = [str(tablewidget.horizontalHeaderItem(col).text())
                                for col in range(tablewidget.columnCount())]
        tablewidget.clear()
        tablewidget.setHorizontalHeaderLabels(labels)
        #tablewidget.setRowCount(0)


class BandInfoDialog(MajorObjectInfoDialog):

    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'banddialog.ui')

    def __init__(self, band, parent=None, flags=QtCore.Qt.Widget):
        assert band, 'a valid GDAL raster band expected'
        MajorObjectInfoDialog.__init__(self, band, parent, flags)

        # Info Tab
        self._setupInfoTab(band)

    def _setupInfoTab(self, band):
        # Info
        self.descriptionValue.setText(band.GetDescription().strip())
        self.overviewCountValue.setText(str(band.GetOverviewCount()))

        # Data
        self.xSizeValue.setText(str(band.XSize))
        self.ySizeValue.setText(str(band.YSize))
        self.dataTypeValue.setText(gdal.GetDataTypeName(band.DataType))
        self.offsetValue.setText(str(band.GetOffset()))
        self.scaleValue.setText(str(band.GetScale()))
        self.blockSizeValue.setText(str(band.GetBlockSize()))

        # Statisics
        self.minimumValue.setText(str(band.GetMinimum()))
        self.maximumValue.setText(str(band.GetMaximum()))
        self.noDataValue.setText(str(band.GetNoDataValue()))

        # Color
        colorint = band.GetRasterColorInterpretation()
        colorint = gdal.GetColorInterpretationName(colorint)
        self.colorInterpretationValue.setText(colorint)

        # @TODO: handle color table
        self.colorTableValue.setText(str(band.GetRasterColorTable()))

        #~ band.Checksum                   ??
        #~ band.ComputeBandStats           ??
        #~ band.ComputeRasterMinMax        ??
        #~ band.GetStatistics(approx_ok, force)    --> (min, max, mean, stddev)


class DatasetInfoDialog(MajorObjectInfoDialog):

    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'datasetdialog.ui')

    def __init__(self, dataset, parent=None, flags=QtCore.Qt.Widget):
        assert dataset, 'a valid GDAL dataset expected'
        MajorObjectInfoDialog.__init__(self, dataset, parent, flags)

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
        self.descriptionValue.setText(os.path.basename(dataset.GetDescription()))
        self.rasterCountValue.setText(str(dataset.RasterCount))
        self.xSizeValue.setText(str(dataset.RasterXSize))
        self.ySizeValue.setText(str(dataset.RasterYSize))

        self.projectionValue.setText(dataset.GetProjection())
        self.projectionRefValue.setText(dataset.GetProjectionRef())

        xoffset, a11, a12, yoffset, a21, a22 = dataset.GetGeoTransform()
        self.xOffsetValue.setText(str(xoffset))
        self.yOffsetValue.setText(str(a11))
        self.a11Value.setText(str(a12))
        self.a12Value.setText(str(yoffset))
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
            tablewidget.setItem(row, 0, QtGui.QTableWidgetItem(str(gcp.GCPLine)))
            tablewidget.setItem(row, 1, QtGui.QTableWidgetItem(str(gcp.GCPPixel)))
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

    #~ uifile = os.path.join(os.path.dirname(__file__), 'ui', 'subdatasetdialog.ui')

    #~ def __init__(self, subdataset, parent=None, flags=QtCore.Qt.Widget):
        #~ assert dataset, 'a valid GDAL dataset expected'
        #~ DatasetInfoDialog.__init__(self, subdataset, parent, flags)

if __name__ == '__main__':
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

    def test_gdalinfowidget():
        app = QtGui.QApplication(sys.argv)
        dialog = QtGui.QDialog()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(GDALInfoWidget())
        dialog.setLayout(layout)
        dialog.show()
        app.exec_()

    def test_gdalpreferencespage():
        app = QtGui.QApplication(sys.argv)
        dialog = QtGui.QDialog()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(GDALPreferencesPage())
        dialog.setLayout(layout)
        dialog.show()
        app.exec_()

    def test_datasetdialog(dataset):
        app = QtGui.QApplication(sys.argv)
        dialog = DatasetInfoDialog(dataset)
        dialog.show()
        sys.exit(app.exec_())

    def test_rasterbanddialog(band):
        app = QtGui.QApplication(sys.argv)
        dialog = BandInfoDialog(band)
        dialog.show()
        sys.exit(app.exec_())

    logging.basicConfig(level=logging.DEBUG)
    #~ test_gdalinfowidget()
    #~ test_gdalpreferencespage()

    filename = 'ASA_IMM_1PXPDE20020730_095830_000001002008_00108_02166_0066.N1'
    filename = os.path.join(os.path.expanduser('~'), filename)
    dataset = gdal.Open(filename)
    band = dataset.GetRasterBand(1)

    test_datasetdialog(dataset)
    #~ test_rasterbanddialog(band)
