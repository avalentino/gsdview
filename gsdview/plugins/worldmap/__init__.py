# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2019 Antonio Valentino <antonio.valentino@tiscali.it>
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


'''World map component for GSDView.'''


from .info import *
from .info import __version__, __requires__


__all__ = [
    'init', 'close', 'loadSettings', 'saveSettings',
    'name', 'version', 'short_description', 'description',
    'author', 'author_email', 'copyright', 'license_type',
    'website', 'website_label',
]

_instance = None


def init(app):
    from qtpy import QtCore, QtGui

    from .core import WorldmapController

    if b'jpg' not in QtGui.QImageReader.supportedImageFormats():
        raise RuntimeError('JPEG image format not supported')

    controller = WorldmapController(app)
    app.addDockWidget(QtCore.Qt.BottomDockWidgetArea, controller.panel)

    global _instance
    _instance = controller


def close(app):
    saveSettings(app.settings)

    global _instance
    instance = _instance
    _instance = None

    if instance:
        app.removeDockWidget(instance.panel)
        instance.panel.deleteLater()


def loadSettings(settings):
    pass


def saveSettings(settings):
    pass
