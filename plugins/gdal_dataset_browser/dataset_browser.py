### Copyright (C) 2007 Antonio Valentino <a_valentino@users.sf.net>

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

'''Browser component for GDAL datasets.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date$'
__revision__ = '$Revision$'

import os
import logging

try:
    from osgeo import gdal
except ImportError:
    import gdal

from PyQt4 import QtCore, QtGui

import resources

# @TODO: context menu
#~ class TreeWidget(QtGui.QTreeWidget):
    #~ def __init__(self, parent=0):
        #~ QtGui.QTreeWidget.__init__(self, parent)

class GdalDatasetBrowser(QtGui.QDockWidget):
    def __init__(self, parent=None): #, flags=0):
        #title = self.tr('Dataset Browser')
        QtGui.QDockWidget.__init__(self, 'GDAL Dataset Browser', parent) #, flags)
        #self.setObjectName('datasetBroeserPanel') # @TODO: check

        self.treeWidget = QtGui.QTreeWidget()
        self.treeWidget.setColumnCount(2)
        self.treeWidget.header().setStretchLastSection(True)
        self.setWidget(self.treeWidget)
        self.treeWidget.setHeaderLabels([self.tr('Name'), self.tr('Value')])

        self.item_to_dataset = {}
        self.dataset_to_item = {}

        self.connect(
            self.treeWidget,
            QtCore.SIGNAL('itemDoubleClicked(QTreeWidgetItem*, int)'),
            self.emitOpenBandRequest)

    def emitOpenBandRequest(self, item, col):
        parent = self.parent()
        if parent:
            text = str(item.text(0))
            if text.startswith(self.tr('Raster Band')):       # @TODO: check
                rootItem = item.parent()
                dataset = self.item_to_dataset[rootItem]
                band_id = int(text.split('n.')[-1])
                band = dataset.GetRasterBand(band_id)
                parent.emit(QtCore.SIGNAL('openBandRequest(PyQt_PyObject)'),
                            band)

    def _getMetadataItem(self, metadataList):
        rootItem = QtGui.QTreeWidgetItem()
        rootItem.setIcon(0, QtGui.QIcon(':/images/metadata.svg'))
        rootItem.setText(0, self.tr('Metadata'))
        rootItem.setFirstColumnSpanned(True)

        # @TODO: group metadata by prefix (e.g. "MPH_", "SPH_", "DS_", "CEOS_"
        #        or "TIFFTAG_")

        if metadataList:
            items = []
            for metadataitem in metadataList:
                try:
                    name, value = metadataitem.split('=', 1)
                    item = QtGui.QTreeWidgetItem()
                    item.setText(0, name)
                    item.setText(1, value.rstrip())
                    items.append(item)
                except KeyError, e:
                    # @TODO: fix
                    # This is needed to handle a strange behaviour I get
                    # trying to use the HDF5 driver
                    logging.debug('exceptin caught setting metadata: "%s"' % e)
            rootItem.addChildren(items)
        else:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, self.tr('None'))
            rootItem.addChild(item)

        return rootItem

    def _getDriverItem(self, driver):
        rootItem = QtGui.QTreeWidgetItem()
        rootItem.setIcon(0, QtGui.QIcon(':/images/driver.svg'))
        rootItem.setText(0, self.tr('Driver'))
        rootItem.setToolTip(0, self.tr('GDAL driver.'))
        rootItem.setFirstColumnSpanned(True)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Short name'))
        item.setText(1, driver.ShortName)
        item.setToolTip(1, self.tr('Short name of the driver.'))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Long name'))
        item.setText(1,driver.LongName)
        item.setToolTip(1, self.tr('Long name of the driver.'))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Desctiption'))
        item.setText(1, driver.GetDescription())
        item.setToolTip(1, self.tr('Driver description.'))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Help topic'))
        item.setText(1, driver.HelpTopic)
        item.setToolTip(1, self.tr('Help topic in the GDAL library '
                                   'documentation.'))
        rootItem.addChild(item)

        metadataItem = self._getMetadataItem(driver.GetMetadata_List())
        rootItem.addChild(metadataItem)

        return rootItem

    # @TODO: separate dock widget
    #~ def _getGCPsItem(self, gcpList):
        #~ rootItem = QtGui.QTreeWidgetItem()
        #~ rootItem.setIcon(0, QtGui.QIcon(':/images/gcp.svg'))
        #~ rootItem.setText(0, self.tr('GCPs'))
        #~ rootItem.setToolTip(0, self.tr('Ground Control Points.'))
        #~ rootItem.setFirstColumnSpanned(True)

        #~ item = QtGui.QTreeWidgetItem()
        #~ item.setText(0, self.tr('Id'))
        #~ item.setText(1, self.tr('Line'))
        #~ item.setText(2, self.tr('Pixel'))
        #~ item.setText(3, self.tr('X'))
        #~ item.setText(4, self.tr('Y'))
        #~ item.setText(5, self.tr('Z'))
        #~ rootItem.addChild(item)

        #~ for gcp in gcpList:
            #~ item = QtGui.QTreeWidgetItem()
            #~ item.setText(0, gcp.Id)
            #~ item.setData(1, QtCore.Qt.DisplayRole, QtCore.QVariant(gcp.GCPLine))
            #~ item.setData(2, QtCore.Qt.DisplayRole, QtCore.QVariant(gcp.GCPPixel))
            #~ item.setData(3, QtCore.Qt.DisplayRole, QtCore.QVariant(gcp.GCPX))
            #~ item.setData(4, QtCore.Qt.DisplayRole, QtCore.QVariant(gcp.GCPY))
            #~ item.setData(5, QtCore.Qt.DisplayRole, QtCore.QVariant(gcp.GCPZ))
            #~ item.setData(6, QtCore.Qt.DisplayRole, QtCore.QVariant(gcp.Info))
            #~ rootItem.addChild(item)

        #~ return rootItem

    def _getGCPsItem(self, gcpList):
        # @TODO: improve
        rootItem = QtGui.QTreeWidgetItem()
        rootItem.setIcon(0, QtGui.QIcon(':/images/gcp.svg'))
        rootItem.setText(0, self.tr('GCPs'))
        rootItem.setToolTip(0, self.tr('Ground Control Points.'))
        rootItem.setFirstColumnSpanned(True)

        fmt = 'line=%f, pixel=%f, X=%f, Y=%f, Z=%f'

        for gcp in gcpList:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, 'GCP n. %s' % gcp.Id)
            item.setIcon(0, QtGui.QIcon(':/images/item.svg'))
            item.setText(1, fmt % (gcp.GCPLine, gcp.GCPPixel,
                                   gcp.GCPX, gcp.GCPY, gcp.GCPZ))
            item.setToolTip(1, gcp.Info)
            rootItem.addChild(item)

        return rootItem

    def _getRasterBandItem(self, band):
        rootItem = QtGui.QTreeWidgetItem()
        #rootItem.setObjectName('rasterBand%d' % band_id)
        rootItem.setIcon(0, QtGui.QIcon(':/images/raster-band.svg'))
        rootItem.setText(0, self.tr('Raster band'))
        rootItem.setToolTip(0, self.tr('Raster band.'))
        rootItem.setFirstColumnSpanned(True)

        metadataItem = self._getMetadataItem(band.GetMetadata_List())
        rootItem.addChild(metadataItem)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Desctiption'))
        item.setText(1, band.GetDescription().strip())
        item.setToolTip(1, self.tr('Raster band description.'))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('XSize'))
        item.setData(1, QtCore.Qt.DisplayRole, QtCore.QVariant(band.XSize))
        item.setToolTip(1, self.tr('X size of the raster band.'))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('YSize'))
        item.setData(1, QtCore.Qt.DisplayRole, QtCore.QVariant(band.YSize))
        item.setToolTip(1, self.tr('Y size of the raster band.'))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('DataType'))
        item.setText(1, gdal.GetDataTypeName(band.DataType))
        item.setToolTip(1, self.tr('The pixel data type for this band.'))
        rootItem.addChild(item)

        # @COMPATIBILITY: NG/pymod API
        try:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, self.tr('BlockSize'))
            bandSize = band.GetBlockSize()
            if bandSize:
                bandSize = QtCore.QSize(bandSize[0], bandSize[1])
            item.setData(1, QtCore.Qt.DisplayRole, QtCore.QVariant(bandSize))
            item.setToolTip(1, self.tr('''The "natural" block size of this band.

