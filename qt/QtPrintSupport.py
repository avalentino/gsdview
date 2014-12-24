# -*- coding: utf-8 -*-

from . import qt_api

__all__ = [
    'QAbstractPrintDialog',
    'QPageSetupDialog',
    'QPrintDialog',
    'QPrintEngine',
    'QPrintPreviewDialog',
    'QPrintPreviewWidget',
    'QPrinter',
    'QPrinterInfo',
]

if qt_api == 'pyqt5':
    from PyQt5.QtPrintSupport import *

elif qt_api == 'pyqt4':
    import PyQt4.QtGui as _QtGui
    locals().update(dict(k, getattr(_QtGui, name)) for name in __all__)
    del _QtGui


elif qt_api == 'pyside':
    import PySide.QtGui as _QtGui
    locals().update(dict(k, getattr(_QtGui, name)) for name in __all__)
    del _QtGui
