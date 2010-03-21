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


'''Helper tools and custom components for binding GDAL and PyQt4.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import logging

import numpy
from PyQt4 import QtCore, QtGui
from osgeo import gdal
from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode

from gsdview import gsdtools
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


# @TODO: move GraphicsView here

class BaseGdalGraphicsItem(QtGui.QGraphicsItem):
    def __init__(self, gdalobj, parent=None, scene=None):
        super(BaseGdalGraphicsItem, self).__init__(parent, scene)

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
        elif QtCore.QT_VERSION_STR >= '4.6.0':
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


class GdalGraphicsItem(BaseGdalGraphicsItem):
    def __init__(self, band, parent=None, scene=None):
        super(GdalGraphicsItem, self).__init__(band, parent, scene)

        self._lut = self.compute_default_LUT()

        if gdal.DataTypeIsComplex(band.DataType):
            # @TODO: raise ItemTypeError or NotImplementedError
            typename = gdal.GetDataTypeName(band.DataType)
            raise NotImplementedError('support for "%s" data type not '
                                      'avalable' % typename)

    def compute_default_LUT(self, band=None, data=None):
        if band is None:
            band = self.gdalobj
        # @TOOD: fix flags (approx, force)
        #min_, max_, mean, stddev = self.band.GetStatistics(False, True)

        # @WARNING: this is potentially slow
        # @TODO: check for overviews and if no one is peresent flag as
        #        uninizialized
        try:
            indx = gdalsupport.ovrBestIndex(band, policy='GREATER')
        except gdalsupport.MissingOvrError:
            if data is not None:
                min_ = data.min()
                max_ = data.max()
                mean = data.mean()
                stddev = data.std()
            else:
                return None
        else:
            min_, max_, mean, stddev = band.GetStatistics(True, True)

        N = 3
        lower = round(max(mean - N * stddev, 0))
        upper = round(min(mean + N * stddev, max_))

        return gsdtools.compute_lin_LUT(min_, max_, lower, upper)

    def paint(self, painter, option, widget):
        #print 'paint', widget.parent()
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
        #    print 'newoption.levelOfDetail', newoption.levelOfDetail
        #    return self.paint(painter, newoption, widget)

        data = ovrband.ReadAsArray(x, y, w, h)

        if numpy.iscomplexobj(data):
            data = numpy.abs(data)
        if self._lut is None:
            self._lut = self.compute_default_LUT(ovrband, data)
        try:
            data = gsdtools.apply_LUT(data, self._lut)
        except IndexError:
            # If the gdal approx stats evaluation is used it than is possible
            # that the image maximum is under-estimated. Fix the LUT.
            new_lut = gsdtools.fix_LUT(data, self._lut)
            self._lut = new_lut
            data = gsdtools.apply_LUT(data, self._lut)

        rect = self._targetRect(x, y, w, h, ovrlevel)
        image = numpy2qimage(data)
        painter.drawImage(rect, image)


class GdalRgbGraphicsItem(BaseGdalGraphicsItem):
    def __init__(self, dataset, parent=None, scene=None):
        if not gdalsupport.isRGB(dataset):
            raise TypeError('RGB or RGBA iamge expected')
        BaseGdalGraphicsItem.__init__(self, dataset, parent, scene)

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
    #~ elif gdal.DataTypeIsComplex(gdalobj.DataType):
        #~ logging.debug('new GdalComplexGraphicsItem')
        #~ return GdalComplexGraphicsItem(gdalobj, parent, scene)
    else:
        logging.debug('new GdalGraphicsItem')
        return GdalGraphicsItem(gdalobj, parent, scene)
