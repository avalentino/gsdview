# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2015 Antonio Valentino <antonio.valentino@tiscali.it>
#
# This module is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 2 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this module if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US


'''Support tools and classes for the GDAL library.'''


import os
import shutil
import logging

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree

import numpy as np

from osgeo import gdal
from osgeo import osr

from gsdview.five import string_types


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
    # @TODO: use also gdal.Band.Checksum or similia

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
        prod_id = os.path.splitext(metadata['MPH_PRODUCT'])[0]
    #~ elif driver_name = 'GTiff':
        #~ # ERS BTIF
        #~ pass
    elif driver_name.startswith('HDF5') or driver_name.startswith('CSK'):
        prod_id = prod.GetDescription()
        parts = prod_id.split(':')
        if len(parts) == 4:
            filename = ':'.join(parts[1:3])
            parts = (parts[0], filename, parts[2])
        if len(parts) == 3:
            filename = os.path.basename(parts[1].strip('"'))
            h5path = parts[2].replace('//', '/')
            prod_id = filename + h5path.replace('/', '_')
        else:
            prod_id = os.path.basename(prod_id)
    elif driver_name == 'RS2':
        metadata = prod.GetMetadata()
        keys = (
            'SATELLITE_IDENTIFIER',     # 'RADARSAT-2'
            'SENSOR_IDENTIFIER',        # 'SAR'
            'PRODUCT_TYPE',             # 'SGF'
            'BEAM_MODE',                # 'W2'
            'ACQUISITION_START_TIME',   # '2008-05-30T14:25:38.076608Z'
        )
        parts = [metadata[key].strip() for key in keys]
        parts[-1] = parts[-1].replace(':', '_')
        prod_id = '-'.join(parts)
    else:
        prod_id = os.path.basename(prod.GetDescription())

    logging.debug('prod_id = %s' % prod_id)
    return prod_id


def driverList(drivertype='raster'):
    '''Return the list of available GDAL/OGR drivers'''

    if not drivertype:
        types = ['gdal']
    elif isinstance(drivertype, string_types):
        types = [drivertype]
    else:
        types = drivertype
        if not set(('raster', 'vector')).issuperset(types):
            raise ValueError('invalid type list: "%s"' % types)

    drivers = []
    if 'raster' in types:
        drivers.extend(
            gdal.GetDriver(index) for index in range(gdal.GetDriverCount()))

    if 'vector' in types:
        # @TODO: check
        from osgeo import ogr
        drivers.extend(
            ogr.GetDriver(index) for index in range(ogr.GetDriverCount()))

    return drivers


def gdalFilters(mode='r'):
    '''Returns the list of GDAL file filters as expected by Qt.'''

    # @TODO: move to gdalqt4
    filters = []
    filters.append('All files (*)')

    for driver in driverList():
        metadata = driver.GetMetadata()
        name = metadata['DMD_LONGNAME']
        try:
            ext = metadata['DMD_EXTENSION']
            if ext:
                if name.endswith(' (.%s)' % ext):
                    name = name[0: -len(ext) - 4]

                if 'w' in mode:
                    CREATECOPY = metadata.get(gdal.DCAP_CREATECOPY)
                    CREATE = metadata.get(gdal.DCAP_CREATE)
                    canwrite = bool((CREATECOPY == 'YES') or
                                    (CREATE == 'YES'))
                    if not canwrite:
                        continue

                filters.append('%s (*.%s)' % (name, ext))
        except KeyError:
            pass

    return filters


