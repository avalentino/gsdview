# -*- coding: utf-8 -*-

### Copyright (C) 2008-2011 Antonio Valentino <a_valentino@users.sf.net>

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


'''Exectools tool descriptors for gsdtools .'''

__author__ = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__ = '$Date$'
__revision__ = '$Revision$'


import os

import gsdtools
from gsdtools.stats import HistogramRequest

from gsdview import utils
from gsdview.gdalbackend.gdalexectools import BaseGdalToolDescriptor


def _gsdtoolcmd(name):
    path = os.path.abspath(gsdtools.__path__)
    script = os.path.join(path, name + '.py')
    for variant in ('o', 'c', ''):
        variant = script + variant
        if os.path.exists(variant):
            script = variant
            break
    else:
        return None

    cmd = utils.scriptcmd(script)
    return cmd


class StatsDescriptor(BaseGdalToolDescriptor):
    '''Descriptor for gsdstats tool.

    .. seealso:: :class:`exectools.ToolDescriptor`

    '''

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

        executable = utils.which('gsdstats')
        if executable:
            cmd = utils.scriptcmd(executable)
        else:
            cmd = _gsdtoolcmd('stats')

        super(StatsDescriptor, self).__init__(cmd, [],
                                    cwd, env, stdout_handler, stderr_handler)

        #: Disable statistics computation (default: False)
        self.nostats = None

        #: Compute statistics for a specific raster band.
        #:
        #: Default: all bands are precessed.
        self.band = None

        #: Allow approximate statistics computation.
        #:
        #: If set then statistics may be computed based on overviews or a
        #: subset of all tiles (default: False)
        self.approxok = None

        #: Only print minimum and maximum on the same line
        self.minmaxonly = None

        #: Specify source window in image coordinates.
        #:
        #: Default: the entire image is processed.
        self.srcwin = None

        #: Write results to FILE.
        self.outfile = None

        #: Suppress progress messages.
        self.quiet = False

        self._histreq = HistogramRequest()
        self._histreq.computehistogram = False

    @property
    def hist(self):
        '''Histogram request.

        Histogram request objects allow to specifie parameters for
        historams computarion or disable histogram computation at all.

        .. seealso:: :class:`gsdtools.stats.HistogramRequest`.

        If set to a non null value the histogram computation is enabled::

          desctiptot.hist = True

        the above code is equivalent to::

          desctiptot.hist.computehistogram = True

        Use histogram request object attributes to speficy custom
        parameters for historam comutation::

          desctiptot.hist.hmin = - 0.5
          desctiptot.hist.hmax = 3000.5
          desctiptot.hist.nbuckets = 101
          desctiptot.hist.include_out_of_range = True

        .. note: the *include_out_of_range* parameter is only taken
                 into account if all *hmin*, *hmax* and *nbuckets* are
                 specified.

        To disable histocram computation set it :attr:`hist` to
        *False*::

            desctiptot.hist = False

        Setting :attr:`hist` to *None* disable histogram computation
        and perform a fiull reset of the histogram requast object::

            desctiptot.hist = None

        '''

        return self._histreq

    @hist.setter
    def hist(self, value):
        self._histreq.computehistogram = bool(value)
        if value is None:
            self._histreq.hmin = None
            self._histreq.hmax = None
            self._histreq.nbuckets = None
            self._histreq.include_out_of_range = None

        if isinstance(value, HistogramRequest):
            self._histreq = value

    def cmdline(self, *args, **kwargs):
        args = list(args)
        if self.nostats is not None and '--no-stats' not in args:
            args = ['--no-stats'] + args
        if self.hist.computehistogram and '--hist' not in args:
            args = ['--hist'] + args
        if (self.band is not None and
                            not set(('-b', '--band')).intersection(args)):
            args = ['--band', str(self.band)] + args
        if (self.approxok is not None and
                            not set(('-a', '--approxok')).intersection(args)):
            args = ['--approxok'] + args
        if self.hist.minmaxonly is not None and '--minmax-only' not in args:
            args = ['--minmax-only'] + args
        if self.hist.iscustom() and '--histreq' not in args:
            values = [str(item) for item in self.hist.values()]
            args = ['--histreq'] + values + args
        if (self.hist.include_out_of_range is not None and
                not set(('-i', '--include_out_of_range')).intersection(args)):
            args = ['--include_out_of_range'] + args
        if self.srcwin and '--srcwin' not in args:
            values = [str(item) for item in self.srcwin]
            args = ['--srcwin'] + values + args
        if (self.outfile is not None and
                            not set(('-o', '--outfile')).intersection(args)):
            args = ['--outfile', self.outfile] + args
        if (self.quiet is not None and
                            not set(('-q', '--quiet')).intersection(args)):
            args = ['--quiet'] + args

        return super(StatsDescriptor, self).cmdline(*args, **kwargs)


class Ras2vecDescriptor(BaseGdalToolDescriptor):
    '''Descriptor for ras2vec tool.

    .. seealso:: :class:`exectools.ToolDescriptor`

    '''

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
            +OutputHandler* for the stderr of the tool

        .. seealso:: :class:`exectools.BaseOutputHandler`

        '''

        executable = utils.which('ras2vec')
        if executable:
            cmd = utils.scriptcmd(executable)
        else:
            cmd = _gsdtoolcmd('ras2vec')

        super(Ras2vecDescriptor, self).__init__(cmd, [],
                                    cwd, env, stdout_handler, stderr_handler)

        #: Generate an additional layer for GCPs.
        self.gcps = None

        #: Generate markers for bounding box corners.
        self.corners = None

        #: Store absolute path in bounding box feature description.
        self.abspath = None

    def cmdline(self, *args, **kwargs):
        args = list(args)
        if (self.gcps is not None and
                            not set(('-g', '--gcps')).intersection(args)):
            args = ['--gcps'] + args
        if (self.corners is not None and
                            not set(('-c', '--corners')).intersection(args)):
            args = ['--corners'] + args
        if (self.abspath is not None and
                            not set(('-a', '--abspath')).intersection(args)):
            args = ['--abspath'] + args

        return super(Ras2vecDescriptor, self).cmdline(*args, **kwargs)
