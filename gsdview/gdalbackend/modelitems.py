# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2015 Antonio Valentino <antonio.valentino@tiscali.it>
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


'''GDAL items for Qt QStandardItemModel.'''


import os
import logging

from osgeo import gdal

from qtpy import QtCore, QtWidgets, QtGui

from gsdview import qtsupport
from gsdview.errors import OpenError
from gsdview.gdalbackend import info
from gsdview.gdalbackend import gdalqt
from gsdview.gdalbackend import gdalsupport


VISIBLE_OVERVIEW_ITEMS = False

_log = logging.getLogger(__name__)


class MajorObjectItem(QtGui.QStandardItem):
    iconfile = qtsupport.geticon('metadata.svg', __name__)
    _type = QtGui.QStandardItem.UserType + 100
    backend = info.name

    def __init__(self, gdalobj, **kwargs):
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

        super(MajorObjectItem, self).__init__(QtGui.QIcon(self.iconfile),
                                              description)  # , **kwargs)
        self.setToolTip(description)

    # Give items the same iterface of GDAL objects.
    # NOTE: the widgets module doesn't need to import modelitems
    def __getattr__(self, name):
        return getattr(self._obj, name)

    def type(self):
        return self._type

    def _closeChildren(self):
        while self.hasChildren():
            try:
                self.child(0).close()
            except AttributeError:
                _log.debug('unexpected child item class: "%s"',
                           type(self.child(0)).__name__)
            # @NOTE: use takeRow instead of removeRow in order to avoid the
            #        underlying C/C++ object is deleted before all sub-windows
            #        that hold a reference to the stditem are destroyed
            self.takeRow(0)

    def close(self):
        self._closeChildren()
        self._obj = None

    def path(self):
        parent = self.partet()
        parentpath = parent.path() if parent else ''
        return '/'.join(parentpath, str(self.row))


class BandItem(MajorObjectItem):
    '''Raster band item.

    This class implements both the QStandardItem and the
    gdal.Band interface.

    It also as attached a graphics scene containing a GdalGraphicsItem

    '''

    iconfile = qtsupport.geticon('rasterband.svg', __name__)
    _type = MajorObjectItem._type + 10

    def __init__(self, band, **kwargs):
        assert band is not None
        super(BandItem, self).__init__(band, **kwargs)
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
        if VISIBLE_OVERVIEW_ITEMS:
            if (index < 0) or (index >= self._obj.GetOverviewCount()):
                return None
            if self.rowCount() <= index:
                self._setup_children()
            return self.child(index)
        else:
            return self._obj.GetOverview(index)

    def GetOverviewCount(self):
        if VISIBLE_OVERVIEW_ITEMS:
            if self.rowCount() < self._obj.GetOverviewCount():
                self._setup_children()
            return self.rowCount()
        else:
            return self._obj.GetOverviewCount()

    def _setup_children(self):
        if not VISIBLE_OVERVIEW_ITEMS:
            return

        for index in range(self.rowCount(), self._obj.GetOverviewCount()):
            ovr = self._obj.GetOverview(index)
            item = OverviewItem(ovr)
            if not item.text():
                text = 'Overview'
                if QtWidgets.qApp is not None:
                    text = QtWidgets.qApp.tr(text)
                description = '%s n. %d' % (text, index)
                item.setText(description)
                item.setToolTip(description)
            self.appendRow(item)

    def _setup_scene(self, parent=None):
        try:
            # @TODO: check for scenes with no parent
            scene = QtWidgets.QGraphicsScene(parent)
            graphicsitem = gdalqt.graphicsItemFactory(self)
            scene.addItem(graphicsitem)
            return scene, graphicsitem
        except NotImplementedError:  # (NoImplementedError, TypeError):
            return None, None

    def close(self):
        self.scene.clear()
        self.graphicsitem = None
        #self.scene = None    # @WARNINIG: causes problems in event filters
        #self._obj.FlushCache() # @TODO: check
        super(BandItem, self).close()

    def _reopen(self, gdalobj=None):
        if not gdalobj:
            # assume self._obj has already been set from caller
            gdalobj = self._obj
        else:
            self._obj = gdalobj

        if self.rowCount() > gdalobj.GetOverviewCount():
            _log.warning(
                'unable to reopen raster band: unexpected number of overviews')
            return

        if VISIBLE_OVERVIEW_ITEMS:
            levelsmap = dict(zip(gdalsupport.ovrLevels(gdalobj),
                                 range(gdalobj.GetOverviewCount())))

            oldlevelsmap = dict(zip(gdalsupport.ovrLevels(self._obj),
                                range(self._obj.GetOverviewCount())))

            toremove = []
            for level, index in oldlevelsmap.items():
                if level not in levelsmap:
                    #self.removeRow(index)
                    toremove.append(index)
                else:
                    item = self.GetOverview(index)
                    newindex = levelsmap[level]
                    item._reopen(gdalobj.GetOverview(newindex))

            for index in toremove:
                self.takeRow(index)

            for level, index in levelsmap.items():
                if level in oldlevelsmap:
                    continue

                ovr = gdalobj.GetOverview(index)
                item = OverviewItem(ovr)
                if not item.text():
                    text = 'Overview'
                    if QtWidgets.qApp is not None:
                        text = QtWidgets.qApp.tr(text)
                    description = '%s n. %d' % (text, index)
                    item.setText(description)
                    item.setToolTip(description)
                self.insertRow(index, item)

            # @TODO: complete
            #self.sortChildren(0, QtCore.Qt.AscendngOrder)

        self._obj = gdalobj
        self.model().itemChanged.emit(self)


