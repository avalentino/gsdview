# -*- coding: utf-8 -*-

from . import qt_api

__all__ = [
    'QWebDatabase',
    'QWebElement',
    'QWebElementCollection',
    'QWebHistory',
    'QWebHistoryInterface',
    'QWebHistoryItem',
    'QWebPluginFactory',
    'QWebSecurityOrigin',
    'QWebSettings',
    'qWebKitMajorVersion',
    'qWebKitMinorVersion',
    'qWebKitVersion',
]

if qt_api == 'pyqt5':
    from PyQt5.QtWebKit import *

elif qt_api == 'pyqt4':
    import PyQt4.QtWebKit as _QtWebKit
    locals().update(dict((name, getattr(_QtWebKit, name)) for name in __all__))
    del _QtWebKit

elif qt_api == 'pyside':
    import PySide.QtWebKit as _QtWebKit
    locals().update(dict((name, getattr(_QtWebKit, name)) for name in __all__))
    del _QtWebKit
