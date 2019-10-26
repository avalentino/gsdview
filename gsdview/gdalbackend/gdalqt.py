# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2019 Antonio Valentino <antonio.valentino@tiscali.it>
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


"""Helper tools and custom components for binding GDAL and Qt."""


import logging
import collections

import numpy as np
from numpy import ma

from osgeo import gdal
from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode

from qtpy import QtCore, QtWidgets, QtGui

from gsdview import imgutils
from gsdview import qtsupport
from gsdview.gdalbackend import gdalsupport


_log = logging.getLogger(__name__)


def gdalcolorentry2qcolor(colorentry, interpretation=gdal.GPI_RGB):
    qcolor = QtGui.QColor()

    if interpretation == gdal.GPI_RGB:
        qcolor.setRgb(
            colorentry.c1, colorentry.c2, colorentry.c3, colorentry.c4)
    elif interpretation == gdal.GPI_Gray:
        qcolor.setRgb(colorentry.c1, colorentry.c1, colorentry.c1)
    elif interpretation == gdal.GPI_CMYK:
        qcolor.setCmyk(
            colorentry.c1, colorentry.c2, colorentry.c3, colorentry.c4)
    elif interpretation == gdal.GPI_HLS:
        qcolor.setHsv(colorentry.c1, colorentry.c2, colorentry.c3)
                      # , colorentry.c4)
    else:
        raise ValueError('invalid color interpretation: "%s"' % interpretation)

    return qcolor


def safeDataStats(data, nodata=None):
    if nodata is not None:
        data = ma.masked_equal(data, nodata)

    stats = (data.min(), data.max(), data.mean(), data.std())
    stddev = stats[-1]
    if ma.isMaskedArray(stddev) or stddev == 0:
        stats = (None, None, None, None)

    return stats


# @TODO: move GraphicsView here


