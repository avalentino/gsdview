#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2011-2019 Antonio Valentino <antonio.valentino@tiscali.it>
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


"""Compute statistics and histograms of geo-spatial data."""


import sys
import logging

try:
    from collections import namedtuple
except ImportError:
    Statistics = None
else:
    Statistics = namedtuple('Statistics', 'min max mean stddev')

from osgeo import gdal

__version__ = '1.0'

EX_FAILURE = 1

GDAL_STATS_KEYS = ('STATISTICS_MINIMUM', 'STATISTICS_MAXIMUM',
                   'STATISTICS_MEAN', 'STATISTICS_STDDEV')


# @NOTE: the band.GetStatistics method called with the second argument
#        set to False (no image rescanning) has been fixed in
#        r19666_ (1.6 branch) and r19665_ (1.7 branch)
#        see `ticket #3572` on `GDAL Trac`_.
#
# .. _r19666: http://trac.osgeo.org/gdal/changeset/19666
# .. _r19665: http://trac.osgeo.org/gdal/changeset/19665
# .. _`ticket #3572`: http://trac.osgeo.org/gdal/ticket/3572
# .. _`GDAL Trac`: http://trac.osgeo.org/gdal
HAS_GETSTATS_FORCE_BUG = (('1640' <= gdal.VersionInfo() < '1700') or
                          (gdal.VersionInfo() > '1720'))


def SafeGetStatistics(band, approxok, force):
    """Retriewe statistics form a GDAL raster band in a safe way.

    If it is not possible to get statistics (e.g. because the force
    flag is set to false and statistics are not available, or because
    the approxok is set and there are too many nodata elements in the
    raster band) then a tuple of four None is returned.

    :param approxok:
        if True statistics may be computed based on overviews or a
        subset of all tiles
    :param force:
        if False statistics will only be returned if it can be done
        without rescanning the image

    .. note:: in order to check errors due to nodata values the GDAL
              internal error status is reset.

    .. important:: this function only works for versions of GDAL in
                   which gdal.Band.GetStatistics correctly reset the
                   return values: 1.6.4 <= GDAL < 1.7.0 and
                   GDAL > 1.7.2 (see `ticket #3572`_ on `GDAL Trac`_.

    .. _`ticket #3572`: http://trac.osgeo.org/gdal/ticket/3572
    .. _`GDAL Trac`: http://trac.osgeo.org/gdal

    """

    if force is False and not HAS_GETSTATS_FORCE_BUG:
        raise RuntimeError('it is not safe to use gada.Band.GetStatistics '
                           'with the "force" parameter set to false with this '
                           'version of GDAL (%s)' % gdal.VersionInfo())

    gdal.ErrorReset()

    stats = band.GetStatistics(approxok, force)
    if stats == [0, 0, 0, -1] or gdal.GetLastErrorNo() != 0:
        stats = (None, None, None, None)

    gdal.ErrorReset()

    if Statistics:
        stats = Statistics(*stats)

    return stats


def GetStatisticsFromMetadata(band):
    metadata = band.GetMetadata()
    stats = [metadata.get(key) for key in GDAL_STATS_KEYS]

    if None in stats:
        stats = (None, None, None, None)
    else:
        stats = [float(item) for item in stats]

    if Statistics:
        stats = Statistics(*stats)

    return stats

SOURCE_TEMPLATE = '''\
<SimpleSource>
  <SourceFilename>%(filename)s</SourceFilename>
  <SourceBand>%(bandno)d</SourceBand>
  <SrcRect xOff="%(xoffset)d" yOff="%(yoffset)d" xSize="%(xsize)d" ySize="%(ysize)d"/>
  <DstRect xOff="0" yOff="0" xSize="%(xsize)d" ySize="%(ysize)d"/>
</SimpleSource>'''


