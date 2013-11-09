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


'''UI front-end for GSDTools.'''


import os
import sys
import logging
import tempfile

from qt import QtCore, QtGui

from gsdview import utils
from gsdview import qt4support
from gsdtools import ras2vec

from . import info


class GSDToolsController(QtCore.QObject):
    def __init__(self, app, **kwargs):
        super(GSDToolsController, self).__init__(app, **kwargs)
        self.app = app

        self.googleearth = None
        self.actions = self._setupActions()
        self.actions.setEnabled(False)
        app.mdiarea.subWindowActivated.connect(self.onSubWindowChanged)
        #app.subWindowClosed.connect(self.onSubWindowChanged)
        #~ app.treeview.clicked.connect(self.onItemChanged)
        #~ app.treeview.selectionModel().selectionChanged(self.self.onItemChanged)
        #~ ##void currentChanged(const QModelIndex& current,
        #~ ##                    const QModelIndex& previous)

    def _googleEarthBin(self):
        pass

    def _setupActions(self):
        actions = QtGui.QActionGroup(self)

        # KML export
        icon = qt4support.geticon('area.svg', 'gsdview')
        QtGui.QAction(icon, self.tr('KML export'), actions,
                      objectName='kmlExportAction',
                      statusTip=self.tr('KML export'),
                      triggered=self.exportKML)

        # Open in google earth
        icon = qt4support.geticon('earth.svg', __name__)
        QtGui.QAction(icon, self.tr('Open in Google Earth'), actions,
                      objectName='openInGoogleEarthAction',
                      statusTip=self.tr('Open in Google Earth'),
                      triggered=self.openInGoogleEarth)

        # Open in google maps
        icon = qt4support.geticon('overview.svg', 'gsdview.gdalbackend')
        QtGui.QAction(icon, self.tr('Open in Google Maps'), actions,
                      objectName='openInGoogleMapsAction',
                      statusTip=self.tr('Open in Google Maps'),
                      triggered=self.openInGoogleMaps)

        return actions

    def loadSettings(self, settings):
        settings.beginGroup('plugins/%s' % info.name)
        try:
            googleearth = settings.value('gogle_earth_path')
            if not googleearth:
                if sys.platform.startswith('win'):
                    googleearth = utils.which('googleearth.exe')
                else:
                    for name in ('googleearth', 'google-earth'):
                        googleearth = utils.which(name)
                        if googleearth:
                            break

            action = self.actions.findChild(QtGui.QAction,
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
            logging.info('no item to export.')
            QtGui.QMessageBox.information(self.app, self.tr('Information'),
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

        dst, filter_ = QtGui.QFileDialog.getSaveFileNameAndFilter(
                                        self.app,
                                        self.tr('Save KML'),
                                        target,
                                        ';;'.join(filters))

        dst = str(dst)

        if dst:
            try:
                ras2vec.export_raster(src, dst, boxlayer='box',
                                      gcplayer='GCPs', mark_corners=True)
            except (OSError, RuntimeError):
                # @TODO: QtGui.QMessageBox.error(...)
                logging.error('unable to export "%s" to "%s".' % (src, dst))

    @QtCore.Slot()
    def openInGoogleEarth(self):
        item = self._currentDatasetItem()

        if item is None:
            logging.info('no item selected.')
            QtGui.QMessageBox.information(self.app, self.tr('Information'),
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
            # @TODO: QtGui.QMessageBox.error(...)
            logging.error('unable to export "%s" to "%s".' % (src, dst))

        #success = QtCore.QProcess.startDetached(self.googleearth, [dst])
        logging.info('GoogleEarth: %s' % self.googleearth)
        logging.info('KML: %s' % dst)
        success = QtCore.QProcess.startDetached('sh', [self.googleearth, dst],
            os.path.dirname(self.googleearth))
        if not success:
            logging.warning('unable to open "%s" in GoogleEarth.' % dst)
            # @TODO: check
            QtGui.QMessageBox.warning(self.app, self.tr('Warning'),
                        self.tr('Unable to open "%s" in GoogleEarth.') % dst)

    @QtCore.Slot()
    def openInGoogleMaps(self):
        '''Open google-maps centering the map on scene centre.

        .. seealso:: http://mapki.com/wiki/Google_Map_Parameters

        '''

        item = self._currentDatasetItem()
        if item is None:
            logging.info('no item selected.')
            QtGui.QMessageBox.information(self.app, self.tr('Information'),
                                          self.tr('No item selected.'))
            return

        try:
            cmapper = item.cmapper
        except AttributeError:
            logging.error('item "%s" seems to heve no geographic info.' %
                                                                item.filename)
            return

        pixel, line = item.RasterXSize / 2., item.RasterYSize / 2.
        lon, lat = cmapper.imgToGeoPoints(pixel, line)

        url = QtCore.QUrl('http://maps.google.com/maps')
        url.addQueryItem('q', '%fN,%fE' % (lat, lon))   # coordinates
        url.addQueryItem('t', 'h')                      # map type (hybrid)
        url.addQueryItem('z', '9')                      # zoom level (1, 20)

        success = QtGui.QDesktopServices.openUrl(url)
        if not success:
            logging.warning('unable to open URL: "%s"' % str(url))
            # @TODO: check
            QtGui.QMessageBox.warning(self.app, self.tr('Warning'),
                            self.tr('Unable to open URL: "%s"') % str(url))

    @QtCore.Slot()
    @QtCore.Slot(QtGui.QMdiSubWindow)
    def onSubWindowChanged(self, subwin=None):
        item = self._currentDatasetItem()
        enabled = bool(item is not None and hasattr(item, 'cmapper'))
        self.actions.setEnabled(enabled)

    #~ @QtCore.Slot(QtCore.QModelIndex)
    #~ def onItemClicked(self, index):
        #~ if not self.app.mdiarea.activeSubWindow():
            #~ item = self.app.datamodel.itemFromIndex(index)
            #~ self.setItemFootprint(item)

    #~ @QtCore.Slot()
    #~ @QtCore.Slot(QtCore.QModelIndex, int, int)
    #~ def onModelChanged(self, index=None, start=None, stop=None):
        #~ subwin = self.app.mdiarea.activeSubWindow()
        #~ if subwin:
            #~ self.onSubWindowChanged(subwin)
        #~ else:
            #~ item = self.app.currentItem()
            #~ self.setItemFootprint(item)
