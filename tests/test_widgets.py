#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>
#
# This module is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 2 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this module if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US

from __future__ import print_function

import os
import sys
import logging

# Fix sys path
GSDVIEWROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, GSDVIEWROOT)

from qt import QtWidgets

from gsdview.widgets import (
    AboutDialog, FileEntryWidget, GeneralPreferencesPage, PreferencesDialog,
    GSDViewExceptionDialog,
)


def test_aboutdialog():
    app = QtWidgets.QApplication(sys.argv)
    d = AboutDialog()
    d.show()
    app.exec_()


def test_fileentrywidget():
    app = QtWidgets.QApplication(sys.argv)
    d = QtWidgets.QDialog()
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(FileEntryWidget())
    d.setLayout(layout)
    d.show()
    app.exec_()


def test_generalpreferencespage():
    app = QtWidgets.QApplication(sys.argv)
    d = QtWidgets.QDialog()
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(GeneralPreferencesPage())
    d.setLayout(layout)
    d.show()
    app.exec_()


def test_preferencesdialog():
    app = QtWidgets.QApplication(sys.argv)
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
        app = QtWidgets.QApplication(sys.argv)
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