class BaseGdalGraphicsItem(QtWidgets.QGraphicsItem):
    Type = QtGui.QStandardItem.UserType + 1

    def __init__(self, gdalobj, parent=None, **kwargs):
        super(BaseGdalGraphicsItem, self).__init__(parent, **kwargs)
        self.setFlag(QtWidgets.QGraphicsItem.ItemUsesExtendedStyleOption)

        self.gdalobj = gdalobj
        try:
            # dataset
            w = gdalobj.RasterXSize
            h = gdalobj.RasterYSize
        except AttributeError:
            # raster band
            w = gdalobj.XSize
            h = gdalobj.YSize

        self._boundingRect = QtCore.QRectF(0, 0, w, h)
        # self.read_threshold = 1600*1200

        self.stretch = imgutils.LinearStretcher()
        # @TODO: use lazy graphicsitem initialization
        # @TODO: initialize stretching explicitly
        self._stretch_initialized = False
        self._data_preproc = None
        self.colortable = None

    def type(self):
        return self.Type

    def boundingRect(self):
        return self._boundingRect

    def _clipRect(self, ovrband, rect, ovrlevel):
        boundingRect = self._boundingRect

        x = int((rect.x() - boundingRect.x()) // ovrlevel)
        y = int((rect.y() - boundingRect.y()) // ovrlevel)
        width = rect.width() // ovrlevel + 1        # @TODO: check
        height = rect.height() // ovrlevel + 1      # @TODO: check

        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if (x + width) * ovrlevel > boundingRect.width():
            width = ovrband.XSize - x
        if (y + height) * ovrlevel > boundingRect.height():
            height = ovrband.YSize - y

        return x, y, width, height

    def _targetRect(self, x, y, w, h, ovrlevel):
        boundingRect = self._boundingRect
        return QtCore.QRect(x * ovrlevel + boundingRect.x(),
                            y * ovrlevel + boundingRect.y(),
                            w * ovrlevel,
                            h * ovrlevel)

    @staticmethod
    def _levelOfDetailFromTransform(worldTransform):
        if worldTransform.type() <= QtGui.QTransform.TxTranslate:
            return 1    # Translation only? The LOD is 1.

        # Two unit vectors.
        v1 = QtCore.QLineF(0, 0, 1, 0)
        v2 = QtCore.QLineF(0, 0, 0, 1)

        # LOD is the transformed area of a 1x1 rectangle.
        return np.sqrt(worldTransform.map(v1).length() *
                       worldTransform.map(v2).length())

    @staticmethod
    def _levelOfDetail(option, painter):
        return option.levelOfDetailFromTransform(painter.transform())

    @staticmethod
    def _bestOvrLevel(band, levelOfDetail):
        ovrlevel = 1
        ovrindex = None

        if band.GetOverviewCount() > 0:
            if levelOfDetail <= 0:
                reqlevel = 1.
            else:
                reqlevel = 1. / levelOfDetail

            try:
                ovrindex = gdalsupport.ovrBestIndex(band, reqlevel)
            except gdalsupport.MissingOvrError:
                pass
            else:
                ovrlevel = gdalsupport.ovrLevels(band)[ovrindex]
                if abs(reqlevel - 1) < abs(reqlevel - ovrlevel):
                    ovrlevel = 1
                    ovrindex = None
                else:
                    band = band.GetOverview(ovrindex)
        return band, ovrlevel, ovrindex

    @staticmethod
    def _defaultStretch(band, data=None, nsigma=5):
        # @NOTE: statistics computation is potentially slow so first check
        #        if fast statistics retrieving is possible

        stats = (None, None, None, None)

        if band and gdalsupport.hasFastStats(band):
            stats = gdalsupport.SafeGetStatistics(band, True, True)

        if None in stats and data is not None and data.size <= 4 * 1024 ** 2:
            stats = safeDataStats(data, band.GetNoDataValue())

        if None in stats:
            if band and band.DataType == gdal.GDT_Byte:
                return 0, 255
            else:
                return None, None

        vmin, vmax, mean, stddev = stats

        lower = max(mean - nsigma * stddev, 0)
        upper = min(mean + nsigma * stddev, vmax)

        return lower, upper

    def setDefaultStretch(self, data=None):
        lower, upper = self._defaultStretch(self.gdalobj, data)

        if None in (lower, upper) or (lower == upper):
            self._stretch_initialized = False
            return

        self.stretch.set_range(lower, upper)
        self._stretch_initialized = True

    @staticmethod
    def _dataRange(band, data=None):
        if band and gdalsupport.hasFastStats(band):
            vmin, vmax, mean, stddev = gdalsupport.SafeGetStatistics(band,
                                                                     True)
            if None not in (vmin, vmax, mean, stddev):
                if gdal.DataTypeIsComplex(band.DataType):
                    vmin, vmax = 0, vmax * np.sqrt(2)
                return vmin, vmax

        if data is not None and data.size <= 4 * 1024 ** 2:
            vmin, vmax, mean, stddev = safeDataStats(band)
            if None not in (vmin, vmax, mean, stddev):
                return data.min(), data.max()

        if band:
            tmap = {
                gdal.GDT_Byte: (0, 255),
                gdal.GDT_UInt16: (0, 2 ** 16 - 1),
                gdal.GDT_UInt32: (0, 2 ** 32 - 1),
                gdal.GDT_Int16: (-2 ** 15, 2 ** 15 - 1),
                gdal.GDT_Int32: (-2 ** 31, 2 ** 31 - 1),
                gdal.GDT_CInt16: (0, 2 ** 15 * np.sqrt(2)),
                gdal.GDT_CInt32: (0, 2 ** 31 * np.sqrt(2)),
                gdal.GDT_CFloat32: (0, None),
                gdal.GDT_CFloat64: (0, None),
            }
            return tmap.get(band.DataType, (None, None))

        return None, None

    def dataRange(self, data=None):
        return None, None

    def paint(self, painter, option, widget):
        levelOfDetail = self._levelOfDetail(option, painter)
        ovrband, ovrlevel, ovrindex = self._bestOvrLevel(self.gdalobj,
                                                         levelOfDetail)
        x, y, w, h = self._clipRect(ovrband,
                                    option.exposedRect.toAlignedRect(),
                                    ovrlevel)

        data = ovrband.ReadAsArray(x, y, w, h)

        if self._data_preproc:
            data = self._data_preproc(data)

        if not self._stretch_initialized:
            self.setDefaultStretch(data)
        data = self.stretch(data)

        rect = self._targetRect(x, y, w, h, ovrlevel)
        image = qtsupport.numpy2qimage(data, self.colortable)
        painter.drawImage(rect, image)

    def _setupContextMenu(self, parent=None):
        menu = QtWidgets.QMenu(parent)
        tr = menu.tr

        # Data pre-processing
        funcs = collections.OrderedDict()
        funcs['None'] = None
        funcs['Abs'] = np.abs
        funcs['Angle'] = np.angle
        funcs['Real'] = np.real
        funcs['Imag'] = np.imag
        # funcs['Pow'] = lambda x: np.abs(x * x)
        # funcs['dB'] = lambda x: 20 * np.log10(np.abs(x))

        inverse_fmap = dict((v, k) for k, v in funcs.items())
        current_func = inverse_fmap.get(self._data_preproc, 'unknown')
        if current_func == 'unknown':
            try:
                current_func = self._data_preproc.__name__
            except AttributeError:
                pass
            funcs[current_func] = self._data_preproc

        menu.addSection(tr('Transformation functions'))

        actiongroup = QtWidgets.QActionGroup(menu)
        actiongroup.setExclusive(True)
        for name in funcs.keys():
            def set_proc_func(checked, key=name):
                # @TODO: also adjust the stretch object
                func = funcs[key]
                if func != self._data_preproc:
                    self._data_preproc = func
                    self.update()

            action = QtWidgets.QAction(
                name,
                actiongroup,
                checkable=True,
                enabled=(self._data_preproc is not None and name != 'None'),
                objectName='actionDataPreProc' + name.capitalize(),
                toolTip=tr('Transformation function applied to data'),
                triggered=set_proc_func)
            action.setChecked(bool(name == current_func))
            menu.addAction(action)

        # Colormap
        colortables = collections.OrderedDict()
        colortables['None'] = None
        colortables['Gray'] = qtsupport.GRAY_COLORTABLE
        colortables['Jet'] = qtsupport.JET_COLORTABLE

        inverse_ctmap = dict((id(v), k) for k, v in colortables.items())
        current_colortable = inverse_ctmap.get(id(self.colortable), 'unknown')
        if current_colortable == 'unknown':
            colortables[current_colortable] = self.colortable

        menu.addSection(tr('Color table'))

        actiongroup = QtWidgets.QActionGroup(menu)
        actiongroup.setExclusive(True)
        for name in colortables.keys():
            def set_colortable(checked, key=name):
                ct = colortables[key]
                if id(ct) != id(self.colortable):
                    self.colortable = ct
                    self.update()

            action = QtWidgets.QAction(
                name,
                actiongroup,
                checkable=True,
                enabled=bool(self.colortable is not None and name != 'None'),
                objectName='actionColorTable' + name.capitalize(),
                toolTip=tr('Set the color table to %s') % name,
                triggered=set_colortable)
            action.setChecked(bool(name == current_colortable))
            menu.addAction(action)

        return menu

    def _parent(self):
        scene = self.scene()
        if scene:
            parent = scene.parent()
        else:
            parent = None
        return parent

    def contextMenuEvent(self, event):
        context_menu = self._setupContextMenu(self._parent())
        context_menu.exec_(event.screenPos())
        event.accept()


class UIntGdalGraphicsItem(BaseGdalGraphicsItem):
    """GDAL graphics item specialized for 8 and 16 it unsigned integers.

    Uses an unchecked LUT for transformations.

    """

    Type = BaseGdalGraphicsItem.Type + 1

    def __init__(self, band, parent=None, **kwargs):
        super(UIntGdalGraphicsItem, self).__init__(band, parent, **kwargs)

        # @TODO: maybe it is batter to use a custom exception: ItemTypeError
        if band.DataType not in (gdal.GDT_Byte, gdal.GDT_UInt16):
            typename = gdal.GetDataTypeName(band.DataType)
            raise ValueError('invalid data type: "%s"' % typename)

        dtype = np.dtype(GDALTypeCodeToNumericTypeCode(band.DataType))
        self.stretch = imgutils.LUTStretcher(fill=2 ** (8 * dtype.itemsize))
        self._stretch_initialized = False
        self.colortable = qtsupport.GRAY_COLORTABLE

    def dataRange(self, data=None):
        if data and self._data_preproc:
            data = self._data_preproc(data)
        return self._dataRange(self.gdalobj, data)


class GdalGraphicsItem(BaseGdalGraphicsItem):

    Type = BaseGdalGraphicsItem.Type + 2

    def __init__(self, band, parent=None, **kwargs):
        super(GdalGraphicsItem, self).__init__(band, parent, **kwargs)
        self.colortable = qtsupport.GRAY_COLORTABLE

        if gdal.DataTypeIsComplex(band.DataType):
            # @TODO: raise ItemTypeError or NotImplementedError
            typename = gdal.GetDataTypeName(band.DataType)
            raise NotImplementedError(
                'support for "%s" data type not avalable' % typename)

    def dataRange(self, data=None):
        if data and self._data_preproc:
            data = self._data_preproc(data)
        return self._dataRange(self.gdalobj, data)


class GdalComplexGraphicsItem(GdalGraphicsItem):

    Type = GdalGraphicsItem.Type + 1

    def __init__(self, band, parent=None, **kwargs):
        # @NOTE: skip GdalGraphicsItem __init__
        BaseGdalGraphicsItem.__init__(self, band, parent, **kwargs)
        self._data_preproc = np.abs
        self.colortable = qtsupport.GRAY_COLORTABLE


class GdalRgbGraphicsItem(BaseGdalGraphicsItem):

    Type = BaseGdalGraphicsItem.Type + 10

    def __init__(self, dataset, parent=None, **kwargs):
        if not gdalsupport.isRGB(dataset):
            raise TypeError('RGB or RGBA iamge expected')
        super(GdalRgbGraphicsItem, self).__init__(dataset, parent, **kwargs)
        self.stretch = None

    def paint(self, painter, option, widget):
        band = self.gdalobj.GetRasterBand(1)
        levelOfDetail = self._levelOfDetail(option, painter)
        ovrband, ovrlevel, ovrindex = self._bestOvrLevel(band, levelOfDetail)
        x, y, w, h = self._clipRect(ovrband,
                                    option.exposedRect.toAlignedRect(),
                                    ovrlevel)

        dataset = self.gdalobj
        data = gdalsupport.ovrRead(dataset, x, y, w, h, ovrindex)
        rect = self._targetRect(x, y, w, h, ovrlevel)
        image = qtsupport.numpy2qimage(data)
        painter.drawImage(rect, image)


def graphicsItemFactory(gdalobj, parent=None):
    """Factory function for GDAL graphics items.

    Instantiates on object of the GDAL graphics item class that best
    fits the *gdalobj* passed as argument.

    """

    if gdalsupport.isRGB(gdalobj):
        _log.debug('new GdalRgbGraphicsItem')
        return GdalRgbGraphicsItem(gdalobj, parent)
    elif gdalobj.DataType in (gdal.GDT_Byte, gdal.GDT_UInt16):
        _log.debug('new GdalUIntGraphicsItem')
        return UIntGdalGraphicsItem(gdalobj, parent)
    elif gdal.DataTypeIsComplex(gdalobj.DataType):
        _log.debug('new GdalComplexGraphicsItem')
        return GdalComplexGraphicsItem(gdalobj, parent)
    else:
        _log.debug('new GdalGraphicsItem')
        return GdalGraphicsItem(gdalobj, parent)
