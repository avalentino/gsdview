### Copyright (C) 2008 Antonio Valentino <a_valentino@users.sf.net>

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

# -*- coding: UTF8 -*-

'''Widgets and dialogs for GSDView.'''

__author__   = '$Author: valentino $'
__date__     = '$Date: 2008-11-25 17:02:03 +0100 (mar, 25 nov 2008) $'
__revision__ = '$Revision: 621 $'

import os
import sys
import logging

try:
    from osgeo import gdal
except ImportError:
    import gdal

from PyQt4 import QtCore, QtGui, uic

import info
import utils
import gdalsupport

import gsdview_resources


class GDALInfoWidget(QtGui.QWidget):
    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'gdalinfo.ui')

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QWidget.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

        # @TODO: check for available info in gdal 1.5 and above
        try:
            self.gdalReleaseNameValue.setText(gdal.VersionInfo('RELEASE_NAME'))
            self.gdalReleaseDateValue.setText(gdal.VersionInfo('RELEASE_DATE'))
        except AttributeError:
            self.gdalVersionGroupBox.hide()

        self.gdalCacheMaxValue.setText('%.3f MB' % (gdal.GetCacheMax()/1024.**2))
        self.gdalCacheUsedValue.setText('%.3f MB' % (gdal.GetCacheUsed()/1024.**2))

        #~ gdal.GetConfigOption('CPL_DEBUG', 'OFF')
        #~ gdal.GetConfigOption('GDAL_PAM_ENABLED', "NULL")
        #~ gdal.GetConfigOption(GDAL_DATA) (path of the GDAL "data" directory)
        #~ #gdal.GetConfigOption(GDAL_CACHEMAX) (memory used internally for caching in megabytes)

        self.setGdalDriversTab()

    def setGdalDriversTab(self):
        driverlist = gdalsupport.getDriverList()
        self.gdalDriversNumValue.setText(str(len(driverlist)))

        tableWidget = self.gdalDriversTableWidget
        #tableWidget.clear()
        #tableWidget.setHorizontalHeaderLabels(['Software', 'Version', 'Home Page'])
        tableWidget.verticalHeader().hide()
        hheader = tableWidget.horizontalHeader()
        hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)
        hheader.setStretchLastSection(True)
        tableWidget.setRowCount(len(driverlist))
        sortingenabled = tableWidget.isSortingEnabled()
        tableWidget.setSortingEnabled(False)

        for row, driver in enumerate(driverlist):
            driver = gdalsupport.DriverProxy(driver)
            # @TODO: check for available ingo in gdal 1.5 and above
            tableWidget.setItem(row, 0, QtGui.QTableWidgetItem(driver.ShortName))
            tableWidget.setItem(row, 1, QtGui.QTableWidgetItem(driver.LongName))
            tableWidget.setItem(row, 2, QtGui.QTableWidgetItem(driver.GetDescription()))
            tableWidget.setItem(row, 3, QtGui.QTableWidgetItem(str(driver.HelpTopic)))

            metadata = driver.GetMetadata()
            if metadata:
                tableWidget.setItem(row, 4, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_EXTENSION, ''))))
                tableWidget.setItem(row, 5, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_MIMETYPE, ''))))
                tableWidget.setItem(row, 6, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_CREATIONDATATYPES, ''))))

                data = metadata.pop(gdal.DMD_CREATIONOPTIONLIST, '')
                # @TODO: parse xml
                tableItem = QtGui.QTableWidgetItem(data)
                tableItem.setToolTip(data)
                tableWidget.setItem(row, 7, tableItem)

                metadata.pop(gdal.DMD_HELPTOPIC, '')
                metadata.pop(gdal.DMD_LONGNAME, '')

                metadatalist = ['%s=%s' % (k, v) for k, v in metadata.items()]
                tableItem = QtGui.QTableWidgetItem(', '.join(metadatalist))
                tableItem.setToolTip('\n'.join(metadatalist))
                tableWidget.setItem(row, 8, tableItem)

        tableWidget.setSortingEnabled(sortingenabled)
        tableWidget.sortItems(0, QtCore.Qt.AscendingOrder)


