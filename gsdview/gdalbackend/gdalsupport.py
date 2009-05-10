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

'''Support tools and classes for the GDAL library.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import os
import logging
import itertools

import numpy

from osgeo import gdal
from osgeo import osr
from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode

from gsdview import utils


GDAL_CONFIG_OPTIONS = '''\
GDAL_DATA
GDAL_SKIP
GDAL_DRIVER_PATH
OGR_DRIVER_PATH

GDAL_CACHEMAX
GDAL_FORCE_CACHING
GDAL_DISABLE_READDIR_ON_OPEN
GDAL_MAX_DATASET_POOL_SIZE
GDAL_IGNORE_AXIS_ORIENTATION
GDAL_SWATH_SIZE
GDAL_DISABLE_READDIR_ON_OPEN
GDAL_VALIDATE_CREATION_OPTIONS
GDAL_ONE_BIG_READ
GDAL_DTED_SINGLE_BLOCK

GDAL_PAM_ENABLED
GDAL_PAM_MODE
GDAL_PAM_PROXY_DIR

GDAL_TIFF_INTERNAL_MASK
GDAL_TIFF_ENDIANNESS

GDAL_JPEG_TO_RGB
GDAL_ECW_CACHE_MAXMEM

OGR_XPLANE_READ_WHOLE_FILE
OGR_SDE_GETLAYERTYPE
OGR_SDE_SEARCHORDER
OGR_S57_OPTIONS
OGR_DEBUG_ORGANIZE_POLYGONS
OGR_ORGANIZE_POLYGONS

CPL_DEBUG
CPL_LOG
CPL_LOG_ERRORS
CPL_ACCUM_ERROR_MSG
CPL_MAX_ERROR_REPORTS
CPL_TIMESTAMP
CPL_TMPDIR

COMPRESS_OVERVIEW
INTERLEAVE_OVERVIEW
PHOTOMETRIC_OVERVIEW

TMPDIR
TEMP

USE_RRD
USE_SPILL

PROJSO

GMLJP2OVERRIDE
GEOTIFF_CSV
JPEGMEM

DODS_CONF
DODS_AIS_FILE

BSB_PALETTE

CONVERT_YCBCR_TO_RGB
ECW_LARGE_OK
IDRISIDIR
DTED_VERIFY_CHECKSUM
IDA_COLOR_FILE
RPFTOC_FORCE_RGBA
HFA_USE_RRD
ADRG_SIMULATE_MULTI_GEN
HDF4_BLOCK_PIXELS
GEOL_AS_GCPS

CENTER_LONG

OCI_FID
OCI_DEFAULT_DIM

MDBDRIVER_PATH
ODBC_OGR_FID
DGN_LINK_FORMAT

TIGER_VERSION
TIGER_LFIELD_AS_STRING

PGSQL_OGR_FID
PGCLIENTENCODING
PG_USE_COPY
PG_USE_POSTGIS
PG_LIST_ALL_TABLES

S57_CSV
S57_PROFILE

INGRES_INSERT_SUB

IDB_OGR_FID

GPX_N_MAX_LINKS
GPX_ELE_AS_25D
GPX_USE_EXTENSIONS

SDE_VERSIONEDITS
SDE_VERSIONOVERWRITE
SDE_DESCRIPTION
SDE_FID

