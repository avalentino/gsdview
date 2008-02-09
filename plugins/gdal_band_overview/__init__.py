### Copyright (C) 2007 Antonio Valentino <a_valentino@users.sf.net>

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

'''Overview pannel for GDAL raster bands.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date$'
__version__ = (1,0,0)
__revision__ = '$Revision$'
__requires__ = []

from PyQt4 import QtCore

from band_overview import GdalBandOverview

__all__ = ['GdalBandOverview', 'init', 'close']

def init(mainwin):
    overviewPanel = GdalBandOverview(mainwin)
    overviewPanel.setObjectName('bandOverviewPanel') # @TODO: check
    mainwin.addDockWidget(QtCore.Qt.LeftDockWidgetArea, overviewPanel)

    # Connect signals
    mainwin.connect(mainwin, QtCore.SIGNAL('openBandRequest(PyQt_PyObject)'),
                    overviewPanel.setBand)
    # @TODO: improve for multiple datasets
    mainwin.connect(mainwin, QtCore.SIGNAL('closeGdalDataset()'),
                    overviewPanel.reset)
    # @TODO: actionFileClose could not be part of the api
    #~ mainwin.connect(mainwin.actionFileClose, QtCore.SIGNAL('triggered()'),
                    #~ datasetBrowser.treeWidget.clear)

    QtCore.QObject.connect(overviewPanel.graphicsview,
                           QtCore.SIGNAL('posMarked(const QPoint&)'),
                           overviewPanel.centerOn)

    # @TODO: check API
    QtCore.QObject.connect(mainwin.graphicsView.horizontalScrollBar(),
                           QtCore.SIGNAL('valueChanged(int)'),
                           overviewPanel.updateBox)
    QtCore.QObject.connect(mainwin.graphicsView.verticalScrollBar(),
                           QtCore.SIGNAL('valueChanged(int)'),
                           overviewPanel.updateBox)
    QtCore.QObject.connect(mainwin.graphicsView,
                           QtCore.SIGNAL('newSize(const QSize&)'),
                           overviewPanel.updateBox)
    QtCore.QObject.connect(mainwin.graphicsView,
                           QtCore.SIGNAL('scaled()'),
                           overviewPanel.updateBox)

def close(mainwin):
    saveSettings()

def loadSettings():
    pass

def saveSettings():
    pass

def getSettingsEditor():
    pass
