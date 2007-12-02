import os

from PyQt4 import QtCore, QtGui

#import resources       # @TODO: fix

class GdalDatasetBrowser(QtGui.QDockWidget):
    def __init__(self, parent=None): #, flags=0):
        #title = self.tr('Dataset Browser')
        QtGui.QDockWidget.__init__(self, 'Dataset Browser', parent) #, flags)
        self.setObjectName('datasetBroeserPanel')

        self.treeWidget = QtGui.QTreeWidget()
        self.treeWidget.setColumnCount(2)
        self.treeWidget.header().setStretchLastSection(True)
        self.setWidget(self.treeWidget)
        self.treeWidget.setHeaderLabels([self.tr('Name'), self.tr('Value')])

    def _getMetadataItem(self, metadataList, metadataDict):
        rootItem = QtGui.QTreeWidgetItem()
        rootItem.setIcon(0, QtGui.QIcon('images/metadata.svg'))
        rootItem.setText(0, self.tr('Metadata'))

        # @TODO: group metadata by prefix (e.g. "MPH_", "SPH_", "DS_", "CEOS_"
        #        or "TIFFTAG_")

        items = []
        for name in metadataList:
            name = name.split('=')[0]
            item = QtGui.QTreeWidgetItem()
            item.setText(0, name)
            item.setText(1, metadataDict[name])
            items.append(item)

        rootItem.addChildren(items)

        return rootItem

    def _getDriverItem(self, driver):
        rootItem = QtGui.QTreeWidgetItem()
        rootItem.setIcon(0, QtGui.QIcon('images/driver.svg'))
        rootItem.setText(0, self.tr('Driver'))
        rootItem.setToolTip(0, self.tr('GDAL driver.'))

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

        metadataItem = self._getMetadataItem(driver.GetMetadata_List(),
                                             driver.GetMetadata_Dict())
        rootItem.addChild(metadataItem)

        return rootItem

    # @TODO: separate dock widget
    #~ def _getGCPsItem(self, gcpList):
        #~ rootItem = QtGui.QTreeWidgetItem()
        #~ rootItem.setIcon(0, QtGui.QIcon('images/gcp.svg'))
        #~ rootItem.setText(0, self.tr('GCPs'))
        #~ rootItem.setToolTip(0, self.tr('Ground Control Points.'))

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
        rootItem.setIcon(0, QtGui.QIcon('images/gcp.svg'))
        rootItem.setText(0, self.tr('GCPs'))
        rootItem.setToolTip(0, self.tr('Ground Control Points.'))

        fmt = 'line=%f, pixel=%f, X=%f, Y=%f, Z=%f'

        for gcp in gcpList:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, gcp.Id)
            item.setIcon(0, QtGui.QIcon('images/item.svg'))
            item.setText(1, fmt % (gcp.GCPLine, gcp.GCPPixel,
                                   gcp.GCPX, gcp.GCPY, gcp.GCPZ))
            item.setToolTip(1, gcp.Info)
            rootItem.addChild(item)

        return rootItem

    def _getRasterBandItem(self, band):
        '''
            band.Checksum                   ??
            band.ComputeBandStats           ??
            band.ComputeRasterMinMax        ??
            band.DataType                           --> to string
            band.GetBlockSize
            band.GetDescription
            band.GetMaximum
                band.GetMetadata
                band.GetMetadata_Dict
                band.GetMetadata_List
            band.GetMinimum
            band.GetNoDataValue
            band.GetOffset
            band.GetOverview                        --> rootItem
            band.GetOverviewCount
            band.GetRasterColorInterpretation       --> convert enum
            band.GetRasterColorTable
            band.GetScale
            band.GetStatistics(approx_ok, force)    --> (min, max, mean, stddev)
            band.XSize
            band.YSize

        '''

        rootItem = QtGui.QTreeWidgetItem()
        rootItem.setIcon(0, QtGui.QIcon('images/raster-band.svg'))
        rootItem.setText(0, self.tr('Raster band'))
        rootItem.setToolTip(0, self.tr('Raster band.'))

        metadataItem = self._getMetadataItem(band.GetMetadata_List(),
                                             band.GetMetadata_Dict())
        rootItem.addChild(metadataItem)

        return rootItem

    def _getDatasetItem(self, dataset):
        rootItem = QtGui.QTreeWidgetItem()
        rootItem.setIcon(0, QtGui.QIcon('images/dataset.svg'))
        rootItem.setText(0, self.tr('Dataset'))
        rootItem.setToolTip(0, self.tr('GDAL dataset.'))
        #rootItem.setText(1, os.path.basename(dataset.GetDescription()))

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

        metadataItem = self._getMetadataItem(dataset.GetMetadata_List(),
                                             dataset.GetMetadata_Dict())
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

        #~ for bandIndex in range(1, dataset.RasterCount+1):
            #~ item = self._getRasterBandItem(dataset.GetRasterBand(bandIndex))
            #~ rootItem.addChild(item)

        return rootItem

    def setDataset(self, dataset):
        rootItem = self._getDatasetItem(dataset)
        self.treeWidget.addTopLevelItem(rootItem)
        rootItem.setExpanded(True)
        header = self.treeWidget.header()
        header.resizeSections(QtGui.QHeaderView.ResizeToContents)
        rootItem.setText(0, os.path.basename(dataset.GetDescription()))
        rootItem.setFirstColumnSpanned(True)


if __name__ == '__main__':
    import sys
    import gdal


    app = QtGui.QApplication(sys.argv)
    mainWin = QtGui.QMainWindow()
    mainWin.setCentralWidget(QtGui.QTextEdit())

    dataset = gdal.Open('/home/antonio/projects/gsdview/data/ENVISAT/ASA_APM_1PNIPA20031105_172352_000000182021_00227_08798_0001.N1')
    datasetBrowser = GdalDatasetBrowser()
    datasetBrowser.setDataset(dataset)

    mainWin.addDockWidget(QtCore.Qt.LeftDockWidgetArea, datasetBrowser)
    mainWin.show()
    sys.exit(app.exec_())

