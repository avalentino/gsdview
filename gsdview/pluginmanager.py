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

from PyQt4 import QtCore    # @TODO: move Qt specific implementation elsewhere


class PluginManager(object):
    def __init__(self, mainwin):
        super(PluginManager, self).__init__()
        self.paths = []
        self.plugins = {}
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

    def load(self, names, paths=None, type_='plugins'):
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

                fullname = name.lstrip('gsdview.').lstrip(type_ + '.')
                fullname = 'gsdview.%s.%s' % (type_, name)

                if fullname in sys.modules:
                    self.plugins[name] = sys.modules[fullname]
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
                try:
                    module.init(self._mainwin)
                    self.plugins[name] = module
                    logger.info('"%s" plugin loaded.' % name)
                except Exception, e:   #AttributeError:
                    logger.warning('error loading "%s" plugin: %s' % (name, e))


    #~ def unload(self, names, type_='plugin'):
        #~ module = self.plugins.pop(name)
        #~ module.close(self._mainwin)

    def reset(self):
        for name in self.plugins.keys():
            plugin = self.plugins.pop(name)
            plugin.close(self._mainwin)
        self.paths = []

    def save_settings(self, settings):
        # @NOTE:  settings is expected to be a QSettings instance
        # @TODO: make it Qt independent
        settings.beginGroup('pluginmanager')
        try:
            settings.setValue('pluginspaths', QtCore.QVariant(self.paths))
            settings.setValue('active_plugins',
                              QtCore.QVariant(list(self.plugins.keys())))
            settings.setValue('available_plugins',
                              QtCore.QVariant(self.allplugins))
        finally:
            settings.endGroup()

    def load_settings(self, settings):
        # @NOTE:  settings is expected to be a QSettings instance
        # @TODO: make it Qt independent
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

            active_plugins = settings.value('active_plugins',
                                            QtCore.QVariant([]))
            active_plugins = map(str, active_plugins.toStringList())
            self.load(active_plugins)

            # @TODO: check
            # @NOTE: by default loads new plugins
            available_plugins = set(self.allplugins)

            old_plugins = settings.value('available_plugins',
                                         QtCore.QVariant([]))
            old_plugins = set(map(str, old_plugins.toStringList()))

            new_plugins = available_plugins.difference(old_plugins)

            self.load(list(new_plugins))
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
