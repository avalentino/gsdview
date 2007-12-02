#!/usr/bin/env python

import os
import logging
import itertools

import numpy
import scipy.ndimage
# @TODO: scipy.misc.bytescale

import gdal

import gdalsupport

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


def apply_LUT(data, lut):
    data = numpy.round(data)
    data = data.astype(numpy.uint32) # @TODO: check
    return lut[data]

def _quicklook_core_rebin(data, qlFact):
    sRow = sCol = qlFact//2
    nRows, nCols = data.shape
    eRows = nRows//qlFact * qlFact
    eCols = nCols//qlFact * qlFact
    data = data[sRow:eRows:qlFact, sRow:eCols:qlFact]
    return data

def _quicklook_core_mean_filter(data, qlFact):
    data = scipy.ndimage.uniform_filter(data, qlFact)
    return _quicklook_core_rebin(data, qlFact)

def _quicklook_core_convolve(data, qlFact):
    #~ print '_quicklook_core_convolve'
    filter = numpy.ones((qlFact, qlFact))/(qlFact**2) # @TODO: check dtype
    data = scipy.ndimage.convolve(data, filter)
    return _quicklook_core_rebin(data, qlFact)

def sliding_win_filter2d(input, function, size=None, step=None, output=None,
                         extra_arguments=(), extra_keywords={}):

    input = numpy.asarray(input)
    if input.shape != 2:
        raise TypeError, 'only bi-dimensional arrays are supported'
    #~ if numpy.iscomplexobj(input):
        #~ raise TypeError, 'Complex type not supported'
    if size == None:
        raise RuntimeError, "no footprint or filter size provided"
    sizes = _ni_support._normalize_sequence(size, input.ndim)
    steps = _ni_support._normalize_sequence(step, input.ndim)

    outsizes = [(size_ - winsize)//step_+1 for size_, winsize, step_ in
                                                zip(input.shape, sizes, steps)]
    if output and output.shape != outsizes:
        raise RuntimeError("incompatible output shape")
    else:
        output = numpy.ndarray(outsizes, dtype=data.dtype)
    for row in xrange(outsizes[0]):
        sRowIn = row*steps[0]
        eRowIn = sRowIn+sizes[0]
        for col in xrange(outsizes[1]):
            sColIn = col*staps[1]
            eColIn = sColIn+sizes[1]
            output[row, col] = function(data[sRowIn:eRowIn, sColIn:eColIn],
                                        *extra_arguments, **extra_keywords)
    return output

def _quicklook_core_loop(data, qlFact):
    nRows, nCols = data.shape
    nRows //= qlFact
    nCols //= qlFact
    out = numpy.ndarray((nRows, nCols), dtype=data.dtype)
    for row in xrange(nRows):
        sRowIn = row*qlFact
        eRowIn = sRowIn+qlFact
        for col in xrange(nCols):
            sColIn = col*qlFact
            eColIn = sColIn+qlFact
            out[row, col] = data[sRowIn:eRowIn, sColIn:eColIn].mean()
    return out

def quicklook(prod, bufsize=5*1024**2, func=_quicklook_core_mean_filter,
              progress_callback=None):
    width = 400
    height = 400
    xScalingFactor = int(numpy.ceil(float(prod.RasterXSize) / width))
    yScalingFactor = int(numpy.ceil(float(prod.RasterYSize) / height))
    qlFact = max(xScalingFactor, yScalingFactor)
    band = prod.GetRasterBand(1)
    bytesPerPixel = gdal.GetDataTypeSize(band.DataType) / 8

    outWidth = prod.RasterXSize // qlFact
    outHeight = prod.RasterYSize // qlFact

    chunkSize = qlFact * bytesPerPixel * prod.RasterXSize
    nChunks = max(prod.RasterYSize // qlFact, 1)
    chunksPerBlock = max(bufsize // chunkSize, 1)
    nBlocks = int(numpy.ceil(float(nChunks) / chunksPerBlock))
    chunksPerBlock = int(numpy.ceil(float(nChunks) / nBlocks))
    chunksPerBlock = max(chunksPerBlock, 1)
    outRowsPerBlock = chunksPerBlock
    rowsPerBlock = chunksPerBlock * qlFact

    inSlices = ((slice(0, prod.RasterXSize),
                 slice(y, min(y+rowsPerBlock, prod.RasterYSize)))
                        for y in xrange(0, prod.RasterYSize, rowsPerBlock))
    outSlices = ((slice(0, outWidth), slice(y, y+outRowsPerBlock))
                        for y in xrange(0, outHeight, outRowsPerBlock))

    # @TODO: check
    #output = numpy.ndarray((outHeight, outWidth), dtype=numpy.uint16)
    output = numpy.ndarray((outHeight, outWidth), dtype=numpy.float)
    count = 0.
    for inSlice, outSlice in itertools.izip(inSlices, outSlices):
        inSliceX, inSliceY = inSlice
        outSliceX, outSliceY = outSlice
        w = inSliceX.stop - inSliceX.start
        h = inSliceY.stop - inSliceY.start
        data = prod.ReadAsArray(inSliceX.start, inSliceY.start, w, h)
        output[outSliceY, outSliceX] = func(data, qlFact)
        if callable(progress_callback):
            count = count + 1
            progress_callback(float(count)/nBlocks)

    # @TOD: fix lut
    lut = numpy.arange(2**16)*255./200
    lut[200:] = 255
    lut = lut.round().astype(numpy.uint8)
    output = lut[output]

    return output

def stats0(prod, bufsize=5*1024**2, progress_callback=None):
    width = 400
    height = 400
    xScalingFactor = int(numpy.ceil(float(prod.RasterXSize) / width))
    yScalingFactor = int(numpy.ceil(float(prod.RasterYSize) / height))
    qlFact = max(xScalingFactor, yScalingFactor)
    band = prod.GetRasterBand(1)
    bytesPerPixel = gdal.GetDataTypeSize(band.DataType) / 8

    outWidth = prod.RasterXSize // qlFact
    outHeight = prod.RasterYSize // qlFact

    chunkSize = qlFact * bytesPerPixel * prod.RasterXSize
    nChunks = max(prod.RasterYSize // qlFact, 1)
    chunksPerBlock = max(bufsize // chunkSize, 1)
    nBlocks = int(numpy.ceil(float(nChunks) / chunksPerBlock))
    chunksPerBlock = int(numpy.ceil(float(nChunks) / nBlocks))
    chunksPerBlock = max(chunksPerBlock, 1)
    outRowsPerBlock = chunksPerBlock
    rowsPerBlock = chunksPerBlock * qlFact

    inSlices = ((slice(0, prod.RasterXSize),
                 slice(y, min(y+rowsPerBlock, prod.RasterYSize)))
                        for y in xrange(0, prod.RasterYSize, rowsPerBlock))
    outSlices = ((slice(0, outWidth), slice(y, y+outRowsPerBlock))
                        for y in xrange(0, outHeight, outRowsPerBlock))

    count = 0.
    min_ = []
    max_ = []
    x = []
    x2 = []
    #std = sqrt(mean((x - x.mean())**2))
    histograms = []

    for inSlice, outSlice in itertools.izip(inSlices, outSlices):
        inSliceX, inSliceY = inSlice
        outSliceX, outSliceY = outSlice
        w = inSliceX.stop - inSliceX.start
        h = inSliceY.stop - inSliceY.start
        data = prod.ReadAsArray(inSliceX.start, inSliceY.start, w, h)

        # stats eval
        min_.append(data.min())
        max_.append(data.max())
        x.append(data.sum())
        x2.append(numpy.sum(data.astype(numpy.float)**2))
        nbins = max_[-1] - min_[-1] + 1
        range_ = (min_[-1], max_[-1]+1)     # @NOTE: dtype = uint16
        histograms.append(numpy.histogram(data, nbins, range_))
        # progress
        if callable(progress_callback):
            count = count + 1
            progress_callback(float(count)/nBlocks)

    # stats eval
    min_ = min(min_)
    max_ = max(max_)
    n = prod.RasterXSize*prod.RasterYSize
    mean_ = sum(x)/float(n)
    std_ = numpy.sqrt(sum(x2)/float(n) - mean_**2)

    nbins = max(len(h) for h, b in histograms)
    histogram_ = numpy.zeros(nbins, dtype=numpy.uint32)
    for h, bins in histograms:
        s = slice(int(bins[0]), int(bins[-1]+1))
        histogram_[s] += h

    return min_, max_, mean_, std_, histogram_

def stats(prod, bufsize=5*1024**2, progress_callback=None):
    width = 400
    height = 400
    xScalingFactor = int(numpy.ceil(float(prod.RasterXSize) / width))
    yScalingFactor = int(numpy.ceil(float(prod.RasterYSize) / height))
    qlFact = max(xScalingFactor, yScalingFactor)
    band = prod.GetRasterBand(1)
    bytesPerPixel = gdal.GetDataTypeSize(band.DataType) / 8

    outWidth = prod.RasterXSize // qlFact
    outHeight = prod.RasterYSize // qlFact

    chunkSize = qlFact * bytesPerPixel * prod.RasterXSize
    nChunks = max(prod.RasterYSize // qlFact, 1)
    chunksPerBlock = max(bufsize // chunkSize, 1)
    nBlocks = int(numpy.ceil(float(nChunks) / chunksPerBlock))
    chunksPerBlock = int(numpy.ceil(float(nChunks) / nBlocks))
    chunksPerBlock = max(chunksPerBlock, 1)
    outRowsPerBlock = chunksPerBlock
    rowsPerBlock = chunksPerBlock * qlFact

    inSlices = ((slice(0, prod.RasterXSize),
                 slice(y, min(y+rowsPerBlock, prod.RasterYSize)))
                        for y in xrange(0, prod.RasterYSize, rowsPerBlock))
    outSlices = ((slice(0, outWidth), slice(y, y+outRowsPerBlock))
                        for y in xrange(0, outHeight, outRowsPerBlock))

    count = 0.
    histograms = []

    for inSlice, outSlice in itertools.izip(inSlices, outSlices):
        inSliceX, inSliceY = inSlice
        outSliceX, outSliceY = outSlice
        w = inSliceX.stop - inSliceX.start
        h = inSliceY.stop - inSliceY.start
        data = prod.ReadAsArray(inSliceX.start, inSliceY.start, w, h)

        # stats eval
        max_ = data.max()
        min_ = data.min()
        nbins = max_ - min_ + 1
        range_ = (min_, max_+1)     # @NOTE: dtype = uint16
        histograms.append(numpy.histogram(data, nbins, range_))
        # progress
        if callable(progress_callback):
            count = count + 1
            progress_callback(float(count)/nBlocks)

    # stats eval


    nbins = max(len(h) for h, b in histograms)
    histogram_ = numpy.zeros(nbins, dtype=numpy.uint32)
    min_ = []
    max_ = []
    for h, bins in histograms:
        s = slice(int(bins[0]), int(bins[-1]+1))
        min_.append(bins[0])
        max_.append(bins[-1])
        histogram_[s] += h

    n = numpy.sum(histogram_.astype(numpy.float))
    min_ = min(min_)
    max_ = max(max_)
    bins = numpy.arange(min_, max_+1, dtype=numpy.float)
    mean_ = numpy.sum(bins * histogram_)/n
    # std = sqrt(mean((x - x.mean())**2))
    x2 = numpy.sum(bins**2 * histogram_)/n
    std_ = numpy.sqrt(x2 - mean_**2)


    return min_, max_, mean_, std_, histogram_

def quicklook_and_stats(prod, bufsize=5*1024**2, progress_callback=None):

    width = 400
    height = 400
    xScalingFactor = int(numpy.ceil(float(prod.RasterXSize) / width))
    yScalingFactor = int(numpy.ceil(float(prod.RasterYSize) / height))
    qlFact = max(xScalingFactor, yScalingFactor)
    band = prod.GetRasterBand(1)

    # checks
    if band.DataType in (gdal.GDT_CInt16, gdal.GDT_CInt32):
        logging.warning('complex integer dataset')
    dtype = gdalsupport.GDT_to_dtype[band.DataType]
    if numpy.iscomplex(dtype()):
        logging.warning('extract module from complex data')
    # @TODO: fix (raise an error if a overview file is opened)
    if prod.ReadAsArray(0, 0, 1, 1).ndim != 2:
        logging.warning('the dataset is not bi-dimenzional')

    # initialization
    bytesPerPixel = gdal.GetDataTypeSize(band.DataType) / 8

    outWidth = prod.RasterXSize // qlFact
    outHeight = prod.RasterYSize // qlFact

    chunkSize = qlFact * bytesPerPixel * prod.RasterXSize
    nChunks = max(prod.RasterYSize // qlFact, 1)
    chunksPerBlock = max(bufsize // chunkSize, 1)
    nBlocks = int(numpy.ceil(float(nChunks) / chunksPerBlock))
    chunksPerBlock = int(numpy.ceil(float(nChunks) / nBlocks))
    chunksPerBlock = max(chunksPerBlock, 1)
    outRowsPerBlock = chunksPerBlock
    rowsPerBlock = chunksPerBlock * qlFact

    inSlices = ((slice(0, prod.RasterXSize),
                 slice(y, min(y+rowsPerBlock, prod.RasterYSize)))
                        for y in xrange(0, prod.RasterYSize, rowsPerBlock))
    outSlices = ((slice(0, outWidth), slice(y, y+outRowsPerBlock))
                        for y in xrange(0, outHeight, outRowsPerBlock))

    output = numpy.ndarray((outHeight, outWidth), dtype=numpy.float)

    count = 0.
    min_ = []
    max_ = []
    x = []
    x2 = []
    #std = sqrt(mean((x - x.mean())**2))
    histograms = []

    for inSlice, outSlice in itertools.izip(inSlices, outSlices):
        inSliceX, inSliceY = inSlice
        outSliceX, outSliceY = outSlice
        w = inSliceX.stop - inSliceX.start
        h = inSliceY.stop - inSliceY.start
        data = prod.ReadAsArray(inSliceX.start, inSliceY.start, w, h)
        if numpy.iscomplexobj(data):
            data = numpy.abs(data)
        if data.ndim > 2:
            data = data[0]
        output[outSliceY, outSliceX] = _quicklook_core_loop(data, qlFact)

        # stats eval
        min_.append(data.min())
        max_.append(data.max())
        x.append(data.sum())
        x2.append(numpy.sum(data.astype(numpy.float)**2))
        nbins = max_[-1] - min_[-1] + 1
        range_ = (min_[-1], max_[-1]+1)     # @NOTE: dtype = uint16
        histograms.append(numpy.histogram(data, nbins, range_))
        # progress
        if callable(progress_callback):
            count = count + 1
            progress_callback(float(count)/nBlocks)

    # stats eval
    min_ = min(min_)
    max_ = max(max_)
    n = prod.RasterXSize*prod.RasterYSize
    mean_ = sum(x)/float(n)
    std_ = numpy.sqrt(sum(x2)/float(n) - mean_**2)

    nbins = max(len(h) for h, b in histograms)
    histogram_ = numpy.zeros(nbins, dtype=numpy.uint32)
    for h, bins in histograms:
        s = slice(int(bins[0]), int(bins[-1]+1))
        histogram_[s] += h

    return output, min_, max_, mean_, std_, histogram_

def test_quicklook():
    import os
    filename = 'ASA_IMP_1PNUPA20030421_061704_000000162015_00392_05957_0020.N1'
    p = gdal.Open(os.path.join(os.path.expanduser('~'), 'tmp', filename))
    ql = quicklook(p, bufsize*1024**2)
    import pylab
    pylab.imshow(ql, pylab.cm.gray)
    pylab.title(filename)
    pylab.show()

def test_quicklook_bufsize():
    import os
    import datetime
    filename = 'ASA_IMP_1PNUPA20030421_061704_000000162015_00392_05957_0020.N1'
    p = gdal.Open(os.path.join(os.path.expanduser('~'), 'tmp', filename))
    for bufsize in (50, 20, 10, 5, 2, 1, 0.5): #(150, 100, 50, 10, 5, 1):
        start = datetime.datetime.now()
        ql = quicklook(p, bufsize*1024**2)
        elapsed = datetime.datetime.now() - start
        print 'bufsize = %f time: %d.%d' % (bufsize, elapsed.seconds,
                                            elapsed.microseconds)

def test_quicklook_func():
    import os
    import datetime
    filename = 'ASA_IMP_1PNUPA20030421_061704_000000162015_00392_05957_0020.N1'
    p = gdal.Open(os.path.join(os.path.expanduser('~'), 'tmp', filename))
    #~ for func in (
    for func in (
                 #~ _quicklook_core_rebin,
                 _quicklook_core_mean_filter,
                 #~ _quicklook_core_convolve,
                 _quicklook_core_loop,
                 ):
        start = datetime.datetime.now()
        ql = quicklook(p, func=func)
        elapsed = datetime.datetime.now() - start
        print '%s:\t%d.%d' % (func.__name__, elapsed.seconds,
                              elapsed.microseconds)
        #~ import pylab
        #~ pylab.figure()
        #~ pylab.imshow(ql, pylab.cm.gray)
        #~ pylab.title(func.__name__)
    #~ pylab.show()

def test_stats():
    import os
    import datetime
    filename = 'ASA_IMP_1PNUPA20030421_061704_000000162015_00392_05957_0020.N1'
    p = gdal.Open(os.path.join(os.path.expanduser('~'), 'tmp', filename))
    for func in (
                 stats0,
                 #~ stats,
                ):
        start = datetime.datetime.now()
        min_, max_, mean_, std_, histogram_ = stats(p)
        elapsed = datetime.datetime.now() - start
        print '%s:\t%d.%d' % (func.__name__, elapsed.seconds,
                              elapsed.microseconds)
        print 'min',min_
        print 'max',max_
        print 'mean',mean_
        print 'std',std_

        # normalization
        histogram_ = histogram_.astype(numpy.float)
        histogram_ /= histogram_.sum()

        ifun = numpy.cumsum(histogram_)
        startView = numpy.where(ifun <= 0.005)[0][-1]
        stopView = numpy.where(ifun > 0.99)[0][0]

        import pylab

        pylab.figure()
        pylab.plot(histogram_[startView:stopView])
        pylab.title('histogram')
        pylab.grid(True)

    pylab.show()

def test_quicklook_and_stats():
    import os
    import datetime
    filename = 'ASA_IMP_1PNUPA20030421_061704_000000162015_00392_05957_0020.N1'
    p = gdal.Open(os.path.join(os.path.expanduser('~'), 'tmp', filename))
    start = datetime.datetime.now()
    ql, min_, max_, mean_, std_, histogram_ = quicklook_and_stats(p)
    elapsed = datetime.datetime.now() - start
    print 'elapsed: %d.%d' % (elapsed.seconds, elapsed.microseconds)

    # normalization
    histogram_ = histogram_.astype(numpy.float)
    histogram_ /= histogram_.sum()

    ifun = numpy.cumsum(histogram_)
    startView = numpy.where(ifun <= 0.005)[0][-1]
    stopView = numpy.where(ifun > 0.99)[0][0]

    lut = numpy.zeros(max_+1, numpy.uint8)
    rate = 255./(stopView-startView-1)
    aux = numpy.arange(stopView-startView) * rate
    print min(aux), max(aux)
    lut[startView:stopView] = aux.round()
    lut[stopView:] = 255

    ql = apply_LUT(ql, lut)

    import pylab

    pylab.figure()
    pylab.imshow(ql, pylab.cm.gray)
    pylab.title('quick-look')

    stopView = numpy.where(ifun > 0.99)[0][0]
    pylab.figure()
    pylab.plot(histogram_[startView:stopView])
    pylab.twinx()
    pylab.plot(lut[startView:stopView], color='red')
    pylab.title('histogram + LUT')
    pylab.grid(True)

    pylab.show()

#~ test_quicklook_func()
#~ test_stats()
#~ test_quicklook_and_stats()
#~ test_quicklook_func()
#~ test_quicklook_func()
#~ test_quicklook_func()

#~ def tobyte(self, data, LUT=None):
    #~ #@TODO: which band?
    #~ rasterBand = self.product.GetRasterBand(1)
    #~ # @TOOD: fix flags (approx, force)
    #~ min_, max_, mean, stddev = rasterBand.GetStatistics(False, True)
    #~ lower = round(max(mean - 3*stddev, 0))
    #~ upper = round(min(mean + 3*stddev, max_))

    #~ indices = numpy.where(data < lower)
    #~ data[indices] = 0
    #~ indices = numpy.where(0 <= data <= upper)
    #~ data[indices] = (data[indices] - lower) * 255. / (upper - lower)
    #~ indices = numpy.where(data > upper)
    #~ data[indices] = 255

    #~ data.round()
    #~ data = data.astype(numpy.uint8)

    #~ return data

#~ class GdalCache(object):
    #~ def __init__(self, product, buffsize=100*1024**2):
        #~ self.band = product.GetRasterBand(1)
        #~ self.bufsize = bufsize
        #~ self._x = 0
        #~ self._y = 0

    #~ def _buffer_shape(windowWidth=1, windowHeight=1):
        #~ band = product.GetRasterBand(1)
        #~ bytesPerPixel = gdal.GetDataTypeSize(band.DataType) / 8
        #~ npixel = buffsize // bytesPerPixel
        #~ if windowWidth * windowHeight * bytesPerPixel > self.buffsize:
            #~ width, height= windowWidth, windowHeight
        #~ else:
            #~ # @TODO: complete
            #~ width = height = int(numpy.sqrt(npixel))
        #~ return width, height

    #~ def get_window_shape(self, width, height):
        #~ return self._window_shape

    #~ def set_window_shape(self, width, height):
        #~ width, height = int(width), int(height)
        #~ if width < 1 or height < 1:
            #~ raise ValueError('Invalid window shape: (%d, %d)' % (width, height))
        #~ self._window_shape = (width, haight)

    #~ window_shape = property(get_window_shape, set_window_shape)

    #~ def read(self, x, y, width, height):
        #~ pass
