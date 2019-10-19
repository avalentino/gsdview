# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2015 Antonio Valentino <antonio.valentino@tiscali.it>
#
# This module is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 2 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this module if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US


'''Log pane.'''

__version__ = (0, 7, 0)
__requires__ = []

__all__ = [
    'init', 'close', 'loadSettings', 'saveSettings',
    'name', 'version', 'short_description', 'description',
    'author', 'author_email', 'copyright', 'license_type',
    'website', 'website_label',
]

# Info
name = 'logpane'
version = '.'.join(map(str, __version__)) + '.dev'

short_description = 'Log pane for GSDView'
description = __doc__

author = 'Antonio Valentino'
author_email = 'antonio.valentino@tiscali.it'
copyright = 'Copyright (C) 2008-2015 %s <%s>' % (author, author_email)
license_type = 'GNU GPL'
website = 'http://gsdview.sourceforge.net'
website_label = website


def init(app):
    import logging

    from qtpy import QtCore, QtWidgets

    from exectools.qt import QtOutputPane, QtLoggingHandler

    panel = QtWidgets.QDockWidget('Output Log', app, objectName='outputPanel')
    # @TODO: try to add actions to a QTextEdit widget instead of using a
    #        custom widget
    logpane = QtOutputPane()
    panel.setWidget(logpane)

    app.addDockWidget(QtCore.Qt.BottomDockWidgetArea, panel)

    # setupLogger
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler = QtLoggingHandler(logpane)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # Connect signals
    logpane.paneHideRequest.connect(panel.hide)


def close(app):
    saveSettings(app.settings)
    #app.logger.remove(_global_aux.pop('handler'))
    #panel = app.findChild(QtWidgets.QDockWidget, 'outputPanel')
    #app.removeDockWidget(panel)


def loadSettings(settings):
    pass


def saveSettings(settings):
    pass
