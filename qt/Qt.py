# -*- coding: utf-8 -*-

from . import qt_api

if qt_api == 'pyqt5':
    from PyQt5.Qt import *

elif qt_api == 'pyqt4':
    from PyQt4.Qt import *

elif qt_api == 'pyside':
    from PySide.Qt import *
    from PySide.QtGui import QKeySequence, QTextCursor
