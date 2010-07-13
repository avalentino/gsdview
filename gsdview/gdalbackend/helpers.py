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


'''Core GDAL backend functions and classes.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import os
import glob
import shutil
import tempfile

from osgeo import gdal
from PyQt4 import QtCore

from gsdview.gdalbackend import modelitems
from gsdview.gdalbackend import gdalsupport


class GdalHelper(object):
    '''Basee helper class for running external GDAL tools.

    Helper classes provide a common set of functionality for running
    GDAL tools in separate processes.
    Task performed are:

        * tool setup,
        * temporay files and diractories creation,
        * temporay files and diractories cleanup,
        * finalization actions

    '''

    def __init__(self, app, tool):
        super(GdalHelper, self).__init__()
        self.app = app
        self.tool = tool
        self._tmpdir = None
        #self._datasetitem = None

        QtCore.QObject.connect(self.controller, QtCore.SIGNAL('finished(int)'),
                               self.finalize)

    @property
    def controller(self):
        return self.app.controller

    @property
    def logger(self):
        return self.app.logger

    def setup_tmpdir(self, dataset):
        '''Create a temporary diran copy the virtual file into it.'''

        vrtdirname = os.path.dirname(dataset.vrtfilename)
        try:
            tmpdir = os.path.join(vrtdirname, 'tmp')
            os.mkdir(tmpdir)
        except OSError:
            tmpdir = tempfile.mkdtemp()
        shutil.copy(dataset.vrtfilename, tmpdir)

        return tmpdir

    def cleanup(self):
        if self._tmpdir:
            shutil.rmtree(self._tmpdir)

            if os.path.exists(self._tmpdir):
                self.logger.warning('unable ro remove remporary dir: '
                                    '"%s"' % self._tmpdir)
            self._tmpdir = None

    def start(self, *args, **kargs):
        pass

    def finalize(self, returncode=0):
        self.cleanup()


class GdalAddoHelper(GdalHelper):
    '''Helper class for gdaladdo execution on live datasets.

    In GSDView an external process running the gdaladdo is used to add
    oveviews to (virtual) dataset that are already open in GSDView
    itself.

    Unfortunately, as far as I know, there is no way to safely handle
    two dataset objects (pointing at the same vrt file) in two different
    processes.

    This helper class provides functions to perform overview
    computation on a private environment and then move the ovr/aux
    file back to the main cache folder of the dataset.
    After that the dataset is re-opened an all changes are safely
    reflected to the GUI.

    In case the overview computation is stopped before completion then
    the private gdaladdo environment is simply cleaned and no side
    effect arises.

    .. note:: if one wants to add overviews to a vrt dataset that
              already has overviews (i.e. the ovr/aux file already
              exists) then the ovr/aux file should be copyed in the
              private gdaladdo environment before starting computation.

              In this way the pre-existing overview are preserved but
              the copy operation could be heavy weight.

              Maybe some suggestion can be asked on the GDAl
              mailing-list.

    '''

    def __init__(self, app, tool):
        super(GdalAddoHelper, self).__init__(app, tool)
        self._datasetitem = None

    def _ovrfiles(self, dirname):
        ovrfiles = []
        for pattern in ('*.ovr', '*.aux'):
            ovrfiles.extend(glob.glob(os.path.join(dirname, pattern)))
        return ovrfiles

    def start(self, item):
        #missingOverviewLevels = gdalsupport.ovrComputeLevels(item)

        if not isinstance(item, modelitems.DatasetItem):
            dataset = item.parent()
        else:
            dataset = item
        assert isinstance(dataset, modelitems.DatasetItem)
        assert isinstance(dataset, modelitems.CachedDatasetItem)

        # @NOTE: use dataset for levels computation because the
        #        IMAGE_STRUCTURE metadata are not propagated from
        #        CachedDatasetItem to raster bands
        missingOverviewLevels = gdalsupport.ovrComputeLevels(dataset)

        # @NOTE: overviews are computed for all bands so I do this at
        #        application level, before a specific band is choosen.
        #        Maybe ths is not the best policy and overviews should be
        #        computed only when needed instead
        if missingOverviewLevels:
            self.logger.debug('missingOverviewLevels: %s' %
                                                        missingOverviewLevels)

            if self.controller.isbusy:
                self.logger.warning('unable to perform overview computation: '
                                    'the subprocess controller is currently '
                                    'busy.')
                return
            else:
                self.logger.debug('run the "%s" subprocess.' %
                                        os.path.basename(self.tool.executable))

            # Run an external process for overviews computation
            self.app.statusBar().showMessage('Quick look image generation ...')

            self._tmpdir = self.setup_tmpdir(dataset)
            vrtfilename = os.path.basename(dataset.vrtfilename)
            vrtfilename = os.path.join(self._tmpdir, vrtfilename)
            self._datasetitem = dataset

            args = [os.path.basename(vrtfilename)]
            args.extend(map(str, missingOverviewLevels))

            self.tool.cwd = os.path.dirname(vrtfilename)
            self.controller.run_tool(self.tool, *args)

    def finalize(self, returncode=0):
        # @TODO: check if opening the dataset in update mode
        #        (gdal.GA_Update) is a better solution

        dataset = self._datasetitem

        if not dataset:
            self.logger.debug('unable to retrieve dataset for finalization')
            return

        # only reload if processing finished successfully
        if returncode == 0 and not self.controller.userstop:
            # move ovr files in the cache dir
            dirname = os.path.dirname(dataset.vrtfilename)
            ovrfiles = self._ovrfiles(self._tmpdir)
            for ovrfile in ovrfiles:
                shutil.move(ovrfile, dirname)

            dataset.reopen()
            for row in range(dataset.rowCount()):
                item = dataset.child(row)
                self.app.treeview.expand(item.index())

        self.cleanup()
        self._datasetitem = None


class GdalStatsHelper(GdalHelper):
    '''Helper class for statistics pre-computation on live raster bands.'''

    def __init__(self, app, tool):
        super(GdalStatsHelper, self).__init__(app, tool)
        self._datasetitem = None
        self._banditem = None

    def start(self, item):
        if not isinstance(item, modelitems.BandItem):
            raise ValueError('invaòid band item: %s' % item)

        dataset = item.parent()

        if self.controller.isbusy:
            self.logger.warning('unable to perform overview computation: '
                                'the subprocess controller is currently '
                                'busy.')
            return
        else:
            self.logger.debug('run the "%s" subprocess.' %
                                    os.path.basename(self.tool.executable))

        # Run an external process for statistics computation
        self.app.statusBar().showMessage('Compute coarse statistics ...')

        self._tmpdir = self.setup_tmpdir(dataset)
        vrtfilename = os.path.basename(dataset.vrtfilename)
        vrtfilename = os.path.join(self._tmpdir, vrtfilename)

        self._banditem = item
        self._datasetitem = dataset

        args = [os.path.basename(vrtfilename)]
        self.tool.cwd = os.path.dirname(vrtfilename)
        self.controller.run_tool(self.tool, *args)

    def finalize(self, returncode=0):
        # @TODO: check if opening the dataset in update mode
        #        (gdal.GA_Update) is a better solution

        dataset = self._datasetitem

        if not dataset:
            self.logger.debug('unable to retrieve dataset for finalization')
            return

        try:
            # only update if processing finished successfully
            if returncode == 0 and not self.controller.userstop:
                # set computed statisstic values
                bandno = self._banditem.GetBand()
                tmpvrt = os.path.join(self._tmpdir,
                                      os.path.basename(dataset.vrtfilename))
                ds = gdal.Open(tmpvrt)
                if not ds:
                    self.logger.warning('unable to open temporary virtual '
                                        'file for getting statistics.')
                    return

                band = ds.GetRasterBand(bandno)
                if not band:
                    self.logger.warning('unable to open raster band n. %d.' %
                                                                        bandno)
                    return

                stats = gdalsupport.GetCachedStatistics(band)
                if None in stats:
                    self.logger.warning('unable to retrieve statistics.')
                    return

                names = ('STATISTICS_MINIMUM', 'STATISTICS_MAXIMUM',
                         'STATISTICS_MEAN', 'STATISTICS_STDDEV')
                for name, value in zip(names, stats):
                    self._banditem.SetMetadataItem(name, str(value))

        finally:
            self.cleanup()
            self._datasetitem = None

            backend = self.app.pluginmanager.plugins['gdalbackend']
            backend.newImageView(self._banditem)

            self._banditem = None