class AboutDialog(QtGui.QDialog):

    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'aboutdialog.ui')

    def __init__(self, parent=None, flags=QtCore.Qt.Widget): # QtCore.Qt.Dialog
        QtGui.QDialog.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

        self.titleLabel.setText('%s v. %s' % (self.tr(info.name), info.version))

        description = '''<p>%s</p>
<p>Home Page: <a href="%s"><span style="text-decoration: underline; color:#0000ff;">%s</span></a>
<BR>
Project Page: <a href="http://sourceforge.net/projects/gsdview"><span style="text-decoration: underline; color:#0000ff;">http://sourceforge.net/projects/gsdview</span></a></p>
<par>
<p><span style="font-size:8pt; font-style:italic;">%s</span></p>
''' % (self.tr(info.description), info.website, info.website_label, info.copyright)
        self.aboutTextBrowser.setText(description)

        self.setVersions()


    def setVersions(self):
        tableWidget = self.versionsTableWidget
        #tableWidget.clear()
        #tableWidget.setHorizontalHeaderLabels(['Software', 'Version', 'Home Page'])
        tableWidget.verticalHeader().hide()
        tableWidget.horizontalHeader().setStretchLastSection(True)
        tableWidget.setRowCount(len(info.all_versions))
        for row, (sw, version_, link) in enumerate(info.all_versions):
            tableWidget.setItem(row, 0, QtGui.QTableWidgetItem(sw))
            tableWidget.setItem(row, 1, QtGui.QTableWidgetItem(version_))
            tableWidget.setItem(row, 2, QtGui.QTableWidgetItem(link))
            #~ tableWidget.setItem(row, 2,
                #~ QtGui.QTableWidgetItem('<a href="%s">%s</a>' % (link, link)))


class FileEntryWidget(QtGui.QWidget):
    def __init__(self, contents='', mode=QtGui.QFileDialog.AnyFile,
                dialog=None, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QWidget.__init__(self, parent, flags)

        self.__completer = QtGui.QCompleter(self)
        model = QtGui.QDirModel(self.__completer)
        #model.setFilter(QtCore.QDir.AllEntries)
        #self.completer.setCompletionMode(QtGui.QCompleter.InlineCompletion)
        self.__completer.setModel(model)

        self.lineEdit = QtGui.QLineEdit()
        self.lineEdit.setCompleter(self.__completer)

        self.button = QtGui.QPushButton(QtGui.QIcon (':/images/open.svg'), '')

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.button)
        self.setLayout(layout)

        self._mode = None
        self.mode = mode
        self.dialog = dialog

        self.connect(self.button, QtCore.SIGNAL('clicked()'), self.choose)

    def _get_mode(self):
        return self._mode

    def _set_mode(self, mode):
        print 'ppp'
        if mode == QtGui.QFileDialog.ExistingFiles:
            raise ValueError('"QtGui.QFileDialog.ExistingFiles": multiple '
                             'files selection not allowed')
        model = self.lineEdit.completer().model()
        if mode in (QtGui.QFileDialog.AnyFile, QtGui.QFileDialog.ExistingFile):
            model.setFilter(QtCore.QDir.AllEntries)
        elif mode in (QtGui.QFileDialog.Directory,
                      QtGui.QFileDialog.DirectoryOnly):
            model.setFilter(QtCore.QDir.Dirs)
        else:
            raise ValueError('invalid mode: "%d"' % mode)

        self._mode = mode

    mode = property(_get_mode, _set_mode)

    def _choose(self, filename='', directory=False):
        if not self.dialog:
            self.dialog = QtGui.QFileDialog(self)

        oldmode = self.dialog.fileMode()
        if filename:
            self.dialog.setDirectory(os.path.dirname(str(filename)))
        try:
            if self.mode is not None:
                self.dialog.setFileMode(self.mode)
            if self.dialog.exec_():
                filename = str(self.dialog.selectedFiles()[0])
        finally:
            self.dialog.setFileMode(oldmode)
        return filename

    def choose(self):
        filename = self.lineEdit.text()
        filename = self._choose(filename)
        if filename:
            self.lineEdit.setText(filename)

    text = QtGui.QLineEdit.text
    setText = QtGui.QLineEdit.setText

