#!/usr/bin/env python

import os
import numpy
import gdal

GDT_to_dtype = {
    #gdal.GDT_Unknown:   numpy.,             # --  0 --
    gdal.GDT_Byte:      numpy.uint8,        # --  1 --
    gdal.GDT_UInt16:    numpy.uint16,       # --  2 --
    gdal.GDT_Int16:     numpy.int16,        # --  3 --
    gdal.GDT_UInt32:    numpy.uint32,       # --  4 --
    gdal.GDT_Int32:     numpy.int32,        # --  5 --
    gdal.GDT_Float32:   numpy.float32,      # --  6 --
    gdal.GDT_Float64:   numpy.float64,      # --  7 --
    gdal.GDT_CInt16:    numpy.complex64,    # --  8 -- converted to (float32, float32)
    gdal.GDT_CInt32:    numpy.complex64,    # --  9 -- converted to (float32, float32)
    gdal.GDT_CFloat32:  numpy.complex64,    # -- 10 -- (float32, float32)
    gdal.GDT_CFloat64:  numpy.complex128,   # -- 11 -- (float64, float64)
    #gdal.GDT_to_dtype:  numpy.,             # -- 12 --
}

def uniqueDatasetID(prod):
    d = prod.GetDriver()
    driver_name = d.GetDescription()
    if driver_name == 'SAR_CEOS':
        # 'CEOS_LOGICAL_VOLUME_ID'
        metadata = prod.GetMetadata()
        prod_id = '%s-%s' % (metadata['CEOS_SOFTWARE_ID'].strip(),
                             metadata['CEOS_ACQUISITION_TIME'].strip())
    elif driver_name == 'ESAT':
        metadata = prod.GetMetadata()
        prod_id = os.path.splitext(metadata ['MPH_PRODUCT'])[0]
    #~ elif driver_name = 'GTiff':
        #~ # ERS BTIF
        #~ pass
    else:
        prod_id = os.path.basename(prod.GetDescription())
    return prod_id

def gdalFilters():
    # @TODO: move to gdalqt4
    filters = []
    filters.append('All files (*)')
    for driver_index in xrange(gdal.GetDriverCount()):
    #~ for driver in gdal.GetDriverList():
        driver = gdal.GetDriver(driver_index)
        metadata = driver.GetMetadata()
        name = metadata['DMD_LONGNAME']
        try:
            ext = metadata['DMD_EXTENSION']
            if ext:
                if name.endswith(' (.%s)' % ext):
                    name = name[0: -len(ext)-4]
                filters.append('%s (*.%s)' % (name, ext))
        except KeyError:
            pass
    return filters

def gdalOvLevelAdjust(ovrlevel, xsize):
    '''Adjust the overview level

    Replicate the GDALOvLevelAdjust function from
    gdal-1.4.4/gcore/gdaldefaultoverviews.cpp

    '''

    oxsize = int(xsize + ovrlevel - 1) // ovrlevel
    return round(xsize / float(oxsize))

class MissingOvrError(Exception):
    def __init__(self, ovrlevel):
        super(MissingOvrError, self).__init__(ovrlevel)
        self.message =\
            'Overview with level %s is not available in the product' % ovrlevel

# @TODO: choose a better name (virtual???)
class BandProxy(object):

    def __init__(self, dataset, band_id):
        self._dataset = dataset
        self.id = band_id
        self._band = dataset._vrtdataset.GetRasterBand(self.id)
        self.lut = None

    def __getattr__(self, name):
        return getattr(self._band, name)

    def compute_ovr_level(self, ovrsize=100*1024):
        '''Compute the overview factor that fits the ovrsize request.'''

        # ovrsize = 100 * 1024 ~= 100 KByte (about 320x320 8 bit pixels)

        #bytePerPixel = gdal.GetDataTypeSize(band.DataType) / 8
        bytesperpixel = 1   # the quicklook image is always converted to byte
        datasetsize = self.XSize * self.YSize * bytesperpixel
        ovrlevel = numpy.sqrt(datasetsize / float(ovrsize))
        ovrlevel = max(round(ovrlevel), 1)
        return gdalOvLevelAdjust(ovrlevel, self.XSize)

    def available_ovr_levels(self):
        ovrlevels = []
        for ovrIndex in range(self.GetOverviewCount()):
            ovrXSize = self.GetOverview(ovrIndex).XSize
            ovrlevel = round(self.XSize / float(ovrXSize))
            ovrlevel = gdalOvLevelAdjust(ovrlevel, self.XSize)
            ovrlevels.append(ovrlevel)

        return ovrlevels

    def best_ovr_index(self, ovrlevel=None):
        if ovrlevel is None:
            ovrlevel = self.compute_ovr_level()
        ovrlevels = numpy.asarray(self.available_ovr_levels())
        if not ovrlevels:
            raise MissingOvrError(ovrlevel)
        distances = numpy.abs(ovrlevels - ovrlevel)
        mindist = distances.min()
        distances = list(distances)

        return distances.index(mindist)

    def reopen(self):
        self._band = self._dataset._vrtdataset.GetRasterBand(self.id)


# @TODO: choose a better name (virtual???)
class DatasetProxy(object):
    # class attributes:
    #   - cache basedir
    # instance attributes:
    #   - mapping overview-level --> overview-band (index?)
    #   - mapping overview index --> overview-level
    #   - source product file location (can one get it from the virtual
    #     dataset? maybe using xml)
    #   - source driver name (??)
    # methods:
    #   - cache opened bands

    def __init__(self, filename, cachedir=None):
        self.filename = filename
        self._rodataset = gdal.Open(filename)
        self.id = uniqueDatasetID(self._rodataset)
        self._bandcache = {}

        # Build the virtual dataset filename
        if cachedir is None:
            cachedir = os.path.join('~', '.gsdview', 'cache')
            cachedir = os.path.expanduser(cachedir)
        cachedir = os.path.join(cachedir, self.id)
        if not os.path.isdir(cachedir):
            os.makedirs(cachedir)
        self.vrtfilename = os.path.join(cachedir, 'virtual-dataset.vrt')

        # Create the virtual dataset
        # @TODO: check 'openshared'
        if not os.path.exists(self.vrtfilename):
            driver = gdal.GetDriverByName('VRT')
            self._vrtdataset = driver.CreateCopy(self.vrtfilename,
                                                 self._rodataset)
        else:
            # @TODO: check if opening the dataset in update mode
            #        (gdal.GA_Update) is a better solution
            self._vrtdataset = gdal.Open(self.vrtfilename)

    def __getattr__(self, name):
        return getattr(self._vrtdataset, name)

    def GetRasterBand(self, nBand):
        __doc__ = self._vrtdataset.GetRasterBand.__doc__

        if nBand not in self._bandcache:
            self._bandcache[nBand] = BandProxy(self, nBand)

        return self._bandcache[nBand]

    def reopen(self):
        self._vrtdataset = gdal.Open(self.vrtfilename)
        for band in self._bandcache.values():
            band.reopen()
