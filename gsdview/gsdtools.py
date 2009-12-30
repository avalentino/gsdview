# -*- coding: utf-8 -*-

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


'''Tools for geo-spatial data handling and visualization.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import numpy


def compute_lin_LUT(min_, max_, lower, upper):
    lut = numpy.arange(round(max_) + 1, dtype=numpy.float)
    lut[0:lower] = 0
    lut[lower:upper+1] = (lut[lower:upper+1] - lower) * 255. / (upper - lower)
    lut[upper+1:] = 255
    return lut.astype(numpy.uint8)


def compute_lin_LUT2(histogram_, lower=0.005, upper=0.99, min_=None, max_=None):
    if min_ is None:
        min_ = 0
    if max_ is None:
        max_ = min_ + len(histogram_) - 1

    # normalization
    histogram_ = histogram_.astype(numpy.float)
    histogram_ /= histogram_.sum()

    ifun = numpy.cumsum(histogram_)
    indexes = numpy.where(ifun <= lower)[0]
    if len(indexes) != 0:
        startView = indexes[-1]
    else:
        startView = 0
    indexes = numpy.where(ifun > upper)[0]
    if len(indexes) != 0:
        stopView = indexes[0]
    else:
        stopView = -1

    # @TODO: use compute_lin_LUT hete
    lut = numpy.zeros(max_+1, numpy.uint8)
    rate = 255./(stopView-startView-1)
    aux = numpy.arange(stopView-startView) * rate
    lut[startView:stopView] = aux.round()
    lut[stopView:] = 255

    return lut


def ovr_lut(data):
    if numpy.iscomplexobj(data):
        data = numpy.abs(data)

    # Compute the LUT
    min_ = numpy.floor(data.min())
    if min_ > 0:    # @TODO: fix
        min_ = 0
    max_ = numpy.ceil(data.max())
    nbins = max_ - min_ + 1
    range_ = (min_, max_ + 1)     # @NOTE: dtype = uint16
    try:
        histogram_ = numpy.histogram(data, nbins, range_, new=True)[0]
    except TypeError:
        histogram_ = numpy.histogram(data, nbins, range_)[0]

    lut = compute_lin_LUT2(histogram_)
    return lut


# @TODO: use numpy.take if the case
def apply_LUT(data, lut):
    data = numpy.round(data)
    data = data.astype(numpy.uint32) # @TODO: check
    return lut[data]


def fix_LUT(data, lut):
    new_max = int(numpy.ceil(data.max()))
    assert new_max >= len(lut)
    new_lut = numpy.ndarray(new_max+1, dtype=numpy.uint8)
    new_lut[:len(lut)] = lut
    new_lut[len(lut)] = 255

    return new_lut
