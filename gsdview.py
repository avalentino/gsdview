#!/usr/bin/env python

# -*- coding: UTF8 -*-

### Copyright (C) 2007 Antonio Valentino <a_valentino@users.sf.net>

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

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date: 2007-12-02 12:28:46 +0100 (dom, 02 dic 2007) $'
__version__ = (1,0,0)
__revision__ = '$Revision: 42 $'

import os
import sys
import logging

import numpy
import gdal

from PyQt4 import QtCore, QtGui
from PyQt4 import Qwt5 as Qwt

import resources

import gsdtools
import qt4support
import gdalsupport
import gdalqt4

from graphicsview import GraphicsView

import exectools

from exectools.qt4tools import Qt4OutputPlane, Qt4ToolController
from exectools.qt4tools import Qt4DialogLoggingHandler, Qt4StreamLoggingHandler

from gdalexectools import GdalAddOverviewDescriptor, GdalOutputHandler


class GSDView(QtGui.QMainWindow):
    # @TODO:
    #   * set all icon (can use the iconset of BEAM)
    #   * map panel (plugin)
    #   * plugin architecture (incomplete)
    #   * cache browser, cache cleanup
    #   * open internal product
    #   * stop button
    #   * disable actions when the external tool is running
    #   * /usr/share/doc/python-qt4-doc/examples/mainwindows/recentfiles.py
    #   * stretching tool

    defaultcachedir = os.path.expanduser(os.path.join('~', '.gsdview', 'cache'))

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr('GSDView'))
        self.setWindowIcon(QtGui.QIcon(':/images/GDALLogoColor.svg'))
        #self.resize(800, 600)

        scene = QtGui.QGraphicsScene(self)
        self.graphicsView = GraphicsView(scene, self)
        self.graphicsView.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.setCentralWidget(self.graphicsView)

        # Progressbar
        self.progressbar = QtGui.QProgressBar(self)
        self.progressbar.setTextVisible(True)
        self.statusBar().addPermanentWidget(self.progressbar)
        self.progressbar.hide()

        # @TODO: improve scrolling performances
        #~ self.graphicsView.horizontalScrollBar.connect(QtCore.SIGNAL('sliderPressed()'), self.startScrolling)
        #~ self.graphicsView.horizontalScrollBar.connect(QtCore.SIGNAL('sliderReleased()'), self.stopScrolling)
        #~ self.graphicsView.verticalScrollBar.connect(QtCore.SIGNAL('sliderPressed()'), self.startScrolling)
        #~ self.graphicsView.verticalScrollBar.connect(QtCore.SIGNAL('sliderReleased()'), self.stopScrolling)
        #~ self.graphicsView.connect(QtCore.SIGNAL('dragMoveEvent()'), self.startScrolling)
        #~ self.graphicsView.connect(QtCore.SIGNAL('dropEvent()'), self.stopScrolling)

        #~ self.graphicsView.connect(QtCore.SIGNAL('mousePressEvent()'), self.startScrolling)
        #~ self.graphicsView.connect(QtCore.SIGNAL('mouseReleaseEvent()'), self.stopScrolling)

        self.imageItem = None

        # @TODO: encapsulate in a gdal.Dataset proxy (--> gdalsupport)
        self.dataset = None

        # File dialog
        self.filedialog = QtGui.QFileDialog(self)
        self.filedialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        self.filedialog.setFilters(gdalsupport.gdalFilters())

        # Panels
        #~ self.quicklookView = None
        self.outputplane = None
        self.setupPanels()      # @TODO: rewrite

        # Settings
        # @TODO: fix filename
        #self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #                                 QtCore.QSettings.UserScope,
        #                                 'gsdview-soft', 'gsdview', self)
        #self.settings = QtCore.QSettings('gsdview-soft', 'gsdview', self)
        self.settings = QtCore.QSettings('gsdview.ini',
                                         QtCore.QSettings.IniFormat,
                                         self)
        self.connect(QtGui.qApp, QtCore.SIGNAL('aboutToQuit()'),
                     self.saveSettings)

        # Setup the log system
        self.logger = self.setupLogging(self.outputplane)

        # Setup the external tools controller
        self.controller = self.setupController(self.outputplane,
                                               self.statusBar(),
                                               self.progressbar,
                                               self.logger)

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
                            # @TODO: rename setWinState or so

        # Connect signals
        self.connect(self, QtCore.SIGNAL('openBandRequest(PyQt_PyObject)'),
                     self.openRasterBand)

        self.statusBar().showMessage('Ready')

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
        pluginsDir = os.path.join(os.path.dirname(__name__), 'plugins')
        sys.path.insert(0, pluginsDir)
        for dirpath, dirnames, filenames in os.walk(pluginsDir):
            for name in dirnames:
                if name.startswith('.') or (name in sys.modules):
                    continue
                try:
                    module = __import__(name)
                    module.init(self)
                    plugins[name] = module
                    self.logger.debug('"%s" plugin loaded.' % name)
                except ImportError, e:
                    self.logger.debug(str(e))
            del dirnames[:]

            for name in filenames:
                name, ext = os.path.splitext(name)
                #if ext.lower() not in ('.py', '.pyc', '.pyo', '.pyd', '.dll', '.so', '.egg', '.zip'):
                    #continue
                if name.startswith('.') or (name in sys.modules):
                    continue
                try:
                    module = __import__(name)
                    module.init(self)
                    plugins[name] = module
                    self.logger.debug('"%s" plugin loaded.' % name)
                except ImportError, e:
                    self.logger.debug(str(e))
        return plugins

    def _setupOutputPanel(self):
        # Output panel
        outputPanel = QtGui.QDockWidget('Output', self)
        outputPanel.setObjectName('outputPanel')
        outputplane = Qt4OutputPlane()
        outputPanel.setWidget(outputplane)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, outputPanel)
        self.connect(outputplane, QtCore.SIGNAL('planeHideRequest()'),
                     outputPanel.hide)
        return outputPanel

    def setupPanels(self):
        outputPanel = self._setupOutputPanel()
        self.outputplane = outputPanel.widget()

    def setupLogging(self, outputplane):
        logger = logging.getLogger()    # 'gsdview' # @TODO: fix

        # Set the log level from preferences
        defaut = QtCore.QVariant(logging.getLevelName(logger.level))
        level = self.settings.value('preferences/loglevel', defaut).toString()
        level = logging.getLevelName(str(level))
        if isinstance(level, int):
            logger.setLevel(level)

        if logger.level == logging.DEBUG:
            logging.basicConfig(level=logging.DEBUG)

        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler = Qt4StreamLoggingHandler(outputplane)
        handler.setLevel(logger.level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        formatter = logging.Formatter('%(message)s')
        handler = Qt4DialogLoggingHandler(parent=self, dialog=None)
        handler.setLevel(logging.WARNING)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def setupController(self, outputplane, statusbar, progressbar, logger):
        handler = GdalOutputHandler(outputplane, statusbar, progressbar)
        tool = GdalAddOverviewDescriptor(stdout_handler=handler)
        controller = Qt4ToolController(logger, parent=self)
        controller.tool = tool
        controller.connect(controller, QtCore.SIGNAL('finished()'),
                           self.processingDone)

        return controller

    ### Settings ##############################################################
    def loadSettings(self):
        # @TODO:
        #   * restore window size and position
        #   * restore windowState

        # mainwindow
        self.settings.beginGroup('mainwindow')
        position = self.settings.value('position')
        if not position.isNull():
            self.move(position.toPoint())
        size = self.settings.value('size')
        if not size.isNull():
            self.resize(size.toSize())
        state = self.settings.value('state')
        if not state.isNull():
            self.restoreState(state.toByteArray())
        self.settings.endGroup()

        # preferences
        self.settings.beginGroup('preferences')
        #self.cachedir = self.settings.value('cachelocation')
        # @TODO: check the default value
        #default= QtCore.QVariant(150*1024**2)
        #cachesize, ok = self.settings.value('gdalcachesize', default).toInt()
        cachesize, ok = self.settings.value('gdalcachesize').toInt()
        if ok:
            gdal.SetCacheMax(cachesize)
        self.settings.endGroup()

    def saveSettings(self):
        # @TODO: remove closeEvent (??)
        #   * save windowState (??)
        #   * de-maximize --> showNormal()  --> only before exiting
        #   * save window size and position

        # mainwindow
        self.settings.beginGroup('mainwindow')
        self.settings.setValue('position', QtCore.QVariant(self.pos()))
        self.settings.setValue('size', QtCore.QVariant(self.size()))
        self.settings.setValue('state', QtCore.QVariant(self.saveState()))
        self.settings.endGroup()

        # preferences
        self.settings.beginGroup('preferences')
        level = QtCore.QVariant(logging.getLevelName(self.logger.level))
        self.settings.setValue('loglevel', level)
        #self.settings.setValue('cachelocation', self.cachedir)
        self.settings.setValue('gdalcachesize',
                               QtCore.QVariant(gdal.GetCacheMax()))
        self.settings.endGroup()

    def _getCacheDir(self):
        defaultcachedir = QtCore.QVariant(self.defaultcachedir)
        cachedir = self.settings.value('preferences/cachedir', defaultcachedir)
        cachedir = cachedir.toString()
        return os.path.expanduser(str(cachedir))

    # @TODO: check and move elseware
    def closeEvent(self, event):
        '''
        void MainWindow::closeEvent(QCloseEvent *event)
        {
            if (maybeSave()) {
                writeSettings();
                event->accept();
            } else {
                event->ignore();
            }
        }

        '''

        self.showNormal()

    ### File actions ##########################################################
    @qt4support.overrideCursor
    def _openFile(self, filename):
        cachedir = self._getCacheDir()
        self.dataset = gdalsupport.DatasetProxy(filename, cachedir)

        # @TODO: when the improved GraphicsView will be available more then
        #        one overview level will be needed
        band = self.dataset.GetRasterBand(1)
        ovrLevel = band.compute_ovr_level()
        missingOverviewLevels = []
        try:
            ovrIndex = band.best_ovr_index(ovrLevel)
            levels = band.available_ovr_levels()
            distance = 1
            if numpy.abs(levels[ovrIndex] - ovrLevel) > distance:
                missingOverviewLevels = [ovrLevel]
            else:
                ovrLevel = levels[ovrIndex]
        except gdalsupport.MissingOvrError:
            missingOverviewLevels = [ovrLevel]
       #self.ovrlevel = ovrLevel

        # @TODO: do this after choosing the band
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

            ## ALTERNATIVE: run in a separate thread
            # gdal.SetConfigOption('USE_RRD', 'YES')
            # ret = p.BuildOverviews('average', [2,4,8])
            # ovr = b.GetOverview(2)
            # data = ovr.ReadAsArray()

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

        # Reset the scene and the view transformation matrix
        #for view in (self.graphicsView, self.quicklookView):
        #    view.clearScene()
        self.graphicsView.clearScene()

        # Reset attributes
        self.imageItem = None
        #~ self.quicklook = None
        self.dataset = None
        self.qlselection = None
        self.virtualDatasetFilename = None

        self.statusBar().showMessage('Ready.')

    ### Help actions ##########################################################
    def about(self):
        QtGui.QMessageBox.about(self, self.tr('GSDView'),
                                self.tr('GeoSpatial Data Viewer'))

    def aboutQt(self):
        QtGui.QMessageBox.aboutQt(self)

    ### Auxiliaary methods ####################################################
    @qt4support.overrideCursor
    def setGraphicsItem(self, dataset, lut):
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

    def openRasterBand(self, band):
        #band = self.dataset.GetRasterBand(band_id)     # @TODO: remove
        if band.lut is None:
            band.lut = gsdtools.compute_band_lut(band)
        self.setGraphicsItem(band, band.lut)

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


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainWin = GSDView()
    mainWin.show()
    sys.exit(app.exec_())
