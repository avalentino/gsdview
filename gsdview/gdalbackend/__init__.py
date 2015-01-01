# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2015 Antonio Valentino <antonio.valentino@tiscali.it>
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


'''GDAL backend for GSDView.'''


from gsdview.gdalbackend.info import *
from gsdview.gdalbackend.info import __version__, __requires__
from gsdview.gdalbackend.core import GDALBackend


__all__ = [
    'init', 'close', 'loadSettings', 'saveSettings',
    'name', 'version', 'short_description', 'description',
    'author', 'author_email', 'copyright', 'license_type',
    'website', 'website_label', 'getUseExceptions',
    'UseExceptions', 'DontUseExceptions',
    'openFile', 'openImageView', 'newImageView', 'openItemMatadataView',
    'openRGBImageView', 'openSubDataset', 'closeCurrentItem',
    'findItemFromFilename', 'itemActions', 'itemContextMenu',
]

UseExceptions = GDALBackend.UseExceptions
DontUseExceptions = GDALBackend.DontUseExceptions
getUseExceptions = GDALBackend.getUseExceptions

_backendobj = None


def init(app):
    import os
    import sys

    from osgeo import gdal

    from gsdview import utils
    from gsdview import qtsupport

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
    icon = qtsupport.geticon('GDALLogoColor.svg', __name__)

    # update the settings dialog
    #page = widgets.GDALPreferencesPage(app.preferencesdialog)
    page = widgets.BackendPreferencesPage(app.preferencesdialog)
    app.preferencesdialog.addPage(page, icon, 'GDAL')

    # add a new page in the about dialog
    page = widgets.GDALInfoWidget(app.aboutdialog)
    tabindex = app.aboutdialog.tabWidget.addTab(page, icon, 'GDAL')
    widget = app.aboutdialog.tabWidget.widget(tabindex)
    widget.setObjectName('gdalTab')

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
        #    QtWidgets.QMessageBox.warning(app, app.tr('WARNING'), msg)
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
                logging.info('GDAL binary path added to system path: '
                             '%s' % binpath)
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
    if methodname not in globals_ and methodname in GDALBackend.__dict__:
        globals_[methodname] = _definefunc(methodname)
del methodname, globals_, _definefunc


def close(app):
    saveSettings(app.settings)


def loadSettings(settings):
    if _backendobj:
        return _backendobj.loadSettings(settings)


def saveSettings(settings):
    if _backendobj:
        return _backendobj.saveSettings(settings)
