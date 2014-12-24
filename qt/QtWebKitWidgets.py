# -*- coding: utf-8 -*-

from . import qt_api

__all__ = [
    'QGraphicsWebView',
    'QWebFrame',
    'QWebHitTestResult',
    'QWebInspector',
    'QWebPage',
    'QWebView',
]

if qt_api == 'pyqt5':
    from PyQt5.QtWebKitWidgets import *

elif qt_api == 'pyqt4':
    import PyQt4.QtWebKit as _QtWebKit
    locals().update(dict(k, getattr(_QtWebKit, name)) for name in __all__)
    del _QtWebKit

elif qt_api == 'pyside':
    import PySide.QtWebKit as _QtWebKit
    locals().update(dict(k, getattr(_QtWebKit, name)) for name in __all__)
    del _QtWebKit
