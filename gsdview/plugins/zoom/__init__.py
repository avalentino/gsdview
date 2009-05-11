### Copyright (C) 2008-2009 Antonio Valentino <a_valentino@users.sf.net>

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

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'
__requires__ = []       # @TODO: move to the info file

__all__ = ['ZoomTool', 'init', 'close']


from info import *

from PyQt4 import QtCore

from core import ZoomTool


__version__ = info.__version__


def init(mainwin):
    zoomTool = ZoomTool(mainwin)
    mainwin.menuBar().addMenu(zoomTool.menu)
    mainwin.addToolBar(zoomTool.toolbar)

    # @TODO: check the API / use QWidget.findChild(name)
    #mainwin.menuBar().insertMenu(mainwin.helpMenu, zoomTool.menu)
    #mainwin.insertToolBar(mainwin.helpToolBar, zoomTool.toolbar)

    zoomTool.actions.setEnabled(False)
    zoomTool.connect(mainwin.mdiarea,
                     QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                     lambda w: zoomTool.actions.setEnabled(True))
    zoomTool.connect(mainwin,
                     QtCore.SIGNAL('subWindowClosed()'),
                     lambda: zoomTool.actions.setEnabled(
                                    bool(mainwin.mdiarea.activeSubWindow())))


def close(mainwin):
    saveSettings(mainwin.settings)

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass
