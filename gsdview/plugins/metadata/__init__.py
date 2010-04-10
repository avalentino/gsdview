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


'''Metadata viewer component for geo-datasets.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'

__all__ = ['MetadataViewer', 'init', 'close',
           'name','version', 'short_description','description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label',
]


from metadata.info import *
from metadata.info import __version__, __requires__


def init(app):
    from PyQt4 import QtCore
    from metadata.core import MetadataViewer

    metadataviewer = MetadataViewer(app)
    metadataviewer.setObjectName('metadataViewerPanel') # @TODO: check
    app.addDockWidget(QtCore.Qt.BottomDockWidgetArea, metadataviewer)

    # @TODO: move to core module - controller
    def setItemMetadata(item, metadataviewer=metadataviewer):
        if not item:
            metadataviewer.clear()
            return

        # @TODO: fix
        # @WARNING: this method contains backend specific code
        if item.backend != 'gdalbackend':
            import logging
            logging.warning('only "gdalbackend" is supported by "overview" '
                            'plugin')
            return

        try:
            metadata = item.GetMetadata_List()
        except RuntimeError:
            # closed sub-dataset
            return
        metadataviewer.setMetadata(metadata)

    def onItemClicked(index, app=app):
        #if not app.mdiarea.activeSubWindow():
        item = app.datamodel.itemFromIndex(index)
        setItemMetadata(item)

    app.connect(app.treeview, QtCore.SIGNAL('clicked(const QModelIndex&)'),
                onItemClicked)

    def onSubWindowChanged(window=None, app=app):
        if not window:
            window = app.mdiarea.activeSubWindow()
        if window:
            try:
                item = window.item
            except AttributeError:
                item = None
        else:
            item = app.currentItem()

        setItemMetadata(item)

    app.connect(app.mdiarea, QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                onSubWindowChanged)

    app.connect(app, QtCore.SIGNAL('subWindowClosed()'), onSubWindowChanged)


def close(app):
    saveSettings(app.settings)

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass
