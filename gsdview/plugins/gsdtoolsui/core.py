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


"""UI front-end for GSDTools."""


import os
import sys
import shutil
import logging
import tempfile

from qtpy import QtCore, QtWidgets, QtGui
import numpy as np

from gsdview import utils
from gsdview import qtsupport
from gsdtools import ras2vec

from . import info


_log = logging.getLogger(__name__)


class GSDToolsController(QtCore.QObject):
    def __init__(self, app, **kwargs):
        super(GSDToolsController, self).__init__(app, **kwargs)
        self.app = app

        self.googleearth = None
        self.actions = self._setupActions()
        self.actions.setEnabled(False)
        app.mdiarea.subWindowActivated.connect(self.onSubWindowChanged)
        # app.subWindowClosed.connect(self.onSubWindowChanged)
        # app.treeview.clicked.connect(self.onItemChanged)
        # app.treeview.selectionModel().selectionChanged(
        #    self.self.onItemChanged)
        # ##void currentChanged(const QModelIndex& current,
        # ##                    const QModelIndex& previous)

    def _googleEarthBin(self):
        pass

    def _setupActions(self):
        actions = QtWidgets.QActionGroup(self)

        # KML export
        icon = qtsupport.geticon('area.svg', 'gsdview')
        QtWidgets.QAction(
            icon, self.tr('KML export'), actions,
            objectName='kmlExportAction',
            statusTip=self.tr('KML export'),
            triggered=self.exportKML)

        # Open in google earth
        icon = qtsupport.geticon('earth.svg', __name__)
        QtWidgets.QAction(
            icon, self.tr('Open in Google Earth'), actions,
            objectName='openInGoogleEarthAction',
            statusTip=self.tr('Open in Google Earth'),
            triggered=self.openInGoogleEarth)

        # Open in google maps
        icon = qtsupport.geticon('overview.svg', 'gsdview.gdalbackend')
        QtWidgets.QAction(
            icon, self.tr('Open in Google Maps'), actions,
            objectName='openInGoogleMapsAction',
            statusTip=self.tr('Open in Google Maps'),
            triggered=self.openInGoogleMaps)

        return actions

    def loadSettings(self, settings):
        settings.beginGroup('plugins/%s' % info.name)
        try:
            googleearth = settings.value('google_earth_path')
            if not googleearth:
                if sys.platform.startswith('win'):
                    googleearth = shutil.which('googleearth.exe')
                else:
                    for name in ('googleearth', 'google-earth'):
                        googleearth = shutil.which(name)
                        if googleearth:
                            break

            action = self.actions.findChild(QtWidgets.QAction,
                                            'openInGoogleEarthAction')
            if googleearth:
                self.googleearth = googleearth
                action.setEnabled(True)
            else:
                self.googleearth = None
                action.setEnabled(False)
        finally:
            settings.endGroup()

    def saveSettings(self, settings):
        pass

    def _currentDatasetItem(self, subwin=None):
        if subwin is None:
            subwin = self.app.mdiarea.activeSubWindow()

        try:
            item = subwin.item
        except AttributeError:
            item = None
        else:
            item = self.app.currentItem()

        while item and not hasattr(item, 'filename'):
            item = item.parent()

        return item

    @QtCore.Slot()
    def exportKML(self):
        item = self._currentDatasetItem()

        if item is None:
            _log.info('no item to export.')
            QtWidgets.QMessageBox.information(
                self.app, self.tr('Information'),
                self.tr('No item to export.'))
            return

        src = item.filename
        filters = [
            'KML files (*.kml)',
            'All files (*)',
        ]
        target = os.path.basename(src)
        target = os.path.splitext(target)[0] + '.kml'
        target = os.path.join(utils.default_workdir(), target)

        dst, filter_ = QtWidgets.QFileDialog.getSaveFileName(
            self.app, self.tr('Save KML'), target, ';;'.join(filters))

        dst = str(dst)

        if dst:
            try:
                ras2vec.export_raster(src, dst, boxlayer='box',
                                      gcplayer='GCPs', mark_corners=True)
            except (OSError, RuntimeError):
                # @TODO: QtWidgets.QMessageBox.error(...)
                _log.error('unable to export "%s" to "%s".', src, dst)

    @QtCore.Slot()
    def openInGoogleEarth(self):
        item = self._currentDatasetItem()

        if item is None:
            _log.info('no item selected.')
            QtWidgets.QMessageBox.information(
                self.app, self.tr('Information'),
                self.tr('No item selected.'))
            return

        src = item.filename
        prefix = os.path.splitext(os.path.basename(src))[0]
        prefix = 'gsdview_ras2vec_%s_' % prefix
        _, dst = tempfile.mkstemp('.kml', prefix)

        try:
            ras2vec.export_raster(src, dst, boxlayer='box', gcplayer='GCPs',
                                  mark_corners=True)
        except (OSError, RuntimeError):
            # @TODO: QtWidgets.QMessageBox.error(...)
            _log.error('unable to export "%s" to "%s".', src, dst)

        # success = QtCore.QProcess.startDetached(self.googleearth, [dst])
        _log.info('GoogleEarth: %s', self.googleearth)
        _log.info('KML: %s', dst)
        success = QtCore.QProcess.startDetached(
            'sh', [self.googleearth, dst], os.path.dirname(self.googleearth))
        if not success:
            _log.warning('unable to open "%s" in GoogleEarth.', dst)
            # @TODO: check
            QtWidgets.QMessageBox.warning(
                self.app, self.tr('Warning'),
                self.tr('Unable to open "%s" in GoogleEarth.') % dst)

    @QtCore.Slot()
    def openInGoogleMaps(self):
        """Open google-maps centering the map on scene centre.

        .. seealso:: http://mapki.com/wiki/Google_Map_Parameters

        """

        item = self._currentDatasetItem()
        if item is None:
            _log.info('no item selected.')
            QtWidgets.QMessageBox.information(
                self.app, self.tr('Information'),
                self.tr('No item selected.'))
            return

        try:
            cmapper = item.cmapper
        except AttributeError:
            _log.error(
                'item "%s" seems to have no geographic info.', item.filename)
            return

        lon, lat = cmapper.imgToGeoGrid([0.5, item.RasterXSize - 0.5],
                                        [0.5, item.RasterYSize - 0.5])
        deltalon = np.max(lon) - np.min(lon)
        deltalat = np.max(lat) - np.min(lat)
        zoomlon = np.floor(np.log2(360/deltalon))
        zoomlat = np.floor(np.log2(180/deltalat))
        zoomlevel = min(zoomlon, zoomlat) + 1

        pixel, line = item.RasterXSize / 2., item.RasterYSize / 2.
        lon, lat = cmapper.imgToGeoPoints(pixel, line)

        url = QtCore.QUrl('http://maps.google.com/maps')

        query = QtCore.QUrlQuery()

        query.addQueryItem('q', '%fN,%fE' % (lat, lon))   # coordinates
        query.addQueryItem('t', 'h')                      # map type (hybrid)
        query.addQueryItem('z', str(zoomlevel))           # zoom level (1, 20)

        url.setQuery(query)

        success = QtGui.QDesktopServices.openUrl(url)
        if not success:
            _log.warning('unable to open URL: "%s"', url)
            # @TODO: check
            QtWidgets.QMessageBox.warning(
                self.app, self.tr('Warning'),
                self.tr('Unable to open URL: "%s"') % str(url))

    @QtCore.Slot()
    @QtCore.Slot(QtWidgets.QMdiSubWindow)
    def onSubWindowChanged(self, subwin=None):
        item = self._currentDatasetItem()
        enabled = bool(item is not None and hasattr(item, 'cmapper'))
        self.actions.setEnabled(enabled)

    # @QtCore.Slot(QtCore.QModelIndex)
    # def onItemClicked(self, index):
    #     if not self.app.mdiarea.activeSubWindow():
    #         item = self.app.datamodel.itemFromIndex(index)
    #         self.setItemFootprint(item)
    #
    # @QtCore.Slot()
    # @QtCore.Slot(QtCore.QModelIndex, int, int)
    # def onModelChanged(self, index=None, start=None, stop=None):
    #     subwin = self.app.mdiarea.activeSubWindow()
    #     if subwin:
    #         self.onSubWindowChanged(subwin)
    #     else:
    #         item = self.app.currentItem()
    #         self.setItemFootprint(item)
