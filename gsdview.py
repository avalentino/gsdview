#!/usr/bin/env python

import os
import sys
import logging

import numpy
import gdal
import tables

from PyQt4 import QtCore, QtGui
from PyQt4 import Qwt5 as Qwt

import resources

import gsdtools
import gdalsupport
import gdalqt4

def overrideCursor(func):
    def aux(*args, **kwargs):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            func(*args, **kwargs)
        finally:
            QtGui.QApplication.restoreOverrideCursor()
    return aux

class GraphicsView(QtGui.QGraphicsView):
    def __init__(self, *args):
        QtGui.QGraphicsView.__init__(self, *args)

    def mouseMoveEvent(self, event):
        if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            self.emit(QtCore.SIGNAL('mousePositionUpdated(const QPoint&)'),
                      event.pos())
            if event.buttons() & QtCore.Qt.LeftButton:
                self.emit(QtCore.SIGNAL('posMarked(const QPoint&)'), event.pos())
            #event.accept()
        QtGui.QGraphicsView.mouseMoveEvent(self, event)
        #event.ignore()

    def mousePressEvent(self, event):
        if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            if event.buttons() & QtCore.Qt.LeftButton:
                self.emit(QtCore.SIGNAL('posMarked(const QPoint&)'), event.pos())
            #event.accept()
        QtGui.QGraphicsView.mousePressEvent(self, event)
        #event.ignore()

    #~ def mouseReleaseEvent(self, event):
        #~ if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            #~ if event.buttons() & QtCore.Qt.LeftButton:
                #~ self.emit(QtCore.SIGNAL('posMarked(const QPoint&)'), event.pos())
            #~ #event.accept()
        #~ QtGui.QGraphicsView.mouseReleaseEvent(self, event)
        #~ #event.ignore()

#~ class QGdalCache(GdalCache,QObject):
    #~ pass



class Worker(QtCore.QThread):
    # @TODO: use a process instead

    def __init__(self, func, *args, **kwargs):
        parent = kwargs.pop('parent', None)
        QtCore.QThread.__init__(self, parent)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def progress_callback(self, fract):
        self.emit(QtCore.SIGNAL('updateProgressBar(double)'), fract)

    def run(self):
        result = self.func(*self.args, **self.kwargs)
        self.emit(QtCore.SIGNAL('finished(PyQt_PyObject)'), result)

