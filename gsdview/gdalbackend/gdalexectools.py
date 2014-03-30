# -*- coding: utf-8 -*-

### Copyright (C) 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>

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


'''Custom exectools components for GDAL.'''


from __future__ import print_function

import re
import logging

import exectools
from exectools.qt4 import Qt4OutputHandler

from osgeo import gdal

from gsdview.five import string_types


class BaseGdalToolDescriptor(exectools.ToolDescriptor):
    '''Base class for GDAL tool descriprors.'''

    def gdal_config_options(self, cmd=''):
        extra_args = []

        if not 'GDAL_CACHEMAX' in cmd:
            value = gdal.GetCacheMax()
            extra_args.extend(('--config', 'GDAL_CACHEMAX', str(value)))

        for key in ('CPL_DEBUG', 'GDAL_SKIP', 'GDAL_DATA',
                    'GDAL_DRIVER_PATH', 'OGR_DRIVER_PATH'):
            if not key in cmd:
                value = gdal.GetConfigOption(key, None)
                if value:
                    extra_args.extend(('--config', key, '"%s"' % value))

        return extra_args

    def cmdline(self, *args, **kwargs):
        parts = super(BaseGdalToolDescriptor, self).cmdline(*args, **kwargs)

        extra_args = self.gdal_config_options(parts)
        if extra_args:
            if (not self.executable or
                    isinstance(self.executable, string_types)):
                parts = [parts[0]] + extra_args + parts[1:]
            else:
                executable = list(self.executable)
                parts = executable + extra_args + parts[len(executable):]

        return parts