class GeneralPreferencesPage(QtGui.QWidget):
    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'general-page.ui')

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QWidget.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

        self.loglevelComboBox.setFocus()

        # Log level
        logger = logging.getLogger() # @TODO: fix
        level = logging.getLevelName(logger.level)
        self.setLoglevel(level)

        self.connect(self.resetLoglevelButton,
                     QtCore.SIGNAL('clicked()'),
                     self.setLoglevel)

        #~ self.connect(self.loglevelComboBox,
                     #~ QtCore.SIGNAL('currentIndexChanged(const QString&)'),
                     #~ self.changeLoglevel)

        # Work directory
        completer = QtGui.QCompleter(self.workdirLineEdit)
        model = QtGui.QDirModel(completer)
        model.setFilter(QtCore.QDir.AllDirs)
        completer.setModel(model)
        #completer.setCompletionMode(QtGui.QCompleter.InlineCompletion)
        self.workdirLineEdit.setCompleter(completer)
        self._workdir_completer = completer # needed to keep the completer alive

        self.connect(self.chooseWorkdirButton,
                     QtCore.SIGNAL('clicked()'),
                     self.chooseWorkdir)

        # Favorite editor
        self.foldersListWidget.addAction(self.actionAddFavorite)
        self.foldersListWidget.addAction(self.actionEditFavorite)
        self.foldersListWidget.addAction(self.actionRemoveFavorite)
        self.foldersListWidget.addAction(self.actionClearFavorites)

        self.setFavoriteActions()
        self.enableClearAction()

        self.connect(self.actionAddFavorite,
                    QtCore.SIGNAL('triggered()'),
                    self.addFavorite)

        self.connect(self.actionEditFavorite,
                    QtCore.SIGNAL('triggered()'),
                    self.editFavorite)

        self.connect(self.actionRemoveFavorite,
                    QtCore.SIGNAL('triggered()'),
                    self.removeFavorite)

        self.connect(self.actionClearFavorites,
                    QtCore.SIGNAL('triggered()'),
                    self.clearFavorites)

        self.connect(self.foldersListWidget,
                     QtCore.SIGNAL('itemSelectionChanged()'),
                     self.setFavoriteActions)

        self.connect(self.foldersListWidget.model(),
                     QtCore.SIGNAL('rowsInserted(const QModelIndex&, int, int)'),
                     self.enableClearAction)

        self.connect(self.foldersListWidget.model(),
                     QtCore.SIGNAL('rowsRemoved(const QModelIndex&, int, int)'),
                     self.enableClearAction)

    def load(self, settings):
        # general
        settings.beginGroup('preferences')

        # log level
        level = settings.value('loglevel').toString()
        index = self.loglevelComboBox.findText(level)
        if 0 <= index < self.loglevelComboBox.count():
            self.loglevelComboBox.setCurrentIndex(index)
        else:
            logging.debug('invalid log level: "%s"' % level)

        settings.endGroup()

        # filedialog
        settings.beginGroup('filedialog')

        # workdir
        workdir = settings.value('workdir').toString()
        self.workdirLineEdit.setText(workdir)

        # sidebar urls
        self.foldersListWidget.clear()
        try:
            # QFileDialog.setSidebarUrls is new in Qt 4.3
            sidebarurls = settings.value('sidebarurls')
            if not sidebarurls.isNull():
                sidebarurls = sidebarurls.toStringList()
                self.foldersListWidget.addItems(sidebarurls)
        except AttributeError:
            logging.debug('unable to restore sidebar URLs of the file dialog')

        settings.endGroup()

    def save(self, settings):
        # general
        settings.beginGroup('preferences')

        # log level
        level = self.loglevelComboBox.setCurrentText()
        settings.SetValue('loglevel', QtCore.QVariant(level))

        settings.endGroup()

        # file dialog
        settings.beginGroup('filedialog')
        # @TODO: clear state

        # workdir
        workdir = self.workdirLineEdit.text()
        workdir = settings.setValue('workdir', QtCore.QVariant(workdir))

        # @TODO: clear history

        # sidebat urls
        try:
            sidebarurls = [self.foldersListWidget.item(row).text()
                              for row in range(self.foldersListWidget.count())]
            settings.setValue('sidebarurls', QtCore.QVariant(sidebarurls))
        except AttributeError:
            logging.debug('unable to save sidebar URLs of the file dialog')
        settings.endGroup()

    def _chooseDir(self, dirname=''):
        try:
            mainwin = self.window()
            filedialog = mainwin.filedialog
            oldmode = filedialog.fileMode()
            if dirname:
                filedialog.setDirectory(dirname)
            try:
                filedialog.setFileMode(QtGui.QFileDialog.Directory)
                if filedialog.exec_():
                    dirname = str(filedialog.selectedFiles()[0])
            finally:
                fiedialog.setFileMode(oldmode)
        except AttributeError:
            if not dirname:
                dirname = utils.default_workdir()
            dirname = QtGui.QFileDialog.getExistingDirectory(
                                    self,
                                    self.tr('Choose the work directory'),
                                    dirname)
        return dirname

    # Log level
    def setLoglevel(self, level='INFO'):
        index = self.loglevelComboBox.findText(level)
        self.loglevelComboBox.setCurrentIndex(index)

    #~ def changeLoglevel(self, level):
        #~ # @TODO: mark as changed an apply changes only when "Apply" or "OK"
        #~ #        are pressed
        #~ logger = logging.getLogger()    # @TODO: fix
        #~ logger.setLevel(logging.getLevelName(level))

    # Workdir
    def chooseWorkdir(self):
        dirname = self.workdirLineEdit.text()
        dirname = self._chooseDir(dirname)
        if dirname:
            self.workdirLineEdit.setText(dirname)

    # Favorite foldes
    def _addFavorite(self, dirname):
        item = QtGui.QListWidgetItem(dirname)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.foldersListWidget.addItem(item)

    def addFavorite(self):
        dirname = self._chooseDir()
        if dirname:
            self._addFavorite(dirname)

    def editFavorite(self, item=None):
        if item is None:
            item = self.foldersListWidget.currentItem()
        self.foldersListWidget.clearSelection()
        dirname = self._chooseDir(dirname=item.text())
        if dirname:
            item.setText(dirname)

    def removeFavorite(self):
        for item in self.foldersListWidget.selectedItems():
            model = self.foldersListWidget.model()
            row = self.foldersListWidget.row(item)
            model.removeRow(row)

    def clearFavorites(self):
        self.foldersListWidget.clear()
        self.enableClearAction()

    def setFavoriteActions(self):
        if len(self.foldersListWidget.selectedItems()):
            enabled = True
        else:
            enabled = False
        self.actionEditFavorite.setEnabled(enabled)
        self.actionRemoveFavorite.setEnabled(enabled)

        self.editFolderButton.setEnabled(enabled)
        self.removeFolderButton.setEnabled(enabled)

    def enableClearAction(self):
        if self.foldersListWidget.count():
            enabled = True
        else:
            enabled = False
        self.actionClearFavorites.setEnabled(enabled)
        self.clearFoldersButton.setEnabled(enabled)