def ogrFilters():   # mode='r'):
    '''Returns the list of OGR file filters as expected by Qt'''

    # @TODO: move to an OGR specific module (??)
    filters = [
        'All files (*)',
        'ESRI Shapefiles (*.shp)',
        'KML (*.kml, *.kmz)',
        'Virtual Format (*.vrt)',
        'Arc/Info Binary Coverage (*.???)',
        'Arc/Info E00 (ASCII) Coverage (*.E00)',
        'Atlas BNA (*.bna)',
        'AutoCAD DXF (*.dfx)'
        'Comma Separated Value (*.csv)',
        'DODS/OPeNDAP (*.???)',
        'ESRI Personal GeoDatabase (*.???)',
        'ESRI ArcSDE (*.???)',
        'FMEObjects Gateway (*.NTF)',
        'GeoJSON (*.???)',
        'GeoConcept text export (*.gxt, *.txt)',
        'GeoRSS: Geographically Encoded Objects for RSS feeds (*,xml)',
        'GML - Geography Markup Language (*.gml)',
        'GMT ASCII Vectors (*.gmt)',
        'GPSBabel (*.???)',
        'GPX - GPS Exchange Format (*.gpx)',
        'GRASS (*.???)',
        'GTM - GPS TrackMaker (*.gtm)',
        'IDB (*.???)',
        'INTERLIS (*.???)',
        'INGRES (*.???)',
        'MapInfo TAB and MIF/MID (*.MIF, *.MID)',
        'Microstation DGN (*.???)',
        'MySQL (*.???)',
        'NAS - ALKIS (*.???)',
        'Oracle Spatial (*.???)',
        'ODBC RDBMS (*.???)',
        'OGDI Vectors (*.???)',
        'OpenAir Special Use Airspace Format (*.???)',
        'PDS - Planetary Data Systems TABLE (*.???)',
        'PostgreSQL SQL Dump (*.sql)',
        'PostgreSQL (*.???)',
        'IHO S-57 (ENC) (*.000)',
        'SDTS (*.???)',
        'SQLite RDBMS (*.???)',
        "SUA - Tim Newport-Peace's Special Use Airspace Format (*.SUA)",
        'UK .NTF (*.NTF)',
        'U.S. Census TIGER/Line (*.RT?)',
        'VFK - Czech cadastral exchange data format (*.???)',
        'X-Plane/Flightgear aeronautical data (*.dat)',
    ]

    return filters


def isRGB(dataset, strict=False):
    '''Return True if a dataset is compatible with RGB representaion.

    Conditions tested are:

      * 3 or 4 raster bands (3 in strict mode)
      * raster band datatype is GDT_Byte
      * color interpretation respect the expected order:

          band1: GCI_RedBand
          band2: GCI_GreenBand
          band3: GCI_BlueBand
          band4: GCI_AlphaBand (RGBA only allowed in non strict mode)

        GCI_Undefined color interpretation is allowed in non strict mode.

    '''

    if not hasattr(dataset, 'RasterCount'):
        # It is not a GDAL dataset
        return False

    if dataset.RasterCount not in (3, 4):
        return False

    # @TODO: allow different color orders (??)
    bands = [
        dataset.GetRasterBand(b) for b in range(1, dataset.RasterCount + 1)
    ]
    for band, colorint in zip(bands, (gdal.GCI_RedBand,
                                      gdal.GCI_GreenBand,
                                      gdal.GCI_BlueBand,
                                      gdal.GCI_AlphaBand)):

        if strict:
            allowed_colorints = (colorint, )
        else:
            allowed_colorints = (colorint, gdal.GCI_Undefined)
        actual_colorint = band.GetRasterColorInterpretation()
        if not band and actual_colorint not in allowed_colorints:
            return False
        if band.DataType != gdal.GDT_Byte:
            return False

    if strict and dataset.dastetCount != 3:
        return False

    return True


# Statistics helpers ########################################################
SAFE_GDAL_STATS = (('1640' <= gdal.VersionInfo() < '1700') or
                   (gdal.VersionInfo() > '1720'))

GDAL_STATS_KEYS = ('STATISTICS_MINIMUM', 'STATISTICS_MAXIMUM',
                   'STATISTICS_MEAN', 'STATISTICS_STDDEV')


def GetCachedStatistics(band):
    '''Retrieve cached statistics from a raster band.

    GDAL usually stores pre-computed statistics in the raster band
    metadata: STATISTICS_MINIMUM, STATISTICS_MAXIMUM, STATISTICS_MEAN
    and STATISTICS_STDDEV.

    This function retrieves cached statistics and returns them as a
    four items tuple: (MINIMUM, MAXIMUM, MEAN, STDDEV).

    '''

    metadata = band.GetMetadata()
    stats = [metadata.get(name) for name in GDAL_STATS_KEYS]

    # @TODO: remove.
    #        It is no more needed if the numeric locale is correctly set.
    #if None not in stats:
    #    stats = [float(item.replace(',', '.')) for item in stats]

    if None not in stats:
        stats = [float(item) for item in stats]

    return stats


