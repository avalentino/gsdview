### Copyright (C) 2008 Antonio Valentino <a_valentino@users.sf.net>

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
__version__ = (0,3,0)
__revision__ = '$Revision$'
__requires__ = []
__all__ = ['GdalDatasetBrowser', 'init', 'close']


from PyQt4 import QtCore

from dataset_browser import GdalDatasetBrowser


def init(mainwin):
    datasetBrowser = GdalDatasetBrowser(mainwin)
    datasetBrowser.setObjectName('datasetBrowserPanel') # @TODO: check
    mainwin.addDockWidget(QtCore.Qt.LeftDockWidgetArea, datasetBrowser)

    mainwin.connect(mainwin, QtCore.SIGNAL('openGdalDataset(PyQt_PyObject)'),
                    datasetBrowser.setDataset)
    # @TODO: improve for multiple datasets
    mainwin.connect(mainwin, QtCore.SIGNAL('closeGdalDataset()'),
                    datasetBrowser.clear)
    # @TODO: actionFileClose could not be part of the api
    #~ mainwin.connect(mainwin.actionFileClose, QtCore.SIGNAL('triggered()'),
                    #~ datasetBrowser.treeWidget.clear)

def close(mainwin):
    saveSettings()

def loadSettings():
    pass

def saveSettings():
    pass

def getSettingsEditor():
    pass
