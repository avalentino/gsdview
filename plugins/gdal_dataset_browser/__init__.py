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

'''Browser component for GDAL datasets.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date$'
__version__ = (1,0,0)
__revision__ = '$Revision$'
__requires__ = []

from PyQt4 import QtCore

from dataset_browser import GdalDatasetBrowser

__all__ = ['GdalDatasetBrowser', 'init', 'close']

def init(mainWin):
    datasetBrowser = GdalDatasetBrowser(mainWin)
    datasetBrowser.setObjectName('datasetBrowserPanel') # @TODO: check
    mainWin.addDockWidget(QtCore.Qt.LeftDockWidgetArea, datasetBrowser)

    mainWin.connect(mainWin, QtCore.SIGNAL('openGdalDataset(PyQt_PyObject)'),
                    datasetBrowser.setDataset)
    # @TODO: actionFileClose could not be part of the api
    mainWin.connect(mainWin.actionFileClose, QtCore.SIGNAL('triggered()'),
                    datasetBrowser.treeWidget.clear)

def close(mainWin):
    saveSettings()

def loadSettings():
    pass

def saveSettings():
    pass

def getSettingsEditor():
    pass
