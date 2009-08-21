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

try:
    import pkg_resources
except ImportError:
    logging.getLogger(__name__).debug('"pkg_resources" not found.')

from gsdview.utils import getresource   # @TODO: check dependency


class PluginManager(object):

    def __init__(self, mainwin, syspath=None):
        super(PluginManager, self).__init__()
        self.paths = []
        self.syspath = syspath
        self.plugins = {}
        self.autoload = []
        self._mainwin = mainwin

    def _get_allplugins(self):
        plugins = set(self.plugins.keys())
        plugins.update(self._scanpaths())

        return sorted(plugins)

    allplugins = property(_get_allplugins, doc='List of all availabe plugins.')

    def _scanpaths(self):
        if not self.paths:
            return []

        plugins = []
        for loader, name, ispkg in pkgutil.iter_modules(self.paths):
            if name.startswith('_'):
                continue
            plugins.append(name)

        for path in self.paths:
            try:
                for egg in pkg_resources.find_distributions(path):
                    if egg.egg_name().startswith('_'):
                        continue
                    plugins.append(egg.key)
            except NameError:
                pass

        return plugins

    def load_module(self, module, name=None):
        logger = logging.getLogger('gsdview')

        if not name:
            name = module.__name__

        try:
            module.init(self._mainwin)
            self.plugins[name] = module
            logger.info('"%s" plugin loaded.' % name)
        except Exception, e:   #AttributeError:
            logger.warning('error loading "%s" plugin: %s' %
                                                        (name, e))

    def load(self, names, paths=None, info_only=False, type_='plugins'):
        if paths is None:
            paths = self.paths
        elif isinstance(paths, basestring):
            paths = [paths]

        if not paths:
            paths = []
            if self.syspath:
                paths.append(self.syspath)

        logger = logging.getLogger('gsdview')
        for path in paths:
            importer = pkgutil.get_importer(path)
            try:
                distributions = pkg_resources.find_distributions(path)
                distributions = dict((egg.key, egg) for egg in distributions)
            except NameError:
                distributions = {}

            if isinstance(names, basestring):
                names = [names]

            for name in names:
                if name in self.plugins:
                    continue

                if name in sys.modules:
                    module = sys.modules[name]
                else:
                    try:
                        loader = importer.find_module(name)
                        if loader:
                            module = loader.load_module(name)
                        elif name in distributions:
                            egg = distributions[name]
                            egg.activate()
                            module = __import__(name)
                        else:
                            logger.warning('unable to find "%s" plugin' % name)
                            continue
                    except ImportError, e:
                        logger.warning('unable to import "%s" plugin: %s' %
                                                                    (name, e))
                        continue

                if not info_only:
                    self.load_module(module, name)

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

        # @NOTE: settings is expected to be a QSettings instance
        # @TODO: make it Qt independent
        settings.beginGroup('pluginmanager')
        try:
            paths = list(self.paths)    # @NOTE: copy
            if self.syspath in paths:
                paths.remove(self.syspath)
            settings.setValue('pluginspaths', QtCore.QVariant(paths))

            autoload = set(self.autoload)
            autoload = list(autoload.intersection(self.allplugins))
            settings.setValue('autoload_plugins',
                              QtCore.QVariant(autoload))

            settings.setValue('available_plugins',
                              QtCore.QVariant(self.allplugins))
        finally:
            settings.endGroup()

    def load_settings(self, settings=None):
        # @NOTE: settings is expected to be a QSettings instance
        # @TODO: make it Qt independent

        if not settings:
            settings = self._mainwin.settings

        settings.beginGroup('pluginmanager')
        try:
            if settings.contains('pluginspaths'):
                pluginspaths = settings.value('pluginspaths')
                self.paths = map(str, pluginspaths.toStringList())
            if self.syspath and not self.syspath in self.paths:
                self.paths.append(self.syspath)

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
            # only marks actually loaded plugins
            new_plugins.intersection_update(self.plugins)
            self.autoload.extend(new_plugins)
        finally:
            settings.endGroup()


