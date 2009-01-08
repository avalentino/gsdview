#!/usr/bin/env python

# -*- coding: UTF8 -*-

### Copyright (C) 2008-2009 Antonio Valentino <a_valentino@users.sf.net>

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

import utils
import gdalqt4
import gsdtools
import exectools
import qt4support
import gdalsupport

from widgets import AboutDialog, PreferencesDialog
from graphicsview import GraphicsView
from gdalexectools import GdalAddOverviewDescriptor, GdalOutputHandler
from exectools.qt4tools import Qt4ToolController, Qt4DialogLoggingHandler

import gsdview_resources


# @TODO: move elseware (site.py ??)
USERCONFIGDIR = os.path.expanduser(os.path.join('~', '.gsdview'))
GSDVIEWROOT = os.path.dirname(os.path.abspath(__file__))


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

    '''Main window class for GSDView application.

    :attributes:

    - filedialog
    - aboutdialog
    - preferencedsdialog
    - progressbar
    - settings_submenu
    - settings
    - logger
    - controller
    - cachedir

    - graphicsView
    - imageItem
    - dataset

    :signals:

    - openGdalDataset(PyQt_PyObject)
    - closeGdalDataset()

    '''

    def __init__(self, parent=None):
        QtGui.qApp.setWindowIcon(QtGui.QIcon(':/images/GSDView.png'))

        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr('GSDView'))
        self.setObjectName('gsdview-mainwin')

        # Dialogs
        self.filedialog = QtGui.QFileDialog(self)
        self.filedialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        self.filedialog.setFilters(gdalsupport.gdalFilters())
        self.filedialog.setViewMode(QtGui.QFileDialog.Detail)

        self.aboutdialog = AboutDialog(self)
        self.preferencesdialog = PreferencesDialog(self)
        self.connect(self.preferencesdialog, QtCore.SIGNAL('apply()'),
                     self.applySettings)

        # Progressbar
        self.progressbar = QtGui.QProgressBar(self)
        self.progressbar.setTextVisible(True)
        self.statusBar().addPermanentWidget(self.progressbar)
        self.progressbar.hide()

        self.cachedir = None

        scene = QtGui.QGraphicsScene(self)
        graphicsview = GraphicsView(scene, self)
        graphicsview.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.setCentralWidget(graphicsview)

        self.graphicsView = graphicsview
        self.imageItem = None
        self.dataset = None

        # Settings
        # @TODO: fix filename
        #self.settings = QtCore.QSettings('gsdview-soft', 'gsdview', self)
        #self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #                                 QtCore.QSettings.UserScope,
        #                                 'gsdview', 'gsdview', self)
        cfgfile = os.path.join(USERCONFIGDIR, 'gsdview.ini')
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
        self._addMenuFromActions(self.fileActions, self.tr('&File'))
        self._addToolBarFromActions(self.fileActions, self.tr('File toolbar'))

        # Setup plugins
        self.setupPlugins() # @TODO: pass settings

        # Settings menu end toolbar
        menu = self._addMenuFromActions(self.settingsActions,
                                        self.tr('&Settings'))
        self._addToolBarFromActions(self.settingsActions,
                                    self.tr('Settings toolbar'))
        self.settings_submenu = QtGui.QMenu(self.tr('&View'))
        menu.addSeparator()
        menu.addMenu(self.settings_submenu)
        self.connect(self.settings_submenu, QtCore.SIGNAL('aboutToShow()'),
                     self.updateSettingsMenu)

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
                # save window size and position
                self.settings.beginGroup('mainwindow')
                self.settings.setValue('position', QtCore.QVariant(self.pos()))
                self.settings.setValue('size', QtCore.QVariant(self.size()))
                self.settings.endGroup()
                event.accept()
        except AttributeError:
            pass

    ### Setup helpers #########################################################
    def _setupFileActions(self):
        actionsgroup = QtGui.QActionGroup(self)

        # Open
        action = QtGui.QAction(QtGui.QIcon(':/images/open.svg'),
                               self.tr('&Open'), actionsgroup)
        #action.setObjectName('actionFileOpen') # @TODO: complete
        action.setShortcut(self.tr('Ctrl+O'))
        action.setStatusTip(self.tr('Open an existing file'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.openFile)
        actionsgroup.addAction(action)

        # Close
        action = QtGui.QAction(QtGui.QIcon(':/images/close.svg'),
                               self.tr('&Close'), actionsgroup)
        action.setShortcut(self.tr('Ctrl+W'))
        action.setStatusTip(self.tr('Close an open file'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.closeFile)
        actionsgroup.addAction(action)

        # Separator
        action = QtGui.QAction(actionsgroup)
        action.setSeparator(True)
        actionsgroup.addAction(action)

        # Exit
        action = QtGui.QAction(QtGui.QIcon(':/images/quit.svg'),
                               self.tr('&Exit'), actionsgroup)
        action.setShortcut(self.tr('Ctrl+X'));
        action.setStatusTip(self.tr('Exit the program'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.close)
        actionsgroup.addAction(action)

        return actionsgroup

    def _setupSettingsActions(self):
        actionsgroup = QtGui.QActionGroup(self)

        # Preferences
        action = QtGui.QAction(QtGui.QIcon(':/images/preferences.svg'),
                               self.tr('&Preferences'), actionsgroup)
        action.setStatusTip(self.tr('Show program preferences dialog'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.showPreferencesDialog)
        actionsgroup.addAction(action)

        return actionsgroup

    def _setupHelpActions(self):
        actionsgroup = QtGui.QActionGroup(self)

        # About
        action = QtGui.QAction(QtGui.QIcon(':/images/about.svg'),
                               self.tr('&About'), actionsgroup)
        action.setStatusTip(self.tr('Show program information'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.aboutdialog.exec_)
        actionsgroup.addAction(action)

        # AboutQt
        action = QtGui.QAction(QtGui.QIcon(':/images/qt-logo.png'),
                               self.tr('About &Qt'), actionsgroup)
        action.setStatusTip(self.tr('Show information about Qt'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     lambda: QtGui.QMessageBox.aboutQt(self))
        actionsgroup.addAction(action)

        return actionsgroup

    def setupActions(self):
        self.fileActions = self._setupFileActions()
        self.settingsActions = self._setupSettingsActions()
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
        # @TODO: move to launcher
        logging.basicConfig(format='%(levelname)s: %(message)s')

        logger = logging.getLogger()    # 'gsdview' # @TODO: fix


        fmt = ('%(levelname)s: %(asctime)s %(filename)s line %(lineno)d in '
               '%(funcName)s: %(message)s')
        formatter = logging.Formatter(fmt)
        logfile = os.path.join(USERCONFIGDIR, 'gsdview.log')
        handler = logging.FileHandler(logfile, 'w')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

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
        try:

            position = settings.value('position')
            if not position.isNull():
                self.move(position.toPoint())
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
            except KeyError:
                logging.debug('unable to restore the window state',
                              exc_info=True)

            # State of toolbars ad docks
            state = settings.value('state')
            if not state.isNull():
                self.restoreState(state.toByteArray())
        finally:
            settings.endGroup()

    def _restoreFileDialogState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('filedialog')
        try:
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
            workdir = settings.value('workdir', QtCore.QVariant(default))
            workdir = str(workdir.toString())
            workdir = os.path.expanduser(os.path.expandvars(workdir))
            self.filedialog.setDirectory(workdir)

            # history
            #history = settings.value('history')
            #if not history.isNull():
            #    self.filedialog.setHistory(history.toStringList())

            # sidebar urls
            try:
                # QFileDialog.setSidebarUrls is new in Qt 4.3
                sidebarurls = settings.value('sidebarurls')
                if not sidebarurls.isNull():
                    sidebarurls = sidebarurls.toStringList()
                    sidebarurls = [QtCore.QUrl(item) for item in sidebarurls]
                    self.filedialog.setSidebarUrls(sidebarurls)
            except AttributeError:
                logging.debug('unable to restore sidebar URLs of the file '
                              'dialog')
        finally:
            settings.endGroup()

    def loadSettings(self, settings=None):
        if settings is None:
            settings = self.settings

        # general
        self._restoreWindowState(settings)
        self._restoreFileDialogState(settings)

        settings.beginGroup('preferences')
        try:
            # log level
            level = settings.value('loglevel', QtCore.QVariant('INFO'))
            level = level.toString()
            levelno = logging.getLevelName(str(level))
            if isinstance(levelno, int):
                self.logger.setLevel(levelno)
                self.logger.debug('"%s" loglevel set' % level)
            else:
                logging.debug('invalid log level: "%s"' % level)

            default = os.path.join(USERCONFIGDIR, 'cache')
            cachedir = settings.value('cachedir', QtCore.QVariant(default))
            cachedir = str(cachedir.toString())
            self.cachedir = os.path.expanduser(os.path.expandvars(cachedir))
        finally:
            settings.endGroup()

        # GDAL
        settings.beginGroup('gdal')
        try:
            cachesize, ok = settings.value('GDAL_CACHEMAX').toULongLong()
            if ok:
                gdal.SetCacheMax(cachesize)
                self.logger.debug('GDAL cache size det to %d' % cachesize)

            value = settings.value('GDAL_DATA').toString()
            if value:
                value = os.path.expanduser(os.path.expandvars(str(value)))
                gdal.SetConfigOption('GDAL_DATA', value)
                self.logger.debug('GDAL_DATA directory set to "%s"' % value)

            register = False
            for optname in ('GDAL_SKIP', 'GDAL_DRIVER_PATH', 'OGR_DRIVER_PATH'):
                value = settings.value(optname).toString()
                if value:
                    value = os.path.expanduser(os.path.expandvars(str(value)))
                    gdal.SetConfigOption(optname, value)
                    self.logger.debug('%s directory set to "%s"' %
                                                            (optname, value))
                    register = True
            if register:
                gdal.AllRegister()
                self.logger.debug('run "gdal.AllRegister()"')
        finally:
            settings.endGroup()

        # cache
        # @TODO

        # plugins
        for plugin in self.plugins.values():
            plugin.loadSettings(settings)

    def _saveWindowState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('mainwindow')
        try:
            settings.setValue('winstate', QtCore.QVariant(self.windowState()))

            if self.windowState() == QtCore.Qt.WindowNoState:
                settings.setValue('position', QtCore.QVariant(self.pos()))
                settings.setValue('size', QtCore.QVariant(self.size()))
            settings.setValue('state', QtCore.QVariant(self.saveState()))
        finally:
            settings.endGroup()

    def _saveFileDialogState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('filedialog')
        try:
            # state
            try:
                # QFileDialog.saveState is new in Qt 4.3
                state = self.filedialog.saveState()
                settings.setValue('state', QtCore.QVariant(state))
            except AttributeError:
                logging.debug('unable to save the file dialog state')

            # workdir
            # @NOTE: uncomment to preserve the session value
            #workdir = self.filedialog.directory()
            #workdir = settings.setValue('workdir', QtCore.QVariant(workdir))

            # history
            #settings.setValue('history',
            #                  QtCore.QVariant(self.filedialog.history()))

            # sidebar urls
            try:
                # QFileDialog.sidebarUrls is new in Qt 4.3
                sidebarurls = self.filedialog.sidebarUrls()
                if sidebarurls:
                    qsidebarurls = QtCore.QStringList()
                    for item in sidebarurls:
                        qsidebarurls.append(QtCore.QString(item.toString()))
                    settings.setValue('sidebarurls',
                                      QtCore.QVariant(qsidebarurls))
            except AttributeError:
                logging.debug('unable to save sidebar URLs of the file dialog')
        finally:
            settings.endGroup()

    def saveSettings(self, settings=None):
        if settings is None:
            settings = self.settings

        # general
        self._saveWindowState(settings)
        self._saveFileDialogState(settings)

        settings.beginGroup('preferences')
        try:
            level = QtCore.QVariant(logging.getLevelName(self.logger.level))
            settings.setValue('loglevel', QtCore.QVariant(level))

            # only changed via preferences
            #settings.setValue('cachedir', QtCore.QVariant(self.cachedir))
        finally:
            settings.endGroup()

        # @NOTE: GDAL preferences are only modified via preferences dialog
        # @NOTE: cache preferences are only modified via preferences dialog

        for plugin in self.plugins.values():
            plugin.saveSettings(settings)

    def updateSettingsMenu(self):
        self.settings_submenu.clear()
        menu = self.createPopupMenu()

        for action in menu.actions():
            if self.tr('toolbar') in action.text():
                self.settings_submenu.addAction(action)
        self.settings_submenu.addSeparator()
        for action in menu.actions():
            if self.tr('toolbar') not in action.text():
                self.settings_submenu.addAction(action)

    def applySettings(self):
        self.preferencesdialog.save(self.settings)
        self.loadSettings()

    def showPreferencesDialog(self):
        # @TODO: complete
        self.saveSettings()
        self.preferencesdialog.load(self.settings)
        if self.preferencesdialog.exec_():
            self.applySettings()

    ### File actions ##########################################################
    @qt4support.overrideCursor
    def _openFile(self, filename):
        self.dataset = gdalsupport.DatasetProxy(filename, self.cachedir)

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
    # @NOTE: needed for UI building of promoted widgets
    sys.path.insert(0, GSDVIEWROOT)

    # @NOTE: needed for path names variables expansion
    os.environ['GSDVIEWROOT'] = GSDVIEWROOT

    app = QtGui.QApplication(sys.argv)
    mainwin = GSDView()
    mainwin.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
