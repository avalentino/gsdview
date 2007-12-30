#!/usr/bin/env python

import os
import logging
import itertools

import numpy
import scipy.ndimage
# @TODO: scipy.misc.bytescale


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
    histogram_ = numpy.histogram(data, nbins, range_)[0]
    lut = compute_lin_LUT2(histogram_)
    return lut


def apply_LUT(data, lut):
    data = numpy.round(data)
    data = data.astype(numpy.uint32) # @TODO: check
    return lut[data]