class GDALPreferencesPage(QtGui.QWidget):
    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'gdal-page.ui')

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QWidget.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

        # info button
        self.connect(self.infoButton, QtCore.SIGNAL('clicked()'), self.showinfo)

        # GDAL config
        self.connect(self.gdalDataChooseDirButton,
                     QtCore.SIGNAL('clicked()'),
                     self.debugComboBox.setEnabled)

        # environment
        hheader = self.envTableWidget.horizontalHeader()
        hheader.hide()
        hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)
        hheader.setStretchLastSection(True)

        #~ for row in range(self.envTableWidget.rowCount()):
            #~ item = QtGui.QTableWidgetItem('')
            #~ item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            #~ self.envTableWidget.setItem(row, 0, item)

        # config options
        #~ gdal.GetConfigOption('CPL_DEBUG', 'OFF')
        #~ gdal.GetConfigOption('GDAL_PAM_ENABLED', "NULL")
        #~ gdal.GetConfigOption('GDAL_PAM_MODE', "NULL")
        #~ gdal.GetConfigOption(GDAL_DATA) (path of the GDAL "data" directory)
        #~ #gdal.GetConfigOption(GDAL_CACHEMAX) (memory used internally for caching in megabytes)
    '''
    GDAL_DATA
    GDAL_SKIP
    GDAL_DRIVER_PATH
    OGR_DRIVER_PATH

    #GDAL_CACHEMAX
    GDAL_FORCE_CACHING
    GDAL_DISABLE_READDIR_ON_OPEN
    GDAL_MAX_DATASET_POOL_SIZE
    GDAL_IGNORE_AXIS_ORIENTATION
    GDAL_SWATH_SIZE
    GDAL_DISABLE_READDIR_ON_OPEN
    GDAL_VALIDATE_CREATION_OPTIONS
    GDAL_ONE_BIG_READ
    GDAL_DTED_SINGLE_BLOCK

    GDAL_PAM_ENABLED
    GDAL_PAM_MODE
    GDAL_PAM_PROXY_DIR

    GDAL_TIFF_INTERNAL_MASK
    GDAL_TIFF_ENDIANNESS

    GDAL_JPEG_TO_RGB
    GDAL_ECW_CACHE_MAXMEM

    OGR_XPLANE_READ_WHOLE_FILE
    OGR_SDE_GETLAYERTYPE
    OGR_SDE_SEARCHORDER
    OGR_S57_OPTIONS
    OGR_DEBUG_ORGANIZE_POLYGONS
    OGR_ORGANIZE_POLYGONS

    CPL_DEBUG
    CPL_LOG
    CPL_LOG_ERRORS
    CPL_ACCUM_ERROR_MSG
    CPL_MAX_ERROR_REPORTS
    CPL_TIMESTAMP
    CPL_TMPDIR

    COMPRESS_OVERVIEW
    INTERLEAVE_OVERVIEW
    PHOTOMETRIC_OVERVIEW

    TMPDIR
    TEMP

    USE_RRD
    USE_SPILL

    PROJSO

    GMLJP2OVERRIDE
    GEOTIFF_CSV
    JPEGMEM

    DODS_CONF
    DODS_AIS_FILE

    BSB_PALETTE

    CONVERT_YCBCR_TO_RGB
    ECW_LARGE_OK
    IDRISIDIR
    DTED_VERIFY_CHECKSUM
    IDA_COLOR_FILE
    RPFTOC_FORCE_RGBA
    HFA_USE_RRD", "NO" ) ) )
    ADRG_SIMULATE_MULTI_GEN
    HDF4_BLOCK_PIXELS
    GEOL_AS_GCPS

    CENTER_LONG

    OCI_FID
    OCI_DEFAULT_DIM

    MDBDRIVER_PATH
    ODBC_OGR_FID
    DGN_LINK_FORMAT

    TIGER_VERSION
    TIGER_LFIELD_AS_STRING

    PGSQL_OGR_FID
    PGCLIENTENCODING
    PG_USE_COPY
    PG_USE_POSTGIS
    PG_LIST_ALL_TABLES

    S57_CSV
    S57_PROFILE

    INGRES_INSERT_SUB

    IDB_OGR_FID

    GPX_N_MAX_LINKS
    GPX_ELE_AS_25D
    GPX_USE_EXTENSIONS

    SDE_VERSIONEDITS
    SDE_VERSIONOVERWRITE
    SDE_DESCRIPTION
    SDE_FID

    GML_FIELDTYPES
    MYSQL_TIMEOUT
    GEOMETRY_AS_COLLECTION
    ATTRIBUTES_SKIP
    KML_DEBUG
    '''

    def showinfo(self):
        try:
            dialog = self.window().aboutdialog
            print 'global AboutDialog'
        except AttributeError:
            dialog = AboutDialog(self)
            print 'new AboutDialog'
        currentpage = dialog.tabWidget.currentIndex()
        try:
            gdalTab = dialog.tabWidget.findChild(QtGui.QWidget, 'gdalTab')
            if not gdalTab:
                raise RuntimeError('unable to locate the "gdalTab" widget in '
                                   'the "AboutDialog"')
            dialog.tabWidget.setCurrentWidget(gdalTab)
            dialog.exec_()
        finally:
            dialog.tabWidget.setCurrentIndex(currentpage)

    def updateConfigToolTips(self):
        #~ void setToolTip ( const QString & )
        self.debugComboBox.setToolTip()


