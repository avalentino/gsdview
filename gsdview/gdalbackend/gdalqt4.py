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

'''Helper tools and custom components for binding GDAL and PyQt4.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import logging

import numpy

from osgeo import gdal
from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode

from PyQt4 import QtCore, QtGui

from gsdview import gsdtools
from qt4support import numpy2qimage

import gdalsupport


# @TODO: move GraphicsView here

# @TODO: use a factory function
class GdalGraphicsItem(QtGui.QGraphicsItem):
    # @TODO:
    #   * child class that uses the quicklook image as a low resolution cache
    #     to speedup scrolling
    def __init__(self, band, parent=None, scene=None):
        QtGui.QGraphicsItem.__init__(self, parent, scene)
        self.band = band
        #~ self._boundingRect = QtCore.QRectF(-self.band.XSize/2.,
                                           #~ -self.band.YSize/2.,
                                           #~ self.band.XSize,
                                           #~ self.band.YSize)
        # @TODO: check (work like QPixmap)
        self._boundingRect = QtCore.QRectF(0, 0,
                                           self.band.XSize,
                                           self.band.YSize)

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
            # @TODO: remove
            logging.warning('extract module from complex data')

    def compute_default_LUT(self):
        # @TOOD: fix flags (approx, force)
        #min_, max_, mean, stddev = self.band.GetStatistics(False, True)
        min_, max_, mean, stddev = self.band.GetStatistics(True, True)

        #~ lower = 0
        #~ upper = round(max_)

        N = 3
        lower = round(max(mean - N * stddev, 0))
        upper = round(min(mean + N * stddev, max_))

        return gsdtools.compute_lin_LUT(min_, max_, lower, upper)

    def boundingRect(self):
        return self._boundingRect

    # @overrideCursor
    def paint(self, painter, option, widget):
        if option.levelOfDetail >= 1 or self.band.GetOverviewCount() == 0:
            band = self.band
            ovrlevel = 1
            ovrindex = None
        else:
            reqlevel = 1. / option.levelOfDetail
            try:
                ovrindex = gdalsupport.best_ovr_index(self.band, reqlevel)
            except ValueError:
                band = self.band
                ovrlevel = 1
                ovrindex = None
            else:
                ovrlevel = gdalsupport.available_ovr_levels(self.band)[ovrindex]
                if abs(reqlevel - 1) < abs(reqlevel - ovrlevel):
                    band = self.band
                    ovrlevel = 1
                    ovrindex = None
                else:
                    band = self.band.GetOverview(ovrindex)

        rect = option.exposedRect.toAlignedRect()

        x = int((rect.x() - self._boundingRect.x()) // ovrlevel)
        y = int((rect.y() - self._boundingRect.y()) // ovrlevel)
        width = rect.width() // ovrlevel + 1        # @TODO: check
        height = rect.height() // ovrlevel + 1      # @TODO: check

        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if (x + width) * ovrlevel > self._boundingRect.width():
            width = band.XSize - x
        if (y + height) * ovrlevel > self._boundingRect.height():
            height = band.YSize - y

        data = band.ReadAsArray(x, y, width, height)

        if numpy.iscomplexobj(data):
            data = numpy.abs(data)
        try:
            data = gsdtools.apply_LUT(data, self._lut)
        except IndexError:
            # Is use the gdal approx stats evaluation it is possible thet the
            # image maximum is under-estimated. Fix the LUT.
            new_lut = gsdtools.fix_LUT(data, self._lut)
            self._lut = new_lut
            data = gsdtools.apply_LUT(data, self._lut)

        image = numpy2qimage(data)
        targetRect = QtCore.QRect(x * ovrlevel + self._boundingRect.x(),
                                  y * ovrlevel + self._boundingRect.y(),
                                  width * ovrlevel,
                                  height * ovrlevel)
        painter.drawImage(targetRect, image)
