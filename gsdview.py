#!/usr/bin/env python

import os
import sys
import logging

import numpy
import gdal

from PyQt4 import QtCore, QtGui
from PyQt4 import Qwt5 as Qwt

import resources

import gsdtools
import gdalsupport
import gdalqt4

import exectools
from exectools.qt4tools import Qt4OutputPlane, Qt4ToolController
from exectools.qt4tools import Qt4DialogLoggingHandler, Qt4StreamLoggingHandler

from gdalexectools import GdalAddOverviewDescriptor, GdalOutputHandler

def overrideCursor(func):
    def aux(*args, **kwargs):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            func(*args, **kwargs)
        finally:
            QtGui.QApplication.restoreOverrideCursor()
    return aux

# @TODO: move to another file (??)
# @TODO: maybe this is not the best solution. Maybe a custom GraphicsItem
#        would be better
class GraphicsView(QtGui.QGraphicsView):
    def mouseMoveEvent(self, event):
        if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            self.emit(QtCore.SIGNAL('mousePositionUpdated(const QPoint&)'),
                      event.pos())
            if event.buttons() & QtCore.Qt.LeftButton:
                self.emit(QtCore.SIGNAL('posMarked(const QPoint&)'), event.pos())
            #event.accept()
        return QtGui.QGraphicsView.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            if event.buttons() & QtCore.Qt.LeftButton:
                self.emit(QtCore.SIGNAL('posMarked(const QPoint&)'), event.pos())
            #event.accept()
        return QtGui.QGraphicsView.mousePressEvent(self, event)

    def resizeEvent(self, event):
        self.emit(QtCore.SIGNAL('newSize(const QSize&)'), event.size())
        return QtGui.QGraphicsView.resizeEvent(self, event)

    def scale(self, sx, sy):
        QtGui.QGraphicsView.scale(self, sx, sy)
        self.emit(QtCore.SIGNAL('scaled()'))

    def resetMatrix(self):
        if not self.matrix().isIdentity():
            QtGui.QGraphicsView.resetMatrix(self)
            self.emit(QtCore.SIGNAL('scaled()'))

    # @TODO: check transform related functions

