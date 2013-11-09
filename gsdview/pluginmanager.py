# -*- coding: utf-8 -*-

### Copyright (C) 2008-2013 Antonio Valentino <a_valentino@users.sf.net>

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


'''Plugin manager.'''


import os
import sys
import pkgutil
import logging
from distutils.versionpredicate import VersionPredicate

try:
    import pkg_resources
except ImportError:
    logging.getLogger(__name__).debug('"pkg_resources" not found.')


class PluginManager(object):
    def __init__(self, app, syspath=None):
        super(PluginManager, self).__init__()
        self.paths = []
        self.syspath = syspath
        self.plugins = {}
        self.autoload = []
        self._app = app

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

    def _check_dependency(self, depstring):
        # @TODO: use pkg_resources' parse_requirements and Requirement
        #        if available:
        #           for r in parse_requirements('gsdview >= 0.5'):
        #               return r.key in self.plugins and avail_ver in r

        depstring = depstring.strip()
        if not depstring:
            return True

        modules = dict(self.plugins)

        # @TODO: use a cleaner way to provide extra modules for check
        #import gsdview
        #modules['gsdview'] = gsdview

        try:
            vp = VersionPredicate(depstring)
        except ValueError as e:
            # @TODO: remove dependency from self._app
            self._app.logger.error('invalid version preficate "%s": %s' % (
                                                                depstring, e))
            return False

        if vp.name in modules:
            try:
                return vp.satisfied_by(modules[vp.name].version)
            except ValueError as e:
                logging.warning(str(e))  # , exc_info=True)
                return False
        else:
            return False

    def _check_deps(self, module):
        try:
            for depstring in module.__requires__:
                if not self._check_dependency(depstring):
                    return False
        except Exception:
            logger = logging.getLogger('gsdview')
            logger.error('error checking dependencies for module: %s' % module)
            raise
        return True

    def load_module(self, module, name=None):
        # @TODO: make the module independent from gsdview
        logger = logging.getLogger('gsdview')

        if not name:
            name = module.__name__

        try:
            # @TODO: find a more general form to pass arguments to plugins
            module.init(self._app)
            self.plugins[name] = module
            logger.info('"%s" plugin loaded.' % name)
        except Exception as e:   # AttributeError:
            logger.warning('error loading "%s" plugin: %s' % (name, e))

    # @WARNING: (pychecker) Parameter (type_) not used
    def load(self, names, paths=None, info_only=False, type_='plugins'):
        if paths is None:
            paths = self.paths
        elif isinstance(paths, basestring):
            paths = [paths]

        if not paths:
            paths = []
            if self.syspath:
                paths.append(self.syspath)

        if names is None:
            names = []
        elif isinstance(names, basestring):
            names = [names]

        # @TODO: make the module independent from gsdview
        logger = logging.getLogger('gsdview')
        delayed = {}
        for path in paths:
            importer = pkgutil.get_importer(path)
            try:
                distributions = pkg_resources.find_distributions(path)
                distributions = dict((egg.key, egg) for egg in distributions)
            except NameError:
                distributions = {}

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
                    except ImportError as e:
                        logger.warning('unable to import "%s" plugin: %s' %
                                                                    (name, e))
                        continue

                if not info_only:
                    if not self._check_deps(module):
                        delayed[name] = module
                        logging.info('loading of "%s" plugin delayed' %
                                                                module.name)
                    else:
                        self.load_module(module, name)

        # @TODO: delayed loading
        if delayed and not info_only:
            MAXATTEMPTS = 10
            delayed_again = delayed
            iter_count = 0
            loaded_count = None
            while delayed_again and loaded_count != 0:
                # check for max number of iterations
                if iter_count > MAXATTEMPTS:
                    logger.warning('max number of attempts reached for '
                                   'delayed plugins loading')
                    break
                else:
                    iter_count += 1

                loaded_count = 0
                delayed = delayed_again
                delayed_again = {}

                for name, module in delayed.iteritems():
                    if not self._check_deps(module):
                        delayed_again[name] = module
                        logging.debug('loading of "%s" plugin delayed '
                                      'again' % name)

                    else:
                        self.load_module(module, name)
                        loaded_count += 1
            if len(delayed_again):
                logger.info('%d modules not loaded because of unmet '
                            'dependency' % len(delayed_again))

                # @TODO: log more verbose info: per module dependency failure

    # @WARNING: (pychecker) Parameter (type_) not used
    def unload(self, names, type_='plugin'):
        if isinstance(names, basestring):
            names = [names]
        for name in names:
            module = self.plugins.pop(name)
            # @TODO: find a more general form to pass arguments to plugins
            module.close(self._app)

    def reset(self):
        # the dictionary is modified during the iteration so the iteration
        # have to be performed on a concrete list
        for name in self.plugins.keys():
            plugin = self.plugins.pop(name)
            # @TODO: find a more general form to pass arguments to plugins
            plugin.close(self._app)
        self.paths = []

    # @NOTE: this method is Qt specific
    # @TODO: move to specialized classes implementations that rely on a
    #        specific external library
    def save_settings(self, settings):
        settings.beginGroup('pluginmanager')
        try:
            paths = list(self.paths)    # @NOTE: copy
            if self.syspath in paths:
                paths.remove(self.syspath)
            settings.setValue('pluginspaths', paths)

            autoload = set(self.autoload)
            autoload = list(autoload.intersection(self.allplugins))
            settings.setValue('autoload_plugins', autoload)

            settings.setValue('available_plugins', self.allplugins)
        finally:
            settings.endGroup()

    # @NOTE: this method is Qt specific
    # @TODO: move to specialized classes implementations that rely on a
    #        specific external library
    def load_settings(self, settings):
        settings.beginGroup('pluginmanager')
        try:
            paths = settings.value('pluginspaths')

            if paths is not None:
                self.paths = paths

            if self.syspath and not self.syspath in self.paths:
                self.paths.append(self.syspath)

            self.autoload = settings.value('autoload_plugins', [])
            if self.autoload is None:
                self.autoload = []

            self.load(self.autoload)

            # @TODO: check
            # @NOTE: by default loads new plugins
            available_plugins = set(self.allplugins)

            old_plugins = settings.value('available_plugins', [])
            new_plugins = available_plugins.difference(old_plugins)

            self.load(list(new_plugins))
            # only marks actually loaded plugins
            new_plugins.intersection_update(self.plugins)
            self.autoload.extend(new_plugins)
        finally:
            settings.endGroup()