class OverviewItem(BandItem):
    iconfile = qtsupport.geticon('overview.svg', __name__)
    _type = BandItem._type + 1


#~ class VirtualBandItem(BandItem):
    #~ iconfile = qt4support.geticon('virtualband.svg', __name__)
    #~ _type = BandItem._type + 2
    # @TODO: remove
    #~ actions = BandItem.actions + ('Delete',)
    #~ #defaultaction = 'Open'


class DatasetItem(MajorObjectItem):
    '''Dataset item

    This class implements both the QStandardItem and the gdal.Dataset
    interface.

    '''

    iconfile = qtsupport.geticon('dataset.svg', __name__)
    _type = MajorObjectItem._type + 100

    def __init__(self, filename, mode=gdal.GA_ReadOnly, **kwargs):
        filename = os.path.abspath(filename)
        gdalobj = self._checkedopen(filename, mode)
        super(DatasetItem, self).__init__(gdalobj, **kwargs)
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
        except RuntimeError as e:
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
            graphicsitem = gdalqt.GdalRgbGraphicsItem(self)
        except TypeError:
            # dataset is not an RGB image
            return None, None
        else:
            scene = QtWidgets.QGraphicsScene(parent)
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
        polygon = QtGui.QPolygonF([
            QtCore.QPointF(lon[0, 0], lat[0, 0]),
            QtCore.QPointF(lon[0, 1], lat[0, 1]),
            QtCore.QPointF(lon[1, 1], lat[1, 1]),
            QtCore.QPointF(lon[1, 0], lat[1, 0])
        ])

        return polygon

    def GetRasterBand(self, index):
        # @NOTE: raster bands numbering starts from 1
        if (index < 1) or (index > self._obj.RasterCount):
            return None
        # @NOTE: raster bands are always inserted before subdatasets
        return self.child(index - 1)

    def GetSubDatasets(self):
        # @NOTE: raster bands are always inserted before subdatasets
        return [self.child(index) for index in range(self.RasterCount,
                                                     self.rowCount())]

    def _setup_child_bands(self, gdalobj):
        # @NOTE: raster bands are always inserted before subdatasets
        for index in range(self.rowCount(), gdalobj.RasterCount):
            item = BandItem(gdalobj.GetRasterBand(index + 1))
            if not item.text():
                text = 'Raster Band'
                if QtWidgets.qApp is not None:
                    text = QtWidgets.qApp.tr(text)
                description = '%s n. %d' % (text, index + 1)
                item.setText(description)
                item.setToolTip(description)
            self.appendRow(item)

    def _setup_child_subdatasets(self, gdalobj):
        for path, extrainfo in gdalobj.GetSubDatasets():
            # @TODO: pass full path for the sub-dataset filename (??)
            item = SubDatasetItem(path, extrainfo)

            # @NOTE: raster bands are always inserted before subdatasets
            self.appendRow(item)

    def _setup_children(self):
        self._setup_child_bands(self._obj)
        self._setup_child_subdatasets(self._obj)

    def close(self):
        #self._obj.FlushCache() # @TODO: check
        self.filename = None
        self._mode = None
        self.cmapper = None
        self.graphicsitem = None
        #self.scene = None    # @WARNINIG: causes problems in event filters
        super(DatasetItem, self).close()

        parent = self.parent()
        if not parent:
            # only remone itself if it is a toplevel item
            parent = self.model().invisibleRootItem()
            # @NOTE: use takeRow instead of removeRow in order to avoid the
            #        underlying C/C++ object is deleted before all sub-windows
            #        that hold a reference to the stditem are destroyed
            parent.takeRow(self.row())

    def path(self):
        parent = self.partet()
        parentpath = parent.path() if parent else ''
        return '/'.join(parentpath, self.filemame + ':')


