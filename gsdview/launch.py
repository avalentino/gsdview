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


class SplashLogHandler(logging.Handler):
    def __init__(self, splash, app=None, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        if not app:
            from qt.QtWidgets import qApp as app
        self._app = app
        self._splash = splash

    def emit(self, record):
        try:
            msg = str(self.format(record))
            self._splash.showMessage(self._splash.tr(msg))
            # Causes an EOFError with pyside
            #self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def flush(self):
        self._app.processEvents()


MODULES = [
    'os', 're', 'sys', 'itertools',
    'numpy',
    'osgeo.gdal', 'osgeo.osr',
    'qt.QtCore', 'qt.QtWidgets',
    'exectools', 'exectools.qt',
    'gsdview.info', 'gsdview.utils', 'gsdview.apptools',
    'gsdview.imgutils', 'gsdview.qt4support', 'gsdview.widgets',
    'gsdview.graphicsview', 'gsdview.mainwin', 'gsdview.app',
    'gsdview.gdalbackend', 'gsdview.gdalbackend.core',
    'gsdview.gdalbackend.gdalqt4', 'gsdview.gdalbackend.widgets',
    'gsdview.gdalbackend.modelitems', 'gsdview.gdalbackend.gdalsupport',
    'gsdview.gdalbackend.gdalexectools',
]


def preload(modules, app=None):
    if not app:
        from qt import QtWidgets
        app = QtWidgets.qApp

    timer = Timer()
    logger = logging.getLogger('gsdview')
    for modname in modules:
        logger.info(app.tr('Importing %s module ...') % modname)
        app.processEvents()
        logging.debug('%s import: %d.%06ds' % ((modname,) + timer.update()))


def cmdline_ui():
    from optparse import OptionParser

    from gsdview import info

    # filter out arguments that cause errors in Mac bundles
    import sys
    args = [arg for arg in sys.argv[1:] if not arg.startswith('-psn_')]

    parser = OptionParser(
        prog='gsdview',
        #usage='%prog [options] [FILENAME [FILENAME [...]]]',
        usage='%prog [options]',
        version='%%prog Open Source Edition %s' % info.version,
        description=info.description,
        epilog='Home Page: %s' % info.website)

    # @TODO: complete
    #~ parser.add_option(
        #~ '-c', '--config-file', dest='configfile', metavar='FILE',
        #~ help='use specified cnfig file instead of default one')
    #~ parser.add_option(
        #~ '-d', '--debug', action='store_true', dest='debug',
        #~ help='print debug messages')
    #~ parser.add_option(
        #~ '-p', '--plugins-path', dest='plugins_path',
        #~ metavar='PATH',
        #~ help='prepend the specified path to default ones. '
        #~ 'A "%s" separated list can be used to specify '
        #~ 'multile paths. ' % os.pathsep)

    options, args = parser.parse_args(args)

    return options, args


def main():
    # @IMPORTANT: force numeric locale to 'C' in order to avoid problems
    #             with GDAL and PPROJ4
    # @SEEALSO: http://trac.osgeo.org/gdal/wiki/FAQMiscellaneous#DoesGDALworkindifferentinternationalnumericlocales
    import os
    os.environ['LC_NUMERIC'] = 'C'

    options, args = cmdline_ui()
    # logging.basicConfig(level=logging.DEBUG,
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s: %(message)s')
    logger = logging.getLogger('gsdview')
    logger.setLevel(logging.DEBUG)

    # @TODO:
    # * config logging using options.configfile, USER_CFG, SYS_CFG
    # * if options.debug: set rootlogger.level = logging.DEBUG
    # * maybe set loglevelfor other loggers

    timer = Timer()

    # splash screen #########################################################
    from qt import QtWidgets, QtGui
    logging.debug('Qt import: %d.%06ds' % timer.update())

    import sys
    from gsdview.info import name as NAME
    from gsdview.info import version as VERSION
    from gsdview.utils import getresource

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(NAME)
    app.setApplicationVersion(VERSION)

    pngfile = getresource(os.path.join('images', 'splash.png'), __name__)
    pixmap = QtGui.QPixmap(pngfile)
    splash = QtWidgets.QSplashScreen(pixmap)
    splash.show()
    app.processEvents()

    splash_loghandler = SplashLogHandler(splash, app)
    splash_loghandler.setFormatter(logging.Formatter('%(message)s'))

    logger.addHandler(splash_loghandler)

    logger.debug('Splash screen setup completed')
    logging.debug('splash screen setup: %d.%06ds' % timer.update())

    # modules loading #######################################################
    preload(MODULES, app)

    # GUI ###################################################################
    logger.info('Build GUI ...')
    from gsdview.app import GSDView
    mainwin = GSDView()    # @TODO: pass plugins_path, loglevel??
    mainwin.show()
    logger.info('GUI setup completed')
    logging.debug('GUI setup: %d.%06ds' % timer.update())

    # close splash and run app ##############################################
    logger.removeHandler(splash_loghandler)
    splash.finish(mainwin)
    app.processEvents()

    logger.info('Install the exception hook')
    sys.excepthook = mainwin.excepthook     # @TODO: check

    logger.info('Enter main event loop')

    # @COMPATIBILITY: this will raise the window on Mac OS X
    mainwin.raise_()

    sys.exit(app.exec_())

if __name__ == '__main__':
    import os
    import sys

    GSDVIEWROOT = os.path.dirname(os.path.abspath(__file__))
    EXTRAPATH, PKGNAME = GSDVIEWROOT.rsplit(os.path.sep, 1)
    if PKGNAME != 'gsdview':
        raise RuntimeError('wrong package name.')

    if EXTRAPATH not in sys.path:
        sys.path.insert(0, EXTRAPATH)

    main()
