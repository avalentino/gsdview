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


'''GUI front-end for the Geospatial Data Abstracton Library (GDAL).'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'

__all__ = ['GSDView']


import os
import sys
import logging

from PyQt4 import QtCore, QtGui

from exectools.qt4 import Qt4ToolController, Qt4DialogLoggingHandler

from gsdview import info
from gsdview import utils
from gsdview import errors
from gsdview import qt4support
from gsdview import graphicsview
from gsdview import mousemanager
from gsdview import pluginmanager

from gsdview.mdi import ItemModelMainWindow
from gsdview.appsite import USERCONFIGDIR, SYSPLUGINSDIR
from gsdview.widgets import AboutDialog, PreferencesDialog
from gsdview.widgets import GSDViewExceptionDialog as ExceptionDialog


class GSDView(ItemModelMainWindow):
    # @TODO:
    #   * cache browser, cache cleanup
    #   * open internal product
    #   * disable actions when the external tool is running
    #   * /usr/share/doc/python-qt4-doc/examples/mainwindows/recentfiles.py

    '''Main window class for GSDView application.'''

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0), **kwargs):
        logger = logging.getLogger('gsdview')

        logger.debug('Main window base classes initialization ...')
        QtGui.qApp.setWindowIcon(qt4support.geticon('GSDView.png', __name__))

        super(GSDView, self).__init__(parent, flags, **kwargs)
        title = self.tr('GSDView Open Source Edition v. %s') % info.version
        self.setWindowTitle(title)
        self.setObjectName('gsdview-mainwin')

        # Dialogs
        logger.debug('Setting up file dialog ...')

        #: application global file dialog instance
        self.filedialog = QtGui.QFileDialog(self)
        self.filedialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        self.filedialog.setViewMode(QtGui.QFileDialog.Detail)

        logger.debug('Setting up the about dialog ...')

        #: application global about dialog instance
        self.aboutdialog = AboutDialog(self)

        logger.debug('Setting up the preferences dialog ...')

        #: prefernces dialog instance
        self.preferencesdialog = PreferencesDialog(self,
                                                   apply=self.applySettings)

        # Stop button
        logger.debug('Setting up the stop button ...')
        qstyle = QtGui.qApp.style()
        icon = qstyle.standardIcon(QtGui.QStyle.SP_BrowserStop)

        #: stop button for external tools
        self.stopbutton = QtGui.QPushButton(icon, self.tr('Stop'), self)
        self.statusBar().addPermanentWidget(self.stopbutton)
        self.stopbutton.hide()

        # Progressbar
        logger.debug('Setting up the progress bar ...')

        #: application progress bar
        self.progressbar = QtGui.QProgressBar(self)
        self.progressbar.setTextVisible(True)
        self.statusBar().addPermanentWidget(self.progressbar)
        self.progressbar.hide()

        # Miscellanea
        logger.debug('Miscellanea setup ...')

        #: cache directory path
        self.cachedir = None

        # GraphicsViewMonitor and mouse manager
        logger.debug('Setting up "monitor" components ...')

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
                qt4support.geticon('plugin.svg', __name__),
                label='Plugins')

        # Settings
        if not os.path.isdir(USERCONFIGDIR):
            os.makedirs(USERCONFIGDIR)

        # @TODO: fix filename
        logger.debug('Read application settings ...')
        #self.settings = QtCore.QSettings('gsdview-soft', 'gsdview', self)
        #self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #                                 QtCore.QSettings.UserScope,
        #                                 'gsdview', 'gsdview', self)
        cfgfile = os.path.join(USERCONFIGDIR, 'gsdview.ini')
        logger.info('Configuration file: "%s".', cfgfile)

        #: application settings
        self.settings = QtCore.QSettings(cfgfile,
                                         QtCore.QSettings.IniFormat,
                                         self)

        # Setup the log system and the external tools controller
        logger.debug('Complete logging setup...')
        # @TODO: logevel could be set from command line
        #: application sandard logger
        self.logger = self.setupLogging()

        logger.debug('Setting up external tool controller ...')

        #: external tool controller
        self.controller = self.setupController(self.logger, self.statusBar(),
                                               self.progressbar)

        # Actions
        logger.debug('Setting up actions ...')

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
        self.toolsmenu = QtGui.QMenu(self.tr('&Tools'), self)
        self.menuBar().addMenu(self.toolsmenu)
        self.toolsmenu.hide()

        # Setup plugins
        logger.debug(self.tr('Setup plugins ...'))
        self.setupPlugins()

        # Settings menu end toolbar
        logger.debug(self.tr('Settings menu setup ...'))
        menu = self._addMenuFromActions(self.settingsActions,
                                        self.tr('&Settings'))
        self._addToolBarFromActions(self.settingsActions,
                                    self.tr('Settings toolbar'))

        #: settings sub-menu
        self.settings_submenu = QtGui.QMenu(self.tr('&View'),
                                            aboutToShow=self.updateSettingsMenu)
        menu.addSeparator()
        menu.addMenu(self.settings_submenu)

        logger.debug(self.tr('Window menu setup ...'))
        self.menuBar().addMenu(self.windowmenu)

        # Help menu end toolbar
        logger.debug('Help menu setup ...')
        self._addMenuFromActions(self.helpActions, self.tr('&Help'))
        self._addToolBarFromActions(self.helpActions, self.tr('Help toolbar'))

        # @NOTE: the window state setup must happen after the plugins loading
        logger.info('Load settings ...')
        self.loadSettings() # @TODO: pass settings
        # @TODO: force the log level set from command line
        #self.logger.setLevel(level)

        self.treeview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeview.customContextMenuRequested.connect(self.itemContextMenu)

        self.statusBar().showMessage('Ready')

    ### Model/View utils ######################################################
    def currentGraphicsView(self):
        window = self.mdiarea.activeSubWindow()
        if window:
            widget = window.widget()
            if isinstance(widget, QtGui.QGraphicsView):
                return widget
        return None

    @QtCore.pyqtSlot(QtCore.QPoint)
    def itemContextMenu(self, pos):
        modelindex = self.treeview.indexAt(pos)
        if not modelindex.isValid():
            return
        # @TODO: check
        # @NOTE: set the current index so that action callback can retrieve
        #        the cottect item
        self.treeview.setCurrentIndex(modelindex)
        item = self.datamodel.itemFromIndex(modelindex)
        backend = self.pluginmanager.plugins[item.backend]
        menu = backend.itemContextMenu(item)
        if menu:
            menu.exec_(self.treeview.mapToGlobal(pos))

    ### Event handlers ########################################################
    def closeEvent(self, event):
        self.controller.stop_tool()
        # @TODO: whait for finished (??)
        # @TODO: save opened datasets (??)
        self.saveSettings()
        self.pluginmanager.save_settings(self.settings)
        self.closeAll()
        self.pluginmanager.reset()
        self.logger.info('Closing application')
        #event.accept()
        super(GSDView, self).closeEvent(event)

    def changeEvent(self, event):
        try:
            if event.oldState() == QtCore.Qt.WindowNoState:
                # save window size and position
                self.settings.beginGroup('mainwindow')
                self.settings.setValue('position', self.pos())
                self.settings.setValue('size', self.size())
                self.settings.endGroup()
                event.accept()
        except AttributeError:
            pass

    ### Custom exception hook #################################################
    def excepthook(self, exctype, excvalue, tracebackobj):
        '''Global function to catch unhandled exceptions.

        :param exctype:
            exception class
        :param excvalue:
            exception instance
        :param tracebackobj:
            traceback object

        '''

        sys.__excepthook__(exctype, excvalue, tracebackobj)
        # No messages for keyboard interruts
        if not issubclass(exctype, Exception):
        #~ if issubclass(exctype, KeyboardInterrupt):
            msg = str(excvalue)
            if not msg:
                msg = excvalue.__class__.__name__
            self.logger.info(msg)
            self.close()
            return

        # #TODO: check
        # Guard for avoiding multiple dialog opening
        if hasattr(self, '_busy'):
            return
        self._busy = True

        # @TODO: sometimes a RuntimeError is raised claiming that the
        #        "underlying C/C++ object has been deleted".
        #        Try to build the dialog without parent (self) and check
        #        modality.
        dialog = ExceptionDialog(exctype, excvalue, tracebackobj, self)
        #dialog.show()
        ret = dialog.exec_()
        if ret == QtGui.QDialog.Rejected:
            self.close()
        else:
            logging.warning('ignoring an unhandled exception may cause '
                            'program malfunctions.')

    ### Setup helpers #########################################################
    def _setupFileActions(self):
        # @TODO: add a "close all" (items) action
        actionsgroup = QtGui.QActionGroup(self)

        # Open
        icon = qt4support.geticon('open.svg', __name__)
        QtGui.QAction(icon, self.tr('&Open'), actionsgroup,
                      objectName='openAction',
                      shortcut=self.tr('Ctrl+O'),
                      toolTip=self.tr('Open an existing file'),
                      statusTip=self.tr('Open an existing file'),
                      triggered=self.openFile)

        # Close
        icon = qt4support.geticon('close.svg', __name__)
        QtGui.QAction(icon, self.tr('&Close'), actionsgroup,
                      objectName='closeAction',
                      # 'Ctrl+W' shortcu is used for closing windows
                      #shortcut=self.tr('Ctrl+W'),
                      toolTip=self.tr('Close the current file'),
                      statusTip=self.tr('Close the current file'),
                      triggered=self.closeItem)

        # Separator
        QtGui.QAction(actionsgroup).setSeparator(True) #objectName='separator')

        # Exit
        icon = qt4support.geticon('quit.svg', __name__)
        QtGui.QAction(icon, self.tr('&Exit'), actionsgroup,
                      objectName='exitAction',
                      shortcut=self.tr('Ctrl+X'),
                      toolTip=self.tr('Exit the program'),
                      statusTip=self.tr('Exit the program'),
                      triggered=self.close)

        return actionsgroup

    def _setupSettingsActions(self):
        actionsgroup = QtGui.QActionGroup(self)

        # Preferences
        icon = qt4support.geticon('preferences.svg', __name__)
        QtGui.QAction(icon, self.tr('&Preferences'), actionsgroup,
                      objectName='preferencesAction',
                      toolTip=self.tr('Open the program preferences dialog'),
                      statusTip=self.tr('Open the program preferences dialog'),
                      triggered=self.showPreferencesDialog)

        return actionsgroup

    def _setupHelpActions(self):
        actionsgroup = QtGui.QActionGroup(self)

        # About
        icon = qt4support.geticon('about.svg', __name__)
        QtGui.QAction(icon, self.tr('&About'), actionsgroup,
                      objectName='aboutAction',
                      toolTip=self.tr('Show program information'),
                      statusTip=self.tr('Show program information'),
                      triggered=lambda: self.aboutdialog.exec_())

        # AboutQt
        icon = QtGui.QIcon(':/trolltech/qmessagebox/images/qtlogo-64.png')
        QtGui.QAction(icon, self.tr('About &Qt'), actionsgroup,
                      objectName='aboutQtAction',
                      toolTip=self.tr('Show information about Qt'),
                      statusTip=self.tr('Show information about Qt'),
                      triggered=lambda: QtGui.QMessageBox.aboutQt(self))

        return actionsgroup

    def setupActions(self):
        self.fileActions = self._setupFileActions()
        self.settingsActions = self._setupSettingsActions()
        self.helpActions = self._setupHelpActions()
        # @TODO: tree view actions: expand/collapse all, expand/collapse subtree
        # @TODO: stop action

    def _addMenuFromActions(self, actions, name):
        menu = qt4support.actionGroupToMenu(actions, name, self)
        self.menuBar().addMenu(menu)
        return menu

    def _addToolBarFromActions(self, actions, name):
        toolbar = qt4support.actionGroupToToolbar(actions, name)
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

    def setupLogging(self):
        logger = logging.getLogger('gsdview')    # 'gsdview' # @TODO: fix

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
        handler = Qt4DialogLoggingHandler(parent=self, dialog=None)
        handler.setLevel(logging.WARNING)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # set log level
        # @WARNING: duplicate loadSettings
        level = self.settings.value('preferences/loglevel', 'INFO')
        levelno = logging.getLevelName(str(level))
        if isinstance(levelno, int):
            logger.setLevel(levelno)
            logger.info('"%s" loglevel set' % level)
        else:
            logging.debug('invalid log level: "%s"' % level)

        return logger

    def setupController(self, logger, statusbar, progressbar):
        controller = Qt4ToolController(logger, parent=self)
        controller.subprocess.started.connect(self.processingStarted)
        controller.finished.connect(self.processingDone)
        self.stopbutton.clicked.connect(controller.stop_tool)

        return controller

    ### Settings ##############################################################
    def _restoreWindowState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('mainwindow')
        try:
            position = settings.value('position')
            if position is not None:
                self.move(position)
            size = settings.value('size')
            if size is not None:
                self.resize(size)
            else:
                # default size
                self.resize(800, 600)

            try:
                winstate = settings.value('winstate', QtCore.Qt.WindowNoState)
                if winstate and winstate != QtCore.Qt.WindowNoState:
                    # @COMPATIBILITY: presumably a bug in PyQt4 4.7.2
                    winstate = qt4support.intToWinState[winstate] # @TODO: check
                    self.setWindowState(winstate)
            except KeyError:
                logging.debug('unable to restore the window state',
                              exc_info=True)

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
                    logging.debug('unable to save the file dialog state')

            # workdir
            workdir = settings.value('workdir', utils.default_workdir())
            workdir = os.path.expanduser(os.path.expandvars(workdir))
            self.filedialog.setDirectory(workdir)

            # history
            #history = settings.value('history')
            #if history:
            #    self.filedialog.setHistory(history)

            # sidebar urls
            try:
                # QFileDialog.setSidebarUrls is new in Qt 4.3
                sidebarurls = settings.value('sidebarurls')
                if sidebarurls:
                    sidebarurls = [QtCore.QUrl(item) for item in sidebarurls]
                    self.filedialog.setSidebarUrls(sidebarurls)
            except AttributeError:
                logging.debug('unable to restore sidebar URLs of the file '
                              'dialog')
        finally:
            settings.endGroup()

    def loadSettings(self, settings=None):
        # @TODO: split app saveSettings frlm plugins one
        if settings is None:
            settings = self.settings

        # general
        self._restoreWindowState(settings)
        self._restoreFileDialogState(settings)

        settings.beginGroup('preferences')
        try:
            # log level
            level = settings.value('loglevel', 'INFO')
            levelno = logging.getLevelName(level)
            if isinstance(levelno, int):
                self.logger.setLevel(levelno)
                self.logger.debug('"%s" loglevel set' % level)
            else:
                logging.debug('invalid log level: "%s"' % level)

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
            if self.windowState() == QtCore.Qt.WindowNoState:
                settings.setValue('position', self.pos())
                settings.setValue('size', self.size())

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
                logging.debug('unable to save the file dialog state')

            # workdir
            # @NOTE: uncomment to preserve the session value
            #workdir = settings.setValue('workdir', self.filedialog.directory())

            # history
            #settings.setValue('history', self.filedialog.history())

            # sidebar urls
            try:
                # QFileDialog.sidebarUrls is new in Qt 4.3
                sidebarurls = self.filedialog.sidebarUrls()
                if sidebarurls:
                    settings.setValue('sidebarurls', sidebarurls)
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
            level = logging.getLevelName(self.logger.level)
            settings.setValue('loglevel', level)

            # only changed via preferences
            #settings.setValue('cachedir', self.cachedir)
        finally:
            settings.endGroup()

        # @NOTE: cache preferences are only modified via preferences dialog

        for plugin in self.pluginmanager.plugins.values():
            #logging.debug('save %s plugin preferences' % plugin.name)
            plugin.saveSettings(settings)

    @QtCore.pyqtSlot()
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

    @QtCore.pyqtSlot()
    def applySettings(self):
        self.preferencesdialog.save(self.settings)
        self.loadSettings()

    @QtCore.pyqtSlot()
    def showPreferencesDialog(self):
        # @TODO: complete
        self.saveSettings()
        self.preferencesdialog.load(self.settings)
        if self.preferencesdialog.exec_():
            self.applySettings()

    ### File actions ##########################################################
    @QtCore.pyqtSlot()
    def openFile(self):
        # @TODO: remove; this is a temporary workaround for a Qt bug in Cocoa version
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
                            self.logger.debug('File "%s" opened with backend '
                                              '"%s"' % (filename, backendname))
                        else:
                            self.logger.info('file %s" already open' % filename)
                        break
                    except errors.OpenError:
                        #self.logger.exception('exception caught')
                        self.logger.debug('Backend "%s" failed to open file '
                                          '"%s"' % (backendname, filename))
                else:
                    self.logger.error('Unable to open file "%s"' % filename)

    @QtCore.pyqtSlot()
    def closeItem(self):
        # @TODO: extend for multiple datasets
        #~ self.closeGdalDataset.emit()

        item = self.currentItem()
        if item:
            # find the toplevel item
            while item.parent():
                item = item.parent()

            try:
                #~ backend = self.pluginmanager.plugins[item.backend]
                #~ backend.closeFile(item)
                item.close()
            except AttributeError:
                self.datamodel.invisibleRootItem().removeRow(item.row())

        self.statusBar().showMessage('Ready.')

    @QtCore.pyqtSlot()
    def closeAll(self):
        root = self.datamodel.invisibleRootItem()
        while root.hasChildren():
            item = root.child(0)
            try:
                #~ backend = self.pluginmanager.plugins[item.backend]
                #~ backend.closeFile(item)
                item.close()
            except AttributeError:
                root.removeRow(item.row())

    ### Auxiliary methods ####################################################
    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(str)
    def processingStarted(self, msg=None):
        if msg:
            self.statusBar().showMessage(msg)
        self.progressbar.show()
        self.stopbutton.setEnabled(True)
        self.stopbutton.show()

    @QtCore.pyqtSlot(int)
    def updateProgressBar(self, fract):
        self.progressbar.show()
        self.progressbar.setValue(int(100.*fract))

    @QtCore.pyqtSlot(int)
    def processingDone(self, returncode=0):
        #self.controller.reset() # @TODO: remove
        try:
            if returncode != 0:
                msg = ('An error occurred during the quicklook generation.\n'
                       'Now close the dataset.')
                QtGui.QMessageBox.warning(self, '', msg)
                self.closeItem()   # @TODO: check
        finally:
            self.progressbar.hide()
            self.stopbutton.setEnabled(False)
            self.stopbutton.hide()
            self.statusBar().showMessage('Ready.')
