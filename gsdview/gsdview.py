#!/usr/bin/env python

# -*- coding: UTF8 -*-

### Copyright (C) 2008 Antonio Valentino <a_valentino@users.sf.net>

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

'''GUI front-end for the Geospatial Data Abstracton Library (GDAL).'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import os
import sys
import logging

import numpy

try:
    from osgeo import gdal
except ImportError:
    import gdal

from PyQt4 import QtCore, QtGui

import gsdview_resources

import gsdtools
import qt4support
import gdalsupport
import gdalqt4

import exectools
from exectools.qt4tools import Qt4ToolController, Qt4DialogLoggingHandler

from gdalexectools import GdalAddOverviewDescriptor, GdalOutputHandler

from widgets import AboutDialog
from graphicsview import GraphicsView


class GSDView(QtGui.QMainWindow):
    # @TODO:
    #   * set all icon (can use the iconset of BEAM)
    #   * plugin architecture (incomplete)
    #   * cache browser, cache cleanup
    #   * open internal product
    #   * stop button
    #   * disable actions when the external tool is running
    #   * /usr/share/doc/python-qt4-doc/examples/mainwindows/recentfiles.py
    #   * stretching tool
    #   * allow to open multiple bands/datasets --> band/dataset regiter + current
    #   * make toolbars and docs controls available in the main menu

    # @TODO: move elseware
    CACHEDIR = os.path.expanduser(os.path.join('~', '.gsdview', 'cache'))
    GSDVIEWROOT = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, parent=None):
        QtGui.qApp.setWindowIcon(QtGui.QIcon(':/images/GSDView.svg'))

        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr('GSDView'))

        scene = QtGui.QGraphicsScene(self)
        self.graphicsView = GraphicsView(scene, self)
        self.graphicsView.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.setCentralWidget(self.graphicsView)

        # Progressbar
        self.progressbar = QtGui.QProgressBar(self)
        self.progressbar.setTextVisible(True)
        self.statusBar().addPermanentWidget(self.progressbar)
        self.progressbar.hide()

        # Dialogs
        self.filedialog = QtGui.QFileDialog(self)
        self.filedialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        self.filedialog.setFilters(gdalsupport.gdalFilters())
        self.filedialog.setViewMode(QtGui.QFileDialog.Detail)

        self.aboutdialog = AboutDialog(self)

        self.imageItem = None
        self.dataset = None

        # Settings
        # @TODO: fix filename
        #self.settings = QtCore.QSettings('gsdview-soft', 'gsdview', self)
        #self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #                                 QtCore.QSettings.UserScope,
        #                                 'gsdview', 'gsdview', self)
        cfgfile = os.path.join('~', '.gsdview', 'gsdview.ini')
        cfgfile = os.path.expanduser(cfgfile)
        self.settings = QtCore.QSettings(cfgfile,
                                         QtCore.QSettings.IniFormat,
                                         self)

        # Setup the log system and the external tools controller
        # @TODO: logevel could be set from command line
        self.logger = self.setupLogging()
        self.controller = self.setupController(self.logger, self.statusBar(),
                                               self.progressbar)

        # Actions
        self.setupActions()

        # File menu end toolbar
        menu = self._addMenuFromActions(self.fileActions, self.tr('&File'))
        menu.insertSeparator(self.actionExit)
        bar = self._addToolBarFromActions(self.fileActions,
                                          self.tr('File toolbar'))
        bar.insertSeparator(self.actionExit)

        # Setup plugins
        self.setupPlugins() # @TODO: pass settings

        # Help menu end toolbar
        self._addMenuFromActions(self.helpActions, self.tr('&Help'))
        self._addToolBarFromActions(self.helpActions, self.tr('Help toolbar'))

        # @NOTE: the window state setup must happen after the plugins loading
        self.loadSettings() # @TODO: pass settings
        # @TODO: force the log level set from command line
        #self.logger.setLevel(level)

        # Connect signals
        self.connect(self, QtCore.SIGNAL('openBandRequest(PyQt_PyObject)'),
                     self.openRasterBand)

        self.statusBar().showMessage('Ready')

    ### Event handlers ########################################################
    def closeEvent(self, event):
        self.controller.stop_tool()
        # @TODO: whait for finished (??)
        self.saveSettings()
        event.accept()

    def changeEvent(self, event):
        try:
            if event.oldState() == QtCore.Qt.WindowNoState:
                self.settings.beginGroup('mainwindow')
                self.settings.setValue('position', QtCore.QVariant(self.pos()))
                self.settings.setValue('size', QtCore.QVariant(self.size()))
                self.settings.endGroup()
                event.accept()
        except AttributeError:
            pass

    ### Setup helpers #########################################################
    def _setupFileActions(self):
        self.fileActions = QtGui.QActionGroup(self)

        # Open
        self.actionFileOpen = QtGui.QAction(QtGui.QIcon(':/images/open.svg'),
                                            self.tr('&Open'), self)
        #self.actionFileOpen.setObjectName('actionFileOpen') # @TODO: complete
        self.actionFileOpen.setShortcut(self.tr('Ctrl+O'))
        self.actionFileOpen.setStatusTip(self.tr('Open an existing file'))
        self.connect(self.actionFileOpen, QtCore.SIGNAL('triggered()'),
                     self.openFile)
        self.fileActions.addAction(self.actionFileOpen)

        # Close
        self.actionFileClose = QtGui.QAction(QtGui.QIcon(':/images/close.svg'),
                                             self.tr('&Close'), self)
        self.actionFileClose.setShortcut(self.tr('Ctrl+W'))
        self.actionFileClose.setStatusTip(self.tr('Close an open file'))
        self.connect(self.actionFileClose, QtCore.SIGNAL('triggered()'),
                     self.closeFile)
        self.fileActions.addAction(self.actionFileClose)

        # Exit
        self.actionExit = QtGui.QAction(QtGui.QIcon(':/images/quit.svg'),
                                        self.tr('&Exit'), self)
        self.actionExit.setShortcut(self.tr('Ctrl+X'));
        self.actionExit.setStatusTip(self.tr('Exit the program'))
        self.connect(self.actionExit, QtCore.SIGNAL('triggered()'),
                     self.close)
        self.fileActions.addAction(self.actionExit)

        return self.fileActions

    def _setupHelpActions(self):
        self.helpActions = QtGui.QActionGroup(self)

        # About
        self.actionAbout = QtGui.QAction(QtGui.QIcon(':/images/about.svg'),
                                         self.tr('&About'), self)
        self.actionAbout.setStatusTip(self.tr('Show program information'))
        self.connect(self.actionAbout, QtCore.SIGNAL('triggered()'),
                     self.about)
        self.helpActions.addAction(self.actionAbout)

        # AboutQt
        self.actionAboutQt = QtGui.QAction(QtGui.QIcon(':/images/qt-logo.png'),
                                           self.tr('About &Qt'), self)
        self.actionAboutQt.setStatusTip(self.tr('Show information about Qt'))
        self.connect(self.actionAboutQt, QtCore.SIGNAL('triggered()'),
                     self.aboutQt)
        self.helpActions.addAction(self.actionAboutQt)

        return self.helpActions

    def setupActions(self):
        self.fileActions = self._setupFileActions()
        self.helpActions = self._setupHelpActions()

    def _addMenuFromActions(self, actions, name):
        menu = qt4support.actionGroupToMenu(actions, name, self)
        self.menuBar().addMenu(menu)
        return menu

    def _addToolBarFromActions(self, actions, name):
        toolbar = qt4support.actionGroupToToolbar(actions, name)
        self.addToolBar(toolbar)
        return toolbar

    def setupPlugins(self):
        # @TODO: move to the PluginManager
        plugins = {}
        # @TODO: set from settings
        pluginsDir = os.path.join(os.path.dirname(__file__), 'plugins')
        sys.path.insert(0, pluginsDir)
        sys.path.insert(0, os.path.dirname(__file__)) # @TODO: fix
        for dirpath, dirnames, filenames in os.walk(pluginsDir):
            for name in dirnames:
                if name.startswith(('.', '_')) or (name in sys.modules):
                    continue
                try:
                    module = __import__(name)
                    module.init(self)
                    plugins[name] = module
                    self.logger.debug('"%s" plugin loaded.' % name)
                except ImportError, e:
                    self.logger.debug('"%s" module not loaded: %s' % (name, e))
            del dirnames[:]

            for name in filenames:
                name, ext = os.path.splitext(name)
                #if ext.lower() not in ('.py', '.pyc', '.pyo', '.pyd', '.dll', '.so', '.egg', '.zip'):
                    #continue
                if name.startswith(('.', '_')) or (name in sys.modules):
                    continue
                try:
                    module = __import__(name)
                    module.init(self)
                    plugins[name] = module
                    self.logger.debug('"%s" plugin loaded.' % name)
                except ImportError, e:
                    self.logger.debug('"%s" module not loaded: %s' % (name, e))
        return plugins

    def setupLogging(self):
        logger = logging.getLogger()    # 'gsdview' # @TODO: fix

        formatter = logging.Formatter('%(message)s')
        handler = Qt4DialogLoggingHandler(parent=self, dialog=None)
        handler.setLevel(logging.WARNING)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def setupController(self, logger, statusbar, progressbar):
        # @TODO: move to plugin (??)
        handler = GdalOutputHandler(None, statusbar, progressbar)
        tool = GdalAddOverviewDescriptor(stdout_handler=handler)
        controller = Qt4ToolController(logger, parent=self)
        controller.tool = tool
        controller.connect(controller, QtCore.SIGNAL('finished()'),
                           self.processingDone)

        return controller


    ### Settings ##############################################################
    def _restoreWindowState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('mainwindow')

        position = settings.value('position')
        if not position.isNull():
            move(position.toPoint())
        size = settings.value('size')
        if not size.isNull():
            self.resize(size.toSize())
        else:
            # default size
            self.resize(800, 600)

        try:
            winstate = settings.value('winstate',
                                      QtCore.QVariant(QtCore.Qt.WindowNoState))
            winstate, ok = winstate.toInt()
            if winstate != QtCore.Qt.WindowNoState:
                winstate = qt4support.intToWinState[winstate]
                self.setWindowState(winstate)
                #QtGui.qApp.processEvents()
        except KeyError:
            logging.debug('unable to restore the window state', exc_info=True)

        # State of toolbars ad docks
        state = settings.value('state')
        if not state.isNull():
            self.restoreState(state.toByteArray())

        settings.endGroup()

    def _restoreFileDialogState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('filedialog')

        # state
        state = settings.value('state')
        if not state.isNull():
            try:
                # QFileDialog.restoreState is new in Qt 4.3
                self.filedialog.restoreState(state.toByteArray())
            except AttributeError:
                logging.debug('unable to save the file dialog state')

        # workdir
        default = utils.default_workdir()
        workdir = settings.value('workdir', QtCore.QVariant(default)).toString()
        self.filedialog.setDirectory(workdir)

        # history
        history = settings.value('history')
        if not history.isNull():
            self.filedialog.setHistory(history.toStringList())

        # sidebar urls
        try:
            # QFileDialog.setSidebarUrls is new in Qt 4.3
            sidebarurls = settings.value('sidebarurls')
            if not sidebarurls.isNull():
                sidebarurls = sidebarurls.toStringList()
                sidebarurls = [QtCore.QUrl(item) for item in sidebarurls]
                self.filedialog.setSidebarUrls(sidebarurls)
        except AttributeError:
            logging.debug('unable to restore sidebar URLs of the file dialog')

        settings.endGroup()

    def loadSettings(self, settings=None):
        if settings is None:
            settings = self.settings

        # general
        self._restoreWindowState(settings)
        self._restoreFileDialogState(settings)

        settings.beginGroup('preferences')

        # log level
        level = settings.value('loglevel', 'INFO').toString()
        levelno = logging.getLevelName(str(level))
        if isinstance(levelno, int):
            self.logger.setLevel(levelno)
        else:
            logging.debug('invalid log level: "%s"' % level)

        settings.endGroup()

        # GDAL

        # cache
        settings.beginGroup('preferences')
        #self.cachedir = settings.value('cachelocation')
        cachesize, ok = settings.value('gdalcachesize').toInt()
        if ok:
            gdal.SetCacheMax(cachesize)
        settings.endGroup()

        # misc

    def _saveWindowState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('mainwindow')

        settings.setValue('winstate', QtCore.QVariant(self.windowState()))

        if self.windowState() == QtCore.Qt.WindowNoState:
            settings.setValue('position', QtCore.QVariant(self.pos()))
            settings.setValue('size', QtCore.QVariant(self.size()))
        settings.setValue('state', QtCore.QVariant(self.saveState()))

        settings.endGroup()

    def _saveFileDialogState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('filedialog')

        # state
        try:
            # QFileDialog.saveState is new in Qt 4.3
            state = self.filedialog.saveState()
            settings.setValue('state', QtCore.QVariant(state))
        except AttributeError:
            logging.debug('unable to save the file dialog state')

        # workdir
        # NOTE: uncomment to preserve the session value
        #workdir = self.filedialog.directory()
        #workdir = settings.setValue('workdir', QtCore.QVariant(workdir))

        # history
        settings.setValue('history',
                          QtCore.QVariant(self.filedialog.history()))

        # sidebat urls
        try:
            sidebarurls = self.filedialog.sidebarUrls()
            qsidebarurls = QtCore.QStringList()
            for item in sidebarurls:
                qsidebarurls.append(QtCore.QString(item.toString()))
            settings.setValue('sidebarurls', QtCore.QVariant(qsidebarurls))
        except AttributeError:
            logging.debug('unable to save sidebar URLs of the file dialog')
        settings.endGroup()

    # @TODO: check (unused at the moment)
    def saveSettings(self, settings=None):
        if settings is None:
            settings = self.settings

        # general
        self._saveWindowState(settings)
        self._saveFileDialogState(settings)

        settings.beginGroup('preferences')

        level = QtCore.QVariant(logging.getLevelName(self.logger.level))
        settings.setValue('loglevel', level)

        settings.setValue('cachedir', self.cachedir)
        settings.setValue('gdalcachesize', QtCore.QVariant(gdal.GetCacheMax()))

        settings.endGroup()
        # GDAL
        # cache
        # misc

    def _getCacheDir(self):
        #defaultcachedir = './cache'
        defaultcachedir = QtCore.QVariant(self.CACHEDIR)
        cachedir = self.settings.value('preferences/cachedir', defaultcachedir)
        cachedir = cachedir.toString()

        # @TODO: improve
        gsdviewroot = os.path.abspath(os.path.dirname(__file__))
        cachedir.replace('$GSDVIEWROOT', gsdviewroot)

        return os.path.expanduser(str(cachedir))

    ### File actions ##########################################################
    @qt4support.overrideCursor
    def _openFile(self, filename):
        cachedir = self._getCacheDir()
        self.dataset = gdalsupport.DatasetProxy(filename, cachedir)

        # @TODO: when the improved GraphicsView will be available more then
        #        one overview level will be needed
        band = self.dataset.GetRasterBand(1)
        ovrLevel = band.compute_ovr_level()
        missingOverviewLevels = [] # [4,8,12]
        try:
            ovrIndex = band.best_ovr_index(ovrLevel)
            levels = band.available_ovr_levels()
            distance = 1
            if numpy.abs(levels[ovrIndex] - ovrLevel) > distance:
                missingOverviewLevels.append(ovrLevel)
            else:
                ovrLevel = levels[ovrIndex]
        except gdalsupport.MissingOvrError:
            missingOverviewLevels.append(ovrLevel)

        # @NOTE: overviews are computed for all bands so I do this at
        #        application level, before a specific band is choosen.
        #        Maybe ths is not the best policy and overviews should be
        #        computed only when needed instead
        if missingOverviewLevels:
            logging.debug('missingOverviewLevels: %s' % missingOverviewLevels)
            # Run an external process for overviews computation
            self.progressbar.show()
            self.statusBar().showMessage('Quick look image generation ...')

            # @TODO: temporary close the dataset; il will be re-opened
            #        after the worker process ending to loaf changes
            #del dataset

            subProc = self.controller.subprocess
            assert subProc.state() == subProc.NotRunning
            logging.debug('Run the subprocess.')

            args = [os.path.basename(self.dataset.vrtfilename)] # @TODO: check
            args.extend(map(str, missingOverviewLevels))

            #self.subprocess.setEnvironmet(...)
            datasetCacheDir = os.path.dirname(self.dataset.vrtfilename)
            self.controller.subprocess.setWorkingDirectory(datasetCacheDir)
            self.controller.run_tool(*args)

        # @TODO: check
        self.emit(QtCore.SIGNAL('openGdalDataset(PyQt_PyObject)'), self.dataset)

    def openFile(self):
        if self.filedialog.exec_():
            filename = str(self.filedialog.selectedFiles()[0])
            if filename:
                self.closeFile()
                self._openFile(filename)

    def closeFile(self):
        # @TODO: extend for multiple datasets
        self.emit(QtCore.SIGNAL('closeGdalDataset()'))
        self.closeRasterBand()
        self.dataset = None
        self.statusBar().showMessage('Ready.')

    def openRasterBand(self, band):
        self.closeRasterBand()

        if band.lut is None:
            ovrindex = band.best_ovr_index()
            ovrBand = band.GetOverview(ovrindex)
            data = ovrBand.ReadAsArray()
            band.lut = gsdtools.ovr_lut(data)

        self.setGraphicsItem(band, band.lut)

    def closeRasterBand(self):
        self.graphicsView.clearScene()
        self.imageItem = None

    ### Help actions ##########################################################
    def about(self):
        self.aboutdialog.exec_()

    def aboutQt(self):
        QtGui.QMessageBox.aboutQt(self)

    ### Auxiliaary methods ####################################################
    @qt4support.overrideCursor
    def setGraphicsItem(self, dataset, lut):
        # @TODO: update for multiple view
        self.graphicsView.setUpdatesEnabled(False)
        try:
            self.imageItem = gdalqt4.GdalGraphicsItem(dataset)
            self.imageItem._lut = lut

            rect = self.imageItem.boundingRect()

            scene = self.graphicsView.scene()
            scene.addItem(self.imageItem)
            scene.setSceneRect(rect)

            self.graphicsView.setSceneRect(scene.sceneRect())
            self.graphicsView.ensureVisible(rect.x(), rect.y(), 1, 1, 0, 0)

        finally:
            self.graphicsView.setUpdatesEnabled(True)

    def updateProgressBar(self, fract):
        self.progressbar.show()
        self.progressbar.setValue(int(100.*fract))

    def processingDone(self):
        self.controller.reset_controller()
        try:
            if self.controller.subprocess.exitCode() != 0: # timeout 30000 ms
                msg = ('An error occurred during the quicklook generation.\n'
                       'Now close the dataset.')
                QtGui.QMessageBox.warning(self, '', msg)
                self.closeFile()   # @TODO: check
                return

            # @TODO: check if opening the dataset in update mode
            #        (gdal.GA_Update) is a better solution
            self.dataset.reopen()
        finally:
            self.progressbar.hide()
            self.statusBar().showMessage('Ready.')


def main():
    app = QtGui.QApplication(sys.argv)
    mainWin = GSDView()
    mainWin.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
