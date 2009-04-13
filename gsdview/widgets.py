### Copyright (C) 2008-2009 Antonio Valentino <a_valentino@users.sf.net>

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


def get_mainwin():
    #mainwin = QtGui.qApp.findChild(QtGui.QMainWindow,  'gsdview-mainwin')
    for mainwin in QtGui.qApp.topLevelWidgets():
        if mainwin.objectName() == 'gsdview-mainwin':
            break
    else:
        # if no widget with the searched name is found then reset
        mainwin = None
    return mainwin

def get_filedialog(parent=None):
    try:
        #mainwin = QtGui.qApp.findChild(QtGui.QMainWindow,  'gsdview-mainwin')
        mainwin = get_mainwin()
        dialog = mainwin.filedialog
    except AttributeError:
        logging.debug('unable to find the GDSView main window widget')
        dialog = QtGui.QFileDialog(parent)
    return dialog

def _choosefile(filename='', dialog=None, mode=None):
    if not dialog:
        dialog = get_filedialog()

    oldmode = dialog.fileMode()
    if filename:
        dialog.setDirectory(os.path.dirname(str(filename)))
    try:
        if mode is not None:
            dialog.setFileMode(mode)
        if dialog.exec_():
            filename = str(dialog.selectedFiles()[0])
    finally:
        dialog.setFileMode(oldmode)
    return filename

def _choosedir(dirname, dialog=None,):
    return _choosefile(dirname, dialog, QtGui.QFileDialog.DirectoryOnly)

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

        self.updateCacheInfo()

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

    def updateCacheInfo(self):
        self.gdalCacheMaxValue.setText('%.3f MB' % (gdal.GetCacheMax()/1024.**2))
        self.gdalCacheUsedValue.setText('%.3f MB' % (gdal.GetCacheUsed()/1024.**2))

    def showEvent(self, event):
        self.updateCacheInfo()
        QtGui.QWidget.showEvent(self, event)

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
        tablewidget = self.versionsTableWidget
        #tableWidget.clear()
        #tableWidget.setHorizontalHeaderLabels(['Software', 'Version', 'Home Page'])
        tablewidget.verticalHeader().hide()
        tablewidget.horizontalHeader().setStretchLastSection(True)
        tablewidget.setRowCount(len(info.all_versions))
        for row, (sw, version, link) in enumerate(info.all_versions):
            tablewidget.setItem(row, 0, QtGui.QTableWidgetItem(sw))
            tablewidget.setItem(row, 1, QtGui.QTableWidgetItem(version))
            tablewidget.setItem(row, 2, QtGui.QTableWidgetItem(link))
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
        self.button.setToolTip(self.tr('select from file dialog'))

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._mode = None
        self.mode = mode
        self.dialog = dialog

        #~ if not self.dialog:
            #~ self.dialog = get_filedialog(self)

        self.connect(self.button, QtCore.SIGNAL('clicked()'), self.choose)

    def _get_mode(self):
        return self._mode

    def _set_mode(self, mode):
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

    def choose(self):
        filename = self.lineEdit.text()
        filename = _choosefile(filename, self.dialog, self.mode)
        if filename:
            self.lineEdit.setText(filename)

    def text(self):
        return self.lineEdit.text()

    def setText(self, text):
        self.lineEdit.setText(text)

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

        # Work directory
        dialog = get_filedialog(self)
        self.workdirEntryWidget.dialog = dialog
        self.workdirEntryWidget.mode = QtGui.QFileDialog.Directory
        #self.workdirEntryWidget.mode = QtGui.QFileDialog.DirectoryOnly
        self.cachedirEntryWidget.dialog = dialog
        self.cachedirEntryWidget.mode = QtGui.QFileDialog.Directory
        #self.cachedirEntryWidget.mode = QtGui.QFileDialog.DirectoryOnly

    def load(self, settings):
        # general
        settings.beginGroup('preferences')
        try:
            # log level
            level = settings.value('loglevel').toString()
            index = self.loglevelComboBox.findText(level)
            if 0 <= index < self.loglevelComboBox.count():
                self.loglevelComboBox.setCurrentIndex(index)
            else:
                logging.debug('invalid log level: "%s"' % level)

            # cache directory
            cachedir = settings.value('cachedir').toString()
            self.cachedirEntryWidget.setText(cachedir)
        finally:
            settings.endGroup()

        # filedialog
        settings.beginGroup('filedialog')
        try:
            # workdir
            workdir = settings.value('workdir').toString()
            self.workdirEntryWidget.setText(workdir)
        finally:
            settings.endGroup()

    def save(self, settings):
        # general
        settings.beginGroup('preferences')
        try:
            # log level
            level = self.loglevelComboBox.currentText()
            settings.setValue('loglevel', QtCore.QVariant(level))

            # cache directory
            cachedir = self.cachedirEntryWidget.text()
            if cachedir:
                settings.setValue('cachedir', QtCore.QVariant(cachedir))
            else:
                settings.remove('cachedir')

            self.cachedirEntryWidget.setText(cachedir)

        finally:
            settings.endGroup()

        # file dialog
        settings.beginGroup('filedialog')
        try:
            # @TODO: clear state

            # workdir
            workdir = self.workdirEntryWidget.text()
            if workdir:
                workdir = settings.setValue('workdir', QtCore.QVariant(workdir))
            else:
                settings.remove('workdir')

            # @TODO: clear history
        finally:
            settings.endGroup()

    # Log level
    def setLoglevel(self, level='INFO'):
        index = self.loglevelComboBox.findText(level)
        self.loglevelComboBox.setCurrentIndex(index)


