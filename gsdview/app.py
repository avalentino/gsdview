# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2019 Antonio Valentino <antonio.valentino@tiscali.it>
#
# This module is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 2 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this module if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US


"""GUI front-end for the Geospatial Data Abstraction Library (GDAL)."""


import os
import sys
import logging

from qtpy import QtCore, QtWidgets, QtGui

from exectools.qt import QtToolController, QtDialogLoggingHandler

from gsdview import info
from gsdview import utils
from gsdview import errors
from gsdview import qtsupport
from gsdview import graphicsview
from gsdview import mousemanager
from gsdview import pluginmanager

from gsdview.mdi import ItemModelMainWindow
from gsdview.appsite import USERCONFIGDIR, SYSPLUGINSDIR
from gsdview.widgets import AboutDialog, PreferencesDialog
from gsdview.widgets import GSDViewExceptionDialog as ExceptionDialog


__all__ = ['GSDView']
_log = logging.getLogger(__name__)


class GSDView(ItemModelMainWindow):
    # @TODO:
    #   * cache browser, cache cleanup
    #   * open internal product
    #   * disable actions when the external tool is running
    #   * /usr/share/doc/python-qt4-doc/examples/mainwindows/recentfiles.py

    """Main window class for GSDView application."""

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0), **kwargs):
        loglevel = kwargs.pop('loglevel', logging.NOTSET)

        _log.debug('Main window base classes initialization ...')
        QtWidgets.QApplication.setWindowIcon(
            qtsupport.geticon('GSDView.png', __name__))

        super(GSDView, self).__init__(parent, flags, **kwargs)
        title = self.tr('GSDView Open Source Edition v. %s') % info.version
        self.setWindowTitle(title)
        self.setObjectName('gsdview-mainwin')

        # Dialogs
        _log.debug('Setting up file dialog ...')

        #: application global file dialog instance
        self.filedialog = QtWidgets.QFileDialog(self)
        self.filedialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        self.filedialog.setViewMode(QtWidgets.QFileDialog.Detail)

        _log.debug('Setting up the about dialog ...')

        #: application global about dialog instance
        self.aboutdialog = AboutDialog(self)

        _log.debug('Setting up the preferences dialog ...')

        #: preferences dialog instance
        self.preferencesdialog = PreferencesDialog(self,
                                                   apply=self.applySettings)

        # Stop button
        _log.debug('Setting up the stop button ...')
        qstyle = QtWidgets.QApplication.style()
        icon = qstyle.standardIcon(QtWidgets.QStyle.SP_BrowserStop)

        #: stop button for external tools
        self.stopbutton = QtWidgets.QPushButton(icon, self.tr('Stop'), self)
        self.statusBar().addPermanentWidget(self.stopbutton)
        self.stopbutton.hide()

        # Progressbar
        _log.debug('Setting up the progress bar ...')

        #: application progress bar
        self.progressbar = QtWidgets.QProgressBar(self)
        self.progressbar.setTextVisible(True)
        self.statusBar().addPermanentWidget(self.progressbar)
        self.progressbar.hide()

        # Miscellanea
        _log.debug('Miscellanea setup ...')

        #: cache directory path
        self.cachedir = None

        # GraphicsViewMonitor and mouse manager
        _log.debug('Setting up "monitor" components ...')

        #: graphics scenes/views monitor
        self.monitor = graphicsview.GraphicsViewMonitor()

        #: mouse manager for graphics scenes/views
        self.mousemanager = mousemanager.MouseManager(self)
        self.mousemanager.mode = 'hand'

        # Plugin Manager

        #: backends list
        self.backends = []

        #: plugin manager instance
        self.pluginmanager = pluginmanager.PluginManager(self, SYSPLUGINSDIR)
        self.preferencesdialog.addPage(
            pluginmanager.PluginManagerGui(self.pluginmanager, self),
            qtsupport.geticon('plugin.svg', __name__),
            label='Plugins')

        # Settings
        if not os.path.isdir(USERCONFIGDIR):
            os.makedirs(USERCONFIGDIR)

        # @TODO: fix filename
        _log.debug('Read application settings ...')
        # self.settings = QtCore.QSettings('gsdview-soft', 'gsdview', self)
        # self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #                                  QtCore.QSettings.UserScope,
        #                                  'gsdview', 'gsdview', self)
        cfgfile = os.path.join(USERCONFIGDIR, 'gsdview.ini')
        _log.info('Configuration file: "%s".', cfgfile)

        #: application settings
        self.settings = QtCore.QSettings(cfgfile,
                                         QtCore.QSettings.IniFormat,
                                         self)

        # Setup the log system and the external tools controller
        _log.debug('Complete logging setup...')
        # @TODO: logevel could be set from command line
        #: application standard logger
        self.logger = self.setupLogging(loglevel=loglevel)

        _log.debug('Setting up external tool controller ...')

        #: external tool controller
        self.controller = self.setupController(self.logger, self.statusBar(),
                                               self.progressbar)

        # Actions
        _log.debug('Setting up actions ...')

        #: actions associated to file menu
        self.fileActions = None

        #: settings actions
        self.settingsActions = None

        #: help actions
        self.helpActions = None

        self.setupActions()

        # File menu end toolbar
        self._addMenuFromActions(self.fileActions, self.tr('&File'))
        self._addToolBarFromActions(self.fileActions, self.tr('File toolbar'))

        # Image menu and toolbar
        self.imagemenu = self._addMenuFromActions(self.mousemanager.actions,
                                                  self.tr('&Image'))
        self._addToolBarFromActions(self.mousemanager.actions,
                                    self.tr('Mouse toolbar'))

        # Tools menu
        self.toolsmenu = QtWidgets.QMenu(self.tr('&Tools'), self)
        self.menuBar().addMenu(self.toolsmenu)
        self.toolsmenu.hide()

        # Setup plugins
        _log.debug(self.tr('Setup plugins ...'))
        self.setupPlugins()

        # Settings menu end toolbar
        _log.debug(self.tr('Settings menu setup ...'))
        menu = self._addMenuFromActions(self.settingsActions,
                                        self.tr('&Settings'))
        self._addToolBarFromActions(self.settingsActions,
                                    self.tr('Settings toolbar'))

        #: settings sub-menu
        self.settings_submenu = QtWidgets.QMenu(
            self.tr('&View'), aboutToShow=self.updateSettingsMenu)
        menu.addSeparator()
        menu.addMenu(self.settings_submenu)

        _log.debug(self.tr('Window menu setup ...'))
        self.menuBar().addMenu(self.windowmenu)

        # Help menu end toolbar
        _log.debug('Help menu setup ...')
        self._addMenuFromActions(self.helpActions, self.tr('&Help'))
        self._addToolBarFromActions(self.helpActions, self.tr('Help toolbar'))

        # @NOTE: the window state setup must happen after the plugins loading
        _log.info('Load settings ...')
        self.loadSettings(loglevel=loglevel)  # @TODO: pass cachedir

        self.treeview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeview.customContextMenuRequested.connect(self.itemContextMenu)

        self.statusBar().showMessage('Ready')

    # Model/View utils ######################################################
    def currentGraphicsView(self):
        window = self.mdiarea.activeSubWindow()
        if window:
            widget = window.widget()
            if isinstance(widget, QtWidgets.QGraphicsView):
                return widget
        return None

    @QtCore.Slot(QtCore.QPoint)
    def itemContextMenu(self, pos):
        modelindex = self.treeview.indexAt(pos)
        if not modelindex.isValid():
            return
        # @TODO: check
        # @NOTE: set the current index so that action callback can retrieve
        #        the correct item
        self.treeview.setCurrentIndex(modelindex)
        item = self.datamodel.itemFromIndex(modelindex)
        backend = self.pluginmanager.plugins[item.backend]
        menu = backend.itemContextMenu(item)
        if menu:
            menu.exec_(self.treeview.mapToGlobal(pos))

    # Event handlers ########################################################
    def closeEvent(self, event):
        self.controller.stop_tool()
        # @TODO: wait for finished (??)
        # @TODO: save opened datasets (??)
        self.saveSettings()
        self.pluginmanager.save_settings(self.settings)
        self.closeAll()
        self.pluginmanager.reset()
        _log.info('Closing application')
        # event.accept()
        super(GSDView, self).closeEvent(event)

    def changeEvent(self, event):
        try:
            if event.oldState() == QtCore.Qt.WindowNoState:
                # save window size and position
                self.settings.beginGroup('mainwindow')
                self.settings.setValue('geometry', self.saveGeometry())
                # @TODO: clean
                # self.settings.setValue('position', self.pos())
                # self.settings.setValue('size', self.size())
                self.settings.endGroup()
                event.accept()
        except AttributeError:
            pass

    # Custom exception hook #################################################
    def excepthook(self, exctype, excvalue, tracebackobj):
        """Global function to catch unhandled exceptions.

        :param exctype:
            exception class
        :param excvalue:
            exception instance
        :param tracebackobj:
            traceback object

        """

        sys.__excepthook__(exctype, excvalue, tracebackobj)
        # No messages for keyboard interruts
        # if issubclass(exctype, KeyboardInterrupt):
        if not issubclass(exctype, Exception):
            msg = str(excvalue)
            if not msg:
                msg = excvalue.__class__.__name__
            _log.info(msg)
            self.close()
            return

        # @TODO: check
        # Guard for avoiding multiple dialog opening
        if hasattr(self, '_busy'):
            return
        self._busy = True

        # @TODO: sometimes a RuntimeError is raised claiming that the
        #        "underlying C/C++ object has been deleted".
        #        Try to build the dialog without parent (self) and check
        #        modality.
        dialog = ExceptionDialog(exctype, excvalue, tracebackobj, self)
        # dialog.show()
        ret = dialog.exec_()
        if ret == QtWidgets.QDialog.Rejected:
            self.close()
        else:
            _log.warning('ignoring an unhandled exception may cause '
                         'program malfunctions.')

    # Setup helpers #########################################################
    def _setupFileActions(self):
        # @TODO: add a "close all" (items) action
        actionsgroup = QtWidgets.QActionGroup(self)

        # Open
        icon = qtsupport.geticon('open.svg', __name__)
        QtWidgets.QAction(
            icon, self.tr('&Open'), actionsgroup,
            objectName='openAction',
            shortcut=self.tr('Ctrl+O'),
            toolTip=self.tr('Open an existing file'),
            statusTip=self.tr('Open an existing file'),
            triggered=self.openFile)

        # Close
        icon = qtsupport.geticon('close.svg', __name__)
        QtWidgets.QAction(
            icon, self.tr('&Close'), actionsgroup,
            objectName='closeAction',
            # 'Ctrl+W' shortcut is used for closing windows
            # shortcut=self.tr('Ctrl+W'),
            toolTip=self.tr('Close the current file'),
            statusTip=self.tr('Close the current file'),
            triggered=self.closeItem)

        # Separator
        QtWidgets.QAction(actionsgroup).setSeparator(True)
        # objectName='separator')

        # Exit
        icon = qtsupport.geticon('quit.svg', __name__)
        QtWidgets.QAction(
            icon, self.tr('&Exit'), actionsgroup,
            objectName='exitAction',
            shortcut=self.tr('Ctrl+X'),
            toolTip=self.tr('Exit the program'),
            statusTip=self.tr('Exit the program'),
            triggered=self.close)

        return actionsgroup

    def _setupSettingsActions(self):
        actionsgroup = QtWidgets.QActionGroup(self)

        # Preferences
        icon = qtsupport.geticon('preferences.svg', __name__)
        QtWidgets.QAction(
            icon, self.tr('&Preferences'), actionsgroup,
            objectName='preferencesAction',
            toolTip=self.tr('Open the program preferences dialog'),
            statusTip=self.tr('Open the program preferences dialog'),
            triggered=self.showPreferencesDialog)

        icon = qtsupport.geticon('full-screen.svg', __name__)
        QtWidgets.QAction(
            icon, self.tr('&Full Screen'), actionsgroup,
            objectName='fullScreenAction',
            shortcut='Ctrl+Meta+F',
            toolTip=self.tr('Toggle full screen mode'),
            statusTip=self.tr('Toggle full screen mode'),
            triggered=self.toggleFullScreenMode)

        return actionsgroup

    def _setupHelpActions(self):
        actionsgroup = QtWidgets.QActionGroup(self)

        # About
        icon = qtsupport.geticon('about.svg', __name__)
        QtWidgets.QAction(
            icon, self.tr('&About'), actionsgroup,
            objectName='aboutAction',
            toolTip=self.tr('Show program information'),
            statusTip=self.tr('Show program information'),
            triggered=lambda: self.aboutdialog.exec_())

        # AboutQt
        icon = QtGui.QIcon.fromTheme(':qtlogo-64')
        QtWidgets.QAction(
            icon, self.tr('About &Qt'), actionsgroup,
            objectName='aboutQtAction',
            toolTip=self.tr('Show information about Qt'),
            statusTip=self.tr('Show information about Qt'),
            triggered=lambda: QtWidgets.QMessageBox.aboutQt(self))

        return actionsgroup

    def setupActions(self):
        self.fileActions = self._setupFileActions()
        self.settingsActions = self._setupSettingsActions()
        self.helpActions = self._setupHelpActions()
        # @TODO: tree view actions: expand/collapse all, expand/collapse
        #        subtree
        # @TODO: stop action

    def _addMenuFromActions(self, actions, name):
        menu = qtsupport.actionGroupToMenu(actions, name, self)
        self.menuBar().addMenu(menu)
        return menu

    def _addToolBarFromActions(self, actions, name):
        toolbar = qtsupport.actionGroupToToolbar(actions, name)
        self.addToolBar(toolbar)

        return toolbar

    def setupPlugins(self):
        # load backends
        # @WARNING: (pychecker) Function (__import__) doesn't support **kwArgs
        module = __import__('gsdview.gdalbackend', fromlist=['gsdview'])
        self.pluginmanager.load_module(module, 'gdalbackend')

        # load settings
        self.pluginmanager.load_settings(self.settings)

        # save initial state
        self.pluginmanager.save_settings(self.settings)

    def setupLogging(self, loglevel=None):
        logger = logging.getLogger('gsdview')

        # move this to launch.py
        fmt = ('%(levelname)s: %(asctime)s %(filename)s line %(lineno)d in '
               '%(funcName)s: %(message)s')
        formatter = logging.Formatter(fmt)
        logfile = os.path.join(USERCONFIGDIR, 'gsdview.log')
        handler = logging.FileHandler(logfile, 'w')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        formatter = logging.Formatter('%(message)s')
        handler = QtDialogLoggingHandler(parent=self, dialog=None)
        handler.setLevel(logging.WARNING)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # set log level
        if loglevel in (None, logging.NOTSET, 'NOTSET'):
            # @WARNING: duplicate loadSettings
            level = self.settings.value('preferences/loglevel', 'INFO')
            levelno = logging.getLevelName(str(level))
            if isinstance(levelno, int):
                logger.setLevel(levelno)
                _log.info('"%s" loglevel set', level)
            else:
                _log.debug('invalid log level: "%s"', level)

        return logger

    def setupController(self, logger, statusbar, progressbar):
        controller = QtToolController(logger, parent=self)
        controller.subprocess.started.connect(self.processingStarted)
        controller.finished.connect(self.processingDone)
        self.stopbutton.clicked.connect(controller.stop_tool)

        return controller

    # Settings ##############################################################
    def _restoreWindowState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('mainwindow')
        try:
            # @TODO: clean
            # position = settings.value('position')
            # if position is not None:
            #     self.move(position)
            # size = settings.value('size')
            # if size is not None:
            #     self.resize(size)
            # else:
            #     # default size
            #     self.resize(800, 600)

            geometry = settings.value('geometry')
            if (not geometry or
                    (geometry and not self.restoreGeometry(geometry))):
                # default size
                self.resize(800, 600)

            state = settings.value('state')
            if state:
                self.restoreState(state)

            # @TODO: clean
            # try:
            #     winstate = settings.value('winstate', QtCore.Qt.WindowNoState)
            #     winstate = int(winstate)
            #     if winstate and winstate != QtCore.Qt.WindowNoState:
            #         self.setWindowState(winstate)
            # except (KeyError, ValueError) as e:
            #     _log.info('unable to restore the window state')
            #     _log.debug('', exc_info=True)

            # State of toolbars ad docks
            state = settings.value('state')
            if state is not None:
                self.restoreState(state)
        finally:
            settings.endGroup()

    def _restoreFileDialogState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('filedialog')
        try:
            # state
            state = settings.value('state')
            if state is not None:
                try:
                    # QFileDialog.restoreState is new in Qt 4.3
                    self.filedialog.restoreState(state)
                except AttributeError:
                    _log.debug('unable to restore the file dialog state')

            # workdir
            workdir = settings.value('workdir', utils.default_workdir())
            workdir = os.path.expanduser(os.path.expandvars(workdir))
            self.filedialog.setDirectory(workdir)

            # history
            # history = settings.value('history')
            # if history:
            #     self.filedialog.setHistory(history)

            # sidebar urls
            try:
                # QFileDialog.setSidebarUrls is new in Qt 4.3
                sidebarurls = settings.value('sidebarurls')
                if sidebarurls:
                    sidebarurls = [QtCore.QUrl(item) for item in sidebarurls]
                    self.filedialog.setSidebarUrls(sidebarurls)
            except AttributeError:
                _log.debug('unable to restore sidebar URLs of the file dialog')
        finally:
            settings.endGroup()

    def loadSettings(self, settings=None, loglevel=None):
        # @TODO: split app saveSettings from plugins one
        if settings is None:
            settings = self.settings

        # general
        self._restoreWindowState(settings)
        self._restoreFileDialogState(settings)

        settings.beginGroup('preferences')
        try:
            # log level
            if loglevel in (None, logging.NOTSET, 'NOTSET'):
                level = settings.value('loglevel', 'INFO')
                levelno = logging.getLevelName(level)
                if isinstance(levelno, int):
                    self.logger.setLevel(levelno)
                    _log.debug('"%s" loglevel set', level)
                else:
                    _log.debug('invalid log level: "%s"', level)

            # cache location
            default = os.path.join(USERCONFIGDIR, 'cache')
            cachedir = settings.value('cachedir', default)
            self.cachedir = os.path.expanduser(os.path.expandvars(cachedir))
        finally:
            settings.endGroup()

        # cache
        # @TODO

        # plugins
        for plugin in self.pluginmanager.plugins.values():
            plugin.loadSettings(settings)

    def _saveWindowState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('mainwindow')
        try:
            settings.setValue('winstate', self.windowState())
            # @TODO: clean
            # if self.windowState() == QtCore.Qt.WindowNoState:
            #     settings.setValue('position', self.pos())
            #     settings.setValue('size', self.size())

            settings.setValue('geometry', self.saveGeometry())
            settings.setValue('state', self.saveState())
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
                settings.setValue('state', self.filedialog.saveState())
            except AttributeError:
                _log.debug('unable to save the file dialog state')

            # workdir
            # @NOTE: uncomment to preserve the session value
            # workdir = settings.setValue('workdir',
            #                             self.filedialog.directory())

            # history
            # settings.setValue('history', self.filedialog.history())

            # sidebar urls
            try:
                # QFileDialog.sidebarUrls is new in Qt 4.3
                sidebarurls = self.filedialog.sidebarUrls()
                if sidebarurls:
                    settings.setValue('sidebarurls', sidebarurls)
            except AttributeError:
                _log.debug('unable to save sidebar URLs of the file dialog')
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
            level = logging.getLevelName(self.logger.level)
            settings.setValue('loglevel', level)

            # only changed via preferences
            # settings.setValue('cachedir', self.cachedir)
        finally:
            settings.endGroup()

        # @NOTE: cache preferences are only modified via preferences dialog

        for plugin in self.pluginmanager.plugins.values():
            # logging.debug('save %s plugin preferences' % plugin.name)
            plugin.saveSettings(settings)

    @QtCore.Slot()
    def toggleFullScreenMode(self):
        self.setWindowState(self.windowState() ^ QtCore.Qt.WindowFullScreen)

    @QtCore.Slot()
    def updateSettingsMenu(self):
        # @TODO: rewrite; it should not be needed to copy the menu into a
        #        new one
        self.settings_submenu.clear()
        menu = self.createPopupMenu()

        for action in menu.actions():
            if self.tr('toolbar') in action.text():
                self.settings_submenu.addAction(action)
        self.settings_submenu.addSeparator()
        for action in menu.actions():
            if self.tr('toolbar') not in action.text():
                self.settings_submenu.addAction(action)

    @QtCore.Slot()
    def applySettings(self):
        self.preferencesdialog.save(self.settings)
        self.loadSettings()

    @QtCore.Slot()
    def showPreferencesDialog(self):
        # @TODO: complete
        self.saveSettings()
        self.preferencesdialog.load(self.settings)
        if self.preferencesdialog.exec_():
            self.applySettings()

    # File actions ##########################################################
    @QtCore.Slot()
    def openFile(self):
        # @TODO: remove; this is a temporary workaround for a Qt bug in
        #        Cocoa version
        self.filedialog.selectNameFilter(self.filedialog.selectedNameFilter())

        # @TODO: allow multiple file selection
        if self.filedialog.exec_():
            filename = str(self.filedialog.selectedFiles()[0])
            if filename:
                for backendname in self.backends:
                    backend = self.pluginmanager.plugins[backendname]
                    try:
                        item = backend.openFile(filename)
                        if item:
                            self.datamodel.appendRow(item)
                            self.treeview.expand(item.index())
                            _log.debug('File "%s" opened with backend "%s"',
                                       filename, backendname)
                        else:
                            _log.info('file %s" already open', filename)
                        break
                    except errors.OpenError:
                        # _log.exception('exception caught')
                        _log.debug('Backend "%s" failed to open file "%s"',
                                   backendname, filename)
                else:
                    _log.error('Unable to open file "%s"', filename)

    @QtCore.Slot()
    def closeItem(self):
        # @TODO: extend for multiple datasets
        # self.closeGdalDataset.emit()

        item = self.currentItem()
        if item:
            # find the toplevel item
            while item.parent():
                item = item.parent()

            try:
                # backend = self.pluginmanager.plugins[item.backend]
                # backend.closeFile(item)
                item.close()
            except AttributeError:
                self.datamodel.invisibleRootItem().removeRow(item.row())

        self.statusBar().showMessage('Ready.')

    @QtCore.Slot()
    def closeAll(self):
        root = self.datamodel.invisibleRootItem()
        while root.hasChildren():
            item = root.child(0)
            try:
                # backend = self.pluginmanager.plugins[item.backend]
                # backend.closeFile(item)
                item.close()
            except AttributeError:
                root.removeRow(item.row())

    # Auxiliary methods ####################################################
    @QtCore.Slot()
    @QtCore.Slot(str)
    def processingStarted(self, msg=None):
        if msg:
            self.statusBar().showMessage(msg)
        self.progressbar.show()
        self.stopbutton.setEnabled(True)
        self.stopbutton.show()

    @QtCore.Slot(int)
    def updateProgressBar(self, fract):
        self.progressbar.show()
        self.progressbar.setValue(int(100. * fract))

    @QtCore.Slot(int)
    def processingDone(self, returncode=0):
        # self.controller.reset()  # @TODO: remove
        try:
            if returncode != 0:
                msg = ('An error occurred during the quicklook generation.\n'
                       'Now close the dataset.')
                QtWidgets.QMessageBox.warning(self, '', msg)
                self.closeItem()   # @TODO: check
        finally:
            self.progressbar.hide()
            self.stopbutton.setEnabled(False)
            self.stopbutton.hide()
            self.statusBar().showMessage('Ready.')