def SafeGetStatistics(band, approx_ok=False, force=True):
    '''Safe replacement of gdal.Band.GetSrtatistics.

    The standard version of GetSrtatistics not always allows to know
    whenever statistics have beed actually computed or not (e.g. "force"
    flag set to False and no statistics available).

    This function gracefully handles this case an also cases in which
    an error happend during statistics computation (e.g. to many nodata
    values).

    :param band:
        GDAL raster band
    :param approx_ok:
        if approximate statistics are sufficient, the approx_ok flag
        can be set to True in which case overviews, or a subset of
        image tiles may be used in computing the statistics
        (default: False)
    :param force:
        if force is False results will only be returned if it can be
        done quickly (ie. without scanning the data).
        If force is False and results cannot be returned efficiently,
        the function will return four None instead of actual statistics
        values.
        Dafault: True.
    :returns:
        a tuple containing (min, max, mean, stddev) if statistics can
        be retriewed according to the input flags.
        A tuple of four None if statistics are not available or can't
        be computer according to input flags or if some error occurs
        during computation.

    '''

    # @NOTE: the band.GetStatistics method called with the second argument
    #        set to False (no image rescanning) has been fixed in
    #        r19666_ (1.6 branch) and r19665_ (1.7 branch)
    #        see `ticket #3572` on `GDAL Trac`_.
    #
    # .. _r19666: http://trac.osgeo.org/gdal/changeset/19666
    # .. _r19665: http://trac.osgeo.org/gdal/changeset/19665
    # .. _`ticket #3572`: http://trac.osgeo.org/gdal/ticket/3572
    # .. _`GDAL Trac`: http://trac.osgeo.org/gdal

    stats = (None, None, None, None)
    if approx_ok and not SAFE_GDAL_STATS:
        stats = GetCachedStatistics(band)

    if None in stats:
        if not force and not SAFE_GDAL_STATS:
            raise ValueError('unable to retrieve statistics in a safe way.')

        gdal.ErrorReset()
        stats = band.GetStatistics(approx_ok, force)
        if (gdal.GetLastErrorNo() == 1) and (gdal.GetLastErrorType() == 3):
            stats = (None, None, None, None)
            gdal.ErrorReset()
        elif SAFE_GDAL_STATS and stats == [0, 0, 0, -1]:
            stats = (None, None, None, None)

    return stats


def hasFastStats(band, approx_ok=True):
    '''Return true if band statistics can be retrieved quickly.

    If precomputed stistics are in band metadata or small enough band
    overviews does exist then it is assumed that band statistics can
    be retriewed in a very quick way.

    if the *approx_ok* only precomputed statistics are taken into
    account.

    '''

    if SAFE_GDAL_STATS:
        stats = band.GetStatistics(True, False)
        result = bool(stats != [0, 0, 0, -1])
    else:
        stats = GetCachedStatistics(band)
        result = bool(None not in stats)

    if not result and approx_ok:
        try:
            ovrBestIndex(band, policy='GREATER')
        except MissingOvrError:
            pass
        else:
            result = True

    return result

# Color table helpers #####################################################
colorinterpretations = {
    gdal.GPI_Gray: {
        'nchannels': 1,
        'label': 'Gray',
        'direct': {
            'Grayscale': 0,
        },
        'inverse': {
            0: 'Grayscale',
        },
    },
    gdal.GPI_RGB: {
        'nchannels': 4,
        'label': 'RGB',
        'direct': {
            'Red': 0,
            'Green': 1,
            'Blue': 2,
            'Alpha': 3,
        },
        'inverse': {
            0: 'Red',
            1: 'Green',
            2: 'Blue',
            3: 'Alpha',
        },
    },
    gdal.GPI_CMYK: {
        'nchannels': 4,
        'label': 'CMYK',
        'direct': {
            'Cyan': 0,
            'Magenta': 1,
            'Yellow': 2,
            'Black': 3,
        },
        'inverse': {
            0: 'Cyan',
            1: 'Magenta',
            2: 'Yellow',
            3: 'Black',
        },
    },
    gdal.GPI_HLS: {
        'nchannels': 3,
        'label': 'HLS',
        'direct': {
            'Hue': 0,
            'Lightness': 1,
            'Saturation': 2,
        },
        'inverse': {
            0: 'Hue',
            1: 'Lightness',
            2: 'Saturation',
        },
    },
}


def colortable2numpy(colortable):
    ncolors = colortable.GetCount()
    colors = np.zeros((ncolors, 4), np.uint8)
    for row in range(ncolors):
        colors[row] = colortable.GetColorEntry(row)

    colorint = colortable.GetPaletteInterpretation()
    nchannels = colorinterpretations[colorint]['nchannels']

    return colors[..., 0:nchannels]


