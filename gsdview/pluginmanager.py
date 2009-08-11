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

# -*- coding: UTF8 -*-

'''Plugin manager.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date: 2009-05-31 10:28:43 +0200 (dom, 31 mag 2009) $'
__revision__ = '$Revision: 430 $'


import os
import sys
import pkgutil
import logging

# @TODO: move Qt specific implementation elsewhere
from PyQt4 import QtCore, QtGui, uic


class PluginManager(object):
    def __init__(self, mainwin):
        super(PluginManager, self).__init__()
        self.paths = []
        self.plugins = {}
        self.autoload = []
        self._mainwin = mainwin

    def _get_allplugins(self):
        plugins = list(self.plugins.keys())
        extra_plugins = self._scanpaths()
        extra_plugins = set(extra_plugins).difference(plugins)
        plugins.extend(extra_plugins)
        plugins.sort()

        return plugins

    allplugins = property(_get_allplugins, doc='List of all availabe plugins.')

    def _scanpaths(self):
        if not self.paths:
            return []

        plugins = []
        for loader, name, ispkg in pkgutil.iter_modules(self.paths):
            if name.startswith('_'):
                continue
            plugins.append(name)

        return plugins

    def load(self, names, paths=None, info_only=False, type_='plugins'):
        if paths is None:
            paths = self.paths
        elif isinstance(paths, basestring):
            paths = [paths]

        if not paths:
            return

        logger = logging.getLogger('gsdview')
        for path in paths:
            importer = pkgutil.get_importer(path)

            if isinstance(names, basestring):
                names = [names]

            for name in names:
                if name in self.plugins:
                    continue

                # @NOTE: this causes:
                #           RuntimeWarning: Parent module 'gsdview.plugins'
                #           not found while handling absolute import
                #fullname = name.lstrip('gsdview.').lstrip(type_ + '.')
                #fullname = 'gsdview.%s.%s' % (type_, name)
                fullname = name

                if fullname in sys.modules:
                    self.plugins[name] = module = sys.modules[fullname]
                else:
                    loader = importer.find_module(name)
                    if not loader:
                        # search in standard path
                        loader = pkgutil.get_loader('numpy')
                    if loader:
                        module = loader.load_module(fullname)
                    else:
                        logger.warning('unable to find "%s" plugin' % name)
                        continue
                if not info_only:
                    try:
                        module.init(self._mainwin)
                        self.plugins[name] = module
                        logger.info('"%s" plugin loaded.' % name)
                    except Exception, e:   #AttributeError:
                        logger.warning('error loading "%s" plugin: %s' %
                                                                    (name, e))

    def unload(self, names, type_='plugin'):
        if isinstance(names, basestring):
            names = [names]
        for name in names:
            module = self.plugins.pop(name)
            module.close(self._mainwin)

    def reset(self):
        for name in self.plugins.keys():
            plugin = self.plugins.pop(name)
            plugin.close(self._mainwin)
        self.paths = []

    def save_settings(self, settings=None):
        if not settings:
            settings = self._mainwin.settings

        # @NOTE:  settings is expected to be a QSettings instance
        # @TODO: make it Qt independent
        settings.beginGroup('pluginmanager')
        try:
            settings.setValue('pluginspaths', QtCore.QVariant(self.paths))
            settings.setValue('autoload_plugins',
                              QtCore.QVariant(self.autoload))
            settings.setValue('available_plugins',
                              QtCore.QVariant(self.allplugins))
        finally:
            settings.endGroup()

    def load_settings(self, settings=None):
        # @NOTE:  settings is expected to be a QSettings instance
        # @TODO: make it Qt independent

        if not settings:
            settings = self._mainwin.settings

        settings.beginGroup('pluginmanager')
        try:
            if settings.contains('pluginspaths'):
                pluginspaths = settings.value('pluginspaths')
                self.paths = map(str, pluginspaths.toStringList())
            else:
                PLUGINSPATH = os.path.join(
                                    os.path.dirname(os.path.abspath(__file__)),
                                    'plugins')
                self.paths = [PLUGINSPATH]

            autoload_plugins = settings.value('autoload_plugins',
                                              QtCore.QVariant([]))
            self.autoload = map(str, autoload_plugins.toStringList())
            self.load(self.autoload)

            # @TODO: check
            # @NOTE: by default loads new plugins
            available_plugins = set(self.allplugins)

            old_plugins = settings.value('available_plugins',
                                         QtCore.QVariant([]))
            old_plugins = set(map(str, old_plugins.toStringList()))

            new_plugins = available_plugins.difference(old_plugins)

            self.load(list(new_plugins))
            self.autoload.extend(new_plugins)
        finally:
            settings.endGroup()

'''
    def setupPlugins(self):
        # @TODO: fix
        sys.path.insert(0, os.path.normpath(os.path.join(GSDVIEWROOT, os.pardir)))

        # @TODO: move to the PluginManager
        plugins = {}

        # load backends
        import gdalbackend
        gdalbackend.init(self)
        plugins['gdalbackend'] = gdalbackend
        _logger.debug('"gdalbackend" plugin loaded.')

        # @TODO: set from settings
        if getattr(sys, 'frozen', False):
            pluginsdir = os.path.join(os.path.dirname(sys.argv[0]), 'plugins')
        else:
            pluginsdir = os.path.join(os.path.dirname(__file__), 'plugins')

            # ensure that the gsdview package is in the PYTHONPATH
            dirname = os.path.dirname(__file__)
            dirname = os.path.join(dirname, os.path.pardir)
            sys.path.insert(0, dirname)

        _logger.debug('pluginsdir = %s' % pluginsdir)
        sys.path.insert(0, pluginsdir)

        pkgnames = []
        for pattern in ('*.py', '*.pyc', '*.pyo'):
            modules = [os.path.splitext(name)[0]
                                for name in glob.glob1(pluginsdir, pattern)
                                            if not name.startswith(('.', '_'))]
            pkgnames.extend(module for module in modules
                                                    if module not in pkgnames)

        #_logger.debug('modules: %s' % str(pkgnames))

        pkgnames.extend(name for name in os.listdir(pluginsdir)
                            if not name.startswith(('.', '_')) and
                                os.path.isdir(os.path.join(pluginsdir, name)))
        #_logger.debug('modules and packages: %s' % str(pkgnames))

        #~ try:
            #~ # @TODO: this require a huge fix
            #~ from setuptools import find_packages
            #~ from pkg_resources import find_distributions
            #~ eggs = [item for item in find_distributions(pluginsdir)]
            #~ for egg in eggs:
                #~ egg.activate()
            #~ pkgnames.extend(item.egg_name().split('_plugin')[0] for item in eggs)
            #~ _logger.debug('modules and eggs: %s' % str(pkgnames))
            #~ pkgnames.extend(name for name in find_packages(pluginsdir)
                                            #~ if not name.startswith(('.', '_')))
            #~ _logger.debug('modules, eggs and packages: %s' % str(pkgnames))
        #~ except ImportError:
            #~ pkgnames.extend(name for name in os.listdir(pluginsdir)
                                            #~ if not name.startswith(('.', '_')))
            #~ _logger.debug('modules and packages: %s' % str(pkgnames))

        for name in pkgnames:
            try:
                module = __import__(name)
                module.init(self)
                plugins[name] = module
                _logger.debug('"%s" plugin loaded.' % name)
            except (ImportError, AttributeError), e:
                #_logger.exception(name)
                _logger.debug('"%s" module not loaded: %s' % (name, e))
            except:
                #init with unknown error
                logging.getLogger('dialog').error(
                            'initialization error', exc_info=True)
        return plugins