class GdalAddOverviewDescriptor(BaseGdalToolDescriptor):
    '''Tool descriptor for the gdaladdo utility program.'''

    #: resampling methods
    RESAMPLING_METHODS = [
        'nearest',
        'average',
        'gauss',
        'cubic',
        'average_mp',
        'average_magphase',
        'mode',
    ]

    #: TIFF compression methods
    TIFF_COMPRESSION_METHODS = (
        'JPEG',
        'LZW',
        'PACKBITS',
        'DEFLATE',
    )

    #: TIFF interleaving methods
    TIFF_INTERLEAVING_METHODS = ('PIXEL', 'BAND')

    #: Allowed options for BigTIFF flag
    TIFF_USE_BIGTIFF_MODE = ('IF_NEEDED', 'IF_SAFER', 'YES', 'NO')

    def __init__(self, cwd=None, env=None,
                 stdout_handler=None, stderr_handler=None):
        '''Initialization:

        :param cwd:
            program working directory
        :param env:
            environment dictionary
        :param envmerge:
            if set to True (default) it is the :attr:`env` dictionaty is
            used to update the system environment
        :param stdout_handler:
            *OutputHandler* for the stdout of the tool
        :param stderr_handler:
            *OutputHandler* for the stderr of the tool

        .. seealso:: :class:`exectools.BaseOutputHandler`

        '''

        super(GdalAddOverviewDescriptor, self).__init__(
            'gdaladdo', [], cwd, env, stdout_handler, stderr_handler)

        #: ensure that gdaladdo works in readonly mode
        self.readonly = False

        self._resampling_method = 'average'

        #: use Erdas Imagine format (.aux) as overview format.
        #: If None use GDAL defaults.
        self.use_rrd = None

        #: photometric interpretation: RGB, YCBCR, etc. (only for external
        #: overviews in GeoTIFF format).
        #: If None use GDAL defaults.
        self.photometric_interpretation = None

        self._compression_method = None
        self._interleaving_method = None
        self._use_bigtiff_mode = None

    def resampling_method(self):
        '''Resampling method for overviews computation.'''

        return self._resampling_method

    def set_resampling_method(self, method):
        '''Set the resampling method for overviews computation.

        If set to None use GDAL defaults.
        Available resampling methods: %s.

        ''' % ', '.join(GdalAddOverviewDescriptor.RESAMPLING_METHODS)

        if method is not None and method not in self.RESAMPLING_METHODS:
            raise ValueError(
                'invalid resampling method: "%s". '
                'Available methods are: %s' % (
                    method, ', '.join(self.RESAMPLING_METHODS)))
        self._resampling_method = method

    def compression_method(self):
        '''TIFF compression method.

        This attribute is only used if external overviews are
        stored in GeoTIFF format.

        '''

        return self._compression_method

    def set_compression_method(self, method):
        '''Set the TIFF compression method.

        This attribute is only used if external overviews are
        stored in GeoTIFF format.

        If set to None use GDAL defaults.
        Available compression methods: %s.

        ''' % ', '.join(GdalAddOverviewDescriptor.TIFF_COMPRESSION_METHODS)

        self._compression_method = method

    def interleaving_method(self):
        '''Ovrviews interleaving method (%s).

        This attribute is only used if external overviews are
        stored in GeoTIFF format.

        ''' % ' or '.join(GdalAddOverviewDescriptor.TIFF_INTERLEAVING_METHODS)

        return self._interleaving_method

    def set_interleaving_method(self, method):
        '''Set the ovrview interleaving method.

        This attribute is only used if external overviews are
        stored in GeoTIFF format.

        If set to None use GDAL defaults.
        Possible interleaving methods are: %s.

        ''' % ' or '.join(GdalAddOverviewDescriptor.TIFF_INTERLEAVING_METHODS)

        self._interleaving_method = method

    def use_bigtiff_mode(self):
        '''Mode of using BigTIFF in overviews (%s).

        This attribute is only used if external overviews are
        stored in GeoTIFF format.

        ''' % ' or '.join(GdalAddOverviewDescriptor.TIFF_USE_BIGTIFF_MODE)

        return self._use_bigtiff_mode

    def set_use_bigtiff_mode(self, mode):
        '''Set the mode of using BigTIFF in overviews.

        This attribute is only used if external overviews are
        stored in GeoTIFF format.

        If set to None use GDAL defaults.
        Possible interleaving methods are: %s.

        ''' % ' or '.join(GdalAddOverviewDescriptor.TIFF_USE_BIGTIFF_MODE)

        self._use_bigtiff_mode = mode

    def gdal_config_options(self, cmd=''):
        extra_args = super(GdalAddOverviewDescriptor,
                           self).gdal_config_options(cmd)

        if self.use_rrd is not None and 'USE_RRD' not in cmd:
            if self.use_rrd:
                value = 'YES'
            else:
                value = 'NO'
            extra_args.extend(('--config', 'USE_RRD', value))

        if (self.photometric_interpretation is not None and
                'PHOTOMETRIC_OVERVIEW' not in cmd):

            extra_args.extend(('--config', 'PHOTOMETRIC_OVERVIEW',
                               self.photometric_interpretation))

        if (self._compression_method is not None and
                'COMPRESS_OVERVIEW' not in cmd):

            extra_args.extend(('--config', 'COMPRESS_OVERVIEW',
                               self._compression_method))

        if (self._interleaving_method is not None and
                'INTERLEAVE_OVERVIEW' not in cmd):

            extra_args.extend(('--config', 'INTERLEAVE_OVERVIEW',
                               self._interleaving_method))

        if (self._use_bigtiff_mode is not None and
                'BIGTIFF_OVERVIEW' not in cmd):

            extra_args.extend(('--config', 'BIGTIFF_OVERVIEW',
                               self._use_bigtiff_mode))

        return extra_args

    def cmdline(self, *args, **kwargs):
        args = list(args)
        if self._resampling_method is not None and '-r' not in args:
            args = ['-r', self._resampling_method] + args
        if self.readonly and '-ro' not in args:
            args.append('-ro')

        return super(GdalAddOverviewDescriptor, self).cmdline(*args, **kwargs)


# @COMPATIBILITY: GDAL >= 1.7.0
if gdal.VersionInfo() < '1700':
    GdalAddOverviewDescriptor.RESAMPLING_METHODS.remove('cubic')


class GdalInfoDescriptor(BaseGdalToolDescriptor):
    '''Tool descriptor for the gdalinfo utility program.'''

    def __init__(self, cwd=None, env=None,
                 stdout_handler=None, stderr_handler=None):
        '''
        :param cwd:
            program working directory
        :param env:
            environment dictionary
        :param envmerge:
            if set to True (default) it is the :attr:`env` dictionaty is
            used to update the system environment
        :param stdout_handler:
            *OutputHandler* for the stdout of the tool
        :param stderr_handler:
            *OutputHandler* for the stderr of the tool

        .. seealso:: :class:`exectools.BaseOutputHandler`

        '''

        super(GdalInfoDescriptor, self).__init__('gdalinfo', [], cwd, env,
                                                 stdout_handler,
                                                 stderr_handler)

        #: force computation of the actual min/max values for each band in the
        #: dataset.
        self.mm = False

        #: read and display image statistics. Force computation if no
        #: statistics are stored in an image.
        self.stats = False

        #: report histogram information for all bands.
        self.hist = False

        #: suppress ground control points list printing. It may be useful for
        #: datasets with huge amount of GCPs, such as L1B AVHRR or HDF4 MODIS
        #: which contain thousands of the ones.
        self.nogcp = False

        #: suppress metadata printing. Some datasets may contain a lot of
        #: metadata strings.
        self.nomd = False

        #: suppress raster attribute table printing.
        self.norat = False

        #: suppress printing of color table.
        self.noct = False

        #: force computation of the checksum for each band in the dataset.
        self.checksum = False

        #: report metadata for the specified domain.
        self.mdd = None

    def cmdline(self, *args, **kwargs):
        extra_args = []
        for name in ('mm', 'stats', 'hist', 'nogcp', 'nomd', 'norat',
                     'noct', 'checksum',):
            flag = '-%s' % name
            if getattr(self, name) and flag not in args:
                extra_args.append(flag)

        if self.mdd is not None and '-mdd' not in args:
            extra_args.extend(('-mdd', self.mdd))

        args = extra_args + list(args)

        return super(GdalInfoDescriptor, self).cmdline(*args, **kwargs)


