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
from PyQt4 import QtCore, QtGui

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

    @property
    def gdalbackend(self):
        return self.app.pluginmanager.plugins['gdalbackend']

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
        raise NotImplementedError('GdalHelper.start(*args, **kargs)')

    def finalize(self, returncode=0):
        self.cleanup()


class AddoHelper(GdalHelper):
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
        super(AddoHelper, self).__init__(app, tool)
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


class StatsHelper(GdalHelper):
    '''Helper class for statistics pre-computation on live raster bands.'''

    _PROGRESS_RANGE = (0, 0)

    # @TODO: test error control and user stop handling

    def __init__(self, app, tool):
        super(StatsHelper, self).__init__(app, tool)
        self._datasetitem = None
        self._banditem = None

    def setProgressRange(self, minimum, maximum):
        self.app.progressbar.setRange(minimum, maximum)

    def start(self, item):
        if not isinstance(item, modelitems.BandItem):
            raise ValueError('invalid band item: %s' % item)

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
        self.setProgressRange(*self._PROGRESS_RANGE)

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

                self.copy_data(band)

                # only try to open the new view if statistics have been
                # computed successfully
                self.apply()
        finally:
            self.cleanup()
            self._banditem = None
            self._datasetitem = None
            self.setProgressRange(0, 100)

    def copy_data(self, vrtband):
        stats = gdalsupport.GetCachedStatistics(vrtband)
        if None in stats:
            self.logger.warning('unable to retrieve statistics.')
            return

        for name, value in zip(gdalsupport.GDAL_STATS_KEYS, stats):
            self._banditem.SetMetadataItem(name, str(value))

    def apply(self):
        self.gdalbackend.newImageView(self._banditem)


class StatsDialogHelper(StatsHelper):
    '''Helper class for statistics computation on live raster bands.'''

    def __init__(self, app, tool, dialog=None):
        super(StatsDialogHelper, self).__init__(app, tool)
        self._dialog = dialog

        self.progressdialog = QtGui.QProgressDialog(app)
        self.progressdialog.setModal(True)
        self.progressdialog.setLabelText(app.tr('Statistics computation.'))
        self.progressdialog.hide()

        self.progressdialog.connect(self.progressdialog,
                                    QtCore.SIGNAL('canceled()'),
                                    self.controller.stop_tool)
        self.progressdialog.connect(self.app.progressbar,
                                    QtCore.SIGNAL('valueChanged(int)'),
                                    self.progressdialog.setValue)

    def _get_dialog(self):
        return self._dialog

    def _set_dialog(self, value):
        if self.controller.isbusy:
            raise RuntimeError("can't set the dialog attribute while an "
                               "external tool is running.")
        self._dialog = value
        #self.progressdialog.setParent(value) # @TODO: check

    dialog = property(_get_dialog, _set_dialog)

    ## @COMPATIBILITY: property.setter nedds Python >= 2.6
    #@property
    #def dialog(self):
    #    return self._dialog
    #
    #@dialog.setter
    #def dialog(self, value):
    #    if self.controller.isbusy:
    #        raise RuntimeError("can't set the dialog attribute while an "
    #                           "external tool is running.")
    #    self._dialog = value
    #    self.progressdialog.setParent(value)

    def setProgressRange(self, minimum, maximum):
        super(StatsDialogHelper, self).setProgressRange(minimum, maximum)
        self.progressdialog.setRange(minimum, maximum)

    def _checkdialog(self):
        if self._dialog is None:
            raise ValueError('"dialog" attribute is None.')

    def start(self, item):
        self._checkdialog()
        if not self.controller.isbusy:
            #self.progressdialog.reset()
            self.progressdialog.show()
        super(StatsDialogHelper, self).start(item)

    def finalize(self, returncode=0):
        super(StatsDialogHelper, self).finalize(returncode)
        self.progressdialog.hide()

    def apply(self):
        self._checkdialog()
        self.dialog.updateStatistics()


class HistDialogHelper(StatsDialogHelper):
    '''Helper class for histogram computation on live raster bands.'''

    _PROGRESS_RANGE = (0, 100)

    def __init__(self, app, tool, dialog=None):
        super(StatsDialogHelper, self).__init__(app, tool)
        self.progressdialog.setLabelText(app.tr('Histogram computation.'))

    def copy_data(self, vrtband):
        hmin, hmax, nbucketsm, hist = vrtband.GetDefaultHistogram()
        self._banditem.SetDefaultHistogram(hmin, hmax, hist)

    def apply(self):
        self._checkdialog()
        hist = self._banditem.GetDefaultHistogram()
        #self.dialog.updateHistogram()
        self.dialog.setHistogram(*hist)

