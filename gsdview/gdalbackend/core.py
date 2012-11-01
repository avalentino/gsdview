# -*- coding: utf-8 -*-

### Copyright (C) 2008-2012 Antonio Valentino <a_valentino@users.sf.net>

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


'''Core GDAL backend functions and classes.'''


import os

from osgeo import gdal

from qt import QtCore, QtGui

from .. import qt4support

from . import widgets
from . import helpers
from . import modelitems
from . import gdalsupport
from . import gdalexectools


__author__ = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__ = '$Date$'
__revision__ = '$Revision$'

__all__ = ['GDALBackend']


class GDALBackend(QtCore.QObject):
    # @TODO:
    #
    # - fix selection mess
    #
    #   * trying to re-oped an already open file should select the
    #     corresponding dataset item (no active sub-window change is expected)
    #
    # - sub-windows title and window menu

    _use_exceptions = None

    # @TODO: fix names
    @staticmethod
    def UseExceptions():
        gdal.UseExceptions()
        gdal.SetConfigOption('PYHTON_USE_EXCEPTIONS', 'TRUE')

    @staticmethod
    def DontUseExceptions():
        gdal.DontUseExceptions()
        gdal.SetConfigOption('PYHTON_USE_EXCEPTIONS', 'FALSE')

    @staticmethod
    def getUseExceptions():
        return gdal.GetConfigOption('PYHTON_USE_EXCEPTIONS', 'FALSE') == 'TRUE'

    def __init__(self, app, **kwargs):
        QtCore.QObject.__init__(self, app, **kwargs)
        self._app = app
        self._helpers = {}
        self._actionsmap = self._setupActions()

        self._app.treeview.activated.connect(self.onItemActivated)

        self._tools = self._setupExternalTools()
        self._helpers = self._setupHelpers(self._tools)

    def _setupExternalTools(self):
        tools = {}

        app = self._app
        handler = gdalexectools.GdalOutputHandler(app.logger, app.statusBar(),
                                                  app.progressbar)

        # gdaladdo
        tool = gdalexectools.GdalAddOverviewDescriptor(stdout_handler=handler)
        tools['addo'] = tool

        # gdalinfo for statistics computation
        tool = gdalexectools.GdalInfoDescriptor(stdout_handler=handler)
        tool.stats = True
        tool.nomd = True
        tool.nogcp = True
        tool.noct = True
        tools['stats'] = tool

        # gdalinfo for histogram computation
        tool = gdalexectools.GdalInfoDescriptor(stdout_handler=handler)
        tool.hist = True
        tool.nomd = True
        tool.nogcp = True
        tool.noct = True
        tools['hist'] = tool

        return tools

    def _setupHelpers(self, tools):
        hmap = {}

        app = self._app

        hmap['addo'] = helpers.AddoHelper(app, tools['addo'])
        hmap['stats'] = helpers.StatsHelper(app, tools['stats'])
        hmap['statsdialog'] = helpers.StatsDialogHelper(app, tools['stats'])
        hmap['histdialog'] = helpers.HistDialogHelper(app, tools['hist'])
        hmap['ovrdialog'] = helpers.AddoDialogHelper(app, tools['addo'])

        return hmap

    def findItemFromFilename(self, filename):
        '''Serch for and return the (dataset) item corresponding to filename.

        If no item is found retirn None.

        '''

        # @NOTE: linear complexity
        # @NOTE: only scan toplevel items
        # @TODO: use an internal regidtry (set or dict) in oder to perfotm
        #        O(1) search over all nesting levels

        filename = os.path.abspath(filename)
        filename = os.path.normpath(filename)
        root = self._app.datamodel.invisibleRootItem()
        for index in range(root.rowCount()):
            try:
                item = root.child(index)
                if item.filename == filename:
                    return item
            except AttributeError:
                pass
        return None

    @qt4support.overrideCursor
    def openFile(self, filename):
        item = self.findItemFromFilename(filename)
        if item:
            self._app.treeview.setCurrentIndex(item.index())

            # @TODO: remove selection code
            sm = self._app.treeview.selectionModel()
            sm.select(item.index(), QtGui.QItemSelectionModel.Select)

            # @TODO: maybe it is better to use an exception here
            return None
        return modelitems.datasetitem(filename)

    def itemActions(self, item):
        try:
            method = getattr(self, '_get%sActions' % item.__class__.__name__)
        except AttributeError:
            actions = self._actionsmap.get(item.__class__.__name__)
        else:
            actions = method(item)
        return actions

    def itemContextMenu(self, item):
        actions = self.itemActions(item)
        if actions:
            return qt4support.actionGroupToMenu(actions,
                                                self.tr('Context menu'),
                                                self._app.treeview)

    @QtCore.Slot(QtCore.QModelIndex)
    def onItemActivated(self, index):
        defaultActionsMap = {
            modelitems.BandItem: 'actionOpenImageView',
            modelitems.DatasetItem: 'actionOpenRGBImageView',
            modelitems.SubDatasetItem: 'actionOpenSubDatasetItem',
        }
        item = self._app.datamodel.itemFromIndex(index)

        actions = self._actionsmap[type(item).__name__]
        name = defaultActionsMap.get(type(item))
        if name:
            action = actions.findChild(QtGui.QAction, name)
            if action:
                action.trigger()
                return

        for itemtype in defaultActionsMap:
            if isinstance(item, itemtype):
                action = actions.findChild(QtGui.QAction,
                                           defaultActionsMap[itemtype])
                if action:
                    action.trigger()
                    break

    ### Actions setup #########################################################
    def _setupMajorObjectItemActions(self, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = QtGui.QActionGroup(self)

        # open metadata view
        icon = qt4support.geticon('metadata.svg', __name__)
        QtGui.QAction(icon, self.tr('Open &Metadata View'), actionsgroup,
                      objectName='actionOpenItemMetadataView',
                      shortcut=self.tr('Ctrl+M'),
                      toolTip=self.tr('Show metadata in a new window'),
                      statusTip=self.tr('Show metadata in a new window'),
                      triggered=self.openItemMatadataView,
                      enabled=False)    # @TODO: remove

        # show properties
        # @TODO: standard info icon from gdsview package
        icon = qt4support.geticon('info.svg', 'gsdview')
        QtGui.QAction(icon, self.tr('&Show Properties'), actionsgroup,
                      objectName='actionShowItemProperties',
                      shortcut=self.tr('Ctrl+S'),
                      toolTip=self.tr('Show the property dialog for the '
                                      'cutent item'),
                      statusTip=self.tr('Show the property dialog for the '
                                        'cutent item'),
                      triggered=self.showItemProperties)

        return actionsgroup

    def _setupBandItemActions(self, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = QtGui.QActionGroup(self)

        # open image view
        icon = qt4support.geticon('open.svg', __name__)
        QtGui.QAction(icon, self.tr('&Open Image View'), actionsgroup,
                      objectName='actionOpenImageView',
                      shortcut=self.tr('Ctrl+O'),
                      toolTip=self.tr('Open an image view'),
                      statusTip=self.tr('Open a new image view'),
                      triggered=self.openImageView)

        # @TODO: add a new action for newImageView

        # @TODO: Masked bands, Compute statistics, Compute histogram
        # @TODO: dataset --> Build overviews

        self._setupMajorObjectItemActions(actionsgroup)

        return actionsgroup

    def _setupOverviewItemActions(self, actionsgroup=None):
        # @TODO: remove open
        # @TODO: remove overviews build
        #~ actionsgroup = self._setupBandItemActions()
        #~ action = actionsgroup.findChild(QtGui.QAction, 'actionBuidOverviews')
        #~ actionsgroup.removeAction(action)
        #~ return actionsgroup
        return self._setupBandItemActions(actionsgroup)

    # @TODO
    #def _setupVirtualBandItemActions(self):
    #    pass

    def _setupDatasetItemActions(self, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = QtGui.QActionGroup(self)

        # open RGB
        # @TODO: find an icon for RGB
        icon = qt4support.geticon('rasterband.svg', __name__)
        QtGui.QAction(icon, self.tr('Open as RGB'), actionsgroup,
                      objectName='actionOpenRGBImageView',
                      #shortcut=self.tr('Ctrl+B'),
                      toolTip=self.tr('Display the dataset as an RGB image'),
                      statusTip=self.tr('Open as RGB'),
                      triggered=self.openRGBImageView)

        # build overviews
        icon = qt4support.geticon('overview.svg', __name__)
        QtGui.QAction(icon, self.tr('&Build overviews'),
                      actionsgroup, objectName='actionBuidOverviews',
                      shortcut=self.tr('Ctrl+B'),
                      toolTip=self.tr('Build overviews for all raster bands'),
                      statusTip=self.tr(
                        'Build overviews for all raster bands'),
                      triggered=self.buildOverviews)

        # @TODO: add band, add virtual band, open GCPs view

        # close
        icon = qt4support.geticon('close.svg', 'gsdview')
        QtGui.QAction(icon, self.tr('Close'), actionsgroup,
                      objectName='actionCloseItem',
                      shortcut=self.tr('Ctrl+W'),
                      toolTip=self.tr('Close the current item'),
                      statusTip=self.tr('Close the current item'),
                      triggered=self.closeCurrentItem)

        self._setupMajorObjectItemActions(actionsgroup)

        return actionsgroup

    def _setupSubDatasetItemActions(self, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = QtGui.QActionGroup(self)

        # open
        icon = qt4support.geticon('open.svg', __name__)
        QtGui.QAction(icon, self.tr('Open Sub Dataset'), actionsgroup,
                      objectName='actionOpenSubDatasetItem',
                      shortcut=self.tr('Ctrl+O'),
                      toolTip=self.tr('Open Sub Dataset'),
                      statusTip=self.tr('Open Sub Dataset'),
                      triggered=self.openSubDataset)

        self._setupDatasetItemActions(actionsgroup)

        return actionsgroup

    def _setupActions(self, actionsmap=None):
        if actionsmap is None:
            actionsmap = {}

        actionsmap['MajorObjectItem'] = self._setupMajorObjectItemActions()
        actionsmap['BandItem'] = self._setupBandItemActions()
        actionsmap['OverviewItem'] = self._setupOverviewItemActions()
        #actionsmap['VirtualBandItem'] = self._setupVirtualBandItemActions()
        actionsmap['DatasetItem'] = self._setupDatasetItemActions()
        actionsmap['CachedDatasetItem'] = actionsmap['DatasetItem']
        actionsmap['SubDatasetItem'] = self._setupSubDatasetItemActions()

        return actionsmap

    ### Actions enabling ######################################################
    def _getBandItemActions(self, item=None, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = self._actionsmap['BandItem']

        action = actionsgroup.findChild(QtGui.QAction, 'actionOpenImageView')
        action.setEnabled(True)

        if item is not None:
            assert isinstance(item, modelitems.BandItem)

            # @TODO: find a better solution
            allowcomplex = True
            if gdal.DataTypeIsComplex(item.DataType) and not allowcomplex:
                action.setEnabled(False)
            else:
                # @TODO: remove this to allow multiple views on the same item
                for subwin in self._app.mdiarea.subWindowList():
                    #if subwin.item == item:
                    #    action.setEnabled(False)
                    #    break

                    # @COMPATIBILITY: pyside 1.0.1
                    try:
                        if subwin.item == item:
                            action.setEnabled(False)
                            break
                    except NotImplementedError:
                        if id(subwin.item) == id(item):
                            action.setEnabled(False)
                            break

        return actionsgroup

    def _getDatasetItemActions(self, item=None, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = self._actionsmap['DatasetItem']

        # RGB
        action = actionsgroup.findChild(QtGui.QAction,
                                        'actionOpenRGBImageView')
        if gdalsupport.isRGB(item):
            # @TODO: remove this to allow multiple views on the same item
            for subwin in self._app.mdiarea.subWindowList():
                #if subwin.item == item:
                #    action.setEnabled(False)
                #    break

                # @COMPATIBILITY: pyside 1.0.1
                try:
                    if subwin.item == item:
                        action.setEnabled(False)
                        break
                except NotImplementedError:
                    if id(subwin.item) == id(item):
                        action.setEnabled(False)
                        break

            else:
                action.setEnabled(True)
        else:
            action.setEnabled(False)

        return actionsgroup

    # @NOTE: this is needed for correct context menu setup
    # @TODO: maybe it is possible to find a better way to handle the problem
    _getCachedDatasetItemActions = _getDatasetItemActions

    def _getSubDatasetItemActions(self, item=None, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = self._actionsmap['SubDatasetItem']

        actionsgroup = self._getDatasetItemActions(item, actionsgroup)

        openaction = actionsgroup.findChild(QtGui.QAction,
                                            'actionOpenSubDatasetItem')
        closeaction = actionsgroup.findChild(QtGui.QAction, 'actionCloseItem')
        propertyaction = actionsgroup.findChild(QtGui.QAction,
                                                'actionShowItemProperties')
        ovraction = actionsgroup.findChild(QtGui.QAction,
                                           'actionBuidOverviews')

        if item is not None:
            assert isinstance(item, modelitems.SubDatasetItem)
            if item.isopen():
                openaction.setEnabled(False)
                closeaction.setEnabled(True)
                propertyaction.setEnabled(True)
                ovraction.setEnabled(True)
            else:
                openaction.setEnabled(True)
                closeaction.setEnabled(False)
                propertyaction.setEnabled(False)
                ovraction.setEnabled(False)

        return actionsgroup

    ### Major object ##########################################################
    @QtCore.Slot()
    def openItemMatadataView(self):
        # @TODO: implementation
        self._app.logger.info('method not yet implemented')

    def _infoDialogFactory(self, item):
        for itemtype in item.__class__.__mro__:
            name = itemtype.__name__
            assert name.endswith('Item')
            name = name[:-4] + 'InfoDialog'
            dialogclass = getattr(widgets, name, None)
            if dialogclass:
                dialog = dialogclass(item, self._app)
                break
        else:
            dialog = None

        # @TODO: rewrite
        if dialog and isinstance(dialog, widgets.BandInfoDialog):
            if isinstance(item, modelitems.OverviewItem):
                # disable some function on overview items
                dialog.overviewWidget.setReadOnly(True)

                dialog.approxStatsCheckBox.hide()
                dialog.computeStatsButton.hide()

                dialog.customHistogramCheckBox.hide()
                dialog.computeHistogramButton.hide()

            # helpers setup
            for helpername in ('statsdialog', 'histdialog', 'ovrdialog'):
                helper = self._helpers[helpername]
                helper.dialog = dialog

            dialog.statsComputationRequest.connect(
                                        self._helpers['statsdialog'].start)
            dialog.histogramComputationRequest.connect(
                                        self._helpers['histdialog'].start)
            dialog.overviewComputationRequest.connect(
                                        self._helpers['ovrdialog'].start)

            dialog.finished.connect(self._resethelpers)

        return dialog

    @QtCore.Slot()
    def _resethelpers(self):
        self._helpers['statsdialog'].reset()
        self._helpers['histdialog'].reset()
        self._helpers['ovrdialog'].reset()

    @QtCore.Slot()
    def showItemProperties(self):
        item = self._app.currentItem()
        dialog = self._infoDialogFactory(item)
        if dialog:
            dialog.exec_()
        else:
            self._app.logger.debug('unable to show info dialog for "%s" '
                                   'item class' % (item.__class__.__name__))

    ### Driver ################################################################
    ### Dataset ###############################################################
    @QtCore.Slot()
    @QtCore.Slot(QtGui.QStandardItem)
    def openRGBImageView(self, item=None):
        if item is None:
            item = self._app.currentItem()
        assert isinstance(item, modelitems.DatasetItem), ('item = %s' %
                                                                    str(item))

        if not item.scene:
            msg = "This dataset can't be opened in RGB mode."
            self._app.logger.info(msg)
            #title = self.tr('WARNING')
            #msg = self.tr(msg)
            #QtGui.QMessageBox.warning(self._app, title, msg)
            return

        # only open a new view if there is no other on the item selected
        if len(item.scene.views()) == 0:
            self.newImageView(item)

    @QtCore.Slot()
    def buildOverviews(self, item=None):
        if item is None:
            item = self._app.currentItem()

        assert isinstance(item, modelitems.DatasetItem), ('item = %s' %
                                                                    str(item))

        dialog = widgets.OverviewDialog(item, self._app)
        helper = self._helpers['ovrdialog']
        helper.dialog = dialog
        dialog.overviewComputationRequest.connect(helper.start)
        dialog.exec_()

    # @TODO: add band, add virtual band, open GCPs view

    @QtCore.Slot()
    def closeCurrentItem(self):
        item = self._app.currentItem()
        self._app.treeview.collapse(item.index())
        item.close()

    ### Sub-dataset ###########################################################
    @QtCore.Slot()
    def openSubDataset(self):
        item = self._app.currentItem()
        assert isinstance(item, modelitems.SubDatasetItem)
        if item.isopen():
            if gdalsupport.isRGB(item):
                self.openRGBImageView(item)
            return

        try:
            # Only works for CachedDatasetItems
            cachedir = os.path.dirname(item.parent().vrtfilename)
        except AttributeError:
            id_ = gdalsupport.uniqueDatasetID(item.parent())
            cachedir = os.path.join(modelitems.SubDatasetItem.CACHEDIR, id_)

        # sub-dataset index (starting from 1)
        index = item.row() - item.parent().RasterCount + 1
        cachedir = os.path.join(cachedir, 'subdataset%02d' % index)

        item.open(cachedir)
        #self._app.treeview.expand(item.index())

        #for row in range(item.rowCount()):
        #    child = item.child(row)
        #    self._app.treeview.expand(child.index())

    ### Raster Band ###########################################################
    @QtCore.Slot()
    @QtCore.Slot(QtGui.QStandardItem)  # @TODO: check
    @qt4support.overrideCursor
    def openImageView(self, item=None):
        if item is None:
            item = self._app.currentItem()
        assert isinstance(item, modelitems.BandItem), 'item = %s' % str(item)

        # NOTE: a reguest of opening an overview is converted into a request
        #       for opening the corresponding raster band
        while isinstance(item, modelitems.OverviewItem):
            item = item.parent()

        if not item.scene:
            if not item.GetDescription():
                msg = 'band "%s" is not visualizable' % (item.row() + 1)
            else:
                msg = 'band "%s" is not visualizable' % item.GetDescription()
            self._app.logger.warning(msg)
            return

        # only open a new view if there is no other on the item selected
        if len(item.scene.views()) == 0:
            stats = gdalsupport.GetCachedStatistics(item)
            if None in stats:
                self._helpers['stats'].start(item)
            else:
                self.newImageView(item)

    def newImageView(self, item=None):
        if item is None:
            item = self._app.currentItem()
        #assert isinstance(item, modelitems.BandItem)
        assert isinstance(item, (modelitems.BandItem, modelitems.DatasetItem))

        # @TODO: check if any graphics view is open on the selected item

        winlist = self._app.mdiarea.subWindowList()
        if len(winlist):
            maximized = winlist[0].windowState() & QtCore.Qt.WindowMaximized
        else:
            maximized = True

        subwin = GraphicsViewSubWindow(item)

        self._app.mdiarea.addSubWindow(subwin)
        grephicsview = subwin.widget()
        self._app.monitor.register(grephicsview)
        self._app.mousemanager.register(grephicsview)

        subwin.destroyed.connect(self._app.subWindowClosed)

        if maximized:
            subwin.showMaximized()
        else:
            subwin.show()

        # @TODO: check
        helper = self._helpers['addo']
        helper.start(item)

    # @TODO: Open, Masked bands
    # @TODO: dataset --> Build overviews

    ### Overview ##############################################################
    ### Virtualband ###########################################################
    def loadGDALSettings(self, settings):
        logger = self._app.logger

        settings.beginGroup('gdal')
        try:
            cachesize = settings.value('GDAL_CACHEMAX')
            if cachesize is not None:
                cachesize = int(cachesize)
                gdal.SetCacheMax(cachesize)
                logger.debug('GDAL cache size det to %d' % cachesize)

            value = settings.value('GDAL_DATA')
            if value:
                value = os.path.expanduser(os.path.expandvars(value))
                gdal.SetConfigOption('GDAL_DATA', value)
                logger.debug('GDAL_DATA directory set to "%s"' % value)

            for optname in ('GDAL_SKIP', 'GDAL_DRIVER_PATH',
                            'OGR_DRIVER_PATH'):
                value = settings.value(optname)
                if value is not None:
                    value = os.path.expanduser(os.path.expandvars(value))
                    # @NOTE: type of arg 2 of SetConfigOption must be str,
                    #        not an unicode
                    gdal.SetConfigOption(optname, str(value))
                    logger.debug('%s set to "%s"' % (optname, value))

            gdal.AllRegister()
            logger.debug('run "gdal.AllRegister()"')

            # update the about dialog
            tabWidget = self._app.aboutdialog.tabWidget
            for index in range(tabWidget.count()):
                if tabWidget.tabText(index) == 'GDAL':
                    gdalinfowidget = tabWidget.widget(index)
                    gdalinfowidget.setGdalDriversTab()
                    break
            else:
                logger.debug('GDAL page ot found in the about dialog')
                return
        finally:
            settings.endGroup()

    def loadSettings(self, settings):
        self.loadGDALSettings(settings)

        settings.beginGroup('gdalbackend')
        try:
            # show overviews in the treeview
            value = settings.value('visible_overview_items')

            # @COMPATIBILITY: presumably a bug in PyQt4 (4.7.2)
            if isinstance(value, basestring):
                value = True if value in ('true', 'True') else False

            modelitems.VISIBLE_OVERVIEW_ITEMS = value
            # @TODO: reload all items
        finally:
            settings.endGroup()

    def saveSettings(self, settings):
        # @NOTE: GDAL preferences are only modified via preferences dialog

        settings.beginGroup('gdalbackend')
        try:
            # show overviews in the treeview
            settings.setValue('visible_overview_items',
                              modelitems.VISIBLE_OVERVIEW_ITEMS)
        finally:
            settings.endGroup()


### MISC ######################################################################
from ..mdi import ItemSubWindow


# @TODO: move elsewhere
class GraphicsViewSubWindow(ItemSubWindow):
    def __init__(self, item, parent=None, flags=QtCore.Qt.WindowFlags(0),
                 **kwargs):
        super(GraphicsViewSubWindow, self).__init__(item, parent, flags,
                                                    **kwargs)
        title = str(item.GetDescription()).strip()
        self.setWindowTitle(title)

        scene = item.scene
        graphicsview = QtGui.QGraphicsView(scene)
        graphicsview.setMouseTracking(True)
        self.setWidget(graphicsview)