class GDALPreferencesPage(QtGui.QWidget):
    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'gdal-page.ui')

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QWidget.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

        # info button
        self.connect(self.infoButton, QtCore.SIGNAL('clicked()'), self.showinfo)

        # standard options
        cachesize = gdal.GetCacheMax()
        self.cacheSpinBox.setValue(cachesize/1024**2)
        dialog = get_filedialog(self)
        for name in ('gdalDataDir', 'gdalDriverPath', 'ogrDriverPath'):
            widget = getattr(self, name + 'EntryWidget')
            widget.dialog = dialog
            widget.mode = QtGui.QFileDialog.Directory

        # extra options
        self._extraoptions = {}
        stdoptions = set(('GDAL_DATA', 'GDAL_SKIP', 'GDAL_DRIVER_PATH',
                          'OGR_DRIVER_PATH', 'GDAL_CACHEMAX', ''))

        extraoptions = gdalsupport.GDAL_CONFIG_OPTIONS.splitlines()
        extraoptions = [opt for opt in extraoptions if opt not in stdoptions]
        self.extraOptTableWidget.setRowCount(len(extraoptions))

        for row, key in enumerate(extraoptions):
            item = QtGui.QTableWidgetItem(key)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.extraOptTableWidget.setItem(row, 0, item)
            value = gdal.GetConfigOption(key, '')
            item = QtGui.QTableWidgetItem(value)
            self.extraOptTableWidget.setItem(row, 1, item)
            if value:
                self._extraoptions[key] = value

        hheader = self.extraOptTableWidget.horizontalHeader()
        #hheader.hide()
        hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)
        hheader.setStretchLastSection(True)

    def showinfo(self):
        try:
            mainwin = QtGui.qApp.findChild(QtGui.QMainWindow,  'gsdview-minwin')
            dialog = mainwin.aboutdialog
        except AttributeError:
            logging.debug('unable to find the GDSView main window widget')
            dialog = AboutDialog(self)

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

    def load(self, settings):
        settings.beginGroup('gdal')
        try:

            # cache size
            cachesize = settings.value('GDAL_CACHEMAX')
            if not cachesize.isNull():
                cachesize, ok = cachesize.toULongLong()
                if ok:
                    self.cacheCheckBox.setChecked(True)
                    self.cacheSpinBox.setValue(cachesize/1024**2)
            else:
                # show the current value and disable the control
                cachesize = gdal.GetCacheMax()
                self.cacheSpinBox.setValue(cachesize/1024**2)
                self.cacheCheckBox.setChecked(False)

            # GDAL data dir
            datadir = settings.value('GDAL_DATA').toString()
            if datadir:
                self.gdalDataCheckBox.setChecked(True)
                self.gdalDataDirEntryWidget.setText(datadir)
            else:
                # show the current value and disable the control
                datadir = gdal.GetConfigOption('GDAL_DATA', '')
                self.gdalDataDirEntryWidget.setText(datadir)
                self.gdalDataCheckBox.setChecked(False)

            # GDAL_SKIP
            gdalskip = settings.value('GDAL_SKIP').toString()
            if gdalskip:
                self.skipCheckBox.setChecked(True)
                self.skipLineEdit.setText(gdalskip)
            else:
                # show the current value and disable the control
                gdalskip = gdal.GetConfigOption('GDAL_SKIP', '')
                self.skipLineEdit.setText(gdalskip)
                self.skipCheckBox.setChecked(False)

            # GDAL driver path
            gdaldriverpath = settings.value('GDAL_DRIVER_PATH').toString()
            if gdaldriverpath:
                self.gdalDriverPathCheckBox.setChecked(True)
                self.gdalDriverPathEntryWidget.setText(gdaldriverpath)
            else:
                # show the current value and disable the control
                gdaldriverpath = gdal.GetConfigOption('GDAL_DRIVER_PATH', '')
                self.gdalDriverPathEntryWidget.setText(gdaldriverpath)
                self.gdalDriverPathCheckBox.setChecked(False)

            # OGR driver path
            ogrdriverpath = settings.value('OGR_DRIVER_PATH').toString()
            if ogrdriverpath:
                self.ogrDriverPathCheckBox.setChecked(True)
                self.ogrDriverPathEntryWidget.setText(ogrdriverpath)
            else:
                # show the current value and disable the control
                ogrdriverpath = gdal.GetConfigOption('OGR_DRIVER_PATH', '')
                self.ogrDriverPathEntryWidget.setText(ogrdriverpath)
                self.ogrDriverPathCheckBox.setChecked(False)

            # extra options
            # @TODO

        finally:
            settings.endGroup()

    def save(self, settings):
        settings.beginGroup('gdal')
        try:

            # cache
            if self.cacheCheckBox.isChecked():
                value = self.cacheSpinBox.value() * 1024**2
                settings.setValue('GDAL_CACHEMAX', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_CACHEMAX')

            # GDAL data dir
            if self.gdalDataCheckBox.isChecked():
                value = self.gdalDataDirEntryWidget.text()
                settings.setValue('GDAL_DATA', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_DATA')

            # GDAL_SKIP
            if self.skipCheckBox.isChecked():
                value = self.skipLineEdit.text()
                settings.setValue('GDAL_SKIP', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_SKIP')

            # GDAL driver path
            if self.gdalDriverPathCheckBox.isChecked():
                value = self.gdalDriverPathEntryWidget.text()
                settings.setValue('GDAL_DRIVER_PATH', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_DRIVER_PATH')

            # OGR driver path
            if self.ogrDriverPathCheckBox.isChecked():
                value = self.ogrDriverPathEntryWidget.text()
                settings.setValue('OGR_DRIVER_PATH', QtCore.QVariant(value))
            else:
                settings.remove('OGR_DRIVER_PATH')

            # extra options
            # @TODO
        finally:
            settings.endGroup()


class PreferencesDialog(QtGui.QDialog):
    '''Extendible preferences dialogg for GSDView.

    :signals:

    - apply

    '''

    # @TODO: also look at
    # /usr/share/doc/python-qt4-doc/examples/tools/settingseditor/settingseditor.py

    uifile = os.path.join(os.path.dirname(__file__), 'ui', 'preferences.ui')

    def __init__(self, parent=None, flags=QtCore.Qt.Widget): # QtCore.Qt.Dialog
        QtGui.QDialog.__init__(self, parent, flags)
        uic.loadUi(self.uifile, self)

        # remove empty page
        page = self.stackedWidget.widget(0)
        self.stackedWidget.removeWidget(page)

        # app pages
        self.addPage(GeneralPreferencesPage(),
                     QtGui.QIcon(':/images/preferences.svg'),
                     self.tr('General'))

        self.addPage(GDALPreferencesPage(),
                     QtGui.QIcon(':/images/GDALLogoColor.svg'),
                     self.tr('GDAL'))

        #~ self.addPage(CachePreferencesPage(),
                     #~ QtGui.QIcon(':/images/harddisk.svg'),
                     #~ self.tr('Cache'))

        assert self.listWidget.count() == self.stackedWidget.count()

        self.connect(
            self.listWidget,
            QtCore.SIGNAL('currentItemChanged(QListWidgetItem*, QListWidgetItem*)'),
            self.changePage)

        self.connect(self.buttonBox,
                     QtCore.SIGNAL('clicked(QAbstractButton*)'),
                     self._onButtonClicked)

    def _onButtonClicked(self, button):
        role = self.buttonBox.buttonRole(button)
        if role == QtGui.QDialogButtonBox.ApplyRole:
            self.emit(QtCore.SIGNAL('apply()'))

    def changePage(self, current, previous):
        if not current:
            current = previous

        self.stackedWidget.setCurrentIndex(self.listWidget.row(current))

    def addPage(self, page, icon, label=None):
        if not (hasattr(page, 'load') and hasattr(page, 'save')):
            raise TypeError('preference pages must have both "load" and '
                            '"save" methods')
        index = self.stackedWidget.addWidget(page)
        item = QtGui.QListWidgetItem(icon, label)
        self.listWidget.addItem(item)
        assert self.listWidget.row(item) == index

    def removePageIndex(self, index):
        if 0 <= index < self.stackedWidget.count():
            page = self.stackedWidget.widget(index)
            self.stackedWidget.removeWidget(page)
            self.listWidget.model().removeRow(index)

    def removePage(self, page):
        index = self.stackedWidget.indexOf(page)
        if 0 <= index < self.stackedWidget.count():
            self.stackedWidget.removeWidget(page)
            self.listWidget.model().removeRow(index)

    def load(self, settings):
        for index in range(self.stackedWidget.count()):
            page = self.stackedWidget.widget(index)
            page.load(settings)

    def save(self, settings):
        for index in range(self.stackedWidget.count()):
            page = self.stackedWidget.widget(index)
            page.save(settings)

    def apply(self):
        self.emit(QtCore.SIGNAL('apply()'))


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

    logging.basicConfig(level=logging.DEBUG)
    #~ test_gdalinfowidget()
    #~ test_aboutdialog()
    #~ test_fileentrywidget()
    #~ test_generalpreferencespage()
    #~ test_gdalpreferencespage()
    test_preferencesdialog()
