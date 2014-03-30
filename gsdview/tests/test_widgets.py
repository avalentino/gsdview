#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Copyright (C) 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>

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

from __future__ import print_function

import os
import sys
import logging

# Fix sys path
from os.path import abspath, dirname
GSDVIEWROOT = abspath(os.path.join(dirname(__file__), os.pardir, os.pardir))
sys.path.insert(0, GSDVIEWROOT)

from qt import QtGui

from gsdview.widgets import (
    AboutDialog, FileEntryWidget, GeneralPreferencesPage, PreferencesDialog,
    GSDViewExceptionDialog,
)


def test_aboutdialog():
    app = QtGui.QApplication(sys.argv)
    d = AboutDialog()
    d.show()
    app.exec_()


def test_fileentrywidget():
    app = QtGui.QApplication(sys.argv)
    d = QtGui.QDialog()
    layout = QtGui.QVBoxLayout()
    layout.addWidget(FileEntryWidget())
    d.setLayout(layout)
    d.show()
    app.exec_()


def test_generalpreferencespage():
    app = QtGui.QApplication(sys.argv)
    d = QtGui.QDialog()
    layout = QtGui.QVBoxLayout()
    layout.addWidget(GeneralPreferencesPage())
    d.setLayout(layout)
    d.show()
    app.exec_()


def test_preferencesdialog():
    app = QtGui.QApplication(sys.argv)
    d = PreferencesDialog()
    d.show()
    app.exec_()


def test_exceptiondialog():
    def f(depth, verbose=False):
        if verbose:
            print(1 / depth)
        else:
            1 / depth
        return f(depth - 1, verbose)
    try:
        f(4)
    except Exception:
        app = QtGui.QApplication(sys.argv)
        d = GSDViewExceptionDialog()
        #d = ExceptionDialog()
        d.show()
        app.exec_()
    print('done.')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #~ test_exceptiondialog()
    #~ test_aboutdialog()
    #~ test_fileentrywidget()
    #~ test_generalpreferencespage()
    test_preferencesdialog()
