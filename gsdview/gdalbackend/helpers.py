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
from PyQt4 import QtGui

from gsdview.gdalbackend import modelitems
from gsdview.gdalbackend import gdalsupport


class GdalHelper(object):
    '''Basee helper class for running external GDAL tools.

    Helper classes provide a common set of functionality for running
    GDAL tools in separate processes.
    Task performed are:

        * tool setup
        * temporay files and diractories creation
        * temporay files and diractories cleanup
        * finalization actions

    '''

    _PROGRESS_RANGE = (0, 100)

    def __init__(self, app, tool):
        super(GdalHelper, self).__init__()
        self.app = app
        self.tool = tool
        self.progressdialog = None
        self._tmpdir = None

    def setup_progress_dialog(self, title=''):
        dialog = QtGui.QProgressDialog(self.app)
        dialog.setModal(True)
        if title:
            dialog.setLabelText(title)
        dialog.hide()

        self.progressdialog = dialog

        return dialog

    @property
    def controller(self):
        return self.app.controller

    @property
    def logger(self):
        return self.app.logger

    @property
    def gdalbackend(self):
        return self.app.pluginmanager.plugins['gdalbackend']

    @staticmethod
    def ovrfiles(dirname):
        files = []
        for pattern in ('*.ovr', '*.aux'):
            files.extend(glob.glob(os.path.join(dirname, pattern)))
        return files

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

    def setProgressRange(self, minimum, maximum):
        self.app.progressbar.setRange(minimum, maximum)
        if self.progressdialog:
            self.progressdialog.setRange(minimum, maximum)

    def _reset_progress(self):
        self.setProgressRange(0, 100)
        if self.progressdialog:
            self.progressdialog.hide()

    def reset(self):
        self._reset_progress()

    def _connect_signals(self):
        self.controller.finished.connect(self.finalize)

        if self.progressdialog:
            self.progressdialog.canceled.connect(self.controller.stop_tool)
            self.app.progressbar.valueChanged.connect(
                                                self.progressdialog.setValue)

    def _disconnect_signals(self):
        # @TODO: catch exceptions
        self.controller.finished.disconnect(self.finalize)
        if self.progressdialog:
            self.app.progressbar.valueChanged.disconnect(
                                                self.progressdialog.setValue)
            self.progressdialog.canceled.disconnect(self.controller.stop_tool)

    def do_start(self, *args, **kwargs):
        raise NotImplementedError(self.__class__.__name__ + '.do_start')

    def start(self, *args, **kwargs):
        if self.controller.isbusy:
            self.logger.warning('unable to perform overview computation: '
                                'the subprocess controller is currently '
                                'busy.')
            return
        else:
            self.logger.debug('run the "%s" subprocess.' %
                                    os.path.basename(self.tool.executable))

        # @TODO: check: this instruuctin in this position don' seems to work
        #        (the progressbar hangs)
        #self.setProgressRange(*self._PROGRESS_RANGE)
        #if self.progressdialog:
        #    #self.progressdialog.reset()
        #    self.progressdialog.show()

        # @TODO: connect signals after the process succefully started (??)
        self._connect_signals()

        try:
            startfailure = self.do_start(*args, **kwargs)
        except Exception, e:
            #self.logger.error(str(e), exc_info=True)
            self.logger.debug(str(e), exc_info=True)
            startfailure = True

        if startfailure:
            self._disconnect_signals()
        else:
            self.setProgressRange(*self._PROGRESS_RANGE)
            if self.progressdialog:
                #self.progressdialog.reset()
                self.progressdialog.show()

    def do_finalize(self):
        pass

    def do_finalize_on_error(self):
        pass

    #@QtCore.pyqtSlot()
    #@QtCore.pyqtSlot(int)
    def finalize(self, returncode=0):
        try:
            self._disconnect_signals()

            # only call do_finalize if processing finished successfully
            if returncode == 0 and not self.controller.userstop:
                self.do_finalize()
            else:
                self.do_finalize_on_error()
        finally:
            self.cleanup()
            self._reset_progress()


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

              Maybe some suggestion can be asked on the GDAL
              mailing-list.

              An alternative solution, the one currently implemented,
              is to force recomputation of all overview levels (exixting
              ones and newly selected) and then replace the ol overview
              file.

              This solution is not efficient since it doesn't re-use
              existing overviews but ensure no data loss in case the
              operation is stopped by the user.

    '''

    def __init__(self, app, tool):
        super(AddoHelper, self).__init__(app, tool)
        self._datasetitem = None
        self._band = None

    def target_levels(self, dataset):
        if self._band is not None:
            band = self._band
        else:
            band = dataset.GetRasterBand(1)

        oldlevels = []
        estep = 3
        threshold = 0.1

        if band.GetOverviewCount():
            oldlevels = gdalsupport.ovrLevels(band)
            if set(oldlevels).issuperset((2, 4)):
                estep = 2
                threshold = 1.1

        # @NOTE: use dataset for levels computation because the
        #        IMAGE_STRUCTURE metadata are not propagated from
        #        CachedDatasetItem to raster bands
        levels = gdalsupport.ovrComputeLevels(dataset, estep=estep,
                                              threshold=threshold)

        # @NOTE: the GDAL band info is configured to force recomputation of
        #        all levels checked
        if levels:
            levels.extend(oldlevels)
            levels.sort()

        return levels

    def do_start(self, item):
        #levels = gdalsupport.ovrComputeLevels(item)

        # @NOTE: use dataset for levels computation because the
        #        IMAGE_STRUCTURE metadata are not propagated from
        #        CachedDatasetItem to raster bands
        if not isinstance(item, modelitems.DatasetItem):
            # NOTE: a reguest of opening an overview is converted into a
            #       request for opening the corresponding raster band
            while isinstance(item, modelitems.OverviewItem):
                item = item.parent()

            self._band = item
            dataset = item.parent()
        else:
            dataset = item

        assert isinstance(dataset, modelitems.CachedDatasetItem), str(dataset)

        levels = self.target_levels(dataset)

        # @NOTE: overviews are computed for all bands so I do this at
        #        application level, before a specific band is choosen.
        #        Maybe ths is not the best policy and overviews should be
        #        computed only when needed instead
        if levels:
            self.logger.debug('requested levels: %s' % levels)

            # Run an external process for overviews computation
            self.app.statusBar().showMessage('Quick look image generation ...')

            self._tmpdir = self.setup_tmpdir(dataset)
            vrtfilename = os.path.basename(dataset.vrtfilename)
            vrtfilename = os.path.join(self._tmpdir, vrtfilename)
            self._datasetitem = dataset

            # use averaging in magphase space for complex raster bands
            if gdalsupport.has_complex_bands(dataset):
                self.tool.set_resampling_method('average_magphase')
            else:
                self.tool.set_resampling_method('average')

            args = [os.path.basename(vrtfilename)]
            args.extend(map(str, levels))
            self.tool.cwd = os.path.dirname(vrtfilename)
            self.controller.run_tool(self.tool, *args)
        else:
            return True

    def do_finalize(self):
        # @TODO: check if opening the dataset in update mode
        #        (gdal.GA_Update) is a better solution

        dataset = self._datasetitem
        if not dataset:
            self.logger.debug('unable to retrieve dataset for finalization')
            return

        # move ovr files in the cache dir
        dirname = os.path.dirname(dataset.vrtfilename)
        ovrfiles = self.ovrfiles(self._tmpdir)
        for ovrfile in ovrfiles:
            dst = os.path.join(dirname, os.path.basename(ovrfile))
            if os.path.exists(dst):
                os.remove(dst)
            shutil.move(ovrfile, dirname)

        dataset.reopen()
        for row in range(dataset.rowCount()):
            item = dataset.child(row)
            self.app.treeview.expand(item.index())

    def reset(self):
        super(AddoHelper, self).reset()
        self._datasetitem = None
        self._band = None


class StatsHelper(GdalHelper):
    '''Helper class for statistics pre-computation on live raster bands.'''

    _PROGRESS_RANGE = (0, 0)

    # @TODO: test error control and user stop handling

    def __init__(self, app, tool):
        super(StatsHelper, self).__init__(app, tool)
        self._datasetitem = None
        self._banditem = None

    def do_start(self, item):
        if not isinstance(item, modelitems.BandItem):
            raise ValueError('invalid band item: %s' % item)

        # NOTE: a reguest of opening an overview is converted into a request
        #       for opening the corresponding raster band
        while isinstance(item, modelitems.OverviewItem):
            item = item.parent()

        dataset = item.parent()

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

    def do_finalize(self):
        # @TODO: check if opening the dataset in update mode
        #        (gdal.GA_Update) is a better solution
        dataset = self._datasetitem
        if not dataset:
            self.logger.debug('unable to retrieve dataset for finalization')
            return

        # set computed statisstic values
        bandno = self._banditem.GetBand()
        tmpvrt = os.path.join(self._tmpdir,
                              os.path.basename(dataset.vrtfilename))
        ds = gdal.Open(tmpvrt)
        if not ds:
            self.logger.warning('unable to open temporary virtual file for '
                                'getting statistics.')
            return

        vrtband = ds.GetRasterBand(bandno)
        if not vrtband:
            self.logger.warning('unable to open raster band n. %d.' % bandno)
            return

        self.copy_data(vrtband)
        self.apply()

    def reset(self):
        super(StatsHelper, self).reset()
        self._banditem = None
        self._datasetitem = None

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

    _PROGRESS_DIALOD_MSG = 'Statistics computation.'

    def __init__(self, app, tool):
        super(StatsDialogHelper, self).__init__(app, tool)
        self.dialog = None
        if self._PROGRESS_DIALOD_MSG:
            self.setup_progress_dialog(app.tr(self._PROGRESS_DIALOD_MSG))

    def start(self, item, dialog=None):
        if dialog:
            self.dialog = dialog

        if not self.dialog:
            raise ValueError('"dialog" attribute not set')

        super(StatsDialogHelper, self).start(item)

    def reset(self):
        super(StatsDialogHelper, self).reset()
        self.dialog = None

    def apply(self):
        self.dialog.updateStatistics()


class HistDialogHelper(StatsDialogHelper):
    '''Helper class for histogram computation on live raster bands.'''

    _PROGRESS_RANGE = (0, 100)
    _PROGRESS_DIALOD_MSG = 'Histogram computation.'

    def copy_data(self, vrtband):
        hmin, hmax, nbucketsm, hist = vrtband.GetDefaultHistogram()
        self._banditem.SetDefaultHistogram(hmin, hmax, hist)

    def apply(self):
        hist = self._banditem.GetDefaultHistogram()
        #self.dialog.updateHistogram()
        self.dialog.setHistogram(*hist)


class AddoDialogHelper(AddoHelper):
    '''Helper class for overviews computation.

    .. seealso:: :class:`AddoHelper`

    '''

    _PROGRESS_DIALOD_MSG = 'Overviews computation.'

    def __init__(self, app, tool):
        super(AddoDialogHelper, self).__init__(app, tool)
        self.dialog = None
        self.setup_progress_dialog(app.tr(self._PROGRESS_DIALOD_MSG))

    def target_levels(self, dataset):
        return self.dialog.overviewWidget.levels()

    def start(self, item, dialog=None):
        if dialog:
            self.dialog = dialog

        if not self.dialog:
            raise ValueError('"dialog" attribute not set')

        super(AddoDialogHelper, self).start(item)

    def reset(self):
        super(AddoDialogHelper, self).reset()
        self.dialog = None

    def do_finalize(self):
        super(AddoDialogHelper, self).do_finalize()
        self.dialog.updateOverviewInfo()
