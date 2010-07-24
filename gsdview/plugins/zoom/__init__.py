# -*- coding: utf-8 -*-

### Copyright (C) 2008-2010 Antonio Valentino <a_valentino@users.sf.net>

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

__all__ = ['init', 'close', 'loadSettings', 'saveSettings',
           'name','version', 'short_description','description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label',
]

from zoom.info import *
from zoom.info import __version__, __requires__


_instance = None


def init(app):
    from zoom.core import AppZoomTool

    tool = AppZoomTool(app)
    app.imagemenu.addSeparator()
    app.imagemenu.addActions(tool.actions.actions())
    app.addToolBar(tool.toolbar)

    tool.actions.setEnabled(False)
    app.mdiarea.subWindowActivated.connect(
                                lambda w: tool.actions.setEnabled(bool(w)))
    app.subWindowClosed.connect(lambda: tool.actions.setEnabled(
                                    bool(app.mdiarea.activeSubWindow())))

    global _instance
    _instance = tool

def close(app):
    saveSettings(app.settings)
    global _instance
    _instance = None

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass
