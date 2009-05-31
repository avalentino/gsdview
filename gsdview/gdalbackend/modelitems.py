### Copyright (C) 2008 Antonio Valentino <a_valentino@users.sf.net>

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

'''GDAL items for PyQt4 QStandardItemModel.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date: 2008-12-22 16:52:46 +0100 (lun, 22 dic 2008) $'
__revision__ = '$Revision: 274 $'

import os
import re

from osgeo import gdal
from PyQt4 import QtCore, QtGui

import info
import gdalqt4
import gdalsupport
import resources

from gsdview import utils


class MajorObjectItem(QtGui.QStandardItem):
    iconfile = ':/gdalbackend/generic.svg'
    _typeoffset = 100
    backend = info.name

    def __init__(self, gdalobj):
        if isinstance(gdalobj, MajorObjectItem):
            self._obj = gdalobj._obj
        else:
            self._obj = gdalobj

        # @TODO: don't use self._obj if __getattr__ is set
        #description = os.path.basename(self._obj.GetDescription())
        if self._obj:
            description = self._obj.GetDescription()
        else:
            description = ''

        QtGui.QStandardItem.__init__(self, QtGui.QIcon(self.iconfile),
                                     description)
        self.setToolTip(description)

    # Give items the same iterface of GDAL objects.
    # NOTE: the widgets module doesn't need to import modelitems
    def __getattr__(self, name):
        return getattr(self._obj, name)

    def type(self):
        return QStandardItem.UserType + self._typeoffset

    def _close(self):
        while self.hasChildren():
            try:
                self.child(0)._close()
            except AttributeError:
                self._mainwin.logger.debug('unexpected child item class: '
                                '"%s"' % type(self.child(index)).__name__)
            self.removeRow(0)


class BandItem(MajorObjectItem):
    '''Raster band item

    This class implements both the QStandardItem and the gdal.Band interface.
    It also as attatched a graphics scene containing a GdalGraphicsItem

    :Extra attributes:

    - scene
    - graphicsitem

    '''

    iconfile = ':/gdalbackend/rasterband.svg'
    _typeoffset = MajorObjectItem._typeoffset + 10

    def __init__(self, band):
        super(BandItem, self).__init__(band)
        self._setup_children()
        self.scene = None
        self.graphicsitem = None

        # @TODO: check
        self.scene, self.graphicsitem = self._setup_scene()

    def footprint(self):
        return self.parent().footprint()

    def get_cmapper(self):
        return self.parent().cmapper

    cmapper = property(get_cmapper) # readonly # @TODO: check

    def GetOverview(self, index):
        if (index < 0) or (index >= self._obj.GetOverviewCount()):
            return None
        if self.rowCount() <= index:
            self._setup_children()
        return self.child(index)

    def GetOverviewCount(self):
        if self.rowCount() < self._obj.GetOverviewCount():
            self._setup_children()
        return self.rowCount()

    def _setup_children(self):
        for index in range(self.rowCount(), self._obj.GetOverviewCount()):
            ovr = self._obj.GetOverview(index)
            item = OverviewItem(ovr)
            if not item.text():
                description = '%s n. %d' % (QtGui.qApp.tr('Overview'), index)
                item.setText(description)
                item.setToolTip(description)
            self.appendRow(item)

    def _setup_scene(self, parent=None):
        # @TODO: check for scenes with no parent
        scene = QtGui.QGraphicsScene(parent)
        #~ # @TODO: use a factory function (RGB etc)
        graphicsitem = gdalqt4.GdalGraphicsItem(self)
        scene.addItem(graphicsitem)
        return scene, graphicsitem

    #~ def _close(self):
        #~ self._obj.FlushCache()
        #~ super(BandItem, self).close()

    ###########################################################################
    ### BEGIN #################################################################
    # @TODO: check
    def _reopen(self, gdalobj=None):
        if not gdalobj:
            # assume self._obj has already been set from caller
            gdalobj = self._obj
        else:
            self._obj = gdalobj
        if self.rowCount() > gdalobj.GetOverviewCount():
            logging.warning('unable to reopen raster band: '
                            'unexpected number of overviews')
            return

        #~ self._close()    # @TODO: remove
        self._setup_children()
        #self.model().itemChanged(self)
        self.model().emit(QtCore.SIGNAL('itemChanged(QStandardItem*)'), self)

    ### END ###################################################################
    ###########################################################################


class OverviewItem(BandItem):
    iconfile = ':/gdalbackend/overview.svg'
    _typeoffset = BandItem._typeoffset + 1

#~ class VirtualBandItem(BandItem):
    #~ iconfile = ':/gdalbackend/virtualband.svg'
    #~ _typeoffset = BandItem._typeoffset + 2
    # @TODO: remove
    #~ actions = BandItem.actions + ('Delete',)
    #~ #defaultaction = 'Open'


class BaseDatasetItem(MajorObjectItem):
    '''Base dataset item

    This class implements both the QStandardItem and the gdal.Dataset
    interface.

    :Attributes:

    - filename
    - cmapper -- coordiante mapper

    '''

    iconfile = ':/gdalbackend/dataset.svg'
    _typeoffset = MajorObjectItem._typeoffset + 100

    def _open_gdal_dataset(self, filename, mode=gdal.GA_ReadOnly):
        filename = os.path.abspath(filename)
        filename = os.path.normpath(filename)
        gdalobj = gdal.Open(filename, mode)
        if gdalobj is None:
            raise ValueError('"%s" is not a valid GDAL dataset' %
                                                    os.path.basename(filename))
        return gdalobj, filename

    def __init__(self, filename, mode=gdal.GA_ReadOnly):
        gdalobj, filename = self._open_gdal_dataset(filename, mode)
        super(BaseDatasetItem, self).__init__(gdalobj)
        if os.path.basename(filename) in self.text():
            self.setText(os.path.basename(filename))
        self.filename = filename
        self._mode = mode
        self._setup_children()

        # TODO: improve attribute name
        self.cmapper = gdalsupport.coordinate_mapper(self._obj)

    def footprint(self):
        '''Return the dataset footprint as a QPolygonF or None'''

        if not self.cmapper:
            return

        lat, lon = self.cmapper.imgToGeoGrid([0.5, self.RasterXSize - 0.5],
                                             [0.5, self.RasterYSize - 0.5])
        polygon = QtGui.QPolygonF([QtCore.QPointF(lon[0,0], lat[0,0]),
                                   QtCore.QPointF(lon[0,1], lat[0,1]),
                                   QtCore.QPointF(lon[1,1], lat[1,1]),
                                   QtCore.QPointF(lon[1,0], lat[1,0])])

        return polygon

    def GetRasterBand(self, index):
        # @NOTE: raster bands numbering starts from 1
        if (index < 1) or (index > self._obj.RasterCount):
            return None
        # @NOTE: raster bands are always inserted before subdatasets
        return self.child(index-1)

    #~ def _getRasterCount(self):
        #~ # @TODO: check
        #~ #if self.rowCount() < self._obj.RasteCount:
        #~ #    self._setup_children()
        #~ return self._obj.RasteCount

    #~ RasterCount = property(_getRasterCount)

    def GetSubDatasets(self):
        # @NOTE: raster bands are always inserted before subdatasets
        return [self.child(index) for index in range(self.RasterCount,
                                                     self.rowCount())]

    def _setup_child_bands(self):
        # @NOTE: raster bands are always inserted before subdatasets
        for index in range(self.rowCount(), self._obj.RasterCount):
            item = BandItem(self._obj.GetRasterBand(index+1))
            if not item.text():
                description = '%s n. %d' % (QtGui.qApp.tr('Raster Band'),
                                            index+1)
                item.setText(description)
                item.setToolTip(description)
            self.appendRow(item)

    def _setup_child_subdatasets(self):
        #~ subdatasets = self._obj.GetSubDatasets()
        #~ subdatasets = subdatasets[self.rowCount():]
        #~ for index, (path, extrainfo) in enumerate(subdatasets):
            #~ # @TODO: pass full path for the sub-dataet filename (??)
            #~ item = SubDatasetItem(path, extrainfo)
            #~ if not item.text():
                #~ description = '%s n. %d' % (QtGui.qApp.tr('Sub Datset'),
                                            #~ index + self.rowCount())
                #~ item.setText(description)
                #~ item.setToolTip(description)
            #~ self.appendRow(item)
        # @COMPATIBILITY: workaround for GDAL versins older than 1.6.1
        metadata = self._obj.GetMetadata('SUBDATASETS')
        subdatasets = [key for key in metadata if key.endswith('NAME')]
        # HDF5 driver incorrectly starts subdataset enumeration from 0
        # In order to handle both cases N+1 subdatasets are scanned
        for index in range(len(subdatasets)+1):
            try:
                path = metadata['SUBDATASET_%d_NAME' % index]
            except KeyError:
                # @NOTE: this is another workaround for the bug in subdatasets
                #        handling in HDF5 driver for GDAL < 1.6.1
                continue
            extrainfo = metadata['SUBDATASET_%d_DESC' % index]
            # @TODO: pass full path for the sub-dataet filename (??)
            item = SubDatasetItem(path, extrainfo)
            if not item.text():
                description = '%s n. %d' % (QtGui.qApp.tr('Sub Datset'),
                                            index)
                item.setText(description)
                item.setToolTip(description)
            # @NOTE: raster bands are always inserted before subdatasets
            self.appendRow(item)

    def _setup_children(self):
        # @NOTE: a dataset can't have both raster bands and subdatasets
        self._setup_child_bands()
        self._setup_child_subdatasets()

    #~ def _close(self):
        #~ self._obj.FlushCache()
        #~ super(DatasetItem, self)._close()

    def close(self):
        self._close()
        parent = self.parent()
        if not parent:
            parent = self.model().invisibleRootItem()
        parent.removeRow(self.row())


class CachedDatasetItem(BaseDatasetItem):
    _typeoffset = BaseDatasetItem._typeoffset + 1
    CACHEDIR = os.path.expanduser(os.path.join('~', '.gsdview', 'cache'))

    def __init__(self, filename, cachedir=None):
        gdalobj, filename = super(CachedDatasetItem,
                                  self)._open_gdal_dataset(filename)
        self.id = gdalsupport.uniqueDatasetID(gdalobj)

        # Build the virtual dataset filename
        if cachedir is None:
            cachedir = self.CACHEDIR
        cachedir = os.path.join(cachedir, self.id)
        if not os.path.isdir(cachedir):
            os.makedirs(cachedir)
        self.vrtfilename = os.path.join(cachedir, 'virtual-dataset.vrt')

        # Create the virtual dataset
        # @TODO: check 'openshared'
        _vrtdataset = None
        if os.path.exists(self.vrtfilename):
            # @TODO: check if opening the dataset in update mode
            #        (gdal.GA_Update) is a better solution
            _vrtdataset = gdal.Open(self.vrtfilename)

        if _vrtdataset is None:
            # Hendle both non existing self.vrtfilename and errors in opening
            # existing self.vrtfilename
            driver = gdal.GetDriverByName('VRT')
            _vrtdataset = driver.CreateCopy(self.vrtfilename, gdalobj)

        if _vrtdataset is None:
            raise ValueError('unable to open the GDAL virtual dataset: "%s"' %
                                            os.path.basename(self.vrtfilename))
        del _vrtdataset, gdalobj

        super(CachedDatasetItem, self).__init__(self.vrtfilename, gdal.GA_Update)

        # if description include the filename then set the basename of the
        # original dataset
        if os.path.basename(self.vrtfilename) in self.text():
            self.setText(os.path.basename(filename))

    ###########################################################################
    ### BEGIN #################################################################
    # @TODO: check
    def reopen(self):
        gdalobj = gdal.Open(self.vrtfilename, self._mode)
        if gdalobj.RasterCount != self.RasterCount:
            logging.warning('unable to reopen dataset: '
                            'unexpected number of raster bands')
            return

        # @WARNING: an error here would require node removel
        for index in range(1, self.RasterCount+1):
            item = self.GetRasterBand(index)
            # @WARNING: using private interface
            #item._obj = gdalobj.GetRasterBand(index)
            #item._reopen()
            item._reopen(gdalobj.GetRasterBand(index))

        self._obj = gdalobj
        #self.model().itemChanged(self)
        self.model().emit(QtCore.SIGNAL('itemChanged(QStandardItem*)'), self)

    ### END ###################################################################
    ###########################################################################

#~ class DatasetItem(BaseDatasetItem):
class DatasetItem(CachedDatasetItem):
    pass

class SubDatasetItem(DatasetItem):
    iconfile = ':/gdalbackend/subdataset.svg'
    _typeoffset = DatasetItem._typeoffset + 10

    def __init__(self, gdalfilename, extrainfo=''):
        # @NOTE: never call DatasetItem.__init__
        MajorObjectItem.__init__(self, None)
        self.setText(extrainfo)
        self.setToolTip(extrainfo)

        self.filename = gdalfilename
        self.extrainfo = extrainfo

        if self._obj:
            self._setup_children()

    def isopen(self):
        return self._obj is not None

    def open(self):
        gdalobj = gdal.Open(self.filename)
        if not gdalobj:
            raise ValueError('"%s" is not a valid GDAL dataset' %
                                                    os.path.basename(filename))
        self._obj = gdalobj

        # @TODO: check
        description = self._obj.GetDescription()

        self._setup_children()

    def close(self):
        # @NOTE: don't call the parent "close()" method because DatasetItem
        #        reoves itself from the model when closed and this is not the
        #        desired behaviour
        self._close()
        self._obj = None

    def __getattr__(self, name):
        if self._obj:
            return DatasetItem.__getattr__(self, name)

        raise RuntimeError('unable to retrieve "RasterCount" from a closed '
                           'object')
