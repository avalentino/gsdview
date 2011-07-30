# -*- coding: utf-8 -*-

#------------------------------------------------------------------------------
# Copyright (c) 2010, Enthought Inc
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD license.

#
# Author: Enthought Inc
# Description: Qt API selector. Can be used to switch between pyQt and PySide
#------------------------------------------------------------------------------

from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.QtSvg import *

else:
    from PySide.QtSvg import *