# Coordinate conversion helpers ############################################
# @TODO: remove
# @NOTE: bugs #3160 and #3709 have been fixed upstream with commits r22289
#        and r22290 (1.8 branch). The fix should be included in GDAL v1.8.1.
def _fixedGCPs(gcps):
    '''Fix Envisat GCPs

    For products with multiple slices the GCPLine coordinate
    refers to the one of the slice so we need to fix it in order
    to have the image coordinate.

    '''

    lines = np.asarray([gcp.GCPLine for gcp in gcps])

    # @TODO: this is a weak check; improve it
    if np.alltrue(lines != np.sort(lines)):
        # @WARNING: here we are assuming that the geolocation grid
        #           has at least 2 lines
        # @WARNING: here we are assuming a particular order of GCPs
        upstepslocation = np.where(lines[1:] > lines[0:-1])[0] + 1
        upsteps = lines[upstepslocation] - lines[upstepslocation - 1]

        # @WARNING: here we are assuming that the distance between geolocation
        #           grid linse is constant
        assert upsteps.max() == upsteps[:-1].min(), ('max = %f, min = %f' %
                                                (upsteps.max(), upsteps.min()))
        linespacing = int(upsteps[0])

        downstepslocation = np.where(lines[1:] < lines[0:-1])[0] + 1
        for index in downstepslocation:
            jumpsize = int(lines[index - 1] - lines[index]) + linespacing
            lines[index:] += jumpsize

        import copy
        gcps = copy.deepcopy(gcps)
        for indx, gcp in enumerate(gcps):
            gcp.GCPLine = lines[indx]

    return gcps


class InvalidProjection(ValueError):
    pass


class CoordinateMapper(object):
    geogCS = 'WGS84'

    def __init__(self, dataset):
        super(CoordinateMapper, self).__init__()

        projection = ''
        self._geotransform = None

        if dataset.GetGCPCount():
            try:
                projection = dataset.GetGCPProjection()
                gcps = dataset.GetGCPs()
                gcps = _fixedGCPs(gcps)      # @TODO: remove
                self._geotransform = gdal.GCPsToGeoTransform(gcps)
            except Exception:
                logging.warning('unable to retrieve geo-transform and '
                                'projection from GCPs for %s' % dataset)

        if not self._geotransform:
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
        M = np.array(((m11, m12), (m21, m22)))
        C = np.array(([xoffset], [yoffset]))
        self._direct_transform = (M, C)

        # Invrse transform
        M = np.linalg.inv(M)
        C = -np.dot(M, C)
        self._inverse_transform = (M, C)

    def _transform(self, x, y, M, C):
        x = np.ravel(x)
        y = np.ravel(y)

        Pin = np.array((x, y))
        return np.dot(M, Pin) + C

    def imgToGeoPoints(self, pixel, line):
        '''Coordinate conversion: (pixel,line) --> (lon,lat).'''

        M, C = self._direct_transform
        xy = self._transform(pixel, line, M, C)
        if self._srTransform:
            for index, (x, y) in enumerate(xy.transpose()):
                xy[:, index] = self._srTransform.TransformPoint(x, y)[:2]
        # @TODO: check single point
        return xy[0], xy[1]  # , 0    # @TODO: h

    def geoToImgPoints(self, lon, lat, h=0):
        '''Coordinate conversion: (lon,lat) --> (pixel,line).'''

        M, C = self._inverse_transform
        rc = self._transform(lon, lat, M, C)
        # @TODO: check single point
        return rc[0], rc[1]

    def imgToGeoGrid(self, pixel, line):
        '''Coordinate conversion: (pixel,line) --> (lon,lat) on regular grids.

        Elements of the return (lon, lat) touple are 2D array with shape
        (len(pixels), len(line)).

        '''

        # @TODO: check single point
        px, py = np.meshgrid(pixel, line)
        lon, lat = self.imgToGeoPoints(px, py)
        lon.shape = lat.shape = (len(pixel), len(line))  # @TODO: check

        return lon, lat  # , 0    # @TODO: h

    def geoToImgGrid(self, lon, lat):
        '''Coordinate conversion: (lon,lat) --> (pixel,line) on regular grids.

        Elements of the return (pixel,line) touple are 2D array with shape
        (len(lon), len(lat)).

        '''

        # @TODO: check single point
        px, py = np.meshgrid(lon, lat)
        pixel, line = self.geoToImgPoints(px, py)
        pixel.shape = line.shape = (len(lon), len(lat))  # @TODO: check

        return line, pixel


def coordinate_mapper(dataset):
    try:
        mapper = CoordinateMapper(dataset)
    except ValueError:
        mapper = None
    else:
        # @TODO: check
        if mapper._geotransform == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
            mapper = None

    if mapper is None:
        logging.debug('unable to setup the coordinate mapper')
    return mapper


