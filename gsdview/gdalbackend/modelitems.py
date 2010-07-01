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


'''GDAL items for PyQt4 QStandardItemModel.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'

import os
import logging

from osgeo import gdal
from PyQt4 import QtCore, QtGui

from gsdview import qt4support
from gsdview.errors import OpenError

from gsdview.gdalbackend import info
from gsdview.gdalbackend import gdalqt4
from gsdview.gdalbackend import gdalsupport


class MajorObjectItem(QtGui.QStandardItem):
    iconfile = qt4support.geticon('metadata.svg', __name__)
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
            description = self._obj.GetDescription().strip()
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
        return QtGui.QStandardItem.UserType + self._typeoffset

    def _closeChildren(self):
        while self.hasChildren():
            try:
                self.child(0)._closeChildren()
                if hasattr(self.child(0), '_obj'):
                    self.child(0)._obj = None
            except AttributeError:
                logging.debug('unexpected child item class: "%s"' %
                                                type(self.child(0)).__name__)
            # @NOTE: use takeRow instead of removeRow in order to avoid the
            #        underlying C/C++ object is deleted before all sub-windows
            #        that hold a reference to the stditem are destroyed
            self.takeRow(0)


class BandItem(MajorObjectItem):
    '''Raster band item.

    This class implements both the QStandardItem and the gdal.Band interface.
    It also as attatched a graphics scene containing a GdalGraphicsItem

    '''

    iconfile = qt4support.geticon('rasterband.svg', __name__)
    _typeoffset = MajorObjectItem._typeoffset + 10

    def __init__(self, band):
        assert band is not None
        super(BandItem, self).__init__(band)
        self._setup_children()

        #: graphics scene associated to the raster band
        self.scene = None

        #: graphics item representing the raster band
        self.graphicsitem = None

        # @TODO: lazy behaviour: postpone the scene/view initialization when
        #        it is actualy needed
        scene, graphicsitem = self._setup_scene()
        self.scene = scene
        self.graphicsitem = graphicsitem

    def footprint(self):
        return self.parent().footprint()

    # readonly
    @property
    def cmapper(self):
        '''Coordinate mapper object.'''

        return self.parent().cmapper

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
        try:
            # @TODO: check for scenes with no parent
            scene = QtGui.QGraphicsScene(parent)
            graphicsitem = gdalqt4.graphicsItemFactory(self)
            scene.addItem(graphicsitem)
            return scene, graphicsitem
        except NotImplementedError:  #(NoImplementedError, TypeError):
            return None, None

    def close(self):
        self._obj.FlushCache()
        super(BandItem, self).close()
        self.graphicsitem = None
        self.scene.clear()
        self.scene = None
        self._obj = None

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

        #~ self._closeChildren()    # @TODO: remove
        self._setup_children()
        self.model().emit(QtCore.SIGNAL('itemChanged(QStandardItem*)'), self)


class OverviewItem(BandItem):
    iconfile = qt4support.geticon('overview.svg', __name__)
    _typeoffset = BandItem._typeoffset + 1

#~ class VirtualBandItem(BandItem):
    #~ iconfile = qt4support.geticon('virtualband.svg', __name__)
    #~ _typeoffset = BandItem._typeoffset + 2
    # @TODO: remove
    #~ actions = BandItem.actions + ('Delete',)
    #~ #defaultaction = 'Open'


class DatasetItem(MajorObjectItem):
    '''Dataset item

    This class implements both the QStandardItem and the gdal.Dataset
    interface.

    '''

    iconfile = qt4support.geticon('dataset.svg', __name__)
    _typeoffset = MajorObjectItem._typeoffset + 100

    def __init__(self, filename, mode=gdal.GA_ReadOnly):
        filename = os.path.abspath(filename)
        gdalobj = self._checkedopen(filename, mode)
        super(DatasetItem, self).__init__(gdalobj)
        if os.path.basename(filename) in self.text():
            self.setText(os.path.basename(filename))

        #: dataset filename
        self.filename = filename
        self._mode = mode
        self._setup_children()

        #: coordiante mapper
        self.cmapper = gdalsupport.coordinate_mapper(self._obj)

        # @TODO: lazy behaviour: postpone the scene/view initialization when
        #        it is actualy needed
        scene, graphicsitem = self._setup_scene()

        #: graphics scene associated to the item
        self.scene = scene

        #: graphics item representing the dataset
        self.graphicsitem = graphicsitem

    def _checkedopen(self, filename, mode=gdal.GA_ReadOnly):
        try:
            gdalobj = gdal.Open(filename, mode)
        except RuntimeError, e:
            # @TODO: fix
            # @NOTE: explicitly reset the GDAL error status to workaround
            #        bug #3077 (http://trac.osgeo.org/gdal/ticket/3077)
            gdal.ErrorReset()

            # NOTE: this is needed when GDAL exceptions are enabled
            raise OpenError(str(e))

        if gdalobj is None:
            raise OpenError('"%s" is not a valid GDAL dataset' %
                                                    os.path.basename(filename))
        return gdalobj

    def _setup_scene(self, parent=None):
        try:
            # @TODO: check
            #graphicsitem = gdalqt4.graphicsItemFactory(self)
            graphicsitem = gdalqt4.GdalRgbGraphicsItem(self)
        except TypeError:
            # dataset is not an RGB image
            return None, None
        else:
            scene = QtGui.QGraphicsScene(parent)
            scene.addItem(graphicsitem)
            return scene, graphicsitem

    def footprint(self):
        '''Return the dataset geographic footprint as a QPolygonF.

        The geographic footprint is a QPolygonF containing the four
        vertices of the image in geographic coordinates.
        If no geographic info is available in the dataset None is
        returned.

        '''

        if not self.cmapper:
            return

        lon, lat = self.cmapper.imgToGeoGrid([0.5, self.RasterXSize - 0.5],
                                             [0.5, self.RasterYSize - 0.5])
        polygon = QtGui.QPolygonF([QtCore.QPointF(lon[0, 0], lat[0, 0]),
                                   QtCore.QPointF(lon[0, 1], lat[0, 1]),
                                   QtCore.QPointF(lon[1, 1], lat[1, 1]),
                                   QtCore.QPointF(lon[1, 0], lat[1, 0])])

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

    def _setup_child_bands(self, gdalobj):
        # @NOTE: raster bands are always inserted before subdatasets
        for index in range(self.rowCount(), gdalobj.RasterCount):
            item = BandItem(gdalobj.GetRasterBand(index+1))
            if not item.text():
                description = '%s n. %d' % (QtGui.qApp.tr('Raster Band'),
                                            index+1)
                item.setText(description)
                item.setToolTip(description)
            self.appendRow(item)

    def _setup_child_subdatasets(self, gdalobj):
        # @COMPATIBILITY: the GetSubDatasets() dataset method is only available
        #                 in GDAL >= 1.6.1
        metadata = gdalobj.GetMetadata('SUBDATASETS')
        subdatasets = [key for key in metadata if key.endswith('NAME')]
        # HDF5 driver incorrectly starts subdataset enumeration from 0
        # In order to handle both cases N+1 subdatasets are scanned
        for index in range(len(subdatasets)+1):
            try:
                path = metadata['SUBDATASET_%d_NAME' % index]
            except KeyError:
                # @NOTE: this is a workaround for a bug in subdatasets
                #        handling in HDF5 driver for GDAL < 1.6.1
                continue
            extrainfo = metadata['SUBDATASET_%d_DESC' % index]
            # @TODO: pass full path for the sub-dataset filename (??)
            item = SubDatasetItem(path, extrainfo)
            if not item.text():
                description = '%s n. %d' % (QtGui.qApp.tr('Sub Datset'),
                                            index)
                item.setText(description)
                item.setToolTip(description)
            # @NOTE: raster bands are always inserted before subdatasets
            self.appendRow(item)

    def _setup_children(self):
        self._setup_child_bands(self._obj)
        self._setup_child_subdatasets(self._obj)

    #~ def _closeChildren(self):
        #~ self._obj.FlushCache()
        #~ super(DatasetItem, self)._closeChildren()

    def close(self):
        self._closeChildren()
        parent = self.parent()
        if not parent:
            parent = self.model().invisibleRootItem()
        # @NOTE: use takeRow instead of removeRow in order to avoid the
        #        underlying C/C++ object is deleted before all sub-windows
        #        that hold a reference to the stditem are destroyed
        parent.takeRow(self.row())
        self._obj = None # @TODO: check


class CachedDatasetItem(DatasetItem):
    _typeoffset = DatasetItem._typeoffset + 1

    CACHEDIR = os.path.expanduser(os.path.join('~', '.gsdview', 'cache'))

    def __init__(self, filename, mode=gdal.GA_Update):
        # @TODO: check
        if mode == gdal.GA_ReadOnly:
            logging.warning('GDAL open mode ignored in cached datasets.')
            mode = gdal.GA_Update

        filename = os.path.abspath(filename)
        gdalobj = self._checkedopen(filename, gdal.GA_ReadOnly)
        # @NOTE: drop DataSetItem initializer
        MajorObjectItem.__init__(self, gdalobj)
        if os.path.basename(filename) in self.text():
            self.setText(os.path.basename(filename))

        #: dataset filename
        self.filename = filename
        self._mode = mode

        vrtfilename, vrtobj = self._vrtinit(self._obj)

        #: filename of the cached virtual dataset
        self.vrtfilename = vrtfilename
        self._vrtobj = vrtobj

        self._setup_children()

        #: coordinate mapper
        self.cmapper = gdalsupport.coordinate_mapper(self._obj)

        # @TODO: lazy behaviour: postpone the scene/view initialization when
        #        it is actualy needed
        scene, graphicsitem = self._setup_scene()

        #: graphics scene associated to the item
        self.scene = scene

        #: graphics item representing the dataset
        self.graphicsitem = graphicsitem

    def _vrtinit(self, gdalobj, cachedir=None):
        # Build the virtual dataset filename
        if cachedir is None:
            id_ = gdalsupport.uniqueDatasetID(gdalobj)
            cachedir = self.CACHEDIR
            cachedir = os.path.join(cachedir, id_)
        if not os.path.isdir(cachedir):
            os.makedirs(cachedir)
        vrtfilename = os.path.join(cachedir, 'virtual-dataset.vrt')

        # Create the virtual dataset
        # @TODO: check 'openshared'
        vrtdataset = None
        if os.path.exists(vrtfilename):
            # @TODO: check if opening the dataset in update mode
            #        (gdal.GA_Update) is a better solution
            vrtdataset = gdal.Open(vrtfilename, gdal.GA_Update)

        if vrtdataset is None:
            # Hendle both non existing self.vrtfilename and errors in opening
            # existing self.vrtfilename
            driver = gdal.GetDriverByName('VRT')
            vrtdataset = driver.CreateCopy(vrtfilename, gdalobj)

        if vrtdataset is None:
            raise ValueError('unable to open the GDAL virtual dataset: "%s"' %
                                            os.path.basename(vrtfilename))
        return vrtfilename, vrtdataset

    # Give items the same iterface of GDAL objects.
    # NOTE: the widgets module doesn't need to import modelitems
    def __getattr__(self, name):
        if name in ('GetDescription', 'GetDriver', 'GetSubDatasets'):
            return getattr(self._obj, name)
        return getattr(self._vrtobj, name)

    def GetMetadata(self, domain=''):
        # @TODO: handle domain.startswith('xml:') and domain == 'OVERVIEW'
        if domain in ('IMAGE_STRUCTURE', 'SUBDATASETS'):
            return self._obj.GetMetadata(domain)
        return self._obj.GetMetadata(domain)

    def GetMetadata_Dict(self, domain=''):
        # @TODO: handle domain.startswith('xml:') and domain == 'OVERVIEW'
        if domain in ('IMAGE_STRUCTURE', 'SUBDATASETS'):
            return self._obj.GetMetadata_Dict(domain)
        return self._obj.GetMetadata_Dict(domain)

    def GetMetadata_List(self, domain=''):
        # @TODO: handle domain.startswith('xml:') and domain == 'OVERVIEW'
        if domain in ('IMAGE_STRUCTURE', 'SUBDATASETS'):
            return self._obj.GetMetadata_List(domain)
        return self._obj.GetMetadata_List(domain)

    if hasattr(gdal.Dataset, 'GetMetadataItem'):
        def GetMetadataItem(self, domain=''):
            # @TODO: handle domain.startswith('xml:') and domain == 'OVERVIEW'
            if domain in ('IMAGE_STRUCTURE', 'SUBDATASETS'):
                return self._obj.GetMetadataItem(domain)
            return self._obj.GetMetadataItem(domain)

    def _setup_children(self):
        self._setup_child_bands(self._vrtobj)
        self._setup_child_subdatasets(self._obj)

    def reopen(self):
        gdalobj = gdal.Open(self.vrtfilename, gdal.GA_Update)

        if gdalobj.RasterCount < self.RasterCount:
            logging.warning('unable to reopen dataset: '
                            'unexpected number of raster bands')
            return

        # @WARNING: an error here would require node removal
        for index in range(1, self.RasterCount+1):
            item = self.GetRasterBand(index)
            item._reopen(gdalobj.GetRasterBand(index))

        self._vrtobj = gdalobj

        # @TODO: check
        #self.model().itemChanged(self)
        self.model().emit(QtCore.SIGNAL('itemChanged(QStandardItem*)'), self)


def datasetitem(filename):
    '''Factory for dataset items.'''

    # Some dataset has only sub-datasets (no raster band).
    # In this case it is not possible to use a virtual datasets like
    # CachedDatasetItem does
    try:
        return CachedDatasetItem(filename)
    except OpenError:
        # @TODO: remove virtualfile created by CachedDatasetItem
        return DatasetItem(filename)

class SubDatasetItem(CachedDatasetItem):
    iconfile = qt4support.geticon('subdataset.svg', __name__)
    _typeoffset = DatasetItem._typeoffset + 10

    def __init__(self, gdalfilename, extrainfo=''):
        # @NOTE: never call DatasetItem.__init__
        MajorObjectItem.__init__(self, None)
        self.setText(extrainfo)
        self.setToolTip(extrainfo)

        #: dataset filename
        self.filename = gdalfilename

        #: GDAL sub-dataset info
        self.extrainfo = extrainfo
        self._mode = None

        #: coordinate mapper
        self.cmapper = None

        #: filename of the cached virtual dataset
        self.vrtfilename = None

        # @TODO: check if it is possible that self._obj not None at this point
        if self._obj:
            self._setup_children()

    def isopen(self):
        return self._obj is not None

    # @staticmethod
    def _normalize(self, filename):
        filename = filename.replace(':', '_')
        filename = filename.replace('/', '_')
        filename = filename.replace('\\', '_')
        return filename

    def open(self, cachedir=None):
        if not cachedir:
            cachedir = os.path.join(self.CACHEDIR,
                                    self._normalize(self.filename))

        gdalobj = self._checkedopen(self.filename)
        self.vrtfilename = self._vrtinit(gdalobj, cachedir)
        del gdalobj

        filename = os.path.abspath(self.vrtfilename)
        gdalobj = self._checkedopen(filename, gdal.GA_Update)

        self._obj = gdalobj
        self._mode = gdal.GA_Update
        self._setup_children()

        # TODO: improve attribute name
        self.cmapper = gdalsupport.coordinate_mapper(self._obj)

    def close(self):
        # @NOTE: don't call the parent "close()" method because DatasetItem
        #        removes itself from the model when closed and this is not the
        #        desired behaviour
        self._closeChildren()
        self._mode = None
        self.cmapper = None
        self.vrtfilename = None
        self._obj = None

    def __getattr__(self, name):
        if self._obj:
            return DatasetItem.__getattr__(self, name)
        elif name in dir(gdal.Dataset):
            raise RuntimeError('unable to access "%s" on a non open '
                               'object' % name)
        else:
            raise AttributeError(name)
