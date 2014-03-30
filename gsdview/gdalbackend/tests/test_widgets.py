#!/usr/bin/env python

from __future__ import pront_function

import os
import sys
import logging

from osgeo import gdal

# Fix sys path
from os.path import abspath, dirname
GSDVIEWROOT = abspath(os.path.join(dirname(__file__),
                                   os.pardir, os.pardir, os.pardir))
sys.path.insert(0, GSDVIEWROOT)

from qt import QtGui

from gsdview.gdalbackend.widgets import (
    GDALInfoWidget, GDALPreferencesPage, DatasetInfoDialog, BandInfoDialog,
    HistogramConfigDialog, OverviewWidget, OverviewDialog,
)


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


def test_histogram_config():
    app = QtGui.QApplication(sys.argv)
    dialog = HistogramConfigDialog()
    dialog.show()
    sys.exit(app.exec_())


def testdriver(target, imagestruct=True):
    logging.basicConfig(level=logging.DEBUG)

    filename = os.path.join(GSDVIEWROOT, 'gsdview', 'plugins',
                            'worldmap', 'images', 'world_4320x2160.jpg')

    if imagestruct is False:
        # convert to palatted image
        pctfilename = os.path.join(GSDVIEWROOT, 'gsdview', 'gdalbackend',
                                   'tests', 'world_pct.jpeg')

        if not os.path.exists(pctfilename):
            import subprocess

            subprocess.call(('rgb2pct.py', filename, pctfilename))
        filename = pctfilename

    dataset = gdal.Open(filename)
    for index in range(1, 6):
        dataset.SetMetadataItem('KEY%d' % index, 'VALUE%d' % index)

    if target == 'dataset':
        test_datasetdialog(dataset)
    elif target == 'band':
        band = dataset.GetRasterBand(1)
        for index in range(11, 16):
            band.SetMetadataItem('KEY%d' % index, 'VALUE%d' % index)

        test_rasterbanddialog(band)
    else:
        raise ValueError('trget: %s' % target)


def test_ovrwidget():
    filename = os.path.join(GSDVIEWROOT, 'gsdview', 'plugins',
                            'worldmap', 'images', 'world_4320x2160.jpg')
    dataset = gdal.Open(filename)
    band = dataset.GetRasterBand(1)

    if True and band.GetOverviewCount() == 0:
        dataset.BuildOverviews('average', [2, 4, 8], gdal.TermProgress)

    app = QtGui.QApplication(sys.argv)

    w = OverviewWidget(band)
    w.show()

    def callback():
        args = w.optionlist()
        levels = [str(level) for level in w.levels()]

        parts = ['gdaladdo']
        parts.extend(args)
        parts.append(os.path.basename(filename))
        parts.extend(levels)

        print(' '.join(parts))

    w.overviewComputationRequest.connect(callback)

    sys.exit(app.exec_())


def test_ovrdialog():
    filename = os.path.join(GSDVIEWROOT, 'gsdview', 'plugins',
                            'worldmap', 'images', 'world_4320x2160.jpg')
    dataset = gdal.Open(filename)

    app = QtGui.QApplication(sys.argv)

    d = OverviewDialog()
    d.setItem(dataset)
    d.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    #~ test_gdalinfowidget()
    #~ test_gdalpreferencespage()
    #~ test_histogram_config()
    testdriver('dataset', True)
    #~ testdriver('dataset', False)
    #~ testdriver('band', True)
    #~ testdriver('band', False)
    #~ test_ovrwidget()
    #~ test_ovrdialog()