GML_FIELDTYPES
MYSQL_TIMEOUT
GEOMETRY_AS_COLLECTION
ATTRIBUTES_SKIP
KML_DEBUG'''


def uniqueDatasetID(prod):
    d = prod.GetDriver()
    driver_name = d.GetDescription()
    logging.debug('driver_name = %s' % driver_name)
    if driver_name == 'SAR_CEOS':
        try:
            # 'CEOS_LOGICAL_VOLUME_ID'
            metadata = prod.GetMetadata()
            prod_id = '%s-%s' % (metadata['CEOS_SOFTWARE_ID'].strip(),
                                 metadata['CEOS_ACQUISITION_TIME'].strip())
        except KeyError:
            prod_id = os.path.basename(prod.GetDescription())
    elif driver_name == 'ESAT':
        metadata = prod.GetMetadata()
        prod_id = os.path.splitext(metadata ['MPH_PRODUCT'])[0]
    #~ elif driver_name = 'GTiff':
        #~ # ERS BTIF
        #~ pass
    elif driver_name.startswith('HDF5') or driver_name.startswith('CSK'):
        prod_id = prod.GetDescription()
        parts = prod_id.split(':')
        if len(parts) == 4:
            fiename = ':'.join(parts[1:3])
            parts = (parts[0], filename, parts[2])
        if len(parts) == 3:
            filename = os.path.basename(parts[1].strip('"'))
            h5path = parts[2].replace('//', '/')
            prod_id = filename + h5path.replace('/', '_')
        else:
            prod_id = os.path.basename(prod_id)
    else:
        prod_id = os.path.basename(prod.GetDescription())

    logging.debug('prod_id = %s' % prod_id)
    return prod_id


def getDriverList():
    return [gdal.GetDriver(index) for index in range(gdal.GetDriverCount())]


def gdalFilters():
    # @TODO: move to gdalqt4
    filters = []
    filters.append('All files (*)')

    for driver in getDriverList():
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


# @TODO: remove
def _fixedGCPs(gcps):
    '''Fix Envisat GCPs

    For products with multiple slices the GCPLine coordinate
    refers to the one of the slice so we need to fix it in order
    to have the image coordinate.

    '''

    lines = [gcp.GCPLine for gcp in gcps]

    # @TODO: this is a weak check; improve it
    if numpy.alltrue(lines != numpy.sort(lines)):
        # @WARNING: here we are assuming that the geolocation grid
        #           has at least 2 lines
        # @WARNING: here we are assuming a particular order of GCPs
        upstepslocation = numpy.where(lines[1:] > lines[0:-1])[0] + 1
        upsteps = lines[upstepslocation] - lines[upstepslocation-1]

        # @WARNING: here we are assuming that the distance between geolocation
        #           grid linse is constant
        assert upsteps.max() == upsteps[:-1].min(), ('max = %f, min = %f' %
                                                (upsteps.max(), upsteps.min()))
        linespacing = int(upsteps[0])

        downstepslocation = numpy.where(lines[1:] < lines[0:-1])[0] + 1
        for index in downstepslocation:
            jumpsize = int(lines[index - 1] - lines[index]) + linespacing
            lines[index:] += jumpsize

        import copy
        gcps = copy.deepcopy(gcps)
        for indx, gcp in enumerate(gcps):
            gcp.GCPLine = lines[index]

    return gcps


class InvalidProjection(ValueError):
    pass


class CoordinateMapper(object):
    geogCS = 'WGS84'

    def __init__(self, dataset):
        super(CoordinateMapper, self).__init__()
        if dataset.GetGCPCount():
            projection = dataset.GetGCPProjection()
            gcps = dataset.GetGCPs()
            gcps = _fixedGCPs(gcps)      # @TODO: remove
            self._geotransform = gdal.GCPsToGeoTransform(gcps)
        else:
            projection = dataset.GetProjection()
            if not projection:
                projection = dataset.GetProjectionRef()
            self._geotransform = dataset.GetGeoTransform()

        if not projection:
            raise InvalidProjection('unable to get a valid projection')

        #sref = osr.SpatialReference(projection) # do not work for Pymod API
        sref = osr.SpatialReference()
        sref.ImportFromWkt(projection)

        if not sref.IsGeographic():
            sref_target = osr.SpatialReference()
            sref_target.SetWellKnownGeogCS(self.geogCS)
            self._srTransform = osr.CoordinateTransformation(sref, sref_target)
        else:
            self._srTransform = None

        # Xgeo = GT(0) + Xpixel*GT(1) + Yline*GT(2)
        # Ygeo = GT(3) + Xpixel*GT(4) + Yline*GT(5)
        #
        # --    --   --       --   --      --   --       --
        # | Xgeo |   | m11 m12 |   | Xpixel |   | xoffset |
        # |      | = |         | * |        | + |         |
        # | Ygeo |   | m21 m22 |   | Yline  |   | yoffset |
        # --    --   --       --   --      --   --       --
        xoffset, m11, m12, yoffset, m21, m22 = self._geotransform
        logging.debug('geotransform = %s' % str(self._geotransform))

        # Direct transform
        M = numpy.array(((m11, m12), (m21, m22)))
        C = numpy.array(([xoffset], [yoffset]))
        self._direct_transform = (M, C)

        # Invrse transform
        M = numpy.linalg.inv(M)
        C = -numpy.dot(M, C)
        self._inverse_transform = (M, C)

    def _transform(self, x, y, M, C):
        x, y = map(numpy.ravel, (x, y))

        Pin = numpy.array((x,y))
        return numpy.dot(M, Pin) + C

    def imgToGeoPoints(self, line, pixel):
        '''Coordinate conversion: (line,pixel) --> (lat,lon).'''

        M, C = self._direct_transform
        xy = self._transform(line, pixel, M, C)
        if self._srTransform:
            for index, (x, y) in enumerate(xy.transpose()):
                xy[:,index] = self._srTransform.TransformPoint(x,y)[:2]
        # @TODO: check single point
        return xy[1], xy[0]

    def geoToImgPoints(self, lat, lon):
        '''Coordinate conversion: (lat,lon) --> (line,pixel).'''

        M, C = self._inverse_transform
        rc = self._transform(lon, lat, M, C)
        # @TODO: check single point
        return rc[0], rc[1]

    def imgToGeoGrid(self, line, pixel):
        '''Coordinate conversion: (line,pixel) --> (lat,lon) on regular grids.

        Elements of the return (lat, lon) touple are 2D array with shape
        (len(line), len(pixels)).

        '''

        # @TODO: check single point
        px, py = numpy.meshgrid(line, pixel)
        lat, lon = self.imgToGeoPoints(px, py)
        lat.shape = lon.shape = (len(line), len(pixel)) # @TODO: check

        return lat, lon

    def geoToImgGrid(self, lat, lon):
        '''Coordinate conversion: (lat,lon) --> (line,pixel) on regular grids.

        Elements of the return (line, pixel) touple are 2D array with shape
        (len(lon), len(lat)).

        '''

        # @TODO: check single point
        px, py = numpy.meshgrid(lon, lat)
        line, pixel = self.geoToImgPoints(px, py)
        line.shape = pixel.shape = (len(lon), len(lat)) # @TODO: check

        return line, pixel


def coordinate_mapper(dataset, precise=False):
    try:
        mapper = CoordinateMapper(dataset)
    except ValueError, e:
        mapper = None
    else:
        # @TODO: check
        if mapper._geotransform == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
            mapper = None

    if mapper is None:
        logging.debug('unable to setup the coordinate mapper')
    return mapper


###############################################################################
### BEGIN #####################################################################
# @TODO: refactorize
def gdalOvLevelAdjust(ovrlevel, xsize):
    '''Adjust the overview level

    Replicate the GDALOvLevelAdjust function from
    gdal-1.4.4/gcore/gdaldefaultoverviews.cpp

    '''

    oxsize = int(xsize + ovrlevel - 1) // ovrlevel
    return int(round(xsize / float(oxsize)))


def compute_ovr_level(band, ovrsize=100*1024):
    '''Compute the overview factor that fits the ovrsize request.'''

    # ovrsize = 100 * 1024 ~= 100 KByte (about 320x320 8 bit pixels)

    #bytePerPixel = gdal.GetDataTypeSize(band.DataType) / 8
    bytesperpixel = 1   # the quicklook image is always converted to byte
    datasetsize = band.XSize * band.YSize * bytesperpixel
    ovrlevel = numpy.sqrt(datasetsize / float(ovrsize))
    ovrlevel = max(round(ovrlevel), 1)

    return gdalOvLevelAdjust(ovrlevel, band.XSize)


def available_ovr_levels(band):
    ovrlevels = []
    for ovrIndex in range(band.GetOverviewCount()):
        ovrXSize = band.GetOverview(ovrIndex).XSize
        ovrlevel = round(band.XSize / float(ovrXSize))
        ovrlevel = gdalOvLevelAdjust(ovrlevel, band.XSize)
        ovrlevels.append(ovrlevel)

    return ovrlevels


def best_ovr_index(band, ovrlevel=None, policy='NEAREST'):
    if ovrlevel is None:
        ovrlevel = compute_ovr_level(band)
    ovrlevels = numpy.asarray(available_ovr_levels(band))
    if len(ovrlevels) == 0:
        raise MissingOvrError(ovrlevel)

    distances = ovrlevels - ovrlevel
    if policy.upper() == 'NEAREST':
        distances = abs(distances)
        mindist = distances.min()
    elif policy.upper() == 'GREATER':
        indices = numpy.where(distances >= 0)[0]
        mindist = distances[indices].min()
    elif policy.upper() == 'SMALLER':
        indices = numpy.where(distances <= 0)[0]
        mindist = distances[indices].max()
    else:
        raise ValueError('invalid policy: "%s"' % policy)

    distances = list(distances)

    return distances.index(mindist)


class MissingOvrError(Exception):
    def __init__(self, ovrlevel):
        super(MissingOvrError, self).__init__(ovrlevel)

        def __str__(self):
            return ('Overview with level "%s" is not available in the '
                    'product' % self.args[0])

### END #######################################################################
###############################################################################

