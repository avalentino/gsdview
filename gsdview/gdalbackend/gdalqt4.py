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


import numpy

from osgeo import gdal
from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode

from PyQt4 import QtCore, QtGui

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
        QtGui.QGraphicsItem.__init__(self, parent, scene)
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
            self._boundingRect = QtCore.QRectF(0, 0,
                                               gdalobj.RasterXSize,
                                               gdalobj.RasterYSize)
        except AttributeError:
            # raster band
            self._boundingRect = QtCore.QRectF(0, 0,
                                               gdalobj.XSize,
                                               gdalobj.YSize)

    def boundingRect(self):
        return self._boundingRect

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

    def _bestOvrLevel(self, band, levelOfDetail):
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

# @TODO: use a factory function
class GdalGraphicsItem(BaseGdalGraphicsItem):
    def __init__(self, band, parent=None, scene=None):
        BaseGdalGraphicsItem.__init__(self, band, parent, scene)
        self._lut = self.compute_default_LUT()

        #~ if band.DataType in (gdal.GDT_CInt16, gdal.GDT_CInt32):
            #~ logging.warning('complex integer dataset')

        # @TODO: gdal.DataTypeIsComplex (??)
        dtype = GDALTypeCodeToNumericTypeCode(band.DataType)
        if isinstance(dtype, basestring):
            dtype = numpy.typeDict[dtype]
        if numpy.iscomplexobj(dtype()):
            # @TODO: raise ItemTypeError or NotImplementedError
            raise NotImplementedError('support for "%s" data type not avalable')

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

        # @TODO: check
        #lower = 0
        #upper = round(max_)

        N = 3
        lower = round(max(mean - N * stddev, 0))
        upper = round(min(mean + N * stddev, max_))

        return gsdtools.compute_lin_LUT(min_, max_, lower, upper)

    def paint(self, painter, option, widget):
        # @COMPATIBILITY: since Qt v. 4.6.0 the levelOfDetail attribute of
        # QStyleOptionGraphicsItem is deprecated
        # @SEEALSO: ItemUsesExtendedStyleOption item at
        # http://doc.qt.nokia.com/4.6/qgraphicsitem.html#GraphicsItemFlag-enum
        if hasattr(option, 'levelOfDetailFromTransform'):
            levelOfDetail = option.levelOfDetailFromTransform(painter.transform())
        elif QtCore.QT_VERSION_STR >= '4.6.0':
            levelOfDetail = self._levelOfDetailFromTransform(painter.transform())
        else:
            levelOfDetail = option.levelOfDetail

        ovrband, ovrlevel, ovrindex = self._bestOvrLevel(self.gdalobj, 
                                                         levelOfDetail)
        x, y, w, h = self._clipRect(ovrband,
                                    option.exposedRect.toAlignedRect(),
                                    ovrlevel)

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
        ovrband, ovrlevel, ovrindex = self._bestOvrLevel(band,
                                                         option.levelOfDetail)
        x, y, w, h = self._clipRect(ovrband,
                                    option.exposedRect.toAlignedRect(),
                                    ovrlevel)

        dataset = self.gdalobj
        data = gdalsupport.ovrRead(dataset, x, y, w, h, ovrindex)
        rect = self._targetRect(x, y, w, h, ovrlevel)
        image = numpy2qimage(data)
        painter.drawImage(rect, image)
