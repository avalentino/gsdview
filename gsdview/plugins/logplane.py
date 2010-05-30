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


'''Log plane.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'
__version__  = (0,6,1)
__requires__ = []

__all__ = ['init', 'close', 'loadSettings', 'saveSettings',
           'name','version', 'short_description','description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label',
]

# Info
name = 'logplane'
version = '.'.join(map(str, __version__))

short_description = 'Log plane for GSDView'
description = __doc__

author = 'Antonio Valentino'
author_email = 'a_valentino@users.sf.net'
copyright = 'Copyright (C) 2008-2010 %s <%s>' % (author, author_email)
license_type = 'GNU GPL'
website = 'http://gsdview.sourceforge.net'
website_label = website


def init(app):
    import logging

    from PyQt4 import QtCore, QtGui

    import exectools
    from exectools.qt4 import Qt4OutputPlane, Qt4LoggingHandler

    panel = QtGui.QDockWidget('Output Log', app)
    # @TODO: try to add actions to a QTextEdit widget instead of using a
    #        custom widget
    logplane = Qt4OutputPlane()
    panel.setWidget(logplane)

    panel.setObjectName('outputPanel')
    app.addDockWidget(QtCore.Qt.BottomDockWidgetArea, panel)

    # setupLogger
    fmt = ('%(levelname)s: %(filename)s line %(lineno)d in %(funcName)s: '
           '%(message)s')

    formatter = logging.Formatter(fmt)
    #formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler = Qt4LoggingHandler(logplane)
    #handler.setLevel(app.logger.level) # NOTSET
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # setupController
    # @TODO: fix for multiple tools
    #app.controller._tool.stdout_handler.stream = Qt4OStream(logplane)

    # @TODO: fix
    # @WARNING: modify class attribute
    exectools._LEVEL2TAG[logging.getLevelName('TRACE')] = 'trace'
    fmt = QtGui.QTextCharFormat()
    fmt.setForeground(QtGui.QColor('green'))
    handler._formats['trace'] = fmt

    # Connect signals
    QtCore.QObject.connect(logplane, QtCore.SIGNAL('planeHideRequest()'),
                           panel.hide)

def close(app):
    saveSettings(app.settings)
    #app.logger.remove(_global_aux.pop('handler'))
    #app.controller._tool.stdout_handler.stream = _global_aux.pop('old_stream')
    #panel = app.findChild(QtGui.QDockWidget, 'outputPanel')
    #app.removeDockWidget(panel)

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass
