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
import types
import logging
import itertools

import numpy

# @COMPATIBILITY: NG/pymod API
try:
    from osgeo import gdal
    from osgeo import osr
    from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode
except ImportError:
    import gdal
    import osr
    import gdalnumeric

    import numpy.numarray
    def GDALTypeCodeToNumericTypeCode(gdal_code):
        typecode = gdalnumeric.GDALTypeCodeToNumericTypeCode(gdal_code)
        return numpy.numarray.typeDict[typecode].name


try:
    # pymod API
    getDriverList = gdal.GetDriverList
except AttributeError:
    # NG API
    def getDriverList():
        return [gdal.GetDriver(index) for index in range(gdal.GetDriverCount())]

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


def gdalOvLevelAdjust(ovrlevel, xsize):
    '''Adjust the overview level

    Replicate the GDALOvLevelAdjust function from
    gdal-1.4.4/gcore/gdaldefaultoverviews.cpp

    '''

    oxsize = int(xsize + ovrlevel - 1) // ovrlevel
    return int(round(xsize / float(oxsize)))


class MissingOvrError(Exception):
    def __init__(self, ovrlevel):
        super(MissingOvrError, self).__init__(ovrlevel)
        self.message =\
            'Overview with level %s is not available in the product' % ovrlevel

class CoordinateMapper(object):
    geogCS = 'WGS84'

    #~ def __init__(self, dataset):
        #~ self._dataset = dataset

    def imgToGeoGrid(self, line, pixel):
        '''Coordinate conversion: (line,pixel) --> (lat,lon) on regular grids.

        Elements of the return (lat, lon) touple are 2D array with shape
        (len(line), len(pixels)).

        '''

        raise NotImplementedError('Abstract class "CoordinateMapper" do not '
                                  'implements the "imgToGeoGrid" method.')

    def geoToImgGrid(self, lat, lon):
        '''Coordinate conversion: (lat,lon) --> (line,pixel) on regular grids.

        Elements of the return (line, pixel) touple are 2D array with shape
        (len(lon), len(lat)).

        '''
        raise NotImplementedError('Abstract class "CoordinateMapper" do not '
                                  'implements the "geoToImgGrid" method.')

    def imgToGeoPoints(self, line, pixel):
        '''Coordinate conversion: (line,pixel) --> (lat,lon).'''

        raise NotImplementedError('Abstract class "CoordinateMapper" do not '
                                      'implements the "imgToGeoPoints" method.')

    def geoToImgPoints(self, lat, lon):
        '''Coordinate conversion: (lat,lon) --> (line,pixel).'''

        raise NotImplementedError('Abstract class "CoordinateMapper" do not '
                                  'implements the "geoToImgPoints" method.')


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


