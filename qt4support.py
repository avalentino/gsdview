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

'''Utility functions and classes for Qt4 applicaions.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date: 2007-12-02 17:26:44 +0100 (dom, 02 dic 2007) $'
__revision__ = '$Revision: 43 $'

from PyQt4 import QtCore, QtGui

def actionGroupToMenu(actionGroup, label, mainwin):
    menu = QtGui.QMenu(label, mainwin)
    for action in actionGroup.actions():
        menu.addAction(action)
    return menu

def actionGroupToToolbar(actionGroup, label, name=None):
    if name is None:
        # get camel case name
        parts = str(label).title().split()
        parts[0] = parts[0].lower()
        name = ''.join(parts)
    toolbar = QtGui.QToolBar(label)
    toolbar.setObjectName(name)
    for action in actionGroup.actions():
        toolbar.addAction(action)
    return toolbar

def overrideCursor(func):
    def aux(*args, **kwargs):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            func(*args, **kwargs)
        finally:
            QtGui.QApplication.restoreOverrideCursor()
    return aux
