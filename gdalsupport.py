#!/usr/bin/env python

import os
import itertools

import numpy
from scipy.interpolate import interp2d

try:
    from osgeo import gdal
    from osgeo import osr
except ImportError:
    import gdal
    import osr


GDT_to_dtype = {
    #gdal.GDT_Unknown:   numpy.,            # --  0 --
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
    #gdal.GDT_to_dtype:  numpy.,            # -- 12 --
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


class GridCoordinateMapper(CoordinateMapper):

    def __init__(self, dataset):
        super(GridCoordinateMapper, self).__init__(dataset)

        ngcp = dataset.GetGCPCount()

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
            for row, gcp in enumerate(dataset.GetGCPs()):
                lines[row], pixels[row] = gcp.GCPLine, gcp.GCPPixel
                # discard gcp.GCPZ
                lons[row], lats[row], dummy = ct.TransformPoint(
                                                gcp.GCPX, gcp.GCPY, gcp.GCPZ)
        else:
            for row, gcp in enumerate(dataset.GetGCPs()):
                lines[row], pixels[row] = gcp.GCPLine, gcp.GCPPixel
                lons[row], lats[row] = gcp.GCPX, gcp.GCPY
                # discard gcp.GCPZ

        # Set interpolators @TODO: use bivariate splines
        self._imgToLat = interp2d(lines, pixels, lats)
        self._imgToLon = interp2d(lines, pixels, lons)
        self._geoToLine = interp2d(lons, lats, lines)
        self._geoToPixel = interp2d(lons, lats, pixels)

    def imgToGeoGrid(self, line, pixel):
        __doc__ = CoordinateMapper.imgToGeoGrid.__doc__

        return self._imgToLat(line, pixel), self._imgToLon(line, pixel)

    def geoToImgGrid(self, lat, lon):
        __doc__ = CoordinateMapper.geoToImgGrid.__doc__

        return self._geoToLine(lat, lon), self._geoToPixel(lat, lon)

    def imgToGeoPoints(self, line, pixel):
        __doc__ = CoordinateMapper.imgToGeoPoints.__doc__

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
        __doc__ = CoordinateMapper.geoToImgPoints.__doc__

        lat, lon = map(numpy.asarray, (lat, lon))
        np = min(lat.size, lon.size)
        line = numpy.zeros(np, numpy.dtype.float64)
        pixel = numpy.zeros(np, numpy.dtype.float64)
        for intex, (x, y) in enumerate(itertools.izip(lon.float, lat.flat)):
            line[index] = self._geoToLine(x, y)
            pixel[index] = self._geoToPixel(x, y)

        # @TODO: check single point
        return line, pixel


class GeoTransformCoordinateMapper(CoordinateMapper):

    def __init__(self, dataset):
        super(GeoTransformCoordinateMapper, self).__init__(dataset)
        assert dataset.GetProjection() or dataset.GetProjectionRef()

        sref = osr.SpatialReference(dataset.GetProjection())
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
        xoffset, m11, m12, yoffset, m21, m22 = dataset.GetGeoTransform()

        # Direct transform
        M = numpy.array(((m11, m12), (m21, m22)))
        C = numpy.array(([xoffset], [yoffset]))
        self._direct_transform = (M, C)

        # Invrse transform
        M = numpy.linalg.inv(M)
        C = -numpy.dot(M, C)
        self._inverse_transform = (M, C)

    def _transform(self, x, y, M, C):
        '''Coordinate conversion: (line,pixel) --> (lat,lon).'''

        x, y = map(numpy.ravel, (x, y))

        Pin = numpy.array((x,y))
        return numpy.dot(M, Pin) + C

    def imgToGeoPoints(self, line, pixel):
        __doc__ = CoordinateMapper.imgToGeoPoints.__doc__

        M, C = self._direct_transform
        xy = self._transform(line, pixel, M, C)
        if self._srTransform:
            for index, (x, y) in enumerate(xy.transpose()):
                xy[:,index] = self._srTransform.TransformPoint(x,y)[:2]
        # @TODO: check single point
        return xy[1], xy[0]

    def geoToImgPoints(self, lat, lon):
        __doc__ = CoordinateMapper.geoToImgPoints.__doc__

        M, C = self._inverse_transform
        rc = self._transform(lon, lat, M, C)
        # @TODO: check single point
        return rc[0], rc[1]

    def imgToGeoGrid(self, line, pixel):
        __doc__ = CoordinateMapper.imgToGeoGrid.__doc__
        #~ # @TODO: check single point
        px, py = numpy.meshgrid(line, pixel)
        lat, lon = self.imgToGeoPoints(px, py)
        lat.shape = lon.shape = (len(line), len(pixel)) # @TODO: check

        return lat, lon

    def geoToImgGrid(self, lat, lon):
        __doc__ = CoordinateMapper.geoToImgGrid.__doc__
        #~ # @TODO: check single point
        px, py = numpy.meshgrid(lon, lat)
        line, pixel = self.geoToImgPoints(px, py)
        line.shape = pixel.shape = (len(lon), len(lat)) # @TODO: check

        return line, pixel


def get_coordinate_mapper(dataset):
    if dataset.GetGCPCount():
        return GridCoordinateMapper(dataset)
    elif dataset.GetProjection():
        assert dataset.GetGeoTransform() != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        return GeoTransformCoordinateMapper(dataset)
    else:
        return None

# @TODO: choose a better name (virtual???)
class BandProxy(object):

    def __init__(self, dataset, band_id):
        self._dataset = dataset
        self.id = band_id
        self._band = dataset._vrtdataset.GetRasterBand(self.id)
        self.lut = None

    coordinateMapper = property(lambda self: self._dataset.coordinateMapper)

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

        self.coordinateMapper = get_coordinate_mapper(self._vrtdataset)

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