def copy_dataset_subwin(dataset, srcwin, bands=None, vrtfile=''):
    xoffset, yoffset, xsize, ysize = srcwin

    driver = gdal.GetDriverByName('VRT')
    vrtds = driver.Create(vrtfile, xsize, ysize, 0)
    if not vrtds:
        if vrtfile:
            msg = 'unable to create a vrtual dataset for "%s" in "%s".' % (
                dataset.GetDescription(), vrtfile)
        else:
            msg = ('unable to create and anonymous vrtual dataset for "%s".' %
                   dataset.GetDescription())
        raise RuntimeError(msg)

    if bands is None:
        bands = range(1, dataset.RasterCount + 1)

    for bandno in bands:
        srcband = dataset.GetRasterBand(bandno)
        if not srcband:
            raise RuntimeError('unable to get raster band n. %s.' % bandno)

        vrtds.AddBand(srcband.DataType)
        dstband = vrtds.GetRasterBand(bandno)
        if not dstband:
            raise RuntimeError('unable to create raster bands in temporary '
                               'virtual file.')

        nodata = srcband.GetNoDataValue()
        if nodata:
            dstband.SetNoDataValue()

        sourcexml = SOURCE_TEMPLATE % locals()
        dstband.SetMetadataItem('source_0', sourcexml, 'new_vrt_sources')

        del srcband, dstband

    return vrtds


class HistogramRequest(object):
    def __init__(self, hmin=None, hmax=None, nbuckets=None,
                 include_out_of_range=False, computehistogram=True):

        #: Enable histogram computation.
        self.computehistogram = computehistogram

        #: Histogram minimum.
        self.hmin = hmin

        #: Histogram maximum.
        self.hmax = hmax

        #: Number of buckets for histogram comutation.
        self.nbuckets = nbuckets

        #: Flag for out of range values handling.
        #:
        #: If set then values below the histogram range will be mapped into
        #: the first bucket, and values above will be mapped into last one.
        #: Otherwise out of range values are discarded.
        self.include_out_of_range = include_out_of_range

    def __str__(self):
        return ('HistogramRequest(hmin=%(hmin)s, hmax=%(hmax)s, '
                'nbuckets=%(nbuckets)s, '
                'include_out_of_range=%(include_out_of_range)s, '
                'computehistogram=%(computehistogram)s)' % self.__dict__)

    def __bool__(self):
        return bool(self.computehistogram)

    if sys.version_info < (3, 0):
        __nonzero__ = __bool__

    def values(self):
        return self.hmin, self.hmax, self.nbuckets

    def iscustom(self):
        return all(
            val is not None for val in (self.hmin, self.hmax, self.nbuckets))


def computestats(dataset, bands=None, computestats=True, histreq=None,
                 approxok=False, minmax_only=False, callback=None):

    statistics = {}
    histograms = {}

    if bands is None:
        bands = range(1, dataset.RasterCount + 1)

    for bandno in bands:
        band = dataset.GetRasterBand(bandno)
        if not band:
            raise RuntimeError('unable to open band n. %d' % bandno)

        if computestats:
            stats = (None, None, None, None)
            if approxok:
                if HAS_GETSTATS_FORCE_BUG:
                    stats = SafeGetStatistics(band, True, False)

                if None in stats:
                    stats = GetStatisticsFromMetadata(band)

            if None in stats:
                stats = band.ComputeStatistics(approxok, callback)

            statistics[bandno] = stats

            vmin, vmax, mean, stddev = stats

            if minmax_only:
                logging.info('%f %f' % (vmin, vmax))
            else:
                logging.info('Statistics for band n. %d' % bandno)
                logging.info('Min:    %f' % vmin)
                logging.info('Max:    %f' % vmax)
                logging.info('Mean:   %f' % mean)
                logging.info('Stddev: %f' % stddev)

            if computestats and histreq:
                logging.info('')

        if histreq:
            if not histreq.iscustom():
                hmin, hmax, nbuckets, hist = band.GetDefaultHistogram(
                    callback=callback)
            else:
                hmin, hmax, nbuckets = histreq.values()
                nbuckets = int(nbuckets)
                hist = band.GetHistogram(hmin, hmax, nbuckets,
                                         histreq.include_out_of_range,
                                         approxok, callback)

            histograms[bandno] = (hmin, hmax, nbuckets, hist)

            logging.info('Histogram for band n. %d' % bandno)
            logging.info('Hist. min: %f' % hmin)
            logging.info('Hist. max: %f' % hmax)
            logging.info('Nuckets:   %d' % nbuckets)
            logging.info('Histogram: %s' % hist)

        if len(bands) > 1:
            logging.info('')

    return statistics, histograms


