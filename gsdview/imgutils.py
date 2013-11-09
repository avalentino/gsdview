# -*- coding: utf-8 -*-

### Copyright (C) 2008-2013 Antonio Valentino <a_valentino@users.sf.net>

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


'''Tools for geo-spatial images handling and visualization.'''


import numpy as np


__author__ = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__ = '$Date$'
__revision__ = '$Revision$'


### LUT utils ################################################################
def linear_lut(vmin=0, vmax=None, dtype='uint8', fill=False, omin=0,
               omax=None):
    '''Compute a linear LUT.

    The returned LUT maps the imput domain (vmin, vmax) onto the output
    one (0, vout) using a linear low. The value of vout depends on
    dtype: 2**8-1 if dtype='uint8', 2**16-1 dtype='uint16'

    The *fill* parameter can be used to controll the length of returned
    LUT (see below).

    :param vmin:
        minimum value (positive or null). Default 0
    :type vmin:
        int or float
    :param vmax:
        maximum value (positive) Default 2**nbits depending on dtype
    :type vmax:
        int or float
    :param dtype:
        numpy data type of the output LUT (default uint8)
    :type dtype:
        np.dtype (uint8 or uint16)
    :param fill:
        the length of the returned lut is:

            * vmax + 1 if bool(fill) == False
            * max(vmax + 1, 2**nbits) if fill == True
            * max(vmax + 1, fill) id fille is an number

    :type fill:
        bool or int
    :param omin:
        @TBW
    :param omax:
        @TBW
    :returns:     the look up tabe (LUT)

    '''

    dtype = np.dtype(dtype)
    if dtype not in (np.uint8, np.uint16):
        raise ValueError('invalid dtype "%s" (uint8 or uint16 expected)' %
                                                                        dtype)
    nmax = 2 ** (8 * dtype.itemsize)

    if omax is None:
        omax = nmax - 1

    if vmax is None:
        vmax = nmax - 1
        nout = nmax
    else:
        nout = int(vmax + 1)

    if vmin < 0:
        vmin = 0

    if fill is True:
        nout = max(nout, nmax)
    elif fill:
        nout = max(nout, fill)

    if nout > 2 ** 32:
        raise ValueError('requested LUT is too large: %d.' % nout)

    lut = np.arange(nout)
    if vmin:
        lut = lut - float(vmin)

    scale = float(omax - omin) / (vmax - vmin)
    if scale != 1.0:
        lut = np.round(scale * lut)
    if omin:
        lut += omin

    return lut.clip(omin, omax).astype(dtype)


def histogram_equalized_lut(hist, dtype='uint8', fill=False):
    '''Compute a histogram equalized LUT.

    :param hist:
        histogram to be equalized
    :type hist:
        ndarray
    :param dtype:
        numpy data type of the output LUT (default uint8)
    :type dtype:
        np.dtype (uint8 or uint16)
    :param fill:
        if False (default) the returned LUT has
        :math:`length = len(hist)`.
        Otherwise the LUT length has a lenght of 2**nbits with nbits
        bein 8 or 16 depending on dtype and  LUT indices greater than
        the last histogram max value are filled with the maximum value
        itself.
    :type fill:
        bool
    :returns: the llok up table (LUT)

    '''

    dtype = np.dtype(dtype)
    if dtype not in (np.uint8, np.uint16):
        raise ValueError('invalid dtype "%s" (uint8 or uint16 expected)' %
                                                                        dtype)
    nmax = 2 ** (8 * dtype.itemsize)

    hist = np.ravel(hist)

    nbins = len(hist)
    if nbins == 0:
        raise ValueError('empty histgram')
    if nbins > nmax:
        raise ValueError('number of bins (%s) is too large to fit in '
                         'selected data type (%s)' % (nbins, dtype.name))

    if fill:
        nout = nbins
    else:
        nout = nmax

    lut = np.cumsum(hist) - hist[0]

    total = float(lut[-1])
    if total == 0:
        return np.zeros(nout)

    lut = nmax / total * (lut + hist / 2.)
    lut.clip(0, nout - 1)
    lut.resize(nout)
    lut[nbins:] = lut[nbins - 1]

    return lut.asarray(dtype)


def log_lut(dtype='uint8'):
    # @TODO: complete

    dtype = np.dtype(dtype)
    if dtype not in (np.uint8, np.uint16):
        raise ValueError('invalid dtype "%s" (uint8 or uint16 expected)' %
                                                                        dtype)
    nmax = 2 ** (8 * dtype.itemsize)
    vmax = nmax - 1

    lut = np.arange(nmax, 'float64')
    lut = np.round(vmax * np.log(lut + 1) / np.log(nmax))
    lut.clip(0, vmax)

    return lut.astype(dtype)


def root(dtype='uint8'):
    # @TODO: complete

    dtype = np.dtype(dtype)
    if dtype not in (np.uint8, np.uint16):
        raise ValueError('invalid dtype "%s" (uint8 or uint16 expected)' %
                                                                        dtype)
    nmax = 2 ** (8 * dtype.itemsize)
    vmax = nmax - 1

    lut = np.arange(nmax, 'float64')
    lut = vmax * np.root(lut / vmax)
    lut.clip(0, vmax)

    return lut.astype(dtype)


def square(dtype='uint8'):
    # @TODO: complete

    dtype = np.dtype(dtype)
    if dtype not in (np.uint8, np.uint16):
        raise ValueError('invalid dtype "%s" (uint8 or uint16 expected)' %
                                                                        dtype)
    nmax = 8 ** dtype.itemsize
    vmax = nmax - 1

    lut = np.arange(nmax, 'float64')
    lut = vmax * (lut / vmax) ** 2
    lut.clip(0, vmax)

    return lut.astype(dtype)


