# -*- coding: utf-8 -*-

from . import qt_api

if qt_api == 'pyqt5':
    from PyQt5.QtHelp import *

elif qt_api == 'pyqt4':
    from PyQt4.QtHelp import *

elif qt_api == 'pyside':
    from PySide.QtHelp import *
