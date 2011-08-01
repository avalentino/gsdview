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


'''Helper tools and custom components for binding OGR and Qt4.'''

__author__ = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__ = '$Date: 2011-07-30 13:19:15 +0200 (sab, 30 lug 2011) $'
__revision__ = '$Revision: 36b7b35ff3b6 $'


import logging

from osgeo import ogr, osr

from qt import QtCore, QtGui

from .. import qt4draw


### Graphics Items ############################################################
#~ class GraphicsLayerItem(qt4draw.GraphicsItemGroup):
    #~ '''Qt graphics item representing an OGR Layer.'''

    #~ Type = QtGui.QGraphicsItem.UserType + 102

    #~ def __init__(self, name=None, index=None, datasource=None,
                 #~ parent=None, scene=None, **kargs):
        #~ super(GraphicsLayerItem, self).__init__(parent, scene, **kargs)

        #~ self.name = name
        #~ self.index = index
        #~ self.datasource = datasource

        #~ if name:
            #~ self.setToolTip('Layer: %s' % name)

    #~ def graphicsFeature(self, fid):
        #~ #return  self.childItems()[fid]
        #~ for item in self.childItems():
            #~ try:
                #~ if item.fid == fid:
                    #~ return item
            #~ except AttributeError:
                #~ logging.debug('item "%s" has no feature ID.' % item)
        #~ return None


#~ class GraphicsFeatureItem(qt4draw.GraphicsItemGroup):
    #~ '''Qt graphics item representing an OGR feature.'''

    #~ Type = QtGui.QGraphicsItem.UserType + 103

    #~ def __init__(self, fid=None, parent=None, scene=None, **kargs):
        #~ super(GraphicsFeatureItem, self).__init__(parent, scene, **kargs)

        #~ self.fid = fid


### Helpers for geometry management ###########################################
def transformGeometry(geom, transform):
    '''Apply an OSR transform to an OGR geometry.

    This function is almost equal to the ogr.Geometry.Transform method
    but raises an exception if the conversion fails and clone the
    geometry before performing the transformation in order to leave the
    original geometry unmodified.

    :param geom:
        OGR geometry
    :param transform:
        OSR transformer
    :returns:
        a new geometry instance with transforation applied

    '''

    geom = geom.Clone()  # @TODO: check
    err = geom.Transform(transform)
    if err:
        raise ValueError('geomery coordinate transformation failed')

    return geom


def singleGeometryToGraphicsItem(geom, transform=None):
    '''Convert a single OGR geometry into a Qt4 graphics item.

    A "single geometry" is an OGR gemetry that don't include other
    geometries (GetGeometryCount() == 0).

    If the *transform* callable is provided then each point in the
    geometry is converted using the `transform(x, y, z)` call before
    genereting the graphics item path.

    .. note: for 2.5D geometries the *z* value is ignored.

    :param geom:
        a single OGR geometry
    :param transform:
        callable object for arbitrary coordinate conversion
    :returns:
        a Qt4 graphics item representing the geometry

    .. seealso:: :func:`geometryToGraphicsItem`

    '''

    assert geom.GetGeometryCount() == 0

    gtype = geom.GetGeometryType()
    if gtype in (ogr.wkbPoint, ogr.wkbPoint25D):

        # @TODO: check
        RADIUS = 3

        point = geom.GetPoint()
        if transform:
            point = transform(*point)
        qitem = qt4draw.GraphicsPointItem(point[0], point[1], RADIUS)

        # @TODO: style options should be set in a more general way.
        #        Probably it is better to set them in an external function.
        # Red point
        pen = qitem.pen()
        pen.setColor(QtCore.Qt.red)
        #pen.setWidth(15)
        qitem.setPen(pen)

        brush = qitem.brush()
        brush.setColor(QtCore.Qt.red)
        #brush.setStyle(QtCore.Qt.SolidPattern)
        qitem.setBrush(brush)

    elif (gtype in (ogr.wkbLineString, ogr.wkbLineString25D) and
                                                geom.GetPointCount() == 2):
        p0 = geom.GetPoint(0)
        p1 = geom.GetPoint(1)
        if transform:
            p0 = transform(*p0)
            p1 = transform(*p1)
        qline = QtCore.QLineF(p0[0], p0[1], p1[0], p1[1])
        qitem = QtGui.QGraphicsLineItem(qline)

    elif gtype in (ogr.wkbLinearRing, ogr.wkbPolygon, ogr.wkbPolygon25D,
                   ogr.wkbLineString, ogr.wkbLineString25D):

        # @NOTE: use only if geometry is a ring
        if geom.IsRing():
            qpoly = QtGui.QPolygonF(geom.GetPointCount())
            for index in range(geom.GetPointCount()):
                point = geom.GetPoint(index)
                if transform:
                    point = transform(*point)
                qpoly[index] = QtCore.QPointF(point[0], point[1])
            qitem = QtGui.QGraphicsPolygonItem(qpoly)
            #qitem.setFillRule(QtCore.Qt.WindingFill)    # @TODO: check
        else:
            qpath = QtGui.QPainterPath()
            #qpath.setFillRule(QtCore.Qt.WindingFill)    # @TODO: check
            point = geom.GetPoint(0)
            if transform:
                point = transform(*point)
            qpath.moveTo(point[0], point[1])
            for index in range(1, geom.GetPointCount()):
                point = geom.GetPoint(index)
                if transform:
                    point = transform(*point)
                qpath.lineTo(point[0], point[1])
            qitem = QtGui.QGraphicsPathItem(qpath)

    elif gtype in (ogr.wkbMultiPoint, ogr.wkbMultiPoint25D,
                   ogr.wkbMultiLineString, ogr.wkbMultiLineString25D,
                   ogr.wkbMultiPolygon, ogr.wkbMultiPolygon25D,
                   ogr.wkbGeometryCollection, ogr.wkbGeometryCollection25D):

        raise ValueError('should not happen.')

    elif gtype in (ogr.wkbUnknown, ogr.wkbNone):
        raise ValueError('invalid geopetry type: '
                         '"%s"' % geom.GetGeometryName())

    else:
        raise ValueError('invalid geopetry type: "%d"' % gtype)

    return qitem