GDAL contains a concept of the natural block size of rasters so that
applications can organized data access efficiently for some file formats.
The natural block size is the block size that is most efficient for accessing
the format. For many formats this is simple a whole scanline in which case
*pnXSize is set to GetXSize(), and *pnYSize is set to 1.

However, for tiled images this will typically be the tile size.

Note that the X and Y block sizes don't have to divide the image size evenly,
meaning that right and bottom edge blocks may be incomplete.'''))
            rootItem.addChild(item)
        except AttributeError:
            logging.debug('exception caught', exc_info=True)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Minimum'))
        minimum = band.GetMinimum()
        if minimum is None:
            minimum = self.tr('None')
        item.setData(1, QtCore.Qt.DisplayRole, QtCore.QVariant(minimum))
        item.setToolTip(1, self.tr('''The minimum value for this band.

For file formats that don't know this intrinsically, the minimum supported
value for the data type will generally be returned (or None).'''))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Maximum'))
        maximum = band.GetMaximum()
        if maximum is None:
            maximum = self.tr('None')
        item.setData(1, QtCore.Qt.DisplayRole, QtCore.QVariant(maximum))
        item.setToolTip(1, self.tr('''The maximum value for this band.

For file formats that don't know this intrinsically, the maximum supported
value for the data type will generally be returned (or None).'''))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('NoDataValue'))
        noDataValue = band.GetNoDataValue()
        if noDataValue is None:
            noDataValue = self.tr('None')
        item.setData(1, QtCore.Qt.DisplayRole, QtCore.QVariant(noDataValue))
        item.setToolTip(1, self.tr('''The no data value for this band.