# Overviews handling helpers ###############################################
OVRMEMSIE = 400 * 1024  # 400 kbytes


class MissingOvrError(Exception):
    def __init__(self, ovrlevel):
        super(MissingOvrError, self).__init__(ovrlevel)

    def __str__(self):
        return ('Overview with level "%s" is not available in the '
                'product' % self.args[0])


def ovrLevelAdjust(ovrlevel, xsize):
    '''Adjust the overview level

    Replicate the GDALOvLevelAdjust function from
    gdal/gcore/gdaldefaultoverviews.cpp:

    .. code-block:: c

        int nOXSize = (nXSize + nOvLevel - 1) / nOvLevel;
        return (int) (0.5 + nXSize / (double) nOXSize);

    '''

    oxsize = int(xsize + ovrlevel - 1) // ovrlevel
    return int(round(xsize / float(oxsize)))


def ovrLevelForSize(gdalobj, ovrsize=OVRMEMSIE):
    '''Compute the overview factor that fits the ovrsize request.

    Default ovrsize = 300 KBytes ==> about 640x640 pixels paletted or
    320x320 pixels RGB32.

    '''

    if hasattr(gdalobj, 'GetOverviewCount'):
        # gdalobj is a raster band

        band = gdalobj

        #bytePerPixel = gdal.GetDataTypeSize(band.DataType) / 8
        bytesperpixel = 1   # the quicklook image is always converted to byte
        datasize = band.XSize * band.YSize * bytesperpixel
        ovrlevel = np.sqrt(datasize / float(ovrsize))
        ovrlevel = max(round(ovrlevel), 1)

        return ovrLevelAdjust(ovrlevel, band.XSize)
    else:
        # assume gdalobj is a dataset to be represented as an RGB32
        dataset = gdalobj
        band = dataset.GetRasterBand(1)
        return ovrLevelForSize(band, ovrsize / 4)


def ovrLevels(gdalobj, raw=False):
    '''Return availabe overview levels.'''

    if hasattr(gdalobj, 'GetOverviewCount'):
        # gdalobj is a raster band
        band = gdalobj
        levels = []

        for index in range(band.GetOverviewCount()):
            ovrXSize = band.GetOverview(index).XSize
            ovrlevel = round(band.XSize / float(ovrXSize))
            if not raw:
                ovrlevel = ovrLevelAdjust(ovrlevel, band.XSize)
            levels.append(ovrlevel)

        return levels
    else:
        # assume gdalobj is a dataset
        dataset = gdalobj
        band = dataset.GetRasterBand(1)
        return ovrLevels(band, raw)


def ovrBestIndex(gdalobj, ovrlevel=None, policy='NEAREST'):
    '''Return the overview index that best fits *ovrlevel*.

    If *ovrlevel* is `None` it is used the level returner by the
    `ovrLevelForSize` function i.e. the lavel ensures that the data
    size doesn't exceede a certain memory size (defaut 300K).

    The *policy* parameter can be set to:

    :NEAREST: between available ovr factors the one closest to the
              requested one (*ovrlevel*) is returned
    :GREATER: between available ovr factors it is returned the closest
              one that is greater or equal to the requested *ovrlevel*
    :SMALLER: between available ovr factors it is returned the closest
              one that is smaller or equal to the requested *ovrlevel*

    .. note:: plase note that *GREATER* for overview level implies a
              larger reduction factor hence a smaller image (and vice
              versa).

    '''

    if hasattr(gdalobj, 'GetOverviewCount'):
        # gdalobj is a raster band
        band = gdalobj
        if ovrlevel is None:
            ovrlevel = ovrLevelForSize(band)  # 400K
        levels = np.asarray(ovrLevels(band))
        if len(levels) == 0:
            raise MissingOvrError(ovrlevel)

        distances = levels - ovrlevel
        if policy.upper() == 'NEAREST':
            distances = abs(distances)
            mindist = distances.min()
        elif policy.upper() == 'GREATER':
            indices = np.where(distances >= 0)[0]
            if np.size(indices) == 0:
                raise MissingOvrError(ovrlevel)
            mindist = distances[indices].min()
        elif policy.upper() == 'SMALLER':
            indices = np.where(distances <= 0)[0]
            if np.size(indices) == 0:
                raise MissingOvrError(ovrlevel)
            mindist = distances[indices].max()
        else:
            raise ValueError('invalid policy: "%s"' % policy)

        distances = list(distances)

        return distances.index(mindist)
    else:
        # assume gdalobj is a dataset
        dataset = gdalobj
        band = dataset.GetRasterBand(1)
        return ovrBestIndex(band, ovrlevel, policy)