class GridCoordinateMapper(CoordinateMapper):

    def __init__(self, dataset):
        # @TODO: time this; it seems to be too slow in reading 3443 GCPs from
        #        SAR_IMM_1PXESA20080116_095222_00000471A133_00122_66609_0269.E2
        #super(GridCoordinateMapper, self).__init__(dataset)
        super(GridCoordinateMapper, self).__init__()

        ngcp = dataset.GetGCPCount()
        gcps = dataset.GetGCPs()
        gcps = _fixedGCPs(gcps)      # @TODO remove

        assert ngcp > 3, 'Insufficient number of points'

        # Extract (row, col) and (lat, lon) data
        lines = numpy.zeros(ngcp, dtype=numpy.float64)
        pixels = numpy.zeros(ngcp, dtype=numpy.float64)
        lats = numpy.zeros(ngcp, dtype=numpy.float64)
        lons = numpy.zeros(ngcp, dtype=numpy.float64)

        sref = osr.SpatialReference(dataset.GetGCPProjection())
        if not sref.IsGeographic():
            sref_target = osr.SpatialReference()
            sref_target.SetWellKnownGeogCS(self.geogCS)
            ct = osr.CoordinateTransformation(sref, sref_target)
            for row, gcp in enumerate(gcps):
                lines[row], pixels[row] = gcp.GCPLine, gcp.GCPPixel
                # discard gcp.GCPZ
                lons[row], lats[row], dummy = ct.TransformPoint(
                                                gcp.GCPX, gcp.GCPY, gcp.GCPZ)
        else:
            for row, gcp in enumerate(gcps):
                lines[row], pixels[row] = gcp.GCPLine, gcp.GCPPixel
                lons[row], lats[row] = gcp.GCPX, gcp.GCPY
                # discard gcp.GCPZ

        # Set interpolators
        from scipy import interpolate                   # @TODO: check
        kx = ky = min(5, int(numpy.sqrt(len(lines)))-1) # @TODO: check
        logging.debug('spline deg = %d' % kx)
        try:
            self._imgToLat = interpolate.SmoothBivariateSpline(lines, pixels, lats, kx=kx, ky=ky)
            self._imgToLon = interpolate.SmoothBivariateSpline(lines, pixels, lons, kx=kx, ky=ky)

            # @TODO: use delaunay from scikits for irregular grid intepolation
            self._geoToLine = interpolate.SmoothBivariateSpline(lons, lats, lines, kx=kx, ky=ky)
            self._geoToPixel = interpolate.SmoothBivariateSpline(lons, lats, pixels, kx=kx, ky=ky)
        except dfitpack.error:
            logging.debug('fallback to splines of degree 1')
            self._imgToLat = interpolate.SmoothBivariateSpline(lines, pixels, lats, kx=1, ky=1)
            self._imgToLon = interpolate.SmoothBivariateSpline(lines, pixels, lons, kx=1, ky=1)

            # @TODO: use delaunay from scikits for irregular grid intepolation
            self._geoToLine = interpolate.SmoothBivariateSpline(lons, lats, lines, kx=1, ky=1)
            self._geoToPixel = interpolate.SmoothBivariateSpline(lons, lats, pixels, kx=1, ky=1)

        #~ # Set interpolators @TODO: use bivariate splines
        #~ self._imgToLat = interpolate.interp2d(lines, pixels, lats)
        #~ self._imgToLon = interpolate.interp2d(lines, pixels, lons)
        #~ self._geoToLine = interpolate.interp2d(lons, lats, lines)
        #~ self._geoToPixel = interpolate.interp2d(lons, lats, pixels)

    def imgToGeoGrid(self, line, pixel):
        return self._imgToLat(line, pixel), self._imgToLon(line, pixel)

    def geoToImgGrid(self, lat, lon):
        return self._geoToLine(lat, lon), self._geoToPixel(lat, lon)

    def imgToGeoPoints(self, line, pixel):
        line, pixel = map(numpy.asarray, (line, pixel))
        np = min(line.size, pixel.size)
        lat = numpy.zeros(np, numpy.dtype.float64)
        lon = numpy.zeros(np, numpy.dtype.float64)
        for intex, (l, p) in enumerate(itertools.izip(line.float, pixel.flat)):
            lat[index] = self._imgToLat(line, pixel)
            lon[index] = self._imgToLon(line, pixel)
        # @TODO: check single point
        return lat, lon

    def geoToImgPoints(self, lat, lon):
        lat, lon = map(numpy.asarray, (lat, lon))
        np = min(lat.size, lon.size)
        line = numpy.zeros(np, numpy.dtype.float64)
        pixel = numpy.zeros(np, numpy.dtype.float64)
        for intex, (x, y) in enumerate(itertools.izip(lon.float, lat.flat)):
            line[index] = self._geoToLine(x, y)
            pixel[index] = self._geoToPixel(x, y)

        # @TODO: check single point
        return line, pixel

class InvalidProjection(ValueError):
    pass

class GeoTransformCoordinateMapper(CoordinateMapper):

    def __init__(self, dataset):
        super(GeoTransformCoordinateMapper, self).__init__()
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


def get_coordinate_mapper(dataset, precise=False):
    mapper = None
    try:
        if dataset.GetGCPCount() and precise:
            mapper = GridCoordinateMapper(dataset)
        else:
            #if dataset.GetProjection():
            mapper = GeoTransformCoordinateMapper(dataset)
    except ValueError, e:
        mapper = None
    else:
        # @TODO: check
        if mapper._geotransform == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
            mapper = None

    if mapper is None:
        logging.debug('unable to setup the coordinate mapper')
    return mapper

# @TODO: choose a better name (virtual???)
class MajorObjectProxy(object):
    def __init__(self, gdalobj):
        super(MajorObjectProxy, self).__init__()
        if isinstance(gdalobj, MajorObjectProxy):
            self._obj = gdalobj._obj
        else:
            self._obj = gdalobj

    def __getattr__(self, name):
        return getattr(self._obj, name)

    # @COMPATIBILITY: NG/pymod API
    if not hasattr(gdal.MajorObject, 'GetMetadata_List'):
        def GetMetadata_List(self):
            metadata = self._obj.GetMetadata()
            return ['%s=%s' % (key, metadata[key])
                                            for key in sorted(metadata.keys())]

    # @COMPATIBILITY: NG/pymod API
    #if not hasattr(gdal.MajorObject, 'GetMetadata_Dict'):
    #    def GetMetadata_Dict(self):
    #        return self._obj.GetMetadata()

class DriverProxy(MajorObjectProxy):
    pass

