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

'''World map component for GSDView.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date$'
__version__ = (1,0,0)
__revision__ = '$Revision$'
__requires__ = []

from PyQt4 import QtCore

from worldmap import WorldmapPanel

__all__ = ['WorldmapPanel', 'init', 'close']

def init(mainwin):
    worldmapPanel = WorldmapPanel(mainwin)
    worldmapPanel.setObjectName('worldmapPanel') # @TODO: check
    mainwin.addDockWidget(QtCore.Qt.BottomDockWidgetArea, worldmapPanel)

    mainwin.connect(mainwin, QtCore.SIGNAL('openGdalDataset(PyQt_PyObject)'),
                    worldmapPanel.setDataset)

    # @TODO: improve for multiple datasets
    mainwin.connect(mainwin, QtCore.SIGNAL('closeGdalDataset()'),
                    worldmapPanel.clear)

def close(mainwin):
    saveSettings()

def loadSettings():
    pass

def saveSettings():
    pass

def getSettingsEditor():
    pass
