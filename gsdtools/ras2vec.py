#!/usr/bin/env python

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


'''Generate a vector file containing the bounding box of raster data.

Take in input one or more raster datasets and generate a vector file
containing the bounding box polygon and, optionally, a GCP layer of
each input dataset.

Note: currently only the KML format is supported for output.

This program aims to be an improved and more flexible version of the
gdaltindex utility.

.. seealso: http://www.gdal.org/gdaltindex.html

'''

# @TODO:
#
#   * support more output formats
#   * confogurable spatial reference system
#   * configurable database field for path storage (see gdaltindex)
#   * colors
#   * filling (with transparency)


import os
import sys
import logging

from osgeo import gdal, ogr, osr


__author__ = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__ = '$Date: 2011-07-30 11:07:42 +0200 (sab, 30 lug 2011) $'
__revision__ = '$Revision: 48e066784396 $'
__version__ = '1.0'

if hasattr(os, 'EX_USAGE'):
    EX_USAGE = os.EX_USAGE
else:
    EX_USAGE = 64

DEFAULT_OGRDRIVER = 'KML'


def makesrs(srs):
    # @NOTE: KML by specification uses only a single projection, EPSG:4326
    #        (a.k.a. WGS84)

    if srs is None:
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS('EPSG:4326')
    elif isinstance(srs, basestring):
        spec = srs
        srs = osr.SpatialReference()
        srs.SetFromUserInput(spec)

    return srs


def create_box_layer(ds, name='', srs=None, gtype=ogr.wkbUnknown, opt=None):
    srs = makesrs(srs)

    if opt == None:
        opt = ''

    layer = ds.CreateLayer(name, srs, gtype, opt)

    if layer is None:
        raise RuntimeError('layer creation failed.')

    #~ field = ogr.FieldDefn('Name', ogr.OFTString)
    #~ layer.CreateField(field)

    #~ field = ogr.FieldDefn('Description', ogr.OFTString)
    #~ layer.CreateField(field)

    return layer


def create_GCP_layer(ds, name='', srs=None, gtype=ogr.wkbPoint25D, opt=None):
    srs = makesrs(srs)

    if opt == None:
        opt = ''

    layer = ds.CreateLayer(name, srs, gtype, opt)

    if layer is None:
        raise RuntimeError('layer creation failed.')

    #~ field = ogr.FieldDefn('Name', ogr.OFTString)
    #~ layer.CreateField(field)

    #~ field = ogr.FieldDefn('Description', ogr.OFTString)
    #~ layer.CreateField(field)

    #field = ogr.FieldDefn('X', ogr.OFTReal)
    #layer.CreateField(field)
    #
    #field = ogr.FieldDefn('Y', ogr.OFTReal)
    #layer.CreateField(field)
    #
    #field = ogr.FieldDefn('Z', ogr.OFTReal)
    #layer.CreateField(field)

    field = ogr.FieldDefn('Pixel', ogr.OFTReal)
    layer.CreateField(field)

    field = ogr.FieldDefn('Line', ogr.OFTReal)
    layer.CreateField(field)

    field = ogr.FieldDefn('Info', ogr.OFTString)
    layer.CreateField(field)

    field = ogr.FieldDefn('Id', ogr.OFTString)
    layer.CreateField(field)

    return layer


