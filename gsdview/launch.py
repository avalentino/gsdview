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
            from qtsix.QtWidgets import qApp as app
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
    'qtsix.QtCore', 'qtsix.QtWidgets',
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
        from qtsix import QtWidgets
        app = QtWidgets.qApp

    timer = Timer()
    log = logging.getLogger(__name__)
    for modname in modules:
        log.info(app.tr('Importing %s module ...'), modname)
        app.processEvents()
        log.debug('%s import: %d.%06ds', modname, *timer.update())


def get_parser():
    from argparse import ArgumentParser
    from gsdview import info


    parser = ArgumentParser(
        prog='gsdview',
        description=info.description,
        epilog='Home Page: %s' % info.website,
    )

    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(info.version)
    )

    # @TODO: complete
    #~ parser.add_argument(
        #~ '-c', '--config-file', dest='configfile', metavar='FILE',
        #~ help='use specified cnfig file instead of default one')
    parser.add_argument(
        '-d', '--debug', action='store_const', dest='log_level',
        const='DEBUG', default='NOTSET', help='print debug messages')
    parser.add_argument(
        '--log-level', default='NOTSET',
        choices=('DEBUG', 'INFO', 'WARNING', 'CRITICAL', 'ERROR'),
        help='set the logging level (by default the logging level stored in '
             'the application settings is used)')
    #~ parser.add_argument(
        #~ '-p', '--plugins-path', dest='plugins_path',
        #~ metavar='PATH',
        #~ help='prepend the specified path to default ones. '
        #~ 'A "%s" separated list can be used to specify '
        #~ 'multile paths. ' % os.pathsep)

    return parser


def parse_args(argv=None):
    import sys

    if argv is None:
        argv = sys.argv[1:]

    # filter out arguments that cause errors in Mac bundles
    argv = [arg for arg in sys.argv[1:] if not arg.startswith('-psn_')]

    parser = get_parser()
    args = parser.parse_args(argv)

    return args


def main():
    # @IMPORTANT: force numeric locale to 'C' in order to avoid problems
    #             with GDAL and PPROJ4
    # @SEEALSO: http://trac.osgeo.org/gdal/wiki/FAQMiscellaneous#DoesGDALworkindifferentinternationalnumericlocales
    import os
    os.environ['LC_NUMERIC'] = 'C'

    args = parse_args()

    if args.log_level != 'NOTSET':
        loglevel = logging.getLevelName(args.log_level)
    else:
        loglevel = logging.INFO

    logging.basicConfig(
        level=loglevel,
        #format='%(levelname)s: %(message)s')
        format='%(asctime)s %(name)s %(levelname)s: %(message)s')

    # set the logging level explicitly on gsdview logger
    #logging.getLogger().setLevel(loglevel)
    logging.getLogger('gsdview').setLevel(loglevel)

    # PyQt loggers
    logging.getLogger('PyQt5.uic').setLevel(logging.WARNING)

    log = logging.getLogger(__name__)
    log.debug('log level set to %s', logging.getLevelName(log.level))

    # @TODO:
    # * config logging using options.configfile, USER_CFG, SYS_CFG
    # * if options.debug: set rootlogger.level = logging.DEBUG
    # * maybe set loglevelfor other loggers

    timer = Timer()

    # splash screen #########################################################
    from qtsix import QtWidgets, QtGui
    log.debug('Qt import: %d.%06ds', *timer.update())

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

    log.addHandler(splash_loghandler)

    log.info('Splash screen setup completed')
    log.debug('splash screen setup: %d.%06ds', *timer.update())

    # modules loading #######################################################
    preload(MODULES, app)

    # GUI ###################################################################
    log.info('Build GUI ...')

    from gsdview.app import GSDView

    # @TODO: pass plugins_path??
    mainwin = GSDView(loglevel=args.log_level)
    mainwin.show()
    log.info('GUI setup completed')
    log.debug('GUI setup: %d.%06ds', *timer.update())

    # close splash and run app ##############################################
    log.removeHandler(splash_loghandler)
    splash.finish(mainwin)
    app.processEvents()

    log.info('Install the exception hook')
    sys.excepthook = mainwin.excepthook     # @TODO: check

    log.info('Enter main event loop')

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