class CachedDatasetItem(DatasetItem):
    _type = DatasetItem._type + 1

    CACHEDIR = os.path.expanduser(os.path.join('~', '.gsdview', 'cache'))

    def __init__(self, filename, mode=gdal.GA_Update, **kwargs):
        # @TODO: check
        if mode == gdal.GA_ReadOnly:
            _log.warning('GDAL open mode ignored in cached datasets.')
            mode = gdal.GA_Update

        filename = os.path.abspath(filename)
        gdalobj = self._checkedopen(filename, gdal.GA_ReadOnly)
        # @NOTE: drop DataSetItem initializer
        MajorObjectItem.__init__(self, gdalobj, **kwargs)
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

    def _get_cachedir(self, gdalobj):
        id_ = gdalsupport.uniqueDatasetID(gdalobj)
        cachedir = self.CACHEDIR
        cachedir = os.path.join(cachedir, id_)

        return cachedir

    def _vrtinit(self, gdalobj, cachedir=None):
        # Build the virtual dataset filename
        if cachedir is None:
            cachedir = self._get_cachedir(gdalobj)

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
            # Handle both non existing self.vrtfilename and errors in opening
            # existing self.vrtfilename
            if gdalobj.GetDriver().ShortName.upper() == 'VRT':
                gdalsupport.safe_vrt_copy(gdalobj, vrtfilename)
                vrtdataset = gdal.Open(vrtfilename, gdal.GA_Update)
            else:
                driver = gdal.GetDriverByName('VRT')
                vrtdataset = driver.CreateCopy(vrtfilename, gdalobj)

        if vrtdataset is None:
            raise ValueError('unable to open the GDAL virtual dataset: "%s"' %
                             os.path.basename(vrtfilename))
        return vrtfilename, vrtdataset

    # Give items the same iterface of GDAL objects.
    # NOTE: the widgets module doesn't need to import modelitems
    def __getattr__(self, name):
        if name in ('GetDescription', 'GetDriver', 'GetSubDatasets',
                    'GetFileList'):
            return getattr(self._obj, name)
        return getattr(self._vrtobj, name)

    def GetMetadata(self, domain=''):
        # @TODO: handle domain.startswith('xml:') and domain == 'OVERVIEW'
        if domain in ('IMAGE_STRUCTURE', 'SUBDATASETS'):
            return self._obj.GetMetadata(domain)

        md = self._vrtobj.GetMetadata(domain)
        if domain and not md:
            # @NOTE: look into the original GDAL obj for metadata
            #        associated to non standard domains
            md = self._obj.GetMetadata(domain)

        return md

    def GetMetadata_Dict(self, domain=''):
        # @TODO: handle domain.startswith('xml:') and domain == 'OVERVIEW'
        if domain in ('IMAGE_STRUCTURE', 'SUBDATASETS'):
            return self._obj.GetMetadata_Dict(domain)

        md = self._vrtobj.GetMetadata_Dict(domain)
        if domain and not md:
            # @NOTE: look into the original GDAL obj for metadata
            #        associated to non standard domains
            md = self._obj.GetMetadata_Dict(domain)

        return md

    def GetMetadata_List(self, domain=''):
        # @TODO: handle domain.startswith('xml:') and domain == 'OVERVIEW'
        if domain in ('IMAGE_STRUCTURE', 'SUBDATASETS'):
            return self._obj.GetMetadata_List(domain)

        md = self._vrtobj.GetMetadata_List(domain)
        if domain and not md:
            # @NOTE: look into the original GDAL obj for metadata
            #        associated to non standard domains
            md = self._obj.GetMetadata_List(domain)

        return md

    if hasattr(gdal.Dataset, 'GetMetadataItem'):

        def GetMetadataItem(self, name, domain=''):
            # @TODO: handle domain.startswith('xml:') and domain == 'OVERVIEW'
            if domain in ('IMAGE_STRUCTURE', 'SUBDATASETS'):
                return self._obj.GetMetadataItem(name, domain)

            value = self._vrtobj.GetMetadataItem(name, domain)
            if domain and value is None:
                # @NOTE: look into the original GDAL obj for metadata
                #        associated to non standard domains
                value = self._obj.GetMetadataItem(name, domain)

            return value

    def _setup_children(self):
        self._setup_child_bands(self._vrtobj)
        self._setup_child_subdatasets(self._obj)

    def close(self):
        super(CachedDatasetItem, self).close()
        # @NOTE: close virtual object after closing all children
        self._vrtobj = None
        self.vrtfilename = None

    def reopen(self):
        gdalobj = gdal.Open(self.vrtfilename, gdal.GA_Update)

        if gdalobj.RasterCount < self.RasterCount:
            _log.warning(
                'unable to reopen dataset: unexpected number of raster bands')
            return

        # @WARNING: an error here would require node removal
        for index in range(1, self.RasterCount + 1):
            item = self.GetRasterBand(index)
            item._reopen(gdalobj.GetRasterBand(index))

        self._vrtobj = gdalobj

        self.model().itemChanged.emit(self)


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
    iconfile = qtsupport.geticon('subdataset.svg', __name__)
    _type = DatasetItem._type + 10

    def __init__(self, gdalfilename, extrainfo='', **kwargs):
        # @NOTE: never call DatasetItem.__init__
        MajorObjectItem.__init__(self, None, **kwargs)
        self.setText(extrainfo)
        self.setToolTip(extrainfo)

        #: dataset filename
        self.filename = gdalfilename

        #: GDAL sub-dataset info
        self.extrainfo = extrainfo
        self._mode = None

        #: coordinate mapper
        self.cmapper = None

        #: graphics scene associated to the item
        self.scene = None

        #: graphics item representing the dataset
        self.graphicsitem = None

        #: filename of the cached virtual dataset
        self.vrtfilename = None
        self._vrtobj = None

    def isopen(self):
        return self._obj is not None and self._vrtobj is not None

    # @staticmethod
    def _normalize(self, filename):
        filename = filename.replace(':', '_')
        filename = filename.replace('/', '_')
        filename = filename.replace('\\', '_')
        return filename

    def open(self, cachedir=None):
        if self.isopen():
            return

        if not cachedir:
            cachedir = os.path.join(self.CACHEDIR,
                                    self._normalize(self.filename))

        if self._mode == gdal.GA_ReadOnly:
            _log.warning('GDAL open mode ignored in cached datasets.')
            self._mode = gdal.GA_Update

        # @TODO: don't use "os.path.abspath" because the filename id to be
        #        intended includes as a gdal-filename using sub-dataset
        #        syntax
        gdalobj = self._checkedopen(self.filename)
        vrtfilename, vrtobj = self._vrtinit(gdalobj, cachedir)

        self.vrtfilename = vrtfilename
        self._obj = gdalobj
        self._vrtobj = vrtobj
        self._setup_children()

        self.cmapper = gdalsupport.coordinate_mapper(self._vrtobj)

        # @TODO: lazy behaviour: postpone the scene/view initialization when
        #        it is actualy needed
        scene, graphicsitem = self._setup_scene()

        #: graphics scene associated to the item
        self.scene = scene

        #: graphics item representing the dataset
        self.graphicsitem = graphicsitem

    def close(self):
        # @NOTE: preserve the filename, extrainfo and mode
        gdalfilename = self.filename
        mode = self._mode
        #self.extrainfo = ''

        super(SubDatasetItem, self).close()

        self.filename = gdalfilename
        self._mode = mode

    def reopen(self):
        if not self.isopen():
            self.open()
        else:
            super(SubDatasetItem, self).reopen()

    def __getattr__(self, name):
        if self._obj:
            return super(SubDatasetItem, self).__getattr__(name)
        elif name in dir(gdal.Dataset):
            raise RuntimeError('unable to access "%s" on a non open '
                               'object' % name)
        else:
            raise AttributeError(name)

    def GetRasterBand(self, index):
        if self.isopen():
            return super(CachedDatasetItem, self).GetRasterBand(index)

        return None

    def GetMetadata(self, domain=''):
        if not self.isopen():
            raise RuntimeError('unable to access "%s" on a non open '
                               'object' % 'GetMetadata')
        return super(SubDatasetItem, self).GetMetadata(domain)

    def GetMetadata_Dict(self, domain=''):
        if not self.isopen():
            raise RuntimeError('unable to access "%s" on a non open '
                               'object' % 'GetMetadata_Dict')
        return super(SubDatasetItem, self).GetMetadata_Dict(domain)

    def GetMetadata_List(self, domain=''):
        if not self.isopen():
            raise RuntimeError('unable to access "%s" on a non open '
                               'object' % 'GetMetadata_List')
        return super(SubDatasetItem, self).GetMetadata_List(domain)

    if hasattr(gdal.Dataset, 'GetMetadataItem'):

        def GetMetadataItem(self, name, domain=''):
            if not self.isopen():
                raise RuntimeError('unable to access "%s" on a non open '
                                   'object' % 'GetMetadataItem')
            return super(SubDatasetItem, self).GetMetadataItem(name, domain)
