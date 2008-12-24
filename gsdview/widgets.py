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
import gdalsupport

import gsdview_resources


class GDALInfoWidget(QtGui.QWidget):
    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'gdalinfo.ui')
    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
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

    def __init__(self, *args):
        QtGui.QDialog.__init__(self, *args)
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


#~ class FileEntryWidget(QtGui.QWidget):
    #~ def __init__(self, *args):
        #~ QtGui.QWidget.__init__(self, *args): #, multple=False, directory=False):

        #~ self.filemode = None

        #~ self.completer = QtGui.QCompleter(self)
        #~ model = QtGui.QDirModel(self.completer)
        #~ model.setFilter(QtCore.QDir.AllDirs)
        #~ #self.completer.setCompletionMode(QtGui.QCompleter.InlineCompletion)
        #~ self.completer.setModel(model)

        #~ self.lineEdit = QtGui.QLineEdit()
        #~ self.lineEdit.setCompleter(completer)

        #~ self.button = QtGui.QPushButton()

        #~ layout = QtGui.QHBoxLayout()
        #~ layout.addWidget(self.lineEdit)
        #~ layout.addWidget(self.button)

        #~ self.addLayout(layout)

        #~ self.connect(self.button, QtCore.SIGNAL('clicked()'), self.choose)

    #~ def _choose(self, filename='', directory=False, multiple=False):
        #~ try:
            #~ mainwin = self.window()
            #~ filedialog = mainwin.filedialog
            #~ oldmode = filedialog.fileMode()
            #~ if filename:
                #~ filedialog.setDirectory(os.path.dirname(filename))
            #~ try:
                #~ if self.filemode is not None:
                    #~ filedialog.setFileMode(self.filemode)
                #~ if filedialog.exec_():
                    #~ filename = str(filedialog.selectedFiles()[0])
            #~ finally:
                #~ fiedialog.setFileMode(oldmode)
        #~ except AttributeError:
            #~ if filename:
                #~ dirname = os.path.dirname(filename)
            #~ else:
                #~ dirname = None

            #~ if self.filemode is None:
                #~ filemode = QtGui.QFileDialog.AnyFile
            #~ else:
                #~ filemode = self.filemode

            #~ if filemode == QtGui.QFileDialog.AnyFile:
                #~ filename = QtGui.QFileDialog.getSaveFileName(
                                    #~ self,
                                    #~ self.tr('Choose a file'),
                                    #~ dirname)
                                    #~ #const QString & filter = QString(),
                                    #~ #QString * selectedFilter = 0,
                                    #~ #Options options = 0)
            #~ elif filemode == QtGui.QFileDialog.ExistingFile:
                #~ filename = QtGui.QFileDialog.getOpenFileName(
                                    #~ self,
                                    #~ self.tr('Choose a file'),
                                    #~ dirname)
                                    #~ #const QString & filter = QString(),
                                    #~ #QString * selectedFilter = 0,
                                    #~ #Options options = 0)
            #~ elif filemode == QtGui.QFileDialog.ExistingFiles:
                #~ filename = QtGui.QFileDialog.getOpenFileNames(
                                    #~ self,
                                    #~ self.tr('Choose a file'),
                                    #~ dirname)
                                    #~ #const QString & filter = QString(),
                                    #~ #QString * selectedFilter = 0,
                                    #~ #Options options = 0)
            #~ elif (filemode == QtGui.QFileDialog.Directory) or
                                #~ (filemode == QtGui.QFileDialog.DirectoryOnly):
                #~ filename = QtGui.QFileDialog.getExistingDirectory(
                                    #~ self,
                                    #~ self.tr('Choose a file'),
                                    #~ dirname)
                                    #~ #Options options = ShowDirsOnly)
            #~ else:
                #~ raise TypeError('invalid file mode: "%s"' % filemode)
        #~ return filename

    #~ def choose(self):
        #~ filename = self.lineEdit.text()
        #~ filename = self._choose(filename)
        #~ if filename:
            #~ self.lineEdit.setText(filename)


class GeneralPreferencesPage(QtGui.QWidget):
    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'general-page.ui')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
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

    def apply():
        # Log level
        # Work directory
        # Favorite foldes
        pass

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
                if sys.platform[:3] == 'win':
                    dirname = 'C:\\'
                else:
                    dirname = os.path.expanduser('~')
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
    def addFavorite(self):
        dirname = self._chooseDir()
        if dirname:
            item = QtGui.QListWidgetItem(dirname)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.foldersListWidget.addItem(item)
            #self.foldersListWidget.addItem(newdir)

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

    def __init__(self, *args):
        QtGui.QWidget.__init__(self, *args)
        uic.loadUi(self.uifile, self)

        # environment
        hheader = self.envTableWidget.horizontalHeader()
        hheader.hide()
        hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)
        hheader.setStretchLastSection(True)

        for row in range(self.envTableWidget.rowCount()):
            item = QtGui.QTableWidgetItem('')
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.envTableWidget.setItem(row, 0, item)

        # config options
        #~ gdal.GetConfigOption('CPL_DEBUG', 'OFF')
        #~ gdal.GetConfigOption('GDAL_PAM_ENABLED', "NULL")
        #~ gdal.GetConfigOption(GDAL_DATA) (path of the GDAL "data" directory)
        #~ #gdal.GetConfigOption(GDAL_CACHEMAX) (memory used internally for caching in megabytes)



class PreferencesDialog(QtGui.QDialog):

    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'preferences.ui')

    def __init__(self, *args):
        QtGui.QDialog.__init__(self, *args)
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
    #~ test_generalpreferencespage()
    #~ test_gdalpreferencespage()
    test_preferencesdialog()