If there is no out of data value, an out of range value will generally be
returned. The no data value for a band is generally a special marker value
used to mark pixels that are not valid data. Such pixels should generally
not be displayed, nor contribute to analysis operations.'''))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Offset'))
        offset = band.GetOffset()
        if offset is None:
            offset = self.tr('None')
        item.setData(1, QtCore.Qt.DisplayRole, QtCore.QVariant(offset))
        item.setToolTip(1, self.tr('''The raster value offset.

This value (in combination with the GetScale() value) is used to transform
raw pixel values into the units returned by GetUnits().
For example this might be used to store elevations in GUInt16 bands with a
precision of 0.1, and starting from -100.

  Units value = (raw value * scale) + offset

For file formats that don't know this intrinsically a value of zero is
returned.'''))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Scale'))
        scale = band.GetScale()
        if scale is None:
            scale = self.tr('None')
        item.setData(1, QtCore.Qt.DisplayRole, QtCore.QVariant(scale))
        item.setToolTip(1, self.tr('''The raster value scale.

This value (in combination with the GetOffset() value) is used to transform
raw pixel values into the units returned by GetUnits().
For example this might be used to store elevations in GUInt16 bands with a
precision of 0.1, and starting from -100.

  Units value = (raw value * scale) + offset

For file formats that don't know this intrinsically a value of one is
returned.'''))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('ColorInterpretation'))
        item.setText(1, gdal.GetColorInterpretationName(
                                        band.GetRasterColorInterpretation()))
        msg = '''How should this band be interpreted as color?

CV_Undefined is returned when the format doesn't know anything about the color
interpretation.'''
        item.setToolTip(1, self.tr(msg))
        rootItem.addChild(item)

        # @TODO: handl color table
        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('ColorTable'))
        item.setText(1, str(band.GetRasterColorTable()))
        item.setToolTip(1, self.tr('''The color table associated with band.

If there is no associated color table, the return result is NULL.
The returned color table remains owned by the GDALRasterBand, and can't be
depended on for long, nor should it ever be modified by the caller.'''))
        rootItem.addChild(item)

        #~ band.Checksum                   ??
        #~ band.ComputeBandStats           ??
        #~ band.ComputeRasterMinMax        ??
        #~ band.GetStatistics(approx_ok, force)    --> (min, max, mean, stddev)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('OverviewCount'))
        item.setData(1, QtCore.Qt.DisplayRole,
                     QtCore.QVariant(band.GetOverviewCount()))
        item.setToolTip(1, self.tr('The number of overview layers available.'))
        rootItem.addChild(item)

        for index in range(band.GetOverviewCount()):
            ovrBand = band.GetOverview(index)
            ovrItem = self._getRasterBandItem(ovrBand)
            ovrItem.setText(0, '%s n. %d' % (self.tr('Overview'), index))
            rootItem.addChild(ovrItem)

        return rootItem

    def _getDatasetItem(self, dataset):
        rootItem = QtGui.QTreeWidgetItem()
        rootItem.setIcon(0, QtGui.QIcon(':/images/dataset.svg'))
        rootItem.setText(0, self.tr('Dataset'))
        rootItem.setToolTip(0, self.tr('GDAL dataset.'))
        #rootItem.setText(1, os.path.basename(dataset.GetDescription()))
        rootItem.setFirstColumnSpanned(True)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Desctiption'))
        item.setText(1, os.path.basename(dataset.GetDescription()))
        item.setToolTip(1, '%s\n\n%s' % (self.tr('Dataset name.'),
                                         dataset.GetDescription()))
        rootItem.addChild(item)

        rootItem.addChild(self._getDriverItem(dataset.GetDriver()))

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('Projection'))
        item.setText(1, dataset.GetProjection())
        item.setToolTip(1, self.tr('The projection reference string for this '
                                   'dataset in OGC WKT or PROJ.4 format.'))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('ProjectionRef'))
        item.setText(1, dataset.GetProjectionRef())
        msg = '''The projection definition string for this dataset.

