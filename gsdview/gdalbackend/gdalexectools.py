# -*- coding: utf-8 -*-

### Copyright (C) 2008-2010 Antonio Valentino <a_valentino@users.sf.net>

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

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import re
import logging

import exectools
from exectools.qt4 import Qt4OutputHandler

from PyQt4 import QtGui
from osgeo import gdal


class BaseGdalToolDescriptor(exectools.ToolDescriptor):

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
                    extra_args.extend(('--config', key, value))

        return extra_args

    def cmdline(self, *args, **kwargs):
        parts = super(BaseGdalToolDescriptor, self).cmdline(*args, **kwargs)

        extra_args = self.gdal_config_options(parts)
        if extra_args:
            if not self.executable or isinstance(self.executable, basestring):
                parts = [parts[0]] + extra_args + parts[1:]
            else:
                executable = list(self.executable)
                parts = executable + extra_args + parts[len(executable):]

        return parts


class GdalAddOverviewDescriptor(BaseGdalToolDescriptor):
    '''Tool descriptor for the gdaladdo utility program.'''

    RESAMPLING_METHODS = (
        'nearest',
        'average',
        'gauss',
        'cubic',
        'average_mp',
        'average_magphase',
        'mode',
    )

    TIFF_COMPRESSION_METHODS = (
        'JPEG',
        'LZW',
        'PACKBITS',
        'DEFLATE',
    )

    TIFF_INTERLEAVING_METHODS = ('PIXEL', 'BAND')

    TIFF_USE_BIGTIFF_MODE = ('IF_NEEDED', 'IF_SAFER', 'YES', 'NO')

    def __init__(self, cwd=None, env=None,
                 stdout_handler=None, stderr_handler=None):

        super(GdalAddOverviewDescriptor, self).__init__(
                    'gdaladdo', [], cwd, env, stdout_handler, stderr_handler)

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

        def set_resampleing_method(seff, method):
            '''Set the resampling method for overviews computation.

            If set to None use GDAL defaults.
            Available resampling methods: %s.

            ''' % ', '.join(GdalAddOverviewDescriptor.RESAMPLING_METHODS)

            if method is not None and method not in self.RESAMPLING_METHODS:
                raise ValueError('invalid resampling method: "%s". '
                                 'Available methods are: %s' % (method,
                                        ', '.join(self.RESAMPLING_METHODS)))
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
        extra_args = super(GdalAddOverviewDescriptor, self).gdal_config_options(cmd)

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
        if self._resampling_method is not None and '-r' not in args:
            args = ['-r', self._resampling_method] + list(args)

        return super(GdalAddOverviewDescriptor, self).cmdline(*args, **kwargs)


class GdalInfoDescriptor(BaseGdalToolDescriptor):
    '''Tool descriptor for the gdalinfo utility program.'''

    def __init__(self, cwd=None, env=None,
                 stdout_handler=None, stderr_handler=None):

        super(GdalInfoDescriptor, self).__init__('gdalinfo', [], cwd, env,
                                                 stdout_handler, stderr_handler)

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

    This progress reporter prints simple progress report to the terminal
    window.  The progress report generally looks something like this:

      "0...10...20...30...40...50...60...70...80...90...100 - done."

    Every 2.5% of progress another number or period is emitted.

    '''

    def __init__(self, logger=None, statusbar=None, progressbar=None,
                 blinker=None):
        super(GdalOutputHandler, self).__init__(logger, statusbar,
                                                progressbar, blinker)
        #pattern = '(?P<percentage>\d{1,3})|(?P<pulse>\.)|((?P<text> - done\.?)$)'
        pattern = '(?P<percentage>\d{1,3})|(?P<pulse>\.)|( - (?P<text>done\.?)\n)'
        self._progress_pattern = re.compile(pattern)
        self.percentage = 0.    # @TODO: remove.  Set the progressbar maximum
                                #        to 1000 instead.

    def handle_progress(self, data):
        pulse = data.get('pulse')
        percentage = data.get('percentage')
        text = data.get('text')

        if pulse:
            if self.progressbar:
                self.percentage = min(100, self.percentage + 2.5)
                self._handle_percentage(self.percentage)
        if percentage is not None:
            if percentage < self.percentage:
                logging.debug('new percentage (%d) is lower than previous '
                              'one (%f)' % (percentage, self.percentage))

            self.percentage = percentage
            self._handle_percentage(percentage)
        if text and not pulse and percentage is None:
            self.percentage = 0.
            if self.statusbar:
                self.statusbar.showMessage(text, self._statusbar_timeout)
        self._handle_pulse(pulse)
        QtGui.qApp.processEvents() # might slow too mutch

    def reset(self):
        super(GdalOutputHandler, self).reset()
        self.percentage = 0.


if __name__ == '__main__':
    def test_GdalOutputHandler_re():
        s = '0...10...20...30...40...50...60...70...80...90...100 - done.\n'

        h = exectools.BaseOutputHandler(exectools.OFStream())
        h._progress_pattern = GdalOutputHandler()._progress_pattern
        h.feed(s)
        h.close()
        print 'done.'

    def test_GdalOutputHandler1():
        s = '0...10...20...30...40...50...60...70...80...90...100 - done.\n'

        class C(GdalOutputHandler):
            def __init__(self):
                exectools.BaseOutputHandler.__init__(self, exectools.OFStream())
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
        print 'done.'

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