class GdalOutputHandler(Qt4OutputHandler):
    '''Handler for the GDAL simple progress report to terminal.

    This progress reporter prints simple progress report to the
    terminal window.
    The progress report generally looks something like this:

      "0...10...20...30...40...50...60...70...80...90...100 - done."

    Every 2.5% of progress another number or period is emitted.

    .. seealso:: :class:`exectools.BaseOutputHandler`,
                 :class:`exectools.qt4.Qt4OutputHandler`

    '''

    def __init__(self, logger=None, statusbar=None, progressbar=None,
                 blinker=None, **kwargs):
        super(GdalOutputHandler, self).__init__(logger, statusbar, progressbar,
                                                blinker, **kwargs)
        #pattern = ('(?P<percentage>\d{1,3})|(?P<pulse>\.)|'
        #           '((?P<text> - done\.?)$)')
        pattern = ('(?P<percentage>\d{1,3})|(?P<pulse>\.)|'
                   '( - (?P<text>done\.?)\n)')
        self._progress_pattern = re.compile(pattern)
        self._percentage = 0.   # @TODO: remove.  Set the progressbar maximum
                                #        to 1000 instead.

    def handle_progress(self, data):
        '''Handle progress data.

        :param data:
            a list containing an item for each named group in the
            "progress" regular expression: (pulse, percentage, text)
            for the default implementation.
            Each item can be None.

        '''

        pulse = data.get('pulse')
        percentage = data.get('percentage')
        #~ text = data.get('text')

        if pulse and percentage is None:
            self._percentage = min(100, self._percentage + 2.5)
            data['percentage'] = self._percentage
        if percentage is not None:
            if percentage < self._percentage:
                logging.debug('new percentage (%d) is lower than previous '
                              'one (%f)' % (percentage, self._percentage))

            self._percentage = percentage
        #~ if text and not pulse and percentage is None:
            #~ # reset percentage
            #~ self._percentage = 0.

        super(GdalOutputHandler, self).handle_progress(data)

    def reset(self):
        super(GdalOutputHandler, self).reset()
        self._percentage = 0.


if __name__ == '__main__':

    def test_GdalOutputHandler_re():
        s = '0...10...20...30...40...50...60...70...80...90...100 - done.\n'

        h = exectools.BaseOutputHandler(exectools.OFStream())
        h._progress_pattern = GdalOutputHandler()._progress_pattern
        h.feed(s)
        h.close()
        print('done.')

    def test_GdalOutputHandler1():
        s = '0...10...20...30...40...50...60...70...80...90...100 - done.\n'

        class C(GdalOutputHandler):
            def __init__(self):
                exectools.BaseOutputHandler.__init__(self,
                                                     exectools.OFStream())

            def feed(self, data):
                return exectools.BaseOutputHandler.feed(self, data)

            def close(self):
                return exectools.BaseOutputHandler.close(self)

            def reset(self):
                return exectools.BaseOutputHandler.reset(self)

            def handle_progress(self, data):
                return exectools.BaseOutputHandler.handle_progress(self, data)

        h = C()
        h.feed(s)
        h.close()
        print('done.')

    def test_GdalOutputHandler2():
        s = '0...10...20...30...40...50...60...70...80...90...100 - done.\n'

        h = exectools.BaseOutputHandler(exectools.OFStream())
        h._progress_pattern = GdalOutputHandler()._progress_pattern
        for c in s:
            h.feed(c)
        h.close()

    #~ test_GdalOutputHandler_re()
    #~ test_GdalOutputHandler1()
    test_GdalOutputHandler2()
