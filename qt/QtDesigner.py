# -*- coding: utf-8 -*-

from . import qt_api

if qt_api == 'pyqt5':
    from PyQt5.QtDesigner import *

elif qt_api == 'pyqt4':
    from PyQt4.QtDesigner import *

elif qt_api == 'pyside':
    from PySide.QtDesigner import *