def ovrComputeLevels(gdalobj, ovrsize=OVRMEMSIE, estep=3, threshold=0.1):
    '''Compute the overview levels to be generated.

    GSDView relies on overviews to provide a confortable image
    navigation experience (scroll, pan, zoom etc).
    This function evaluated the number and overview factors to be
    pre-calculated in order to provide such a confortable experience.

    :param ovrsize:
        memory size that the smallest overview should not exceede
    :param estep:
        step for overview levels computation::

            estep = 3 ==> 3, 9, 27, 81, ...

    :param threshold:
        if already exist overview levels close (with respect to
        threshold) to requested ones then computation is skipped

    '''

    maxfactor = ovrLevelForSize(gdalobj, ovrsize)
    if maxfactor == 1:
        return []

    metadata = gdalobj.GetMetadata('IMAGE_STRUCTURE')
    compressed = bool(metadata.get('COMPRESSION'))
    if compressed:
        startexponent = 0
    else:
        startexponent = 1

    maxesponent = np.ceil(maxfactor ** (1. / estep))
    exponents = np.arange(startexponent, maxesponent + 1)
    missinglevels = estep ** exponents
    missinglevels = missinglevels.astype(np.int)

    # Remove exixtng levels to avoid re-computation
    levels = ovrLevels(gdalobj)
    missinglevels = sorted(set(missinglevels).difference(levels))

    # remove levels close to target ones (threshold 10%)
    candidates = missinglevels
    missinglevels = []
    for level in candidates:
        try:
            index = ovrBestIndex(gdalobj, level)
        except MissingOvrError:
            pass
        else:
            bestlevel = levels[index]
            if bestlevel and abs(bestlevel - level) / float(level) < threshold:
                continue
        missinglevels.append(level)

    return missinglevels


def ovrRead(dataset, x=0, y=0, w=None, h=None, ovrindex=None,
            bstart=1, bcount=None, dtype=None):
    '''Read an image block from overviews of all spacified bands.

    This function read a data block from the overview corresponding to
    *ovrindex* for all *bcount* raster bands starting drom the
    *bstart*\ th one.

    Parameters:

    dataset: GDAL dataset object
        the GDAL dataset to read from
    x, y: int
        origin of the box to read in overview coordinates
    w, h: int
        size of the box to read in overview coordinates
    ovrindex: int
        index of the overview to read from.
        If the overview index is `None` data are retrieved directly
        from the raster band instead of overviews.
    bstart: int
        raster band start index (default 1).
    bcount: int or None
        raster band count (defaut all starting from *bstart*)

    Returns:

    data: ndarray
        the array of data read with shape (h, w, bcount)

    '''

    # @TODO: check RasterColorInterpretation

    if bcount is None:
        bcount = dataset.RasterCount

    assert bstart > 0
    assert bstart - 1 + bcount <= dataset.RasterCount

    #data = np.zeros((h, w, dataset.RasterCount), np.ubyte)
    channels = []
    for bandindex in range(bstart, bstart + bcount):
        band = dataset.GetRasterBand(bandindex)
        if ovrindex is not None:
            band = band.GetOverview(ovrindex)
        channels.append(band.ReadAsArray(x, y, w, h))

    data = np.dstack(channels)
    if dtype and dtype != data.dtype:
        return np.astype(data)
    else:
        return data


# Misc helpers ##############################################################
def has_complex_bands(dataset):
    result = False
    for band_id in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(band_id)
        result = gdal.DataTypeIsComplex(band.DataType)
        if result:
            break
    return result


def safe_vrt_copy(src, dst):
    if isinstance(src, gdal.Dataset):
        driver = gdal.GetDriverByName('VRT')
        driver.CreateCopy(dst, src)
        srcpath = os.path.dirname(src.GetDescription())
    else:
        # assume src is a path
        shutil.copy(src, dst)
        srcpath = os.path.dirname(src)

    xml = etree.parse(dst)
    for srcfile in xml.iter('SourceFilename'):
        relativeToVRT = int(srcfile.get('relativeToVRT', 0))
        if relativeToVRT and not os.path.isabs(srcfile.text):
            srcfile.text = os.path.join(srcpath, srcfile.text)
        srcfile.set('relativeToVRT', '0')

    with open(dst, 'wb') as fd:
        fd.write(etree.tostring(xml.getroot()))