def geometryToGraphicsItem(geom, transform=None):
    '''Convert an OGR geometry into a Qt4 graphics item.

    If the *transform* callable is provided then each point in the
    geometry is converted using the `transform(x, y, z)` call before
    genereting the graphics item path.

    .. note: for 2.5D geometries the *z* value is ignored.

    :param geom:
        an OGR geometry
    :param transform:
        callable object for arbitrary coordinate conversion
    :returns:
        a Qt4 graphics item representing the geometry

    .. seealso:: :func:`singleGeometryToGraphicsItem`

    '''

    if geom.GetGeometryCount() > 1:
        #qitem = QtGui.QGraphicsItemGroup()
        qitem = qt4draw.GraphicsItemGroup()
        for index, subgeom in enumerate(geom):
            qsubitem = geometryToGraphicsItem(subgeom, transform)
            if qsubitem:
                qsubitem.setData(DATAKEY['index'], index)
                qitem.addToGroup(qsubitem)
            else:
                logging.debug('unable to instantiate a graphics item from '
                              'OGR geometry "%s"' % subgeom)
        #qitem.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        return qitem
    elif geom.GetGeometryCount() == 1:
        subgeom = geom.GetGeometryRef(0)
        return geometryToGraphicsItem(subgeom, transform)
    else:
        qitem = singleGeometryToGraphicsItem(geom, transform)

    qitem.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)

    return qitem

#: the max number of features that are converted whan the graphics item
#: for a layer is generated
MAX_FEATURE_COUNT = 600
DATAKEY = {
    'name': 1,
    'index': 2,
    'datasource': 3,
    'FID': 4,
}


