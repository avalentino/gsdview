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

from PyQt4 import QtCore

from metadata.core import MetadataViewer


def init(mainwin):
    metadataviewer = MetadataViewer(mainwin)
    metadataviewer.setObjectName('metadataViewerPanel') # @TODO: check
    mainwin.addDockWidget(QtCore.Qt.BottomDockWidgetArea, metadataviewer)

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

    def onItemClicked(index, mainwin=mainwin):
        #if not mainwin.mdiarea.activeSubWindow():
        item = mainwin.datamodel.itemFromIndex(index)
        setItemMetadata(item)

    mainwin.connect(mainwin.treeview,
                    QtCore.SIGNAL('clicked(const QModelIndex&)'),
                    onItemClicked)

    def onSubWindowChanged(window=None, mainwin=mainwin):
        if not window:
            window = mainwin.mdiarea.activeSubWindow()
        if window:
            try:
                item = window.item
            except AttributeError:
                item = None
        else:
            item = mainwin.currentItem()

        setItemMetadata(item)

    mainwin.connect(mainwin.mdiarea,
                    QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                    onSubWindowChanged)

    mainwin.connect(mainwin, QtCore.SIGNAL('subWindowClosed()'),
                    onSubWindowChanged)


def close(mainwin):
    saveSettings(mainwin.settings)

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass
