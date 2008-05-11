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

'''Log plane.'''

__author__  = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__    = '$Date$'
__version__ = (0,3,0)
__revision__ = '$Revision$'
__requires__ = []
__all__ = ['init', 'close']


import logging

from PyQt4 import QtCore, QtGui

from exectools.qt4tools import Qt4OStream, Qt4OutputPlane, \
                               Qt4StreamLoggingHandler


def init(mainwin):
    panel = QtGui.QDockWidget('Output Log', mainwin)
    logplane = Qt4OutputPlane()
    panel.setWidget(logplane)

    panel.setObjectName('outputPanel')
    mainwin.addDockWidget(QtCore.Qt.BottomDockWidgetArea, panel)

    # setupLogger
    fmt = ('%(levelname)s: %(filename)s line %(lineno)d in %(funcName)s: '
           '%(message)s')

    formatter = logging.Formatter(fmt)
    #formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler = Qt4StreamLoggingHandler(logplane)
    handler.setLevel(mainwin.logger.level)
    handler.setFormatter(formatter)
    mainwin.logger.addHandler(handler)

    # seupController
    # @TODO: fix for multiple tools
    mainwin.controller.tool.stdout_handler.stream = Qt4OStream(logplane)

    # @TODO: fix
    # @WARNING: modify class attribute
    handler.level2tag[logging.getLevelName('TRACE')] = 'trace'
    fmt = QtGui.QTextCharFormat()
    fmt.setForeground(QtGui.QColor('green'))
    handler.stream._formats['trace'] = fmt

    # Connect signals
    QtCore.QObject.connect(logplane, QtCore.SIGNAL('planeHideRequest()'),
                           panel.hide)

def close(mainwin):
    saveSettings()

def loadSettings():
    pass

def saveSettings():
    pass

def getSettingsEditor():
    pass