### GUI #######################################################################

# @TODO: move Qt specific implementation elsewhere
import functools

from qt import QtCore, QtGui

# @TODO: check dependency - getuiform, geticon, setViewContextActions
from gsdview import qt4support


PluginManagerGuiBase = qt4support.getuiform('pluginmanager', __name__)


class PluginManagerGui(QtGui.QWidget, PluginManagerGuiBase):

    # @TODO: emit signal for ???

    def __init__(self, pluginmanager, parent=None,
                 flags=QtCore.Qt.WindowFlags(0), **kwargs):
        super(PluginManagerGui, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

        # Set icons
        geticon = qt4support.geticon
        self.addButton.setIcon(geticon('add.svg', __name__))
        self.removeButton.setIcon(geticon('remove.svg', __name__))
        self.editButton.setIcon(geticon('edit.svg', __name__))
        self.upButton.setIcon(geticon('go-up.svg', __name__))
        self.downButton.setIcon(geticon('go-down.svg', __name__))

        # Set plugin manager attribute
        self.pluginmanager = pluginmanager

        # Context menu
        qt4support.setViewContextActions(self.pathListWidget)
        qt4support.setViewContextActions(self.pluginsTableWidget)

        # @TODO: check edit triggers
        #int(self.pathListWidget.editTriggers() &
        #                                   self.pathListWidget.DoubleClicked)

        self.pathListWidget.itemSelectionChanged.connect(
                                        self.pathSelectionChanged)

        self.addButton.clicked.connect(self.addPathItem)
        self.removeButton.clicked.connect(self.removeSelectedPathItem)
        self.upButton.clicked.connect(self.moveSelectedPathItemsUp)
        self.downButton.clicked.connect(self.moveSelectedPathItemsDown)
        self.editButton.clicked.connect(self.editSelectedPathItem)

    @QtCore.Slot()
    def pathSelectionChanged(self):
        enabled = bool(self.pathListWidget.selectedItems())
        self.editButton.setEnabled(enabled)
        self.removeButton.setEnabled(enabled)
        self.upButton.setEnabled(enabled)
        self.downButton.setEnabled(enabled)

    @QtCore.Slot()
    def addPathItem(self):
        # @TODO: don't directly use _app attribute
        filedialog = self.pluginmanager._app.filedialog
        filedialog.setFileMode(filedialog.Directory)
        if(filedialog.exec_()):
            dirs = filedialog.selectedFiles()
            existingdirs = [str(self.pathListWidget.item(row).text())
                                for row in range(self.pathListWidget.count())]
            for dir_ in dirs:
                if dir_ not in existingdirs:
                    self.pathListWidget.addItem(dir_)

    @QtCore.Slot()
    def removeSelectedPathItem(self):
        model = self.pathListWidget.model()
        for item in self.pathListWidget.selectedItems():
            model.removeRow(self.pathListWidget.row(item))

    @QtCore.Slot()
    def editSelectedPathItem(self):
        items = self.pathListWidget.selectedItems()
        if items:
            item = items[0]

            # @TODO: don't directly use _app attribute
            filedialog = self.pluginmanager._app.filedialog
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

    @QtCore.Slot()
    def moveSelectedPathItemsUp(self):
        selected = sorted(self.pathListWidget.selectedItems(),
                          key=self.pathListWidget.row)

        if self.pathListWidget.row(selected[0]) == 0:
            return

        for item in selected:
            self._movePathItem(item, -1)

    @QtCore.Slot()
    def moveSelectedPathItemsDown(self):
        selected = sorted(self.pathListWidget.selectedItems(),
                          key=self.pathListWidget.row, reverse=True)

        if (self.pathListWidget.row(selected[0]) ==
                                            self.pathListWidget.count() - 1):
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
                except AttributeError as e:
                    msg = str(e)
                    if (not "'name'" in msg
                                    and not  "'short_description'" in msg):
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
            icon = qt4support.geticon('info.svg', __name__)
            w = QtGui.QPushButton(icon, '', tablewidget,
                                  toolTip=self.tr('Show plugin info.'),
                                  clicked=functools.partial(
                                                self.showPluginInfo, index))
                                  #clicked=lambda index=index:
                                  #              self.showPluginInfo(index))
            tablewidget.setCellWidget(index, 2, w)

            # active
            checked = bool(plugin in self.pluginmanager.plugins)
            w = QtGui.QCheckBox(tablewidget, checked=checked)
            tablewidget.setCellWidget(index, 3, w)

            # TODO: remove this block when plugins unloading will be
            #       available
            if w.isChecked():
                w.setEnabled(False)

            # autoload
            checked = bool(plugin in self.pluginmanager.autoload)
            w = QtGui.QCheckBox(tablewidget, checked=checked,
                                toolTip=self.tr('Load on startup'))
            tablewidget.setCellWidget(index, 4, w)

            if disabled:
                for col in range(tablewidget.columnCount() - 1):
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

    def load(self, settings):
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

    def save(self, settings):
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
            except KeyError:
                return

        d = PluginInfoDialog(plugin, active)
        d.exec_()


PluginInfoFormBase = qt4support.getuiform('plugininfo', __name__)


class PluginInfoForm(QtGui.QFrame, PluginInfoFormBase):

    def __init__(self, plugin=None, active=None, parent=None,
                 flags=QtCore.Qt.WindowFlags(0), **kwargs):
        super(PluginInfoForm, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

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

    def __init__(self, plugin, active, parent=None,
                 flags=QtCore.Qt.WindowFlags(0), **kwargs):
        super(PluginInfoDialog, self).__init__(parent, flags, **kwargs)
        self.setModal(True)

        bbox = QtGui.QDialogButtonBox()
        bbox.addButton(bbox.Close)
        b = bbox.button(bbox.Close)
        b.clicked.connect(self.accept)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(PluginInfoForm(plugin, active))
        layout.addWidget(bbox)
        self.setLayout(layout)
