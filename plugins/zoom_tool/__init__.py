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

'''Zoom tool.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date: 2007-12-02 17:26:44 +0100 (dom, 02 dic 2007) $'
__version__ = (1,0,0)
__revision__ = '$Revision: 43 $'
__requires__ = []

from PyQt4 import QtCore

from zoom import ZoomTool

__all__ = ['ZoomTool', 'init', 'close']

def init(mainwin):
    zoomTool = ZoomTool(mainwin)
    mainwin.menuBar().addMenu(zoomTool.menu)
    mainwin.addToolBar(zoomTool.toolbar)

    # @TODO: check the API
    if mainwin.imageItem is None:
        zoomTool.actions.setEnabled(False)

    # @TODO: improve for multiple datasets
    zoomTool.connect(mainwin, QtCore.SIGNAL('openGdalDataset(PyQt_PyObject)'),
                     lambda x: zoomTool.actions.setEnabled(True))
    zoomTool.connect(mainwin, QtCore.SIGNAL('closeGdalDataset()'),
                     lambda: zoomTool.actions.setEnabled(False))


def close(mainwin):
    saveSettings()

def loadSettings():
    pass

def saveSettings():
    pass

def getSettingsEditor():
    pass

