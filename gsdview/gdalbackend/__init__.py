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


'''GDAL backend for GSDView.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'

__all__ = ['init', 'close', 'loadSettings', 'saveSettings',
           'name','version', 'short_description','description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label', 'getUseExceptions',
           'UseExceptions', 'DontUseExceptions',
           'openFile', 'openImageView', 'newImageView', 'openItemMatadataView',
           'openRGBImageView', 'openSubDataset', 'closeItem',
           'findItemFromFilename', 'itemActions', 'itemContextMenu',
]

# @TODO: should use absolute imports (from gsdview.gdalbackend import something)
from info import *
from info import __version__, __requires__
from core import GDALBackend

UseExceptions = GDALBackend.UseExceptions
DontUseExceptions = GDALBackend.DontUseExceptions
getUseExceptions = GDALBackend.getUseExceptions

_backendobj = None

def init(app):
    import os
    import sys

    from osgeo import gdal

    from gsdview import utils
    from gsdview import qt4support

    from gsdview.gdalbackend import widgets
    from gsdview.gdalbackend import gdalsupport

    # @TODO: check
    #UseExceptions()

    # set file dialog filters
    app.filedialog.setNameFilters(gdalsupport.gdalFilters())

    # update versions info in about dialog
    app.aboutdialog.addSoftwareVersion('GDAL',
                                        gdal.VersionInfo('RELEASE_NAME'),
                                        'http://www.gdal.org')

    # GDAL icon
    icon = qt4support.geticon('GDALLogoColor.svg', __name__)

    # add a new page in the about dialog
    page = widgets.GDALInfoWidget(app.aboutdialog)
    tabindex = app.aboutdialog.tabWidget.addTab(page, icon, 'GDAL')
    widget = app.aboutdialog.tabWidget.widget(tabindex)
    widget.setObjectName('gdalTab')

    # update the settings dialog
    page = widgets.GDALPreferencesPage(app.preferencesdialog)
    app.preferencesdialog.addPage(page, icon, 'GDAL')

    # @TODO: check
    # register the backend
    app.backends.append(name)

    global _backendobj
    _backendobj = GDALBackend(app)

    # @TODO: fix
    #~ gdal.SetConfigOption('GDAL_PAM_ENABLED', 'YES')
    #~ gdal.SetConfigOption('GDAL_PAM_PROXY_DIR',
                         #~ os.path.expanduser(os.path.join('~', '.gsdview',
                                                         #~ 'cache')))
    # @TODO: fix
    # @NOTE: explicitly disable GDAL exceptions due to bug #3077
    #        (http://trac.osgeo.org/gdal/ticket/3077)
    #UseExceptions()
    DontUseExceptions()

    # Fix path for GDAL tools
    if getattr(sys, 'frozen', False):
        from gsdview import appsite
        os.environ['PATH'] = os.pathsep.join((appsite.GSDVIEWROOT,
                                              os.getenv('PATH', '')))
        gdal.SetConfigOption('GDAL_DATA',
                             os.path.join(appsite.GSDVIEWROOT, 'data'))
        # @TODO: check
        #if app.settings.value('GDAL_DATA').isValid():
        #    msg = app.tr('"GDAL_DATA" from the user configuration file '
        #                     'overrides the default value')
        #    QtGui.QMessageBox.warning(app, app.tr('WARNING'), msg)
    elif sys.platform == 'darwin':
        gdaladdobin = utils.which('gdaladdo')
        if not gdaladdobin:
            frameworkroot = os.path.join(os.path.dirname(gdal.__file__),
                                         os.pardir, os.pardir, os.pardir)
            frameworkroot = os.path.abspath(frameworkroot)
            binpath = os.path.join(frameworkroot, 'unix', 'bin')
            PATH = os.getenv('PATH', '')
            if binpath not in PATH:
                PATH = os.pathsep.join((binpath, PATH))
                os.environ['PATH'] = PATH

                import logging
                logging.info('GDAL binary path added to system path: %s' %
                                                                        binpath)
    #elif sys.platform[:3] == 'win':
    #    gdaladdobin = utils.which('gdaladdo')
    #    if not gdaladdobin:
    #        pass

    return _backendobj


def _definefunc(methodname):
    def func(*args, **kwargs):
        if _backendobj is None:
            raise RuntimeError('GDAL backend is still not initialized')
        return getattr(_backendobj, methodname)(*args, **kwargs)
    func.__name__ = methodname
    return func


# @TODO: check (maybe it is better to make it explicitly)
globals_ = globals()
for methodname in __all__:
    if not methodname in globals_ and methodname in GDALBackend.__dict__:
        globals_[methodname] = _definefunc(methodname)
del methodname, globals_, _definefunc


def close(app):
    saveSettings(app.settings)


def loadSettings(settings):
    import os
    import logging

    from osgeo import gdal

    settings.beginGroup('gdal')
    try:
        cachesize, ok = settings.value('GDAL_CACHEMAX').toULongLong()
        if ok:
            gdal.SetCacheMax(cachesize)
            logging.debug('GDAL cache size det to %d' % cachesize)

        value = settings.value('GDAL_DATA').toString()
        if value:
            value = os.path.expanduser(os.path.expandvars(str(value)))
            gdal.SetConfigOption('GDAL_DATA', value)
            logging.debug('GDAL_DATA directory set to "%s"' % value)

        for optname in ('GDAL_SKIP', 'GDAL_DRIVER_PATH', 'OGR_DRIVER_PATH'):
            value = settings.value(optname).toString()
            value = os.path.expanduser(os.path.expandvars(str(value)))
            gdal.SetConfigOption(optname, value)
            logging.debug('%s set to "%s"' % (optname, value))
        gdal.AllRegister()
        logging.debug('run "gdal.AllRegister()"')

        # update the about dialog
        tabWidget = _backendobj._app.aboutdialog.tabWidget
        for index in range(tabWidget.count()):
            if tabWidget.tabText(index) == 'GDAL':
                gdalinfowidget = tabWidget.widget(index)
                gdalinfowidget.setGdalDriversTab()
                break
        else:
            _backendobj._app.logger.debug('GDAL page ot found in the '
                                          'about dialog')
            return
    finally:
        settings.endGroup()


def saveSettings(settings):
    # @NOTE: GDAL preferences are only modified via preferences dialog
    pass