class PreferencesDialog(QtGui.QDialog):
    # @TODO: aloso loook at
    # /usr/share/doc/python-qt4-doc/examples/tools/settingseditor/settingseditor.py

    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'preferences.ui')

    def __init__(self, parent=None, flags=QtCore.Qt.Widget): # QtCore.Qt.Dialog
        QtGui.QDialog.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

        self.connect(
            self.listWidget,
            QtCore.SIGNAL('currentItemChanged(QListWidgetItem*, QListWidgetItem*)'),
            self.changePage)

    def changePage(self, current, previous):
        if not current:
            current = previous

        self.stackedWidget.setCurrentIndex(self.listWidget.row(current))

if __name__ == '__main__':
    def test_gdalinfowidget():
        app = QtGui.QApplication(sys.argv)
        d = QtGui.QDialog()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(GDALInfoWidget())
        d.setLayout(layout)
        d.show()
        app.exec_()

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

    def test_gdalpreferencespage():
        app = QtGui.QApplication(sys.argv)
        d = QtGui.QDialog()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(GDALPreferencesPage())
        d.setLayout(layout)
        d.show()
        app.exec_()

    def test_preferencesdialog():
        app = QtGui.QApplication(sys.argv)
        d = PreferencesDialog()
        d.show()
        app.exec_()

    #~ test_gdalinfowidget()
    #~ test_aboutdialog()
    test_fileentrywidget()
    #~ test_generalpreferencespage()
    #~ test_gdalpreferencespage()
    #~ test_preferencesdialog()