class GSDView(QtGui.QMainWindow):
    # @TODO:
    #   * set all icon (can use the iconset of BEAM)
    #   * fix the 'key' column width of info table
    #   * show metadata in a tree
    #   * map panel
    #   * plugin architecture
    #   * cache browser, cache cleanup
    #   * open internal product
    #   * stop button
    #   * disable actions when the external tool is running
    #   * /usr/share/doc/python-qt4-doc/examples/mainwindows/recentfiles.py
    #   * stretching tool

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr('GSDView'))
        self.setWindowIcon(QtGui.QIcon(':/images/GDALLogoColor.svg'))
        self.resize(800, 600)

        scene = QtGui.QGraphicsScene(self)
        self.graphicsView = GraphicsView(scene, self)
        self.graphicsView.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.setCentralWidget(self.graphicsView)

        # Connect signals for the quicklook box
        # @TODO: check
        # @TODO: connect only if the quicklook is present
        self.connect(self.graphicsView.horizontalScrollBar(),
                     QtCore.SIGNAL('valueChanged(int)'),
                     self.updateQuicklookBox)
        self.connect(self.graphicsView.verticalScrollBar(),
                     QtCore.SIGNAL('valueChanged(int)'),
                     self.updateQuicklookBox)
        self.connect(self.graphicsView,
                     QtCore.SIGNAL('newSize(const QSize&)'),
                     self.updateQuicklookBox)
        self.connect(self.graphicsView,
                     QtCore.SIGNAL('scaled()'),
                     self.updateQuicklookBox)

        # Progressbar
        self.progressbar = QtGui.QProgressBar(self)
        self.progressbar.setTextVisible(True)
        self.statusBar().addPermanentWidget(self.progressbar)
        self.progressbar.hide()

        # @TODO: improve scrolling performances
        #~ self.graphicsView.horizontalScrollBar.connect(QtCore.SIGNAL('sliderPressed()'), self.startScrolling)
        #~ self.graphicsView.horizontalScrollBar.connect(QtCore.SIGNAL('sliderReleased()'), self.stopScrolling)
        #~ self.graphicsView.verticalScrollBar.connect(QtCore.SIGNAL('sliderPressed()'), self.startScrolling)
        #~ self.graphicsView.verticalScrollBar.connect(QtCore.SIGNAL('sliderReleased()'), self.stopScrolling)
        #~ self.graphicsView.connect(QtCore.SIGNAL('dragMoveEvent()'), self.startScrolling)
        #~ self.graphicsView.connect(QtCore.SIGNAL('dropEvent()'), self.stopScrolling)

        #~ self.graphicsView.connect(QtCore.SIGNAL('mousePressEvent()'), self.startScrolling)
        #~ self.graphicsView.connect(QtCore.SIGNAL('mouseReleaseEvent()'), self.stopScrolling)

        self.imageItem = None
        self.quicklook = None

        # @TODO: encapsulate in a gdal.Dataset proxy (--> gdalsupport)
        self.dataset = None
        self.qlFactor = None  # @TODO: check int/float (maybe it is not needed)
        self.virtualDatasetFilename = None

        # File dialog
        self.filedialog = QtGui.QFileDialog(self)
        self.filedialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        self.filedialog.setFilters(gdalsupport.gdalFilters())

        # Panels
        #~ self.quicklookView = None
        #~ self.mapView = None
        #~ self.infoTable = None
        self.setupPanels()

        # Actions
        self.setupActions()
        self.setupMenu()
        self.setupToolbars()

        self.zoomActions.setEnabled(False)
        self.statusBar().showMessage('Ready')

        # Settings
        # @TODO: fix filename
        #self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #                                 QtCore.QSettings.UserScope,
        #                                 'gsdview-soft', 'gsdview', self)
        #self.settings = QtCore.QSettings('gsdview-soft', 'gsdview', self)
        self.settings = QtCore.QSettings('gsdview.ini',
                                         QtCore.QSettings.IniFormat,
                                         self)
        self.connect(QtGui.qApp, QtCore.SIGNAL('aboutToQuit()'),
                     self.saveSettings)
        self.loadSettings()

        # Setup the log system
        self.logger = self.setupLogging(self.outputplane)

        # Setup external tool s controller
        self.controller = self.setupController(self.outputplane,
                                               self.statusBar(),
                                               self.progressbar,
                                               self.logger)

    ### Setup helpers #########################################################
    def _setupFileActions(self):
        self.fileActions = QtGui.QActionGroup(self)

        # Open
        self.actionFileOpen = QtGui.QAction(QtGui.QIcon(':/images/open.svg'),
                                            self.tr('&Open'), self)
        self.actionFileOpen.setShortcut(self.tr('Ctrl+O'))
        self.actionFileOpen.setStatusTip(self.tr('Open an existing file'))
        self.connect(self.actionFileOpen, QtCore.SIGNAL('triggered()'),
                     self.openFile)
        self.fileActions.addAction(self.actionFileOpen)

        # Close
        self.actionFileClose = QtGui.QAction(QtGui.QIcon(':/images/close.svg'),
                                             self.tr('&Close'), self)
        self.actionFileClose.setShortcut(self.tr('Ctrl+W'))
        self.actionFileClose.setStatusTip(self.tr('Close an open file'))
        self.connect(self.actionFileClose, QtCore.SIGNAL('triggered()'),
                     self.closeFile)
        self.fileActions.addAction(self.actionFileClose)

        # Exit
        self.actionExit = QtGui.QAction(QtGui.QIcon(':/images/quit.svg'),
                                        self.tr('&Exit'), self)
        self.actionExit.setShortcut(self.tr('Ctrl+X'));
        self.actionExit.setStatusTip(self.tr('Exit the program'))
        self.connect(self.actionExit, QtCore.SIGNAL('triggered()'),
                     self.close)
        self.fileActions.addAction(self.actionExit)

        return self.fileActions

    def _setupZoomActions(self):
        self.zoomActions = QtGui.QActionGroup(self)

        # Zoom in
        self.actionZoomIn = QtGui.QAction(QtGui.QIcon(':/images/zoom-in.svg'),
                                          self.tr('Zoom In'), self)
        self.actionZoomIn.setStatusTip(self.tr('Zoom In'))
        self.actionZoomIn.setShortcut(QtGui.QKeySequence(self.tr('Ctrl++')))
        self.connect(self.actionZoomIn, QtCore.SIGNAL('triggered()'),
                     self.zoomIn)
        self.zoomActions.addAction(self.actionZoomIn)

        # Zoom out
        self.actionZoomOut = QtGui.QAction(QtGui.QIcon(':/images/zoom-out.svg'),
                                           self.tr('Zoom Out'), self)
        self.actionZoomOut.setStatusTip(self.tr('Zoom Out'))
        self.actionZoomOut.setShortcut(QtGui.QKeySequence(self.tr('Ctrl+-')))
        self.connect(self.actionZoomOut, QtCore.SIGNAL('triggered()'),
                     self.zoomOut)
        self.zoomActions.addAction(self.actionZoomOut)

        # Zoom fit
        self.actionZoomFit = QtGui.QAction(QtGui.QIcon(':/images/zoom-fit.svg'),
                                           self.tr('Zoom Fit'), self)
        self.actionZoomIn.setStatusTip(self.tr('Zoom to fit the window size'))
        self.connect(self.actionZoomFit, QtCore.SIGNAL('triggered()'),
                     self.zoomFit)
        self.zoomActions.addAction(self.actionZoomFit)

        # Zoom 100
        self.actionZoom100 = QtGui.QAction(QtGui.QIcon(':/images/zoom-100.svg'),
                                           self.tr('Zoom 100%'), self)
        self.actionZoom100.setStatusTip(self.tr('Original size'))
        self.connect(self.actionZoom100, QtCore.SIGNAL('triggered()'),
                     self.zoom100)
        self.zoomActions.addAction(self.actionZoom100)

        return self.zoomActions

    def _setupHelpActions(self):
        self.helpActions = QtGui.QActionGroup(self)

        # About
        self.actionAbout = QtGui.QAction(QtGui.QIcon(':/images/about.svg'),
                                        self.tr('&About'), self)
        self.actionAbout.setStatusTip(self.tr('Show program information'))
        self.connect(self.actionAbout, QtCore.SIGNAL('triggered()'),
                     self.about)
        self.helpActions.addAction(self.actionAbout)

        # AboutQt
        self.actionAboutQt = QtGui.QAction(QtGui.QIcon(':/images/qt-logo.png'),
                                        self.tr('About &Qt'), self)
        self.actionAboutQt.setStatusTip(self.tr('Show information about Qt'))
        self.connect(self.actionAboutQt, QtCore.SIGNAL('triggered()'),
                     self.aboutQt)
        self.helpActions.addAction(self.actionAboutQt)

        return self.helpActions

    def setupActions(self):
        self.fileActions = self._setupFileActions()
        self.zoomActions = self._setupZoomActions()
        self.helpActions = self._setupHelpActions()

    def setupMenu(self):
        def actionGroupToMenu(actionGroup, label):
            menu = QtGui.QMenu(label, self)
            for action in actionGroup.actions():
                menu.addAction(action)
            self.menuBar().addMenu(menu)
            return menu

        menu = actionGroupToMenu(self.fileActions, self.tr('&File'))
        menu.insertSeparator(self.actionExit)
        menu = actionGroupToMenu(self.zoomActions, self.tr('&Zoom'))
        menu = actionGroupToMenu(self.helpActions, self.tr('&Help'))

    def setupToolbars(self):
        def actionGroupToToolbar(actionGroup, label, name=None):
            if name is None:
                # get camel case name
                parts = str(label).title().split()
                parts[0] = parts[0].lower()
                name = ''.join(parts)
            toolbar = QtGui.QToolBar(label, self)
            toolbar.setObjectName(name)
            for action in actionGroup.actions():
                toolbar.addAction(action)
            self.addToolBar(toolbar)
            return toolbar

        bar = actionGroupToToolbar(self.fileActions, self.tr('File toolbar'))
        bar.insertSeparator(self.actionExit)
        bar = actionGroupToToolbar(self.zoomActions, self.tr('Zoom toolbar'))
        bar = actionGroupToToolbar(self.helpActions, self.tr('Help toolbar'))

    def _setupOutputPanel(self):
        # Output panel
        outputPanel = QtGui.QDockWidget('Output', self)
        outputPanel.setObjectName('outputPanel')
        outputplane = Qt4OutputPlane()
        outputPanel.setWidget(outputplane)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, outputPanel)
        self.connect(outputplane, QtCore.SIGNAL('planeHideRequest()'),
                     outputPanel.hide)
        return outputPanel

    def _setupQuickLookPanel(self):
        # Quick-look panel
        # @TODO: rename "overview"
        quicklookPanel = QtGui.QDockWidget('Quick Look', self)
        quicklookPanel.setObjectName('quickLookPanel')
        quicklookView = GraphicsView(QtGui.QGraphicsScene(self))
        #quicklookView.setDragMode(QtGui.QGraphicsView.ScrollHandDrag) # @TODO: check
        quicklookPanel.setWidget(quicklookView)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, quicklookPanel)
        #quicklookPanel.hide()              # @TODO: check
        #self.connect(quicklookView, QtCore.SIGNAL('mousePositionUpdated(const QPoint&)'),
        #             self.updatePosLabels)
        self.connect(quicklookView, QtCore.SIGNAL('posMarked(const QPoint&)'),
                     self.centerOn)

        # @TODO: it is required that a custom widget re-imptement the
        #        "mousePressEvent" evant handler
        #self.connect(quicklookView, QtCore.SIGNAL('mousePressEvent(QMouseEvent*)'), self.centerOn)
        return quicklookPanel

    def _setupMapPanel(self):
        # Map panel @TODO: use the marble widget
        mapPanel = QtGui.QDockWidget('Map', self)
        mapPanel.setObjectName('mapPanel')
        self.mapView = QtGui.QGraphicsView(self)
        mapPanel.setWidget(self.mapView)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, mapPanel)
        mapPanel.hide()             # @TODO: check

        return mapPanel

    def _setupInfoPanel(self):
        # Info panel
        # @TODO: rename "metadata"
        infoPanel = QtGui.QDockWidget('Info', self)
        infoPanel.setObjectName('infoPanel')
        self.infoTable = QtGui.QTableWidget(5, 2, self)
        self.infoTable.verticalHeader().hide()
        self.infoTable.setHorizontalHeaderLabels(['Key', 'Value'])
        self.infoTable.horizontalHeader().setStretchLastSection(True)
        #self.tableWidget.horizontalHeader().hide()
        infoPanel.setWidget(self.infoTable)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, infoPanel)
        #infoPanel.hide()            # @TODO: check

        return infoPanel

    def setupPanels(self):
        outputPanel = self._setupOutputPanel()
        quicklookPanel = self._setupQuickLookPanel()
        #mapPanel = self._setupMapPanel()      # @TODO: fix
        infoPanel = self._setupInfoPanel()

        self.outputplane = outputPanel.widget()
        self.quicklookView = quicklookPanel.widget()

    def setupLogging(self, outputplane):
        logger = logging.getLogger()    # 'gsdview' # @TODO: fix

        # Set the log level from preferences
        defaut = QtCore.QVariant(logging.getLevelName(logger.level))
        level = self.settings.value('preferences/loglevel', defaut).toString()
        level = logging.getLevelName(str(level))
        if isinstance(level, int):
            logger.setLevel(level)

        if logger.level == logging.DEBUG:
            logging.basicConfig(level=logging.DEBUG)

        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler = Qt4StreamLoggingHandler(outputplane)
        handler.setLevel(logger.level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        formatter = logging.Formatter('%(message)s')
        handler = Qt4DialogLoggingHandler(parent=self, dialog=None)
        handler.setLevel(logging.WARNING)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def setupController(self, outputplane, statusbar, progressbar, logger):
        handler = GdalOutputHandler(outputplane, statusbar, progressbar)
        tool = GdalAddOverviewDescriptor(stdout_handler=handler)
        controller = Qt4ToolController(logger, parent=self)
        controller.tool = tool
        controller.connect(controller, QtCore.SIGNAL('finished()'),
                           self.processingDone)

        return controller

    ### Settings ##############################################################
    def loadSettings(self):
        # mainwindow
        self.settings.beginGroup('mainwindow')
        position = self.settings.value('position')
        if not position.isNull():
            self.move(position.toPoint())
        size = self.settings.value('size')
        if not size.isNull():
            self.resize(size.toSize())
        state = self.settings.value('state')
        if not state.isNull():
            self.restoreState(state.toByteArray())
        self.settings.endGroup()

        # preferences
        self.settings.beginGroup('preferences')
        #self.cachedir = self.settings.value('cachelocation')
        # @TODO: check the default value
        #default= QtCore.QVariant(150*1024**2)
        #cachesize, ok = self.settings.value('gdalcachesize', default).toInt()
        cachesize, ok = self.settings.value('gdalcachesize').toInt()
        if ok:
            gdal.SetCacheMax(cachesize)
        self.settings.endGroup()

    def saveSettings(self):
        # mainwindow
        self.settings.beginGroup('mainwindow')
        self.settings.setValue('position', QtCore.QVariant(self.pos()))
        self.settings.setValue('size', QtCore.QVariant(self.size()))
        self.settings.setValue('state', QtCore.QVariant(self.saveState()))
        self.settings.endGroup()

        # preferences
        self.settings.beginGroup('preferences')
        level = QtCore.QVariant(logging.getLevelName(self.logger.level))
        self.settings.setValue('loglevel', level)
        #self.settings.setValue('cachelocation', self.cachedir)
        self.settings.setValue('gdalcachesize',
                               QtCore.QVariant(gdal.GetCacheMax()))
        self.settings.endGroup()

    # @TODO: check and move elseware
    def closeEvent(self, event):
        '''
        void MainWindow::closeEvent(QCloseEvent *event)
        {
            if (maybeSave()) {
                writeSettings();
                event->accept();
            } else {
                event->ignore();
            }
        }

        '''

        self.showNormal()

    ### File actions ##########################################################
    @overrideCursor
    def _openFile(self, filename):
        assert filename
        inDataset = gdal.Open(str(filename))

        # Check the cache
        # @TODO: fix
        defaultcachedir = os.path.join('~', '.gsdview', 'cache')
        defaultcachedir = os.path.expanduser(defaultcachedir)
        defaultcachedir = QtCore.QVariant(defaultcachedir)
        cachedir = self.settings.value('preferences/cachedir', defaultcachedir)
        cachedir = cachedir.toString()
        cachedir = os.path.expanduser(str(cachedir))

        datasetID = gdalsupport.uniqueDatasetID(inDataset)
        datasetCacheDir = os.path.join(cachedir, datasetID)
        if not os.path.isdir(datasetCacheDir):
            os.makedirs(datasetCacheDir)

        # Check the cache
        virtualDatasetFilename = os.path.join(datasetCacheDir,
                                              'virtual-dataset.vrt')
        if not os.path.exists(virtualDatasetFilename):
            driver = gdal.GetDriverByName('VRT')
            dataset = driver.CreateCopy(virtualDatasetFilename, inDataset)
        else:
            # @TODO: check if opening the dataset in update mode
            #        (gdal.GA_Update) is a better solution
            dataset = gdal.Open(virtualDatasetFilename)
        del inDataset
        self.virtualDatasetFilename = virtualDatasetFilename
        self.dataset = dataset

        # Update the info table
        self.infoTable.clear()
        metadata = dataset.GetMetadata()
        self.infoTable.setHorizontalHeaderLabels(['Key', 'Value'])
        self.infoTable.setRowCount(len(metadata))
        self.infoTable.horizontalHeader().setResizeMode(
                                            QtGui.QHeaderView.ResizeToContents)
        for row, key in enumerate(metadata):
            value = str(metadata[key])
            self.infoTable.setItem(row, 0, QtGui.QTableWidgetItem(key))
            self.infoTable.setItem(row, 1, QtGui.QTableWidgetItem(value))
        self.infoTable.sortByColumn(0, QtCore.Qt.AscendingOrder)

        # @TODO: check second time
        self.infoTable.horizontalHeader().setResizeMode(
                                                QtGui.QHeaderView.Interactive)

        self.zoomActions.setEnabled(True)

        # Check for overviews and statistics
        # @TODO: move this to settings
        maxQuicklookSize = 100 * 1024 # 100 KByte (about 320x320 8 bit pixels)

        # @TODO: add a mechanism for band slection
        band = dataset.GetRasterBand(1)

        # Compute the desires quicklook factor
        #bytePerPixel = gdal.GetDataTypeSize(band.DataType) / 8
        bytePerPixel = 1    # the quicklook image is always converted to byte
        datasetMemSize = dataset.RasterXSize*dataset.RasterYSize*bytePerPixel
        self.qlFactor = numpy.sqrt(datasetMemSize/float(maxQuicklookSize))
        self.qlFactor = max(round(self.qlFactor), 2)

        # @TODO: check GDALOvLevelAdjust
        #int GDALOvLevelAdjust(int nOvLevel, int nXSize) {
        #   int nOXSize = (nXSize + nOvLevel - 1) / nOvLevel;
        #   return (int) (0.5 + nXSize / (double) nOXSize);
        #}

        # @TODO: when the improved GraphicsView will be available more then
        #        one overview level will be needed
        overviewLevels = [int(self.qlFactor)]

        # Check existing overviews
        nOverviews = band.GetOverviewCount()
        if nOverviews > 0:
            # Retrieve the scale factors
            factors = []
            for ovrIndex in range(nOverviews):
                ovrXSize = band.GetOverview(ovrIndex).XSize
                factors.append(dataset.RasterXSize / ovrXSize)
                logging.debug('RasterXSize = %d, ovrXSize = %d' % (dataset.RasterXSize, ovrXSize))

            logging.debug('factors: %s' % factors)

            # Criterion is too strict
            #~ missingOverviewLevels = set(overviewLevels).difference(factors)
            #~ missingOverviewLevels = sorted(overviewLevels)
            factorsArray = numpy.asarray(sorted(factors))
            missingOverviewLevels = []
            distance = 1
            for level in overviewLevels:
                if numpy.min(numpy.abs(factorsArray - level)) > distance:
                    missingOverviewLevels.append(level)

            # Fix the qlFactor
            aux = list(numpy.abs(factorsArray - self.qlFactor))
            index = aux.index(min(aux))
            self.qlFactor = factorsArray[index]
        else:
            missingOverviewLevels = overviewLevels

        # @TODO: do this after choosing the band
        if not missingOverviewLevels:
            ovrIndex = factors.index(self.qlFactor)
            ovrBand = band.GetOverview(ovrIndex)
            quicklook = ovrBand.ReadAsArray()

            # Compute the LUT
            # @TODO: use a function here
            min_ = quicklook.min()
            max_ = quicklook.max()
            nbins = max_ - min_ + 1
            range_ = (min_, max_+1)     # @NOTE: dtype = uint16
            histogram_ = numpy.histogram(quicklook, nbins, range_)[0]

            # Display the image and the quick look
            # @TODO: refactorize (the same code already in _openFile)
            lut = gsdtools.compute_lin_LUT2(histogram_)
            self.setGraphicsItem(dataset, lut)
            self.setQuickLook(quicklook, lut)
        else:
            logging.debug('missingOverviewLevels: %s' % missingOverviewLevels)
            # Run an external process for overviews computation
            self.progressbar.show()
            self.statusBar().showMessage('Quick look image generation ...')

            # @TODO: temporary close the dataset; il will be re-opened
            #        after the worker process ending to loaf changes
            #del dataset

            subProc = self.controller.subprocess
            assert subProc.state() == subProc.NotRunning
            logging.debug('Run the subprocess.')

            args = [os.path.basename(virtualDatasetFilename)] # @TODO: check
            args.extend(map(str, missingOverviewLevels))

            #self.subprocess.setEnvironmet(...)
            self.controller.subprocess.setWorkingDirectory(datasetCacheDir)
            self.controller.run_tool(*args)

            ## ALTERNATIVE: run in a separate thread
            # gdal.SetConfigOption('USE_RRD', 'YES')
            # ret = p.BuildOverviews('average', [2,4,8])
            # ovr = b.GetOverview(2)
            # data = ovr.ReadAsArray()

    def openFile(self):
        if self.filedialog.exec_():
            filename = self.filedialog.selectedFiles()[0]
            if filename:
                self.closeFile()
                self._openFile(filename)

    def closeFile(self):
        # Reset the scene and the view transformation matrix
        for view in (self.graphicsView, self.quicklookView):
            scene = view.scene()
            for item in scene.items():
                scene.removeItem(item)
                del item

            scene.setSceneRect(0, 0, 1, 1)
            view.setSceneRect(scene.sceneRect())
            view.resetMatrix()

        # Reset the info table
        self.infoTable.clear()
        self.infoTable.setHorizontalHeaderLabels(['Key', 'Value'])
        self.infoTable.setRowCount(0)

        # Reset attributes
        self.imageItem = None
        self.quicklook = None
        self.dataset = None
        self.qlFactor = None
        self.qlselection = None
        self.virtualDatasetFilename = None

        # Disable zoom actions
        self.zoomActions.setEnabled(False)

        self.statusBar().showMessage('Ready.')

    ### Zoom actions ##########################################################
    def zoomIn(self):
        factor = 1.2
        self.graphicsView.scale(factor, factor)

    def zoomOut(self):
        factor = 1./1.2
        self.graphicsView.scale(factor, factor)

    def zoomFit(self):
        self.graphicsView.fitInView(self.imageItem, QtCore.Qt.KeepAspectRatio)

    def zoom100(self):
        self.graphicsView.setMatrix(QtGui.QMatrix())

    ### Drag actions ##########################################################
    # @TODO:

    ### Help actions ##########################################################
    def about(self):
        QtGui.QMessageBox.about(self, self.tr('GSDView'),
                                self.tr('GeoSpatial Data Viewer'))

    def aboutQt(self):
        QtGui.QMessageBox.aboutQt(self)

    ### Auxiliaary methods ####################################################
    @overrideCursor
    def setGraphicsItem(self, dataset, lut):
        self.graphicsView.setUpdatesEnabled(False)
        try:
            self.imageItem = gdalqt4.GdalGraphicsItem(dataset)
            self.imageItem._lut = lut

            rect = self.imageItem.boundingRect()

            scene = self.graphicsView.scene()
            scene.addItem(self.imageItem)
            scene.setSceneRect(rect)

            self.graphicsView.setSceneRect(scene.sceneRect())
            self.graphicsView.ensureVisible(rect.x(), rect.y(), 1, 1, 0, 0)

        finally:
            self.graphicsView.setUpdatesEnabled(True)

    @overrideCursor
    def setQuickLook(self, data, lut):
        self.graphicsView.setUpdatesEnabled(False)
        try:
            data = gsdtools.apply_LUT(data, lut)
            image = Qwt.toQImage(data.transpose())
            pixmap = QtGui.QPixmap.fromImage(image)
            self.quicklook = pixmap
            self.qlFactor = self.dataset.RasterXSize // self.quicklook.width()

            scene = self.quicklookView.scene()
            item = scene.addPixmap(pixmap)
            rect = item.boundingRect()
            scene.setSceneRect(rect.x(), rect.y(), rect.width(), rect.height())
            self.quicklookView.setSceneRect(scene.sceneRect())
            self.quicklookView.ensureVisible(rect.x(), rect.y(), 1, 1, 0, 0)

            # Quicklook box
            pen = QtGui.QPen(QtCore.Qt.SolidLine)
            pen.setColor(QtGui.QColor(QtCore.Qt.red))
            scene = self.quicklookView.scene()
            self.qlselection = scene.addRect(QtCore.QRectF(), pen)
            self.qlselection.setZValue(1)
            self.updateQuicklookBox()
        finally:
            self.graphicsView.setUpdatesEnabled(True)

    # @TODO: update this
    def quickLookGenerationCompleted(self):
        try:
            if self.controller.subprocess.exitCode() != 0: # timeout 30000 ms
                msg = ('An error occurred during the quicklook generation.\n'
                       'Now close the dataset.')
                QtGui.QMessageBox.warning(self, '', msg)
                self.closeFile()   # @TODO: check
                return

            # @TODO: check if opening the dataset in update mode
            #        (gdal.GA_Update) is a better solution
            dataset = gdal.Open(self.virtualDatasetFilename)
            band = dataset.GetRasterBand(1)
            nOverviews = band.GetOverviewCount()
            if nOverviews < 1:
                msg = ('Unable to retrieve the quicklook image.\n'
                       'Now close the dataset.')
                QtGui.QMessageBox.warning(self, text=msg)
                self.closeFile()   # @TODO: check
                return

            self.dataset = dataset

            factors = []
            for ovrIndex in range(nOverviews):
                ovrXSize = band.GetOverview(ovrIndex).XSize
                factors.append(dataset.RasterXSize / ovrXSize)
                logging.debug('RasterXSize = %d, ovrXSize = %d' %
                                            (dataset.RasterXSize, ovrXSize))

            logging.debug('factors: %s' % map(str, factors))

            try:
                ovrIndex = factors.index(self.qlFactor)
            except ValueError:
                qlFactor = min(factors)
                ovrIndex = factors.index(min(factors))
                #logging.warning(       # @TODO: check
                logging.info('Overview with desired scale factor (%d) not '
                              'found.\n'
                              'Use scale factor %s instead.' %
                                                    (self.qlFactor, qlFactor))
                # Fix the qlFactor
                self.qlFactor = qlFactor

            ovrBand = band.GetOverview(ovrIndex)
            quicklook = ovrBand.ReadAsArray()

            # Compute the LUT
            # @TODO: use a function here
            min_ = quicklook.min()
            max_ = quicklook.max()
            nbins = max_ - min_ + 1
            range_ = (min_, max_ + 1)     # @NOTE: dtype = uint16
            histogram_ = numpy.histogram(quicklook, nbins, range_)[0]

            # Display the image and the quick look
            # @TODO: refactorize (the same code already in _openFile)
            lut = gsdtools.compute_lin_LUT2(histogram_)
            self.setGraphicsItem(dataset, lut)
            self.setQuickLook(quicklook, lut)
        finally:
            self.progressbar.hide()
            self.statusBar().showMessage('Ready.')

    def updateProgressBar(self, fract):
        self.progressbar.show()
        self.progressbar.setValue(int(100.*fract))

    def centerOn(self, pos):
        if self.dataset:
            qlfactor = float(self.dataset.RasterXSize) / self.quicklook.width()
            pos = self.quicklookView.mapToScene(pos.x(), pos.y())
            self.graphicsView.centerOn(pos.x()*qlfactor,
                                       pos.y()*qlfactor)

    def updateQuicklookBox(self):
        if self.quicklook:
            hbar = self.graphicsView.horizontalScrollBar()
            vbar = self.graphicsView.verticalScrollBar()
            x = hbar.value()
            y = vbar.value()
            w = hbar.pageStep()
            h = vbar.pageStep()

            # @TODO: bug report: mapping to scene seems to introduce a
            #        spurious offset "x1 = 2*x0"; this doesn't happen for "w"
            #~ polygon = self.graphicsView.mapToScene(x, y, w, h)
            #~ rect = polygon.boundingRect()

            qlfactor = float(self.dataset.RasterXSize) / self.quicklook.width()
            #~ x = rect.x() / qlfactor
            #~ y = rect.y() / qlfactor
            #~ w = rect.width() / qlfactor
            #~ h = rect.height() / qlfactor

            # @NOTE: this is a workaround; mapToScene should be used instead
            factor = qlfactor * self.graphicsView.matrix().m11()
            x /= factor
            y /= factor
            w /= factor
            h /= factor

            self.qlselection.setRect(x, y, w, h)

    def processingDone(self):
        self.controller.reset_controller()
        self.quickLookGenerationCompleted()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainWin = GSDView()
    mainWin.show()
    sys.exit(app.exec_())