The returned string defines the projection coordinate system of the image in
OpenGIS WKT format.'''
        item.setToolTip(1, self.tr(msg))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('GeoTransform'))
        item.setText(1, ', '.join(map(str, dataset.GetGeoTransform())))
        # @TODO:use QTRansform instead
        #item.setData(1, QtCore.Qt.DisplayRole, QtCore.QVariant(transform))
        msg = '''The affine transformation coefficients.

Fetches the coefficients for transforming between pixel/line (P,L) raster space,
and projection coordinates (Xp,Yp) space.

   Xp = padfTransform[0] + P*padfTransform[1] + L*padfTransform[2];
   Yp = padfTransform[3] + P*padfTransform[4] + L*padfTransform[5];

In a north up image, padfTransform[1] is the pixel width, and padfTransform[5]
is the pixel height. The upper left corner of the upper left pixel is at
position (padfTransform[0],padfTransform[3]).

The default transform is (0,1,0,0,0,1) and it is returned for formats that
don't support transformation to projection coordinates.'''
        item.setToolTip(1, self.tr(msg))
        rootItem.addChild(item)

        metadataItem = self._getMetadataItem(dataset.GetMetadata_List())
        rootItem.addChild(metadataItem)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('GCPProjection'))
        item.setText(1, dataset.GetGCPProjection())
        item.setToolTip(1, self.tr('''Get output projection for GCPs.

The projection string follows the normal rules from ProjectionRef.'''))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('GCPCount'))
        item.setData(1, QtCore.Qt.DisplayRole,
                     QtCore.QVariant(dataset.GetGCPCount()))
        item.setToolTip(1, self.tr('Get number of GCPs.'))
        rootItem.addChild(item)

        rootItem.addChild(self._getGCPsItem(dataset.GetGCPs()))

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('RasterXSize'))
        item.setData(1, QtCore.Qt.DisplayRole,
                     QtCore.QVariant(dataset.RasterXSize))
        item.setToolTip(1, self.tr('The raster width in pixels.'))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('RasterYSize'))
        item.setData(1, QtCore.Qt.DisplayRole,
                     QtCore.QVariant(dataset.RasterYSize))
        item.setToolTip(1, self.tr('The raster height in pixels.'))
        rootItem.addChild(item)

        item = QtGui.QTreeWidgetItem()
        item.setText(0, self.tr('RasterCount'))
        item.setData(1, QtCore.Qt.DisplayRole,
                     QtCore.QVariant(dataset.RasterCount))
        item.setToolTip(1, self.tr('The number of raster bands on this '
                                   'dataset.'))
        rootItem.addChild(item)

        for bandIndex in range(1, dataset.RasterCount+1):
            item = self._getRasterBandItem(dataset.GetRasterBand(bandIndex))
            item.setText(0, '%s n. %d' % (self.tr('Raster Band'), bandIndex))
            rootItem.addChild(item)

        return rootItem

    def setDataset(self, dataset):
        rootItem = self._getDatasetItem(dataset)
        self.treeWidget.addTopLevelItem(rootItem)
        rootItem.setExpanded(True)
        header = self.treeWidget.header()
        header.resizeSections(QtGui.QHeaderView.ResizeToContents)
        rootItem.setText(0, os.path.basename(dataset.GetDescription()))
        #rootItem.setFirstColumnSpanned(True)
        self.dataset_to_item[dataset] = rootItem
        self.item_to_dataset[rootItem] = dataset

    def remveDataset(self, dataset):
        try:
            item = self.dataset_to_item.pop()
            index = self.treeWidget.indexOfTopLevelItem(item)
            self.treeWidget.takeTopLevelItem(index)
        except KeyError:
            pass

    def clear(self):
        self.treeWidget.clear()
        self.dataset_to_item.clear()
        self.item_to_dataset.clear()

if __name__ == '__main__':
    import sys

    try:
        from osgeo import gdal
    except ImportError:
        import gdal

    app = QtGui.QApplication(sys.argv)
    mainWin = QtGui.QMainWindow()
    mainWin.setCentralWidget(QtGui.QTextEdit())

    dataset = gdal.Open('/home/antonio/projects/gsdview/data/ENVISAT/ASA_APM_1PNIPA20031105_172352_000000182021_00227_08798_0001.N1')
    datasetBrowser = GdalDatasetBrowser()
    datasetBrowser.setDataset(dataset)

    mainWin.addDockWidget(QtCore.Qt.LeftDockWidgetArea, datasetBrowser)
    mainWin.showMaximized()
    sys.exit(app.exec_())