def geographic_info(ds, srsout=None):
    # Read geotransform matrix and source reference system
    srs = osr.SpatialReference()
    if ds.GetGCPCount():
        gcps = ds.GetGCPs()
        srs.ImportFromWkt(ds.GetGCPProjection())
        geomatrix = gdal.GCPsToGeoTransform(gcps)
    else:
        gcps = []
        if not ds.GetProjection():
            raise ValueError('no geographic info in "%s"' %
                                                        ds.GetDescription())
        srs.ImportFromWkt(ds.GetProjection())
        geomatrix = ds.GetGeoTransform()

    if geomatrix == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        raise ValueError('no geographic info in "%s"' % ds.GetDescription())

    # Set the target reference system
    srsout = makesrs(srsout)

    # Instantiate the coordinate transformer
    transformer = osr.CoordinateTransformation(srs, srsout)

    # dataset corners setup
    corners = []
    for id_, (pixel, line) in enumerate((
                                (0,                  0),
                                (0,                  ds.RasterYSize - 1),
                                (ds.RasterXSize - 1, ds.RasterYSize - 1),
                                (ds.RasterXSize - 1, 0))):

        X = geomatrix[0] + geomatrix[1] * pixel + geomatrix[2] * line
        Y = geomatrix[3] + geomatrix[4] * pixel + geomatrix[5] * line

        # Shift to the center of the pixel
        X += geomatrix[1] / 2.0
        Y += geomatrix[5] / 2.0
        Z = 0.

        (x, y, z) = transformer.TransformPoint(X, Y, Z)

        gcp = gdal.GCP(x, y, z, pixel, line, '', str(id_ + 1))
        corners.append(gcp)

    # convert GCPs to the targer srs
    outgcps = []
    for gcp in gcps:
        (x, y, z) = transformer.TransformPoint(gcp.GCPX, gcp.GCPY, gcp.GCPZ)
        gcp = gdal.GCP(x, y, z, gcp.GCPPixel, gcp.GCPLine, gcp.Info, gcp.Id)
        outgcps.append(gcp)

    return corners, outgcps


def export_bounding_box(layer, corners, description='', mark_corners=True):
    # ring
    ring = ogr.Geometry(type=ogr.wkbLinearRing)
    for gcp in corners:
        ring.AddPoint_2D(gcp.GCPX, gcp.GCPY)
    ring.CloseRings()

    # polygon
    poly = ogr.Geometry(type=ogr.wkbPolygon)
    poly.AddGeometry(ring)

    # feature
    featurename = 'bounding box'
    if description and os.path.basename(description) not in layer.GetName():
        featurename = os.path.basename(description)

    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetField('Name', featurename)
    feature.SetField('Description', description)
    feature.SetStyleString('BRUSH(fc:#FF000064);PEN(c:#FF0000)')  # red filled
    feature.SetGeometry(poly)

    if layer.CreateFeature(feature) != 0:
        raise RuntimeError('failed to create a new feature.')
    feature.Destroy()

    if mark_corners:
        for gcp in corners:
            point = ogr.Geometry(type=ogr.wkbPoint)
            point.SetPoint_2D(0, gcp.GCPX, gcp.GCPY)

            line, pixel = gcp.GCPLine, gcp.GCPPixel
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField('Name', '(%.1f, %.1f)' % (line, pixel))
            feature.SetField('Description',
                             'row = %.1f\ncol = %.1f' % (line, pixel))
            feature.SetStyleString('SYMBOL(c:#FF0000)')     # red

            feature.SetGeometry(point)

            if layer.CreateFeature(feature) != 0:
                raise RuntimeError('failed to create a new feature.')
            feature.Destroy()


def export_gcps(layer, gcps):
    for id_, gcp in enumerate(gcps):

        if gcp.Id:
            id_ = gcp.Id

        point = ogr.Geometry(type=ogr.wkbPoint25D)
        point.SetPoint(0, gcp.GCPX, gcp.GCPY, gcp.GCPZ)

        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField('Name', 'GCPs %s' % id_)
        feature.SetField('Description', gcp.Info)

        #feature.SetField('X', gcp.GCPX)
        #feature.SetField('Y', gcp.GCPY)
        #feature.SetField('Z', gcp.GCPZ)

        feature.SetField('Pixel', gcp.GCPPixel)
        feature.SetField('Line', gcp.GCPLine)
        feature.SetField('Info', gcp.Info)
        feature.SetField('Id', gcp.Id)
        feature.SetGeometry(point)

        if layer.CreateFeature(feature) != 0:
            raise RuntimeError('failed to create a new feature.')
        feature.Destroy()


