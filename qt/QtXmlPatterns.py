# -*- coding: utf-8 -*-

from . import qt_api

if qt_api == 'pyqt5':
    from PyQt5.QtXmlPatterns import *

elif qt_api == 'pyqt4':
    from PyQt4.QtXmlPatterns import *

elif qt_api == 'pyside':
    from PySide.QtXmlPatterns import *
