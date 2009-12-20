#!/usr/bin/env python

import os
import sys
import logging

from PyQt4 import QtGui

sys.path.insert(0, os.path.join(os.pardir, os.pardir))

from gsdview.widgets import *

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
            print 1/depth
        else:
            1/depth
        return f(depth-1, verbose)
    try:
        f(4)
    except Exception:
        app = QtGui.QApplication(sys.argv)
        d = GSDViewExceptionDialog()
        #d = ExceptionDialog()
        d.show()
        app.exec_()
    print 'done.'

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_exceptiondialog()
    #~ test_aboutdialog()
    #~ test_fileentrywidget()
    #~ test_generalpreferencespage()
    #~ test_preferencesdialog()