class GSDView(QtGui.QMainWindow):
    # @TODO:
    #   * set cache location from settings
    #   * set all icon (can use the iconset of BEAM)
    #   * fix the 'key' column width of info table
    #   * show metadata in a tree
    #   * map panel
    #   * plugin architecture
    #   * rectangle on ql window (rubberband connected to fullres viewport
    #     motion --> requires a custom GraphicsView widget that re-implement
    #     the mouse event handlers)
    #   * click on ql --> update the fullres viewport --> requires a custom
    #     GraphicsView widget that re-implement the mouse event handlers

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(self.tr('GSDView'))
        self.resize(800, 600)

        self.graphicsView = QtGui.QGraphicsView(QtGui.QGraphicsScene(self), self)
        self.graphicsView.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        # @TODO: check
        #~ self.connect(self.graphicsView.horizontalScrollBar(), QtCore.SIGNAL('valueChange(int)'), self.updateQuicklookBox)
        #~ self.connect(self.graphicsView.verticalScrollBar(), QtCore.SIGNAL('valueChange(int)'), self.updateQuicklookBox)
        self.setCentralWidget(self.graphicsView)

        self.progressbar = QtGui.QProgressBar(self)
        self.progressbar.setTextVisible(True)
        self.statusBar().addPermanentWidget(self.progressbar)
        self.progressbar.hide()

        # @TODO
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
        self.prod = None

        # File dialog
        self.filedialog = QtGui.QFileDialog(self)
        self.filedialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        self.filedialog.setFilters(gdalsupport.gdalFilters())

        # Quick-look panel
        qlPanel = QtGui.QDockWidget('Quick Look panel', self)
        qlPanel.setObjectName('quickLookPanel')
        self.qlView = GraphicsView(QtGui.QGraphicsScene(self))
        #self.qlView.setDragMode(QtGui.QGraphicsView.ScrollHandDrag) # @TODO: check
        qlPanel.setWidget(self.qlView)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, qlPanel)
        #qlPanel.hide()              # @TODO: check
        #~ self.connect(self.qlView, QtCore.SIGNAL('mousePositionUpdated(const QPoint&)'),
                     #~ self.updatePosLabels)
        self.connect(self.qlView, QtCore.SIGNAL('posMarked(const QPoint&)'),
                     self.centerOn)

        # @TODO: it is required that a custom widget re-imptement the
        #        "mousePressEvent" evant handler
        #self.connect(self.qlView, QtCore.SIGNAL('mousePressEvent(QMouseEvent*)'), self.centerOn)

        # Map panel @TODO: use the marble widget
        mapPanel = QtGui.QDockWidget('Map panel', self)
        mapPanel.setObjectName('mapPanel')
        self.mapView = QtGui.QGraphicsView(self)
        mapPanel.setWidget(self.mapView)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, mapPanel)
        mapPanel.hide()             # @TODO: check

        # Info panel
        infoPanel = QtGui.QDockWidget('Info panel', self)
        infoPanel.setObjectName('infoPanel')
        self.infoTable = QtGui.QTableWidget(5, 2, self)
        self.infoTable.verticalHeader().hide()
        self.infoTable.setHorizontalHeaderLabels(['Key', 'Value'])
        self.infoTable.horizontalHeader().setStretchLastSection(True)
        #self.tableWidget.horizontalHeader().hide()
        infoPanel.setWidget(self.infoTable)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, infoPanel)
        #infoPanel.hide()            # @TODO: check

        # Actions
        self.setupActions()
        self.setupMenu()
        self.setupToolbars()

        self.zoomActions.setEnabled(False)
        self.statusBar().showMessage('Ready')

        # @TODO: check
        gdal.SetCacheMax(150*1024**2)

        # Thread
        # @TODO: use a process
        # @TODO: compute stats over the quicklook image
        self.qlWorker = Worker(gsdtools.quicklook_and_stats, parent=self)
        self.qlWorker.kwargs['progress_callback'] = self.qlWorker.progress_callback
        self.connect(self.qlWorker, QtCore.SIGNAL('finished(PyQt_PyObject)'),
                     self.quickLookGenerationCompleted)
        self.connect(self.qlWorker, QtCore.SIGNAL('updateProgressBar(double)'),
                     self.updateProgressBar)

        # Set cache folder
        self.cachedir = os.path.abspath('cache')
        if not os.path.exists(self.cachedir):
            os.makedirs(self.cachedir)

        # Settings
        #self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #                                 QtCore.QSettings.UserScope,
        #                                 'gsdview-soft', 'gsdview', self)
        #self.settings = QtCore.QSettings('gsdview-soft', 'gsdview', self)
        self.settings = QtCore.QSettings('gsdview.ini',
                                         QtCore.QSettings.IniFormat,
                                         self)
        self.connect(QtGui.qApp, QtCore.SIGNAL('aboutToQuit()'), self.saveSettings)
        self.loadSettings()

    ### Setup helpers #########################################################
    def setupActions(self):
        ### fileActions #######################################################
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
        self.actionExit = QtGui.QAction(QtGui.QIcon(':images/quit.svg'),
                                        self.tr('&Exit'), self)
        self.actionExit.setShortcut(self.tr('Ctrl+X'));
        self.actionExit.setStatusTip(self.tr('Exit the program'))
        self.connect(self.actionExit, QtCore.SIGNAL('triggered()'),
                     self.close)
        self.fileActions.addAction(self.actionExit)

        ### zoomActions #######################################################
        self.zoomActions = QtGui.QActionGroup(self)

        # Zoom in
        self.actionZoomIn = QtGui.QAction(QtGui.QIcon(':images/zoom-in.svg'),
                                          self.tr('Zoom In'), self)
        self.actionZoomIn.setStatusTip(self.tr('Zoom In'))
        self.actionZoomIn.setShortcut(QtGui.QKeySequence(self.tr('Ctrl++')))
        self.connect(self.actionZoomIn, QtCore.SIGNAL('triggered()'),
                     self.zoomIn)
        self.zoomActions.addAction(self.actionZoomIn)

        # Zoom out
        self.actionZoomOut = QtGui.QAction(QtGui.QIcon(':images/zoom-out.svg'),
                                           self.tr('Zoom Out'), self)
        self.actionZoomOut.setStatusTip(self.tr('Zoom Out'))
        self.actionZoomOut.setShortcut(QtGui.QKeySequence(self.tr('Ctrl+-')))
        self.connect(self.actionZoomOut, QtCore.SIGNAL('triggered()'),
                     self.zoomOut)
        self.zoomActions.addAction(self.actionZoomOut)

        # Zoom fit
        self.actionZoomFit = QtGui.QAction(QtGui.QIcon(':images/zoom-fit.svg'),
                                           self.tr('Zoom Fit'), self)
        self.actionZoomIn.setStatusTip(self.tr('Zoom to fit the window size'))
        self.connect(self.actionZoomFit, QtCore.SIGNAL('triggered()'),
                     self.zoomFit)
        self.zoomActions.addAction(self.actionZoomFit)

        # Zoom 100
        self.actionZoom100 = QtGui.QAction(QtGui.QIcon(':images/zoom-100.svg'),
                                           self.tr('Zoom 100%'), self)
        self.actionZoom100.setStatusTip(self.tr('Original size'))
        self.connect(self.actionZoom100, QtCore.SIGNAL('triggered()'),
                     self.zoom100)
        self.zoomActions.addAction(self.actionZoom100)

        ### helpActions #######################################################
        self.helpActions = QtGui.QActionGroup(self)

        # About
        self.actionAbout = QtGui.QAction(QtGui.QIcon(':images/about.svg'),
                                        self.tr('&About'), self)
        self.actionAbout.setStatusTip(self.tr('Show program information'))
        self.connect(self.actionAbout, QtCore.SIGNAL('triggered()'),
                     self.about)
        self.helpActions.addAction(self.actionAbout)

        # AboutQt
        self.actionAboutQt = QtGui.QAction(QtGui.QIcon(':images/qt-logo.png'),
                                        self.tr('About &Qt'), self)
        self.actionAboutQt.setStatusTip(self.tr('Show information about Qt'))
        self.connect(self.actionAboutQt, QtCore.SIGNAL('triggered()'),
                     self.aboutQt)
        self.helpActions.addAction(self.actionAboutQt)

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

    ### Settings ##############################################################
    def loadSettings(self):
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
        self.settings.endGroup() # mainwindow

    def saveSettings(self):
        self.settings.beginGroup('mainwindow')
        self.settings.setValue('position', QtCore.QVariant(self.pos()))
        self.settings.setValue('size', QtCore.QVariant(self.size()))
        self.settings.setValue('state', QtCore.QVariant(self.saveState()))
        self.settings.endGroup() # mainwindow

    ### File actions ##########################################################
    @overrideCursor
    def _openFile(self, filename):
        assert filename
        prod = gdal.Open(str(filename))

        # Update the info table
        self.infoTable.clear()
        metadata = prod.GetMetadata()
        self.infoTable.setHorizontalHeaderLabels(['Key', 'Value'])
        self.infoTable.setRowCount(len(metadata))
        self.infoTable.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        for row, key in enumerate(metadata):
            value = str(metadata[key])
            self.infoTable.setItem(row, 0, QtGui.QTableWidgetItem(key))
            self.infoTable.setItem(row, 1, QtGui.QTableWidgetItem(value))
        self.infoTable.sortByColumn(0, QtCore.Qt.AscendingOrder)

        # @TODO: check second time
        self.infoTable.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)

        self.prod = prod

        self.zoomActions.setEnabled(True)

        # Check the cache
        prod_id = gdalsupport.uniqueProdID(prod)
        cachefilename = os.path.join(self.cachedir, prod_id + '.h5')
        if os.path.exists(cachefilename):
            # Retrieve data from cache
            h5file = tables.openFile(cachefilename)
            quicklook = h5file.root.quicklook.read()
            histogram_ = h5file.root.statistics.histogram.read()
            attrs = h5file.root.statistics._v_attrs
            min_ = attrs.min
            max_ = attrs.max
            mean_ = attrs.mean
            std_ = attrs.std
            h5file.close()

            # Display the image and the quick look
            lut = gsdtools.compute_lin_LUT2(histogram_)
            self.setGraphicsItem(prod, lut)
            self.setQuickLook(quicklook, lut)
        else:
            self.progressbar.show()
            self.statusBar().showMessage('Quick look image generation ...')

            assert not self.qlWorker.isRunning()
            self.qlWorker.args = (prod,)
            self.qlWorker.start()

        #~ gdal.SetConfigOption('USE_RRD', 'YES')
        #~ ret = p.BuildOverviews('average', [2,4,8])
        #~ ov2 = b.GetOverview(2)
        #~ data2 = ov2.ReadAsArray()

        ## subprocess/QProcess
        ## gdaladdo --config USE_RRD YES $(filename)s 3 9 27 81
        ## gdaladdo --config USE_RRD YES $(filename)s 4 8 16 24


    def openFile(self):
        if self.filedialog.exec_():
            filename = self.filedialog.selectedFiles()[0]
            if filename:
                self.closeFile()
                self._openFile(filename)

    def closeFile(self):
        # Reset the scene and the view transformation matrix
        for view in (self.graphicsView, self.qlView):
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
        self.prod = None

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
    def setGraphicsItem(self, prod, lut):
        self.graphicsView.setUpdatesEnabled(False)
        try:
            self.imageItem = gdalqt4.GdalGraphicsItem(prod)
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
    def setQuickLook(self, quicklook, lut):
        self.graphicsView.setUpdatesEnabled(False)
        try:
            quicklook = gsdtools.apply_LUT(quicklook, lut)
            image = Qwt.toQImage(quicklook.transpose())
            pixmap = QtGui.QPixmap.fromImage(image)
            self.quicklook = pixmap
            self.qlFactor = self.prod.RasterXSize // self.quicklook.width()

            scene = self.qlView.scene()
            item = scene.addPixmap(pixmap)
            rect = item.boundingRect()
            scene.setSceneRect(rect.x(), rect.y(), rect.width(), rect.height())
            self.qlView.setSceneRect(scene.sceneRect())
            self.qlView.ensureVisible(rect.x(), rect.y(), 1, 1, 0, 0)
        finally:
            self.graphicsView.setUpdatesEnabled(True)

    def quickLookGenerationCompleted(self, result):
        try:
            self.qlWorker.wait()
            ql, min_, max_, mean_, std_, histogram_ = result

            # Store tata in the cache file
            prod_id = gdalsupport.uniqueProdID(self.prod)
            cachefilename = os.path.join(self.cachedir, prod_id + '.h5')

            h5file = tables.openFile(cachefilename, 'w')
            h5file.createArray(h5file.root, 'quicklook', ql, 'Quick-look image')

            statistics = h5file.createGroup(h5file.root, 'statistics',
                                            'Full resolution image statisrics')
            h5file.createArray(statistics, 'histogram', histogram_)
            attrs = statistics._v_attrs
            attrs.min = min_
            attrs.max = max_
            attrs.mean = mean_
            attrs.std = std_
            h5file.close()

            # Display the image and the quick look
            lut = gsdtools.compute_lin_LUT2(histogram_)
            self.setGraphicsItem(self.prod, lut)
            self.setQuickLook(ql, lut)
        finally:
            self.progressbar.hide()
            self.statusBar().showMessage('Ready.')

    def updateProgressBar(self, fract):
        self.progressbar.show()
        self.progressbar.setValue(int(100.*fract))

    def centerOn(self, pos):
        if self.prod:
            self.graphicsView.centerOn(pos.x()*self.qlFactor,
                                       pos.y()*self.qlFactor)

    #~ def updateQuicklookBox(self):
        #~ x = self.graphicsView.horizontalScrollBar().value()
        #~ y = self.graphicsView.verticalScrollBar().value()
        #~ w = self.graphicsView.viewport().width()
        #~ h = self.graphicsView.viewport().height()
        #~ print x,y,w,h

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainWin = GSDView()
    mainWin.show()
    sys.exit(app.exec_())