# Command line tool #########################################################
def get_parser():
    import argparse

    parser = argparse.ArgumentParser(prog='stats', description=__doc__)
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(__version__))
    parser.add_argument(
        '--no-stats', dest='stats', action='store_false', default=True,
        help='disable statistics computation (default: False)')
    parser.add_argument(
        '--hist', action='store_true', default=False,
        help='enable histogram computation (default: %(default)s)')
    parser.add_argument(
        '-b', '--band', type=int,
        help='compute statistics for a specific raster band '
             '(default: all bands are precessed)')
    parser.add_argument(
        '-a', '--approxok', action='store_true', default=False,
        help='if set then statistics may be computed based on overviews or '
             'a subset of all tiles (default: %(default)s)')
    parser.add_argument(
        '--minmax-only', action='store_true', default=False,
        help='only print minimum and maximum on the same line.')
    parser.add_argument(
        '--histreq', nargs=3, type=float, metavar=('MIN', 'MAX', 'NBUCKETS'),
        help='specify lower bound, upper bound and the number of buckets for '
             'histogram computation (automatically computed otherwise)')
    parser.add_argument(
        '-i', '--include_out_of_range', action='store_true', default=False,
        help='if set then values below the histogram range will be mapped '
             'into the first bucket, and values above will be mapped into '
             'last one. Otherwise out of range values are discarded.')
    parser.add_argument(
        '--srcwin', nargs=4, type=int,
        metavar=('XOFFSET', 'YOFFSET', 'XSIZE', 'YSIZE'),
        help='specify source window in image coordinates: '
             '(default: the entire image is processed)')
    parser.add_argument(
        '-o', '--outfile', metavar='FILE',
        help='write results to FILE (default: stdout)', )
    parser.add_argument(
        '-q', '--quiet', action='store_true',
        help='suppress progress messages')
    parser.add_argument('filename', help='input file name')

    return parser


def parse_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if argv:
        argv = gdal.GeneralCmdLineProcessor(argv)

    parser = get_parser()
    args = parser.parse_args(argv)

    if args.histreq and not args.hist:
        args.hist = True
        #parser.error('"histreq" option requires "hist"')

    if args.include_out_of_range and not args.hist:
        parser.error('"include_out_of_range" option requires "hist"')

    if args.band is not None and args.band < 1:
        parser.error('the "band" parameter should be a not null positive '
                     'integer.')

    histonly = bool(args.hist and not args.stats)
    if histonly and args.approxok and not args.histreq:
        logging.warning('the "approxok" option is ignored if "histreq" '
                        'is not set.')

    if not args.stats and not args.hist:
        parser.error('nothing to compute: '
                     'please check "--hist" and "--no-stats" options.')

    return args


def main(argv=None):
    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=logging.INFO)

    try:
        args = parse_args(argv)

        if args.outfile:
            logger = logging.getLogger('gsdtools.stats')

            streamhandler = logger.handlers[0]
            streamhandler.setLevel(logging.WARNING)

            formatter = streamhandler.formatter

            filehandler = logging.FileHandler(args.outfile, 'w')
            filehandler.setLevel(logging.INFO)
            filehandler.setFormatter(formatter)

            logger.addHandler(filehandler)

        filename = args.filename

        if args.quiet:
            progressfunc = None
        else:
            progressfunc = gdal.TermProgress

        if args.hist:
            histreq = HistogramRequest()
            if args.histreq:
                histreq.hmin, histreq.hmax, histreq.nbuckets = args.histreq

            if args.include_out_of_range:
                histreq.include_out_of_range = args.include_out_of_range
        else:
            histreq = None

        ds = gdal.Open(filename)
        if not ds:
            raise RuntimeError('unable to open "%s"' % filename)

        if args.band is not None:
            if args.band > ds.RasterCount:
                raise ValueError('band %d requested, but only bands 1 to %d '
                                 'are available.' % (args.band,
                                                     ds.RasterCount))
            bands = [args.band]
        else:
            bands = range(1, ds.RasterCount + 1)

        if args.srcwin:
            ds = copy_dataset_subwin(ds, args.srcwin)

        # core
        computestats(ds, bands, args.stats, histreq, args.approxok,
                     args.minmax_only, progressfunc)

        ds.FlushCache()
        ds = None

    except Exception as e:
        logging.error(str(e))
        logging.debug(str(e), exc_info=True)
        sys.exit(EX_FAILURE)


if __name__ == '__main__':
    main()
