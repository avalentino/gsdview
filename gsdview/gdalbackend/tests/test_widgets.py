#!/usr/bin/env python

import os
import sys
sys.path.insert(0, os.path.join(os.pardir, os.pardir, os.pardir))

import logging

from osgeo import gdal
from PyQt4 import QtGui

from gsdview.gdalbackend.widgets import *

def test_gdalinfowidget():
    app = QtGui.QApplication(sys.argv)
    dialog = QtGui.QDialog()
    layout = QtGui.QVBoxLayout()
    layout.addWidget(GDALInfoWidget())
    dialog.setLayout(layout)
    dialog.resize(500, 400)
    dialog.show()
    app.exec_()

def test_gdalpreferencespage():
    app = QtGui.QApplication(sys.argv)
    dialog = QtGui.QDialog()
    layout = QtGui.QVBoxLayout()
    layout.addWidget(GDALPreferencesPage())
    dialog.setLayout(layout)
    dialog.resize(500, 400)
    dialog.show()
    app.exec_()

def test_datasetdialog(dataset):
    app = QtGui.QApplication(sys.argv)
    dialog = DatasetInfoDialog(dataset)
    dialog.show()
    sys.exit(app.exec_())

def test_rasterbanddialog(band):
    app = QtGui.QApplication(sys.argv)
    dialog = BandInfoDialog(band)
    dialog.show()
    sys.exit(app.exec_())

def main():
    logging.basicConfig(level=logging.DEBUG)

    filename = '../../plugins/worldmap/images/world_4320x2160.jpg'

    #~ pctfilename = 'world_pct.jpeg'
    #~ if not os.path.exists(pctfilename):
        #~ import subprocess

        #~ subprocess.call(('rgb2pct.py',  filename, pctfilename))
    #~ filename = pctfilename

    dataset_ = gdal.Open(filename)
    band_ = dataset_.GetRasterBand(1)

    #~ test_datasetdialog(dataset_)
    test_rasterbanddialog(band_)

if __name__ == '__main__':
    #~ test_gdalinfowidget()
    #~ test_gdalpreferencespage()
    main()
