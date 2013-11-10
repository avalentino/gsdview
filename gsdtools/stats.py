#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Copyright (C) 2011-2013 Antonio Valentino <a_valentino@users.sf.net>

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


'''Compute statistics and histograms of geo-spatial data.'''


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
    '''Retriewe statistics form a GDAL raster band in a safe way.

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

    '''

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

    def __nonzero__(self):
        return bool(self.computehistogram)

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
def handlecmd(argv=None):
    import optparse

    if argv is None:
        argv = sys.argv

    argv = gdal.GeneralCmdLineProcessor(argv)

    parser = optparse.OptionParser(
        usage='%prog [options] FILENAME',
        version='%%prog %s' % __version__,
        description=__doc__)
    parser.add_option('--no-stats', dest='stats', action='store_false',
                      default=True,
                      help='disable statistics computation (default: False)')
    parser.add_option('--hist', action='store_true', default=False,
                      help='enable histogram computation (default: %default)')
    parser.add_option('-b', '--band', type='int',
                      help='compute statistics for a specific raster band '
                           '(default: all bands are precessed)')
    parser.add_option('-a', '--approxok', action='store_true', default=False,
                      help='if set then statistics may be computed based on '
                           'overviews or a subset of all tiles '
                           '(default: %default)')
    parser.add_option('--minmax-only', action='store_true', default=False,
                      help='only print minimum and maximum on the same line.')
    parser.add_option('--histreq', nargs=3, type='float',
                      metavar='MIN MAX NBUCKETS',
                      help='specify lower bound, upper bound and the number '
                           'of buckets for histogram computation '
                           '(automatically computed otherwise)')
    parser.add_option('-i', '--include_out_of_range', action='store_true',
                      default=False,
                      help='if set then values below the histogram range will '
                           'be mapped into the first bucket, and values above '
                           'will be mapped into last one. '
                           'Otherwise out of range values are discarded.')
    parser.add_option('--srcwin', nargs=4, type='int',
                      metavar='XOFFSET YOFFSET XSIZE YSIZE',
                      help='specify source window in image coordinates: '
                           '(default: the entire image is processed)')
    parser.add_option('-o', '--outfile', metavar='FILE',
                      help='write results to FILE (default: stdout)', )
    parser.add_option('-q', '--quiet', action='store_true',
                      help='suppress progress messages')

    options, args = parser.parse_args()

    if options.histreq and not options.hist:
        options.hist = True
        #parser.error('"histreq" option requires "hist"')
    if options.include_out_of_range and not options.hist:
        parser.error('"include_out_of_range" option requires "hist"')
    if options.band is not None and options.band < 1:
        parser.error('the "band" parameter shoulb be a not null positive '
                     'integer.')
    histonly = bool(options.hist and not options.stats)
    if histonly and options.approxok and not options.histreq:
        logging.warning('the "approxok" option is ignored if "histreq" '
                        'is not set.')

    if not options.stats and not options.hist:
        parser.error('nothing to compute: '
                     'please check "--hist" and "--no-stats" optoions.')
    if len(args) != 1:
        parser.error('at least one argument is required.')

    return options, args


def main(*argv):
    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=logging.INFO)

    try:
        if not argv:
            argv = sys.argv

        options, args = handlecmd(argv)

        if options.outfile:
            logger = logging.getLogger()

            streamhandler = logger.handlers[0]
            streamhandler.setLevel(logging.WARNING)

            formatter = streamhandler.formatter

            filehandler = logging.FileHandler(options.outfile, 'w')
            filehandler.setLevel(logging.INFO)
            filehandler.setFormatter(formatter)

            logger.addHandler(filehandler)

        filename = args[0]

        if options.quiet:
            progressfunc = None
        else:
            progressfunc = gdal.TermProgress

        if options.hist:
            histreq = HistogramRequest()
            if options.histreq:
                histreq.hmin, histreq.hmax, histreq.nbuckets = options.histreq
            if options.include_out_of_range:
                histreq.include_out_of_range = options.include_out_of_range
        else:
            histreq = None

        ds = gdal.Open(filename)
        if not ds:
            raise RuntimeError('unable to open "%s"' % filename)

        if options.band is not None:
            if options.band > ds.RasterCount:
                raise ValueError('band %d requested, but only bands 1 to %d '
                                 'are available.' % (options.band,
                                                     ds.RasterCount))
            bands = [options.band]
        else:
            bands = range(1, ds.RasterCount + 1)

        if options.srcwin:
            ds = copy_dataset_subwin(ds, options.srcwin)

        # core
        computestats(ds, bands, options.stats, histreq, options.approxok,
                     options.minmax_only, progressfunc)

        ds = None

    except Exception as e:
        logging.error(str(e))   # , exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