# @TODO: choose a better name (virtual???)
class BandProxy(MajorObjectProxy):

    def __init__(self, band, parent=None):
        super(BandProxy, self).__init__(band)

        assert isinstance(parent, (gdal.Dataset, DatasetProxy,
                                   gdal.Band, BandProxy, types.NoneType)), \
               'invalid parent type: %s' % type(parent)

        self.parent = parent
        self.lut = None

    def _get_coordinateMapper(self):
        if self.parent:
            return self.parent.coordinateMapper

    coordinateMapper = property(_get_coordinateMapper)

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
        if len(ovrlevels) == 0:
            raise MissingOvrError(ovrlevel)
        distances = numpy.abs(ovrlevels - ovrlevel)
        mindist = distances.min()
        distances = list(distances)

        return distances.index(mindist)

    def GetOverview(self, ov_index):
        __doc__ = self._obj.GetOverview.__doc__

        return BandProxy(self._obj.GetOverview(ov_index))

    # @COMPATIBILITY: NG/pymod API
    def ReadAsArray(self, xoff=0, yoff=0, win_xsize=None, win_ysize=None,
                    **kwargs):
        # xoff, yoff, xsize, ysize, buf_xsize=None, buf_ysize=None, buf_type=None
        __doc__ = self._obj.ReadAsArray.__doc__

        # This is a workaround for a bug in python-gdal_1.4.4 that raises::
        #
        #   TypeError: Unaligned buffer
        #
        # any time one tries to use ReadAsArray

        try:
            data = self._obj.ReadAsArray(xoff, yoff, win_xsize, win_ysize,
                                         **kwargs)
        except TypeError, e:
            if win_xsize is None:
                win_xsize = self.XSize
            if win_ysize is None:
                win_ysize = self.YSize

            # @TODO: handle complex data types
            import numpy.numarray

            data = self._obj.ReadRaster(xoff, yoff, win_xsize, win_ysize,
                                        **kwargs)
            if self._obj.DataType == gdal.GDT_CInt16:
                dtype = numpy.int16
                shape = (win_ysize, win_xsize, 2)
            elif self._obj.DataType == gdal.GDT_CInt32:
                dtype = numpy.int32
                shape = (win_ysize, win_xsize, 2)
            else:
                dtype = GDALTypeCodeToNumericTypeCode(self._obj.DataType)
                shape = (win_ysize, win_xsize)
            data = numpy.fromstring(data, dtype=dtype)
            data.shape = shape
            if data.ndim == 3:
                tmp = data
                data = numpy.ndarray(shape[:2], numpy.complex64)
                data.real = tmp[:,:,0]
                data.imag = tmp[:,:,1]

        return data


# @TODO: choose a better name (virtual???)
class DatasetProxy(MajorObjectProxy):
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
        filename = os.path.abspath(filename)
        filename = os.path.normpath(filename)
        self.filename = filename
        self._readonly_dataset = gdal.Open(filename)
        assert(self._readonly_dataset)

        # Handle CSK data @TODO: fix
        try:
            subdataset = self._readonly_dataset.GetSubDatasets()
            logging.debug('subdataset = %s' % subdataset)
            if subdataset:
                subdataset = [sd for sd in subdataset
                                                if ('/S01/SBI' in sd[0])
                                                    or ('/S01/MBI' in sd[0])]
                if subdataset:
                    sdfilename = subdataset[0][0]
                    dataset = gdal.Open(sdfilename)
                    if dataset:
                        self._readonly_dataset = dataset
        except AttributeError:
            pass
        # END: CSK data handling

        self.id = uniqueDatasetID(self._readonly_dataset)

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
        _vrtdataset = None
        if os.path.exists(self.vrtfilename):
            # @TODO: check if opening the dataset in update mode
            #        (gdal.GA_Update) is a better solution
            _vrtdataset = gdal.Open(self.vrtfilename)

        if _vrtdataset is None:
            # Hendle both non existing self.vrtfilename and errors in opening
            # existing self.vrtfilename
            driver = gdal.GetDriverByName('VRT')
            _vrtdataset = driver.CreateCopy(self.vrtfilename,
                                            self._readonly_dataset)

        super(DatasetProxy, self).__init__(_vrtdataset)

        self.coordinateMapper = get_coordinate_mapper(self._obj)

    def GetDescription(self):
        return self._readonly_dataset.GetDescription()

    def GetRasterBand(self, band_index):
        __doc__ = self._obj.GetRasterBand.__doc__

        return BandProxy(self._obj.GetRasterBand(band_index), parent=self)

    def GetOverview(self, ov_index):
        __doc__ = self._obj.GetOverview.__doc__

        return BandProxy(self._obj.GetOverview(ov_index), parent=self)

    def GetDriver(self):
        #return DriverProxy(self._obj.GetDriver())
        return DriverProxy(self._readonly_dataset.GetDriver())

    def reopen(self):
        self._obj = gdal.Open(self.vrtfilename)
