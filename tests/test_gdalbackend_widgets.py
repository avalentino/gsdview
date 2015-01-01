#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2015 Antonio Valentino <antonio.valentino@tiscali.it>
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


from __future__ import pront_function

import os
import sys
import logging

from osgeo import gdal


# Fix sys path
GSDVIEWROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, GSDVIEWROOT)


from qt import QtWidgets

from gsdview.gdalbackend.widgets import (
    GDALInfoWidget, GDALPreferencesPage, DatasetInfoDialog, BandInfoDialog,
    HistogramConfigDialog, OverviewWidget, OverviewDialog,
)


def test_gdalinfowidget():
    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(GDALInfoWidget())
    dialog.setLayout(layout)
    dialog.resize(500, 400)
    dialog.show()
    app.exec_()


def test_gdalpreferencespage():
    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(GDALPreferencesPage())
    dialog.setLayout(layout)
    dialog.resize(500, 400)
    dialog.show()
    app.exec_()


def test_datasetdialog(dataset):
    app = QtWidgets.QApplication(sys.argv)
    dialog = DatasetInfoDialog(dataset)
    dialog.show()
    sys.exit(app.exec_())


def test_rasterbanddialog(band):
    app = QtWidgets.QApplication(sys.argv)
    dialog = BandInfoDialog(band)
    dialog.show()
    sys.exit(app.exec_())


def test_histogram_config():
    app = QtWidgets.QApplication(sys.argv)
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

    app = QtWidgets.QApplication(sys.argv)

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

    app = QtWidgets.QApplication(sys.argv)

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