def create_datasource(filename, drivername=None):
    if not drivername:
        drivername = DEFAULT_OGRDRIVER
    driver = ogr.GetDriverByName(drivername)
    if not driver:
        raise RuntimeError('unable to instantiate the "%s" driver.' %
                                                                drivername)
    else:
        logging.info('using "%s" driver.' % drivername)

    ds = driver.CreateDataSource(filename)
    if ds is None:
        raise RuntimeError('creation of output file ("%s") failed.' % filename)
    logging.info('output file: "%s".' % filename)

    return ds


def export_raster(src, dst, boxlayer=None, gcplayer=None, srsout=None,
                  mark_corners=True):
    if isinstance(src, basestring):
        filename = src
        src = gdal.Open(filename)
        if src is None:
            raise RuntimeError('unable to open source dataset: "%s"' %
                                                                    filename)

    if isinstance(dst, basestring):
        dst = create_datasource(dst)

    # Set the target reference system
    srsout = makesrs(srsout)

    # Instantiate the coordinate transformer
    corners, gcps = geographic_info(src, srsout)

    # Bounding box
    description = src.GetDescription().strip()
    if boxlayer is None or boxlayer == '':
        boxlayername = os.path.basename(description)
        boxlayer = create_box_layer(dst, boxlayername, srsout)
    elif boxlayer and isinstance(boxlayer, basestring):
        boxlayername = boxlayer
        boxlayer = dst.GetLayerByName(boxlayername)
        if boxlayer is None:
            boxlayer = create_box_layer(dst, boxlayername, srsout)

    if boxlayer is None:
        raise RuntimeError('unable to create a new layer.')

    export_bounding_box(boxlayer, corners, description, mark_corners)

    # GCPs
    if gcps and gcplayer is not False:
        if gcplayer in (None, True, ''):
            gcplayername = 'gcps_%s' % os.path.basename(description)
            gcplayer = create_GCP_layer(dst, gcplayername, srsout)
        elif gcplayer and isinstance(gcplayer, basestring):
            gcplayername = gcplayer
            gcplayer = dst.GetLayerByName(gcplayername)
            if gcplayer is None:
                gcplayer = create_GCP_layer(dst, gcplayername, srsout)

        if gcplayer is None:
            raise RuntimeError('unable to create a new layer.')

        export_gcps(gcplayer, gcps)

    return boxlayer, gcplayer


def compact_index(srclist, dst):
    if isinstance(dst, basestring):
        dst = create_datasource(dst)

    # Bounding box
    boxlayername = 'index'

    boxlayer = dst.GetLayerByName(boxlayername)
    if boxlayer is None:
        boxlayer = create_box_layer(dst, boxlayername)

    for src in srclist:
        logging.info('adding "%s"' % src)

        if isinstance(src, basestring):
            filename = src
            src = gdal.Open(filename)
            if src is None:
                logging.error('unable to open source dataset: "%s"' % filename)
                continue

        try:
            export_raster(src, dst, boxlayer, False, mark_corners=False)
        except ValueError, e:
            if 'no geographic info' in str(e):
                logging.error(str(e))
            else:
                raise

        subdatasets = [subds for subds, descr in src.GetSubDatasets()]
        if subdatasets:
            compact_index(subdatasets, dst)


def raster_index(srclist, dst, gcplayer=False, mark_corners=False):
    if isinstance(dst, basestring):
        dst = create_datasource(dst)

    # Bounding box
    for src in srclist:
        logging.info('adding "%s"' % src)

        if isinstance(src, basestring):
            filename = src
            src = gdal.Open(filename)
            if src is None:
                logging.error('unable to open source dataset: "%s"' % filename)
                continue

        try:
            export_raster(src, dst, None, gcplayer, mark_corners=mark_corners)
        except ValueError, e:
            if 'no geographic info' in e.message:
                logging.error(str(e))
            else:
                raise

        subdatasets = [subds for subds, descr in src.GetSubDatasets()]
        if subdatasets:
            raster_index(subdatasets, dst, gcplayer, mark_corners)


def raster_tree_index(src, dst, boxlayer=None, gcplayer=None,
                      mark_corners=False):
    assert os.path.isdir(src)

    if isinstance(dst, basestring):
        dst = create_datasource(dst)

    gdal.PushErrorHandler('CPLQuietErrorHandler')
    for root, dirs, files,  in os.walk(src):
        for filename in files:
            try:
                filename = os.path.join(root, filename)
                export_raster(filename, dst, boxlayer, gcplayer,
                              mark_corners=mark_corners)
            except (RuntimeError, ValueError):
                #logging.exception(str(e))
                logging.info('skip "%s"' % filename)
            else:
                logging.info('adding "%s"' % filename)

    gdal.PopErrorHandler()


### Command line tool #########################################################
def handlecmd(argv=None):
    import optparse

    # @NOTE: ogr.GeneralCmdLineProcessor is not available in GDAL 1.6.x
    argv = gdal.GeneralCmdLineProcessor(argv)

    parser = optparse.OptionParser(
                        usage='%prog [options] OUTPUT INPUT [INPUT [...]]',
                        version='%%prog %s' % __version__,
                        description=__doc__)
    #parser.add_option('-o', '--outfile', type='str',
    #                  help='output file name (default: generated)')
    #parser.add_option('-f', '--format', type='str', default='KML',
    #                  help='output vector format (default: %default)')
    #parser.add_option('-s', '--t_srs', type='str', default='EPSG:4326'
    #                  help='target spatial reference system '
    #                       '(default: %default)')
    parser.add_option('-g', '--gcps', action='store_true', default=False,
                      help='generate an additional layer for GCPs '
                           '(default: %default)')
    parser.add_option('-c', '--corners', action='store_true', default=False,
                      help='generate markers for bounding box corners '
                           '(default: %default)')
    parser.add_option('-a', '--abspath', action='store_true', default=False,
                      help='store absolute path in bounding box feature '
                           'description (default: %default)')

    options, args = parser.parse_args()

    if len(args) < 2:
        parser.error('at least two arguments are required.')

    #~ if options.t_srs and options.format in ('KML', 'LIBKML'):
        #~ epsg4326 = osr.SpatialReference()
        #~ epsg4326.SetWellKnownGeogCS('EPSG:4326')

        #~ tsrs = osr.SpatialReference()
        #~ tsrs.SetFromUserInput(oprions.t_srs)
        #~ if not epsg4326.IsSame(tsrs):
            #~ logging.warning('KML format only supports "EPSG:4326" as '
                            #~ 'target spatial reference system: '
                            #~ '"t_srs" parameter will be ignred.')
            #~ options.t_srs = epsg4326
        #~ else:
            #~ options.t_srs = tsrs

    return options, args


def main(*argv):
    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=logging.INFO)

    try:
        if not argv:
            argv = sys.argv

        options, args = handlecmd(argv)
        outfile = args.pop(0)
        if os.path.exists(outfile):
            logging.error('the output file ("%s") already exists.' % outfile)
            sys.exit(EX_USAGE)
        dst = create_datasource(outfile)    # , options.format)

        if len(args) > 1:
            if options.abspath:
                args = [os.path.abspath(name) for name in args]

            if options.gcps or options.corners:
                raster_index(args, dst, options.gcps, options.corners)
            else:
                compact_index(args, dst)
        else:
            inputpath = args[0]
            if options.abspath:
                inputpath = os.path.abspath(inputpath)

            if options.gcps:
                gcplayer = 'GCPs'
            else:
                gcplayer = False

            if os.path.isdir(inputpath):
                if options.gcps or options.corners:
                    boxlayer = None
                else:
                    boxlayer = os.path.basename(os.path.normpath(inputpath))
                raster_tree_index(inputpath, dst,
                                  boxlayer=boxlayer, gcplayer=options.gcps,
                                  mark_corners=options.corners)
            else:
                export_raster(inputpath, dst,
                              boxlayer='box', gcplayer=gcplayer,
                              mark_corners=options.corners)

    except Exception as e:
        logging.error(str(e), exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
