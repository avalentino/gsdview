#!/usr/bin/env python

# -*- coding: UTF8 -*-

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

'''Launcher script for gsdview.'''


import logging
import datetime

class Timer(object):
    def __init__(self):
        self.start = datetime.datetime.now()
        self.last = self.start

    def elapsed(self):
        return datetime.datetime.now() - self.start

    def update(self):
        now = datetime.datetime.now()
        delta = now - self.last
        self.last = now
        return delta.seconds, delta.microseconds


def traced_import(modname, splash, timer, app, level=logging.DEBUG):
    splash.showMessage(splash.tr('Importing %1 module ...').arg(modname))
    app.processEvents()
    __import__(modname)
    logging.log(level, '%s import: %d.%06ds' % ((modname,) + timer.update()))


def splash_message(msg, splash, app, level=logging.DEBUG):
    splash.showMessage(splash.tr(msg))
    app.processEvents()
    logging.log(level, msg)


MODULES = ['os', 're', 'sys', 'itertools',
          'numpy',
          'osgeo.gdal', 'osgeo.osr',
          'PyQt4.QtCore', 'PyQt4.QtGui',
          'gsdview.info', 'gsdview.utils', 'gsdview.widgets',
          'gsdview.mainwin', 'gsdview.gsdtools', 'gsdview.qt4support',
          'gsdview.graphicsview',
          'gsdview.exectools', 'gsdview.exectools.qt4tools',
          'gsdview.gdalbackend', #'gsdview.gdalbackend.core',
          #~ 'gsdview.gdalbackend.gdalqt4', 'gsdview.gdalbackend.widgets',
          #~ 'gsdview.gdalbackend.modelitems',
          #~ 'gsdview.gdalbackend.gdalsupport',
          #~ 'gsdview.gdalbackend.gdalexectools',
          #~ 'gsdview.gdalbackend.gdalbackend_resources',
]

def preload(modules, splash, app=None):
    if not app:
        from PyQt4 import QtGui
        app = QtGui.qApp

    def _traced_import(modname, splash=splash, timer=Timer(), app=app):
        return traced_import(modname, splash, timer, app)

    def _splash_message(msg, splash=splash, app=app):
        return _splash_message(msg, splash, app)

    for modname in modules:
        _traced_import(modname)


def setup_env():
    import os, sys
    GSDVIEWROOT = os.path.dirname(os.path.abspath(__file__))

    # @NOTE: needed for UI building of promoted widgets
    if GSDVIEWROOT not in sys.path:
        sys.path.insert(0, GSDVIEWROOT)

    # @NOTE: needed for path names variables expansion
    os.environ['GSDVIEWROOT'] = GSDVIEWROOT


def cmdline_ui():
    import os
    from optparse import OptionParser

    from gsdview import info

    parser = OptionParser(prog='GSDView',
                    usage='%prog [options] [FILENAME [FILENAME [...]]]',
                    version='%%prog Open Source Edition %s' % info.version,
                    description=info.description,
                    epilog='Home Page: %s' % info.website)

    # @TODO: complete
    #~ parser.add_option('-c', '--config-file', dest='configfile', metavar='FILE',
                      #~ help='use specified cnfig file instead of default one')
    #~ parser.add_option('-d', '--debug', action='store_true', dest='debug',
                      #~ help='print debug messages')
    #~ parser.add_option('-p', '--plugins-path', dest='plugins_path',
                      #~ metavar='PATH',
                      #~ help='prepend the specified path to default ones. '
                      #~ 'A "%s" separated list can be used to specify multile '
                      #~ 'paths. ' % os.pathsep)

    options, args = parser.parse_args()

    return options, args


def main():
    options, args = cmdline_ui()
    # @TODO:
    # * config logging using options.configfile, USER_CFG, SYS_CFG
    # * if options.debug: set rootlogger.level = logging.DEBUG
    # * maybe set loglevelfor other loggers

    timer = Timer()

    ### splash screen #########################################################
    from PyQt4 import QtGui
    logging.debug('Qt4 import %d.%06ds' % timer.update())

    import splash_resources
    logging.debug('splash resources import %d.%06ds' % timer.update())

    import sys
    app = QtGui.QApplication(sys.argv)
    pixmap = QtGui.QPixmap(':images/splash.png')
    splash = QtGui.QSplashScreen(pixmap)
    splash.show()
    #app.processEvents()

    splash_message('Splash screen setup completed', splash, app)
    logging.debug('splash screen setup %d.%06ds' % timer.update())

    ### environment setup #####################################################
    splash_message('Setup environment ...', splash, app)
    setup_env()
    logging.debug('environment setup %d.%06ds' % timer.update())

    ### modules loading #######################################################
    preload(MODULES, splash, app)

    ### GUI ###################################################################
    splash_message('Build GUI ...', splash, app)
    from gsdview.gsdview import GSDView
    mainwin = GSDView(splash=splash)    # @TODO: pass plugins_path, loglevel??
    mainwin.show()
    logging.debug('GUI setup %d.%06ds' % timer.update())

    ### close splash and run app ##############################################
    splash.finish(mainwin)
    app.processEvents()
    sys.exit(app.exec_())

if __name__ == '__main__':
    import os, sys
    GSDVIEWROOT = os.path.dirname(os.path.abspath(__file__))
    EXTRAPATH, PKGNAME = GSDVIEWROOT.rsplit(os.path.sep, 1)
    if PKGNAME != 'gsdview':
        raise RuntimeError('wrong package name.')

    if EXTRAPATH not in sys.path:
        sys.path.insert(0, EXTRAPATH)

    main()
