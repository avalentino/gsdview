#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Copyright (C) 2008-2011 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of GSDView.

### GSDView is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### GSDView is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with GSDView; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA.

import os
import sys
import logging

from gsdview.qt import QtGui

# Fix sys path
from os.path import abspath, dirname
parts = [dirname(__file__)] + [os.pardir] * 4
GSDVIEWROOT = abspath(os.path.join(*parts))
del parts
sys.path.insert(0, GSDVIEWROOT)
sys.path.insert(1, os.path.join(GSDVIEWROOT, 'gsdview', 'plugins'))

from stretch.widgets import *


def test_stretchingdialog(floatmode=False):
    app = QtGui.QApplication(sys.argv)
    d = StretchDialog()
    #state = d.stretchwidget.state()
    d.stretchwidget.floatmode = floatmode
    d.show()
    app.exec_()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #~ test_stretchingdialog()
    test_stretchingdialog(True)
