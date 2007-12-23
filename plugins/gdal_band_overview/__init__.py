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
__date__    = '$Date: 2007-12-02 20:30:11 +0100 (dom, 02 dic 2007) $'
__version__ = (1,0,0)
__revision__ = '$Revision: 47 $'
__requires__ = []

from PyQt4 import QtCore

from band_overview import GdalBandOverview

__all__ = ['GdalBandOverview', 'init', 'close']

def init(mainwin):
    overviewPanel = GdalBandOverview(mainwin)
    overviewPanel.setObjectName('bandOverviewPanel') # @TODO: check
    mainwin.addDockWidget(QtCore.Qt.LeftDockWidgetArea, overviewPanel)

    mainwin.connect(mainwin, QtCore.SIGNAL('openBandRequest(PyQt_PyObject)'),
                    overviewPanel.setBand)
    # @TODO: improve for multiple datasets
    mainwin.connect(mainwin, QtCore.SIGNAL('closeGdalDataset()'),
                    overviewPanel.graphicsview.clearScene)
    # @TODO: actionFileClose could not be part of the api
    #~ mainwin.connect(mainwin.actionFileClose, QtCore.SIGNAL('triggered()'),
                    #~ datasetBrowser.treeWidget.clear)

    # Connect signals
    overviewPanel.connect(mainwin.graphicsView,
                 QtCore.SIGNAL('posMarked(const QPoint&)'),
                 overviewPanel.centerOn)

    # @TODO: check API
    overviewPanel.connect(mainwin.graphicsView.horizontalScrollBar(),
                          QtCore.SIGNAL('valueChanged(int)'),
                          overviewPanel.updateBox)
    overviewPanel.connect(mainwin.graphicsView.verticalScrollBar(),
                          QtCore.SIGNAL('valueChanged(int)'),
                          overviewPanel.updateBox)
    overviewPanel.connect(mainwin.graphicsView,
                          QtCore.SIGNAL('newSize(const QSize&)'),
                          overviewPanel.updateBox)
    overviewPanel.connect(mainwin.graphicsView,
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