class PluginManagerGui(QtGui.QWidget):
    uifile = getresource(os.path.join('ui', 'pluginmanager.ui'), __name__)

    def __init__(self, pluginmanager, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QWidget.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

        # Set icons
        iconfile = getresource(os.path.join('images', 'add.svg'))
        self.addButton.setIcon(QtGui.QIcon(iconfile))
        iconfile = getresource(os.path.join('images', 'remove.svg'))
        self.removeButton.setIcon(QtGui.QIcon(iconfile))
        iconfile = getresource(os.path.join('images', 'edit.svg'))
        self.editButton.setIcon(QtGui.QIcon(iconfile))
        iconfile = getresource(os.path.join('images', 'go-up.svg'))
        self.upButton.setIcon(QtGui.QIcon(iconfile))
        iconfile = getresource(os.path.join('images', 'go-down.svg'))
        self.downButton.setIcon(QtGui.QIcon(iconfile))

        # Set plugin manager attribute
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
            name = plugin
            short_description = tablewidget.tr('NOT AVAILABLE')
            disabled = False
            for dict_ in (self.pluginmanager.plugins, sys.modules):
                try:
                    module = dict_[name]
                    name = module.name
                    short_description = module.short_description
                    break
                except AttributeError, e:
                    msg = str(e)
                    if not "'name'" in msg and not  "'short_description'" in msg:
                        raise
                    disabled = True
                except KeyError:
                    disabled = True

            index = tablewidget.rowCount()
            tablewidget.insertRow(index)

            # name/description
            tablewidget.setItem(index, 0, QtGui.QTableWidgetItem(name))
            tablewidget.setItem(index, 1,
                                QtGui.QTableWidgetItem(short_description))

            # info
            icon = QtGui.QIcon(getresource('images/info.svg', __name__))
            w = QtGui.QPushButton(icon, '', tablewidget)
            tablewidget.setCellWidget(index, 2, w)
            w.connect(w, QtCore.SIGNAL('clicked()'),
                      lambda index=index: self.showPluginInfo(index))
            w.setToolTip(w.tr('Show plugin info.'))

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

            if disabled:
                for col in range(tablewidget.columnCount()):
                    item = tablewidget.item(index, col)
                    if item:
                        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEnabled)
                        msg = tablewidget.tr("Plugin don't seems to be "
                                             "compatible with GSDView.")
                        item.setToolTip(msg)
                    else:
                        w = tablewidget.cellWidget(index, col)
                        w.setEnabled(False)
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

    def showPluginInfo(self, index):
        item = self.pluginsTableWidget.item(index, 0)
        name = str(item.text())
        try:
            plugin = self.pluginmanager.plugins[name]
            active = True
        except KeyError:
            active = False
            try:
                plugin = sys.modules[name]
            except KetError:
                return

        d = PluginInfoDialog(plugin, active)
        d.exec_()


class PluginInfoForm(QtGui.QFrame):
    uifile = getresource(os.path.join('ui', 'plugininfo.ui'), __name__)

    def __init__(self, plugin=None, active=None, parent=None,
                 flags=QtCore.Qt.Widget):
        QtGui.QFrame.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)
        if plugin is not None and active is not None:
            self.loadinfo(plugin, active)
        else:
            self.clear()

    def loadinfo(self, plugin, active):
        self.nameValue.setText(plugin.name.capitalize())
        self.descriptionValue.setText(plugin.description)

        self.authorValue.setText(plugin.author)
        self.emailValue.setText(
                '&lt;<a href="mailto:%(email)s">%(email)s</a>&gt;' %
                                            dict(email=plugin.author_email))
        self.versionValue.setText(plugin.version)
        self.revisionValue.setText(plugin.__revision__)
        self.licenseValue.setText(plugin.license_type)
        self.copyrightValue.setText(plugin.copyright)
        self.websiteValue.setText('<a href="%s">%s</a>' %
                                        (plugin.website, plugin.website_label))

        fullpath = plugin.__file__
        if fullpath.endswith('.pyc') or fullpath.endswith('.pyo'):
            fullpath = fullpath.rstrip('co')

        s = '%s__init__.py' % os.sep
        if fullpath.endswith(s):
            fullpath = fullpath[:-len(s)]

        self.fullPathValue.setText(fullpath)
        self.loadedCheckBox.setChecked(active)


    def clear(self):
        self.nameValue.setText('')
        self.descriptionValue.setText('')

        self.authorValue.setText('')
        self.emailValue.setText('')
        self.versionValue.setText('')
        self.revisionValue.setText('')
        self.licenseValue.setText('')
        self.copyrightValue.setText('')
        self.websiteValue.setText('')

        self.fullPathValue.setText('')
        self.loadedCheckBox.setChecked(False)


class PluginInfoDialog(QtGui.QDialog):

    def __init__(self, plugin, active, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QDialog.__init__(self, parent, flags)
        self.setModal(True)

        bbox = QtGui.QDialogButtonBox()
        bbox.addButton(bbox.Close)
        b = bbox.button(bbox.Close)
        b.connect(b, QtCore.SIGNAL('clicked()'), self.accept)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(PluginInfoForm(plugin, active))
        layout.addWidget(bbox)
        self.setLayout(layout)
