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

# @TODO: choose a better name (virtual???)
class DatasetProxy(object):
    # class attributes:
    #   - cache basedir
    # instance attributes:
    #   - filename of the virtual dataset
    #   - gdal.Dataset
    #   - list of scale factors of available overviews
    #   - mapping overview-level --> overview-band (index?)
    #   - mapping overview index --> overview-level
    #   - source product file location (can one get it from the virtual
    #     dataset? maybe using xml)
    #   - source driver name (??)
    # methods:
    #   - get the nearesr overview level between the available ones
    pass
