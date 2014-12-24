# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# Copyright (c) 2010, Enthought Inc
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license.
#
#
# Author: Enthought Inc
# Description: Qt API selector. Can be used to switch between pyQt and PySide
# -----------------------------------------------------------------------------

from . import qt_api

if qt_api == 'pyqt5':
    from PyQt5.QtCore import *

    from PyQt5.QtCore import pyqtProperty as Property
    from PyQt5.QtCore import pyqtSignal as Signal
    from PyQt5.QtCore import pyqtSlot as Slot

    __version__ = QT_VERSION_STR
    __version_info__ = tuple(map(int, QT_VERSION_STR.split('.')))

elif qt_api == 'pyqt4':
    from PyQt4.QtCore import *

    from PyQt4.QtCore import pyqtProperty as Property
    from PyQt4.QtCore import pyqtSignal as Signal
    from PyQt4.QtCore import pyqtSlot as Slot

    __version__ = QT_VERSION_STR
    __version_info__ = tuple(map(int, QT_VERSION_STR.split('.')))

elif qt_api == 'pyside':
    from PySide.QtCore import *

    try:
        from PySide import __version__, __version_info__
    except ImportError:
        pass
    else:
        QT_VERSION_STR = __version__