'''


class PluginManagerGui(QtGui.QWidget):
    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'pluginmanager.ui')

    def __init__(self, pluginmanager, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QWidget.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)
        self.pluginmanager = pluginmanager

        # @TODO: check edit triggers
        #int(self.pathListWidget.editTriggers() & self.pathListWidget.DoubleClicked)

        tablewidget = self.pluginsTableWidget

        tablewidget.verticalHeader().setVisible(False)
        tablewidget.horizontalHeader().setStretchLastSection(True)

        self.connect(self.pathListWidget,
                     QtCore.SIGNAL('itemSelectionChanged()'),
                     self.pathSelectionChanged)

        self.connect(self.addButton, QtCore.SIGNAL('clicked()'),
                     self.addPathItem)
        self.connect(self.removeButton, QtCore.SIGNAL('clicked()'),
                     self.removePathItem)
        self.connect(self.upButton, QtCore.SIGNAL('clicked()'),
                     self.movePathItemsUp)
        self.connect(self.downButton, QtCore.SIGNAL('clicked()'),
                     self.movePathItemsDown)
        self.connect(self.editButton, QtCore.SIGNAL('clicked()'),
                     self.editPathItem)

    def pathSelectionChanged(self):
        enabled = bool(self.pathListWidget.selectedItems())
        self.editButton.setEnabled(enabled)
        self.removeButton.setEnabled(enabled)
        self.upButton.setEnabled(enabled)
        self.downButton.setEnabled(enabled)

    def addPathItem(self):
        filedialog = self.pluginmanager._mainwin.filedialog
        filedialog.setFileMode(filedialog.Directory)
        if(filedialog.exec_()):
            dirs = filedialog.selectedFiles()
            existingdirs = [str(self.pathListWidget.item(row).text())
                                for row in range(self.pathListWidget.count())]
            for dir_ in dirs:
                if dir_ not in existingdirs:
                    self.pathListWidget.addItem(dir_)

    def removePathItem(self):
        model = self.pathListWidget.model()
        for item in self.pathListWidget.selectedItems():
            model.removeRow(self.pathListWidget.row(item))

    def editPathItem(self):
        items = self.pathListWidget.selectedItems()
        if items:
            item = items[0]

            filedialog = self.pluginmanager._mainwin.filedialog
            filedialog.setFileMode(filedialog.Directory)
            filedialog.selectFile(item.text())
            if(filedialog.exec_()):
                dirs = filedialog.selectedFiles()
                if dirs:
                    dir_ = dirs[0]
                    item.setText(dir_)

    def _movePathItem(self, item, offset):
        if offset == 0:
            return

        listwidget = self.pathListWidget
        row = listwidget.row(item)

        if (row + offset) < 0:
            offset = -row
        elif (row + offset) >= listwidget.count():
            offset = listwidget.count() - 1 - row

        if offset == 0:
            return

        selected = item.isSelected()
        item = listwidget.takeItem(row)
        listwidget.insertItem(row + offset, item)
        item.setSelected(selected)

    def movePathItemsUp(self):
        selected = sorted(self.pathListWidget.selectedItems(),
                          key=self.pathListWidget.row)

        if self.pathListWidget.row(selected[0]) == 0:
            return

        for item in selected:
            self._movePathItem(item, -1)

    def movePathItemsDown(self):
        selected = sorted(self.pathListWidget.selectedItems(),
                          key=self.pathListWidget.row, reverse=True)

        if self.pathListWidget.row(selected[0]) == self.pathListWidget.count()-1:
            return

        for item in selected:
            self._movePathItem(item, 1)

    def update_view(self):
        self.pathListWidget.clear()

        for item in self.pluginmanager.paths:
            self.pathListWidget.addItem(item)

        self.pluginmanager.load(self.pluginmanager.allplugins, info_only=True)

        tablewidget = self.pluginsTableWidget
        tablewidget.clear()
        tablewidget.setRowCount(0)
        tablewidget.setHorizontalHeaderLabels([self.tr('Name'),
                                               self.tr('Description'),
                                               self.tr('Info'),
                                               self.tr('Active'),
                                               self.tr('Load on startup')])

        for plugin in self.pluginmanager.allplugins:
            try:
                name = sys.modules[plugin].name
                short_description = sys.modules[plugin].short_description
            except AttributeError, e:
                msg = str(e)
                if not "'name'" in msg and not  "'short_description'" in msg:
                    raise
            else:
                index = tablewidget.rowCount()
                tablewidget.insertRow(index)

                # name/description
                tablewidget.setItem(index, 0, QtGui.QTableWidgetItem(name))
                tablewidget.setItem(index, 1,
                                    QtGui.QTableWidgetItem(short_description))

                # info
                w = QtGui.QPushButton(QtGui.QIcon(':/info.svg'),
                                      '', # tablewidget.tr('Info'),
                                      tablewidget)
                tablewidget.setCellWidget(index, 2, w)
                w.connect(w, QtCore.SIGNAL('clicked()'),
                          lambda: self.showPluginInfo(index))
                w.setToolTip(w.tr('Show plugin info.'))
                w.setEnabled(False) # @TODO: remove

                # active
                w = QtGui.QCheckBox()
                tablewidget.setCellWidget(index, 3, w)
                w.setChecked(plugin in self.pluginmanager.plugins)
                # TODO: remove this block when plugins unloading will be
                #       available
                if w.isChecked():
                    w.setEnabled(False)

                # autoload
                w = QtGui.QCheckBox()
                tablewidget.setCellWidget(index, 4, w)
                w.setChecked(plugin in self.pluginmanager.autoload)
                w.setToolTip(w.tr('Load on startup'))
        tablewidget.resizeColumnsToContents()

    def load(self, settings=None):
        self.pluginmanager.load_settings(settings)
        self.update_view()

    def update_pluginmanager(self):
        paths = []
        for row in range(self.pathListWidget.count()):
            paths.append(str(self.pathListWidget.item(row).text()))
        self.pluginmanager.paths = paths

        tablewidget = self.pluginsTableWidget

        active = set()
        autoload = []
        for row in range(tablewidget.rowCount()):
            name = str(tablewidget.item(row, 0).text())
            if tablewidget.cellWidget(row, 3).isChecked():
                active.add(name)

            if tablewidget.cellWidget(row, 4).isChecked():
                autoload.append(name)

        toload = active.difference(self.pluginmanager.plugins)
        tounload = set(self.pluginmanager.plugins).difference(active)
        assert not set(toload).intersection(tounload)

        self.pluginmanager.load(toload)
        # TODO: do not allow backends unloading
        self.pluginmanager.unload(tounload)

        self.pluginmanager.autoload = autoload

    def save(self, settings=None):
        self.update_pluginmanager()
        self.pluginmanager.save_settings(settings)
