# -*- coding: utf-8 -*-

### Copyright (C) 2008-2011 Antonio Valentino <a_valentino@users.sf.net>

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


'''Helper tools and custom components for binding GDAL and PyQt4.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import logging

import numpy
from numpy import ma

from PyQt4 import QtCore, QtGui
from osgeo import gdal

# @WARNING: this line seems to cause a crash on Fedora 13
from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode

from gsdview import imgutils
from gsdview.qt4support import numpy2qimage

from gsdview.gdalbackend import gdalsupport


def gdalcolorentry2qcolor(colrentry, interpretation=gdal.GPI_RGB):
    qcolor = QtGui.QColor()

    if interpretation == gdal.GPI_RGB:
        qcolor.setRgb(colrentry.c1, colrentry.c2, colrentry.c3, colrentry.c4)
    elif interpretation == gdal.GPI_Gray:
        qcolor.setRgb(colrentry.c1, colrentry.c1, colrentry.c1)
    elif interpretation == gdal.GPI_CMYK:
        qcolor.setCmyk(colrentry.c1, colrentry.c2, colrentry.c3, colrentry.c4)
    elif interpretation == gdal.GPI_HLS:
        qcolor.setHsv(colrentry.c1, colrentry.c2, colrentry.c3) #, colrentry.c4)
    else:
        raise ValueError('invalid color intepretatin: "%s"' % interpretation)

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

class BaseGdalGraphicsItem(QtGui.QGraphicsItem):

    Type = QtGui.QStandardItem.UserType + 1

    def __init__(self, gdalobj, parent=None, scene=None, **kwargs):
        super(BaseGdalGraphicsItem, self).__init__(parent, scene, **kwargs)

        # @COMPATIBILITY: Qt >= 4.6.0 needs this flag to be set otherwise the
        #                 exact exposedRect is not computed
        # @SEEALSO: ItemUsesExtendedStyleOption item at
        # http://doc.qt.nokia.com/4.6/qgraphicsitem.html#GraphicsItemFlag-enum
        try:
            self.setFlag(QtGui.QGraphicsItem.ItemUsesExtendedStyleOptions)
        except AttributeError:
            ItemUsesExtendedStyleOptions = 0x200
            self.setFlag(ItemUsesExtendedStyleOptions)

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
        #self.read_threshold = 1600*1200

        self.stretch = imgutils.LinearStretcher()
        # @TODO: use lazy gaphicsitem inirialization
        # @TODO: initilize stretching explicitly
        self._stretch_initialized = False

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
        # @COMPATIBILITY: since Qt v. 4.6.0 the levelOfDetail attribute of
        # QStyleOptionGraphicsItem is deprecated
        # @SEEALSO: ItemUsesExtendedStyleOption item at
        # http://doc.qt.nokia.com/4.6/qgraphicsitem.html#GraphicsItemFlag-enum
        #
        # From qt/src/gui/styles/qstyleoption.cpp:5130
        if worldTransform.type() <= QtGui.QTransform.TxTranslate:
            return 1    # Translation only? The LOD is 1.

        # Two unit vectors.
        v1 = QtCore.QLineF(0, 0, 1, 0)
        v2 = QtCore.QLineF(0, 0, 0, 1)
        # LOD is the transformed area of a 1x1 rectangle.
        return numpy.sqrt(worldTransform.map(v1).length() *
                                            worldTransform.map(v2).length())

    @staticmethod
    def _levelOfDetail(option, painter):
        # @COMPATIBILITY: since Qt v. 4.6.0 the levelOfDetail attribute of
        # QStyleOptionGraphicsItem is deprecated
        # @SEEALSO: ItemUsesExtendedStyleOption item at
        # http://doc.qt.nokia.com/4.6/qgraphicsitem.html#GraphicsItemFlag-enum
        if hasattr(option, 'levelOfDetailFromTransform'):
            levelOfDetail = option.levelOfDetailFromTransform(
                                                    painter.transform())
        elif QtCore.qVersion() >= '4.6.0':
            levelOfDetail = BaseGdalGraphicsItem._levelOfDetailFromTransform(
                                                        painter.transform())
        else:
            levelOfDetail = option.levelOfDetail
        return levelOfDetail

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
        #        if fast statistics retriewing is possible

        stats = (None, None, None, None)

        if band and gdalsupport.hasFastStats(band):
            stats = gdalsupport.SafeGetStatistics(band, True, True)

        if None in stats and data is not None and data.size <= 4*1024**2:
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
            vmin, vmax, mean, stddev = gdalsupport.SafeGetStatistics(band, True)
            if None not in (vmin, vmax, mean, stddev):
                if gdal.DataTypeIsComplex(band.DataType):
                    vmin, vmax = 0, vmax * numpy.sqrt(2)
                return vmin, vmax

        if data is not None and data.size <= 4*1024**2:
            vmin, vmax, mean, stddev = safeDataStats(band)
            if None not in (vmin, vmax, mean, stddev):
                return data.min(), data.max()

        if band:
            tmap = {
                gdal.GDT_Byte:      (0, 255),
                gdal.GDT_UInt16:    (0, 2**16-1),
                gdal.GDT_UInt32:    (0, 2**32-1),
                gdal.GDT_Int16:     (-2**15, 2**15-1),
                gdal.GDT_Int32:     (-2**31, 2**31-1),
                gdal.GDT_CInt16:    (0, 2**15 * numpy.sqrt(2)),
                gdal.GDT_CInt32:    (0, 2**31 * numpy.sqrt(2)),
                gdal.GDT_CFloat32:  (0, None),
                gdal.GDT_CFloat64:  (0, None),
            }
            return tmap.get(band.DataType, (None, None))

        return None, None

    def dataRange(self, data=None):
        return None, None


class UIntGdalGraphicsItem(BaseGdalGraphicsItem):
    '''GDAL graphics item specialized for 8 and 16 it unsigned integers.

    Uses an unchecked LUT for transformations.

    '''

    Type = BaseGdalGraphicsItem.Type + 1

    def __init__(self, band, parent=None, scene=None, **kwargs):
        super(UIntGdalGraphicsItem, self).__init__(band, parent, scene,
                                                   **kwargs)

        # @TODO: maybe it is batter to use a custo mexception: ItemTypeError
        if band.DataType not in (gdal.GDT_Byte, gdal.GDT_UInt16):
            typename = gdal.GetDataTypeName(band.DataType)
            raise ValueError('invalid data type: "%s"' % typename)

        dtype = numpy.dtype(GDALTypeCodeToNumericTypeCode(band.DataType))
        self.stretch = imgutils.LUTStretcher(fill=2**(8*dtype.itemsize))
        self._stretch_initialized = False

    def dataRange(self, data=None):
        return self._dataRange(self.gdalobj, data)

    def paint(self, painter, option, widget):
        levelOfDetail = self._levelOfDetail(option, painter)
        ovrband, ovrlevel, ovrindex = self._bestOvrLevel(self.gdalobj,
                                                         levelOfDetail)
        x, y, w, h = self._clipRect(ovrband,
                                    option.exposedRect.toAlignedRect(),
                                    ovrlevel)

        # @TODO: threshold check
        # @WARNING: option.levelOfDetail is no more usable
        #threshold = 1600*1600
        #if w * h > threshold:
        #    newoption = QtGui.QStyleOptionGraphicsItem(option)
        #    newoption.levelOfDetail = option.levelOfDetail*threshold/(w*h)
        #    return self.paint(painter, newoption, widget)

        data = ovrband.ReadAsArray(x, y, w, h)

        if not self._stretch_initialized:
            self.setDefaultStretch(data)
        data = self.stretch(data)
        image = numpy2qimage(data)

        rect = self._targetRect(x, y, w, h, ovrlevel)
        painter.drawImage(rect, image)


class GdalGraphicsItem(BaseGdalGraphicsItem):

    Type = BaseGdalGraphicsItem.Type + 2

    def __init__(self, band, parent=None, scene=None, **kwargs):
        super(GdalGraphicsItem, self).__init__(band, parent, scene, **kwargs)

        if gdal.DataTypeIsComplex(band.DataType):
            # @TODO: raise ItemTypeError or NotImplementedError
            typename = gdal.GetDataTypeName(band.DataType)
            raise NotImplementedError('support for "%s" data type not '
                                      'avalable' % typename)

    def dataRange(self, data=None):
        return self._dataRange(self.gdalobj, data)

    def paint(self, painter, option, widget):
        levelOfDetail = self._levelOfDetail(option, painter)
        ovrband, ovrlevel, ovrindex = self._bestOvrLevel(self.gdalobj,
                                                         levelOfDetail)
        x, y, w, h = self._clipRect(ovrband,
                                    option.exposedRect.toAlignedRect(),
                                    ovrlevel)

        # @TODO: threshold check
        # @WARNING: option.levelOfDetail is no more usable
        #threshold = 1600*1600
        #if w * h > threshold:
        #    newoption = QtGui.QStyleOptionGraphicsItem(option)
        #    newoption.levelOfDetail = option.levelOfDetail * threshold / (w * h)
        #    return self.paint(painter, newoption, widget)

        data = ovrband.ReadAsArray(x, y, w, h)

        if not self._stretch_initialized:
            self.setDefaultStretch(data)
        data = self.stretch(data)

        rect = self._targetRect(x, y, w, h, ovrlevel)
        image = numpy2qimage(data)
        painter.drawImage(rect, image)


class GdalComplexGraphicsItem(GdalGraphicsItem):

    Type = GdalGraphicsItem.Type + 1

    def __init__(self, band, parent=None, scene=None, **kwargs):
        # @NOTE: skip GdalGraphicsItem __init__
        BaseGdalGraphicsItem.__init__(self, band, parent, scene, **kwargs)

    def dataRange(self, data=None):
        if data:
            data = numpy.abs(data)
        return self._dataRange(self.gdalobj, data)

    def paint(self, painter, option, widget):
        levelOfDetail = self._levelOfDetail(option, painter)
        ovrband, ovrlevel, ovrindex = self._bestOvrLevel(self.gdalobj,
                                                         levelOfDetail)
        x, y, w, h = self._clipRect(ovrband,
                                    option.exposedRect.toAlignedRect(),
                                    ovrlevel)

        # @TODO: threshold check
        #threshold = 1600*1600
        #if w * h > threshold:
        #    newoption = QtGui.QStyleOptionGraphicsItem(option)
        #    newoption.levelOfDetail = option.levelOfDetail * threshold / (w * h)
        #    return self.paint(painter, newoption, widget)

        data = ovrband.ReadAsArray(x, y, w, h)

        data = numpy.abs(data)
        if not self._stretch_initialized:
            self.setDefaultStretch(data)

        data = self.stretch(data)

        rect = self._targetRect(x, y, w, h, ovrlevel)
        image = numpy2qimage(data)
        painter.drawImage(rect, image)


class GdalRgbGraphicsItem(BaseGdalGraphicsItem):

    Type = BaseGdalGraphicsItem.Type + 3

    def __init__(self, dataset, parent=None, scene=None, **kwargs):
        if not gdalsupport.isRGB(dataset):
            raise TypeError('RGB or RGBA iamge expected')
        super(GdalRgbGraphicsItem, self).__init__(dataset, parent, scene,
                                                  **kwargs)
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
        image = numpy2qimage(data)
        painter.drawImage(rect, image)


def graphicsItemFactory(gdalobj, parent=None, scene=None):
    '''Factory function for GDAL graphics items.

    Instantiates on object of the GDAL graphics item class taht best
    fits the *gdalobj* passed as argument.

    '''

    if gdalsupport.isRGB(gdalobj):
        logging.debug('new GdalRgbGraphicsItem')
        return GdalRgbGraphicsItem(gdalobj, parent, scene)
    elif gdalobj.DataType in (gdal.GDT_Byte, gdal.GDT_UInt16):
        logging.debug('new GdalUIntGraphicsItem')
        return UIntGdalGraphicsItem(gdalobj, parent, scene)
    elif gdal.DataTypeIsComplex(gdalobj.DataType):
        logging.debug('new GdalComplexGraphicsItem')
        return GdalComplexGraphicsItem(gdalobj, parent, scene)
    else:
        logging.debug('new GdalGraphicsItem')
        return GdalGraphicsItem(gdalobj, parent, scene)