### Stretching utils #########################################################
class BaseStretcher(object):
    '''Base class for stretcher objects.

    The base implementation of the *__call__* method just performs
    clipping and type conversion (both are optional).

    .. note:: outout extrema (*min* and *max*) have to be compatible
              with the data type (*dtype*) set.

    Example::

        data = np.arange(.10, 300.)
        stretch = BaseStretch(0, 255, 'uint8')
        data = stretch(data)

    '''

    stretchtype = 'clip'

    def __init__(self, vmin=0, vmax=255, dtype='uint8'):
        assert min != max

        #: the minimum value for output data
        self.min = vmin

        #: the maximum value for output data
        self.max = vmax

        #: data type for output data
        self.dtype = dtype

    def __call__(self, data):
        data = np.asarray(data)
        if self.min is not None and self.max is not None:
            data = data.clip(self.min, self.max, out=data)
        if self.dtype is not None and data.dtype != np.dtype(self.dtype):
            data = data.astype(self.dtype)
        return data


class LinearStretcher(BaseStretcher):
    '''Linear stretch.

    Perform linear scaling (including offest application) and clipping.

    .. note:: offset is applyed before scaling:


        .. math:: output = scale \cdot (data - offset)

    '''

    stretchtype = 'linear'

    def __init__(self, scale=1.0, offset=0, vmin=0, vmax=255, dtype='uint8'):
        super(LinearStretcher, self).__init__(vmin, vmax, dtype)
        self.scale = scale
        self.offset = offset

    def __call__(self, data):
        data = np.asarray(data)
        if self.offset:
            data = data - self.offset
        if self.scale != 1.0:
            data = self.scale * data
        return super(LinearStretcher, self).__call__(data)

    # @TODO: if the API is compatible use
    #           range = property(get_range, set_range)
    @property
    def range(self):
        imin = self.min / self.scale + self.offset
        imax = self.max / self.scale + self.offset
        return imin, imax

    def set_range(self, imin, imax):
        if (imin, imax) == self.range:
            return
        assert imin != imax
        omax = self.max
        omin = self.min

        self.scale = float(omax - omin) / (imax - imin)
        self.offset = 0.5 * ((imax + imin) - (omax + omin) / self.scale)

        return self.offset, self.scale

    # @TODO:
    #@property
    #def outmax(self):
    #    return self.__call__(self.max)


class LUTStretcher(BaseStretcher):
    '''Stretch using LUT.

    Perform an arbitrary scaling on unsigned data using a look-up table
    (LUT).

    An optional offset is applied before LUT application.

    '''

    stretchtype = 'lut'

    def __init__(self, offset=0, vmin=0, vmax=255, dtype='uint8', fill=True):
        if np.dtype(dtype) not in (np.uint8, np.uint16):
            raise ValueError('only "uint8" and "uint16" are allowed.')
        super(LUTStretcher, self).__init__(vmin, vmax, dtype)
        self.fill = fill
        self.offset = offset
        self.lut = linear_lut(offset, vmax, 'uint8', fill, vmin, vmax)

    def __call__(self, data):
        data = np.asarray(data)
        if self.offset:
            data = data - self.offset
        if data.dtype != self.dtype:
            data = data.clip(0, len(self.lut) - 1, out=data)
            data = data.astype('uint32')
        return self.lut[data]

    @property
    def range(self):
        indices = np.where(self.lut != self.lut[-1])[0]
        imax = self.offset + len(indices)
        return self.offset, imax

    def set_range(self, imin, imax, fill=None):
        if (imin, imax) == self.range:
            return
        if imin == imax:
            self.lut[...] = imin
            return self.lut

        omax = self.max
        omin = self.min
        #assert omin != omax
        self.offset = imin
        if imin < 0:
            imin = 0
            imax -= self.offset
        if fill is None:
            fill = self.fill

        self.lut = linear_lut(imin, imax, self.dtype, fill, omin, omax)

        return self.lut


class LogarithmicStretcher(BaseStretcher):
    '''Linear stretch.

    Perform logarithmic stretching and clipping:

    .. math::

        output = scale \cdot log_{base}(data - offset)

    .. note:: both *base* and *scale* default to 10 while the default
              value for *offset* is 0 so the strecher returns values
              expressed in *dB*: :math:`output = 10 \cdot log_{10}(data)`

    '''

    stretchtype = 'logarithmic'
    _logfunctions = {
        None: np.log,
        'e': np.log,
        np.e: np.log,
        2: np.log2,
        10: np.log10,
    }
    _bases = {
        'e': np.e,
        np.log: np.e,
        np.log2: 2,
        np.log10: 10,
    }

    def __init__(self, scale=10, offset=0, base=10,
                 vmin=0, vmax=255, dtype='uint8'):
        super(LogarithmicStretcher, self).__init__(vmin, vmax, dtype)
        self.offset = offset
        self.scale = scale
        assert base in self.logfunctions
        self.base = base

    def __call__(self, data):
        data = np.asarray(data)
        if self.offset:
            data = data - self.offset

        base = self._bases[self.base]
        clipmin = base ** (self.min / self.scale)
        clipmax = base ** (self.max / self.scale)
        assert clipmin > 0
        data = data.clip(clipmin, clipmax, out=data)

        logfunc = self._logfunctions[self.base]
        data = logfunc(data)

        if self.scale != 1.0:
            data = self.scale * data
        return super(LogarithmicStretcher, self).__call__(data)
