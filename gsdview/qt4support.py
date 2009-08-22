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

'''Utility functions and classes for Qt4 applicaions.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import os

from PyQt4 import QtCore, QtGui

from gsdview import utils


intToWinState = {
    int(QtCore.Qt.WindowNoState):       QtCore.Qt.WindowNoState,
    int(QtCore.Qt.WindowMinimized):     QtCore.Qt.WindowMinimized,
    int(QtCore.Qt.WindowMaximized):     QtCore.Qt.WindowMaximized,
    int(QtCore.Qt.WindowFullScreen):    QtCore.Qt.WindowFullScreen,
    int(QtCore.Qt.WindowActive):        QtCore.Qt.WindowActive,
}

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

try:
    from PyQt4.Qwt5 import toQImage
    def numpy2qimage(data):
        return toQImage(data.transpose())

    del toQImage

except ImportError:
    import numpy
    GRAY_COLORTABLE = [QtGui.QColor(i, i, i).rgb() for i in range(256)]

    def numpy2qimage(data):
        '''Convert a numpy array into a QImage'''

        colortable = None

        if data.dtype in (numpy.uint8, numpy.ubyte):
            if data.ndim == 2:
                h, w = data.shape

                shape = (h, numpy.ceil(w / 4.) * 4)
                if shape != data.shape:
                    # build aigned matrix
                    image = numpy.zeros(shape, numpy.ubyte)
                    image[:,:w] = data
                else:
                    image = numpy.require(data, numpy.uint8, 'CO') # 'CAO'
                format = QtGui.QImage.Format_Indexed8

                # @TODO: check
                #~ colortable = [QtGui.QColor(i, i, i).rgb() for i in range(256)]
                colortable = GRAY_COLORTABLE

            elif data.ndim == 3 and data.shape[2] == 3:
                image = numpy.require(data, numpy.uint8, 'CO') # 'CAO'
                format = QtGui.QImage.Format_RGB

            elif data.ndim == 3 and data.shape[2] == 4:
                image = numpy.require(data, numpy.uint8, 'CO') # 'CAO'
                format = QtGui.QImage.Format_ARGB32

        elif data.dtype == numpy.uint16 and data.ndim == 2:
            # @TODO: check
            h, w = data.shape

            shape = (h, numpy.ceil(w / 2.) * 2)
            if shape != data.shape:
                # build aigned matrix
                image = numpy.zeros(shape, numpy.ubyte)
                image[:,:w] = data
            else:
                image = numpy.require(data, numpy.uint16, 'CO') # 'CAO'
            format = QtGui.QImage.Format_RGB16

        elif data.dtype == numpy.uint32 and data.ndim == 2:
            image = numpy.require(data, numpy.uint32, 'CO') # 'CAO'
            format = QtGui.QImage.Format_ARGB32

        else:
            raise ValueError('unable to convert data: shape=%s, '
                        'dtype="%s"' % (data.shape, numpy.dtypr(data.dtype)))

        result = QtGui.QImage(image.data, w, h, format)
        result.ndarray = image
        if colortable:
            result.setColorTable(colortable)

        return result

def getuifile(name, package=None):
    '''Return the ui file path.

    It is assumed that Qt UI files are located in the "ui" subfolfer of
    the package.

    .. seealso:: :autolink:`gsdview.utils.getresource`

    '''

    return utils.getresource(os.path.join('ui', name), package)


def geticonfile(name, package=None):
    '''Return the icon file path.

    It is assumed that icon files are located in the "images" subfolder
    of the package.

    .. seealso:: :autolink:`gsdview.utils.getresource`

    '''

    return utils.getresource(os.path.join('images', name), package)


def geticon(name, package=None):
    '''Build and return requested icon.

    It is assumed that icon files are located in the "images" subfolder
    of the package.

    .. seealso:: :autolink:`gsdview.utils.getresource`

    '''

    iconfile = utils.getresource(os.path.join('images', name), package)

    return QtGui.QIcon(iconfile)