def layerToGraphicsItem(layer, srs=None, transform=None):
    '''Convert an OGR layer into a Qt4 graphics item.

    If the *srs* parameter is provided each feature is converted into
    the target spatial reference system before generating the graphics
    item.

    If the *transform* callable is provided then each point in the
    geometry is converted using the `transform(x, y, z)` call before
    genereting the graphics item path.

    .. note: for 2.5D geometries the *z* value is ignored.

    :param layer:
        ane OGR layer
    :param srs:
        the target OSR spatial reference system
    :param transform:
        callable object for arbitrary coordinate conversion
    :returns:
        a Qt4 graphics item (QGraphicsItemGroup) representing the layer

    .. seealso:: :func:`singleGeometryToGraphicsItem`,
                 :func:`geometryToGraphicsItem` and
                 :data:`MAX_FEATURE_COUNT`

    '''

    layer_srs = layer.GetSpatialRef()
    if (srs is not None and layer_srs is not None and
                                            not layer_srs.IsSame(srs)):
        srs_transform = osr.CoordinateTransformation(layer_srs, srs)
    else:
        srs_transform = None

    if layer.GetFeatureCount() > MAX_FEATURE_COUNT:
        raise RuntimeError('too many features in layed %s: %d' % (
                                    layer.GetName(), layer.GetFeatureCount()))

    #~ print 'extent:', layer.GetExtent() # @TODO: check
    #qlayer = GraphicsLayerItem(layer.GetName())
    qlayer = qt4draw.GraphicsItemGroup()
    qlayer.setData(DATAKEY['name'], layer.GetName())
    for feature in layer:
        #qfeature = GraphicsFeatureItem(feature.GetFID())
        qfeature = qt4draw.GraphicsItemGroup()
        qfeature.setData(DATAKEY['FID'], feature.GetFID())

        geom = feature.GetGeometryRef()
        if geom:
            geotransform = srs_transform
            geom_srs = geom.GetSpatialReference()
            if geom_srs:
                if (layer_srs is not None and not geom_srs.IsSame(layer_srs)):
                    if srs is not None:
                        geotransform = osr.CoordinateTransformation(geom_srs,
                                                                    srs)
                    else:
                        geotransform = osr.CoordinateTransformation(geom_srs,
                                                                    layer_srs)
                elif srs is not None and not geom_srs.IsSame(srs):
                    geotransform = osr.CoordinateTransformation(geom_srs, srs)

            if geotransform:
                geom = transformGeometry(geom, geotransform)

            qitem = geometryToGraphicsItem(geom, transform)
            if qitem:
                qfeature.addToGroup(qitem)
            else:
                logging.warning('unable to instantiate a graphics '
                                'item from OGR geometry "%s"' % geom)
        else:
            logging.info('feature %d has no geometry' %
                                                    feature.GetFID())
        qlayer.addToGroup(qfeature)

    nfeatures = len(qlayer.childItems())
    if nfeatures != layer.GetFeatureCount():
        logging.warning('only %d of %d geometries converted to graphics items '
                        'for layer "%s"' % (nfeatures, layer.GetFeatureCount(),
                                            layer.GetName()))

    qlayer.setToolTip('Layer "%s": %d features.' % (layer.GetName(),
                                                    nfeatures))

    return qlayer


### Helpers for layers management #############################################
#~ class LayerItemModel(QtGui.QStandardItemModel):
    #~ #def __init__(self, parent=None, **kargs):
    #~ #    super(LayerItemModel, self).__init__(parent, **kargs)
    #~ #    # @TODO: spatial filter

    #~ def addLayer(self, layer):
        #~ '''Add a new layer on top of the stack.'''

        #~ pass

    #~ def insertLayer(self, row, layer):
        #~ '''Insert a new layer in the specified position.'''

        #~ pass

    #~ def removeLayer(self, layer):
        #~ '''Remove specified layer.'''

        #~ if not isinstance(layer, basestring):
            #~ name = layer.GetName()
        #~ else:
            #~ name = layer

        #~ pass

    #~ def move(self, src, dst):
        #~ pass

    #~ def move(self, itemselection, dst):
        #~ #QItemSelection
        #~ pass

    #~ def moveToTop(self, row):
        #~ pass

    #~ def moveToTop(self, itemselection):
        #~ #QItemSelection
        #~ pass

    #~ def moveToBottom(self, row):
        #~ pass

    #~ def moveToBottom(self, itemselection):
        #~ #QItemSelection
        #~ pass

    #~ def _updateZValues(self):
        #~ # ??
        #~ pass


### OGR feature style #########################################################
'''Style String Syntax

Each feature object has a style property (a string)::

  <style_property> = "<style_def>" | "" | "@<style_name>" | "{<field_name>}"

* "<style_def>" is defined later in this section.
* An empty style property means that the feature directly inherits its
  style from the layer it is in.
* "@<style_name>" is a reference to a predefined style in the layer or
  the dataset's style table. The layer's table is looked up first,
  and if style_name is not found there then the dataset's table will be
  looked up.
* Finally, "{<field_name>}" means that the style property should be
  read from the specified attribute field.

The <style_def> is the real style definition.
It is a combination of 1 or more style parts separated by semicolons.
Each style_part uses a drawing tool to define a portion of the complete
graphical representation::

  <style_def>   = <style_part>[;<style_part>[;...]]
  <style_part>  = <tool_name>([<tool_param>[,<tool_param>[,...]]])
  <tool_name>   = name of a drawing tool, for now: PEN | BRUSH | SYMBOL | LABEL
  <tool_param>  = <param_name>:<param_value>
  <param_name>  = see list of parameters names for each drawing tool
  <param_value> = <value> | <value><units>
  <value>       = "<string_value>" | <numeric_value> | {<field_name>}
  <units>       = g | px | pt | mm | cm | in


.. seealso:: http://www.gdal.org/ogr/ogr_feature_style.html sect 2.2

'''


#gdal-1.8.x/src/autotest/ogr/ogr_dgn.py
#gdal-1.8.x/src/autotest/ogr/ogr_dxf.py
#gdal-1.8.x/src/autotest/ogr/ogr_openir.py
#gdal-1.8.x/src/autotest/ogr/ogr_sqltest.py
