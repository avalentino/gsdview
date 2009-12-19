# -*- coding: UTF8 -*-

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


'''Widgets and dialogs for GSDView.'''

__author__   = '$Author$'
__date__     = '$Date$'
__revision__ = '$Revision$'

import os
import sys
import email
import logging
import traceback

from PyQt4 import QtCore, QtGui

from gsdview import info
from gsdview import utils
from gsdview import qt4support


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


AboutDialogBase = qt4support.getuiform('aboutdialog', __name__)
class AboutDialog(QtGui.QDialog, AboutDialogBase):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget): # QtCore.Qt.Dialog
        super(AboutDialog, self).__init__(parent, flags)
        self.setupUi(self)

        # Set icons
        logofile = qt4support.geticonfile('GSDView.png', __name__)
        self.setLogo(logofile)

        # Set contents
        self.titleLabel.setText('%s v. %s' % (self.tr(info.name), info.version))

        description = '''<p>%s</p>
<p>Home Page: <a href="%s">%s</a>
<BR>
Project Page: <a href="http://sourceforge.net/projects/gsdview">http://sourceforge.net/projects/gsdview</a></p>
<par>
<p><span style="font-size:9pt; font-style:italic;">%s</span></p>
''' % (self.tr(info.description), info.website, info.website_label, info.copyright)
        self.aboutTextBrowser.setText(description)

        self.setVersions()

    def setLogo(self, logofile):
        self.gsdviewLogoLabel.setPixmap(QtGui.QPixmap(logofile))


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

    def addSoftwareVersion(self, sw, version, link=''):
        tablewidget = self.versionsTableWidget
        index = tablewidget.rowCount()
        tablewidget.setRowCount(index+1)

        tablewidget.setItem(index, 0, QtGui.QTableWidgetItem(sw))
        tablewidget.setItem(index, 1, QtGui.QTableWidgetItem(version))
        tablewidget.setItem(index, 2, QtGui.QTableWidgetItem(link))


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

        icon = qt4support.geticon('open.svg', __name__)
        self.button = QtGui.QPushButton(icon, '')
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


GeneralPreferencesPageBase = qt4support.getuiform('general-page', __name__)
class GeneralPreferencesPage(QtGui.QWidget, GeneralPreferencesPageBase):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        super(GeneralPreferencesPage, self).__init__(parent, flags)
        self.setupUi(self)

        # Avoid promoted widgets
        self.cachedirEntryWidget = FileEntryWidget()
        self.cachedirEntryWidget.setToolTip(
                    self.tr('Location of the directory for file cache.\n'
                            'Default: "$HOME/.gsdview".'))
        self.preferencesGridLayout.addWidget(self.cachedirEntryWidget, 1, 1)

        self.workdirEntryWidget = FileEntryWidget()
        self.workdirEntryWidget.setToolTip(
                    self.tr('Base directory for files and directories '
                            'selection.\nDefault: "$HOME".'))
        self.fileDialogHorizontalLayout.addWidget(self.workdirEntryWidget)

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


PreferencesDialogBase = qt4support.getuiform('preferences', __name__)
class PreferencesDialog(QtGui.QDialog, PreferencesDialogBase):
    '''Extendible preferences dialogg for GSDView.

    :signals:

    - apply

    '''

    # @TODO: also look at
    # /usr/share/doc/python-qt4-doc/examples/tools/settingseditor/settingseditor.py

    def __init__(self, parent=None, flags=QtCore.Qt.Widget): # QtCore.Qt.Dialog
        super(PreferencesDialog, self).__init__(parent, flags)
        self.setupUi(self)

        self.setWindowIcon(qt4support.geticon('preferences.svg', __name__))

        # remove empty page
        page = self.stackedWidget.widget(0)
        self.stackedWidget.removeWidget(page)

        # app pages
        icon = qt4support.geticon('preferences.svg', __name__)
        self.addPage(GeneralPreferencesPage(), icon, self.tr('General'))

        #~ icon = qt4support.geticon('harddisk.svg', __name__)
        #~ self.addPage(CachePreferencesPage(), icon, self.tr('Cache'))

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


ExceptionDialogBase = qt4support.getuiform('exceptiondialog', __name__)
class ExceptionDialog(QtGui.QDialog, ExceptionDialogBase):

    def __init__(self, exctype=None, excvalue=None, tracebackobj=None,
                 parent=None, flags=QtCore.Qt.Widget): # QtCore.Qt.Dialog
        super(ExceptionDialog, self).__init__(parent, flags)
        self.setupUi(self)

        style = QtGui.qApp.style()

        icon = style.standardIcon(style.SP_CommandLink)
        sendbutton = QtGui.QPushButton(icon, self.tr('Send'))
        sendbutton.setToolTip(self.tr('Send the bug-report via email.'))
        sendbutton.setAutoDefault(False)
        self.buttonBox.addButton(sendbutton, QtGui.QDialogButtonBox.ActionRole)
        self.connect(sendbutton, QtCore.SIGNAL('clicked()'), self.sendBugReport)
        self.sendbutton = sendbutton

        icon = style.standardIcon(style.SP_DialogSaveButton)
        savebutton = QtGui.QPushButton(icon, self.tr('&Save'))
        savebutton.setToolTip(self.tr('Save the bug-report on file.'))
        savebutton.setAutoDefault(False)
        self.buttonBox.addButton(savebutton, QtGui.QDialogButtonBox.ActionRole)
        self.connect(savebutton, QtCore.SIGNAL('clicked()'), self.saveBugReport)
        self.savebutton = savebutton

        try:
            from PyQt4 import Qsci
            self.groupboxVerticalLayout.removeWidget(self.tracebackTextEdit)
            self.tracebackTextEdit.setParent(None)
            del self.tracebackTextEdit

            self.tracebackTextEdit = Qsci.QsciScintilla()
            self.groupboxVerticalLayout.addWidget(self.tracebackTextEdit)

            self.tracebackTextEdit.setMarginLineNumbers(
                                        Qsci.QsciScintilla.NumberMargin, True)
            self.tracebackTextEdit.setMarginWidth(
                                        Qsci.QsciScintilla.NumberMargin, 30)

            lexer = Qsci.QsciLexerPython()
            self.tracebackTextEdit.setLexer(lexer)
            self.tracebackTextEdit.recolor()

            self.tracebackTextEdit.setReadOnly(True)

            self.connect(self.tracebackGroupBox,
                         QtCore.SIGNAL('toggled(bool)'),
                         self.tracebackTextEdit,
                         QtCore.SLOT('setVisible(bool)'))
        except ImportError:
            pass

        title = 'Critical error: unhandled exception occurred'
        self.setWindowTitle(self.tr(title))

        style = QtGui.qApp.style()
        pixmap = style.standardPixmap(style.SP_MessageBoxCritical)
        self.iconLabel.setPixmap(pixmap)

        self.exctype = exctype
        self.excvalue = excvalue
        self.tracebackobj = tracebackobj

        if not self._excInfoSet():
            self.setExcInfo(*sys.exc_info())
        else:
            self._fill()

        self.connect(self.textLabel,
                     QtCore.SIGNAL('linkActivated(const QString&)'),
                     self._linkActivated)

    def _linkActivated(self, link):
        if 'mailto' in str(link):
            self.sendBugReport()
        else:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(link))

    def errorMsg(self):
        self.errormsgLabel.text()

    def setErrorMsg(self, text):
        #errormsg = traceback.format_exception_only(exctype, excvalue)
        self.errorMsgLabel.setText(text)

    def traceback(self):
        return self.tracebackTextEdit.text()

    def setTraceback(self, tb):
        if not isinstance(tb, basestring):
            self.tracebackobj = tb
            tb = ''.join(traceback.format_tb(tb))
        else: # @TODO: check
            self.resetExcInfo()
        self.tracebackTextEdit.setText(tb)

    def timeStamp(self):
        return self.timestampLabel.text()

    def setTimeStamp(self, timestamp=None):
        if timestamp is None:
            timestamp = email.utils.formatdate(localtime=True)
        self.timestampLabel.setText(timestamp)

    def _fill(self):
        if self._excInfoSet():
            lines = traceback.format_exception_only(self.exctype, self.excvalue)
            msg = '\n'.join(lines)
            self.setErrorMsg(msg)
            self.setTraceback(self.tracebackobj)
            self.setTimeStamp()
        else:
            self.setErrorMsg('None')
            self.tracebackTextEdit.setText('None')
            self.setTimeStamp('None')

    def setExcInfo(self, exctype, excvalue, tracebackobj):
        self.exctype = exctype
        self.excvalue = excvalue
        self.tracebackobj = tracebackobj
        self._fill()

    def resetExcInfo(self):
        self.setExcInfo(None, None, None)

    def text(self):
        return self.textLabel.text()

    def setText(self, text):
        self.textLabel.setText(text)

    def _excInfoSet(self):
        return all((self.exctype, self.excvalue, self.tracebackobj))

    def sendBugReport(self):
        if not self._excInfoSet():
            exctype, excvalue, tracebackobj = sys.exc_info()
        else:
            exctype = self.exctype
            excvalue = self.excvalue
            tracebackobj = self.tracebackobj

        error = traceback.format_exception_only(exctype, excvalue)[-1].strip()
        appname = QtGui.qApp.applicationName()
        if appname:
            subject = '[%s] Bug report - %s' % (appname, error)
        else:
            subject = 'Bug report - %s' % error
        body = '[Please instest your comments and additinal info here.]'
        body += '\n\n' + '-' * 80 + '\n'
        body += ''.join(utils.foramt_bugreport(exctype, excvalue, tracebackobj))

        url = QtCore.QUrl('mailto:%s <%s>' % (info.author, info.author_email))
        url.addQueryItem('subject', subject)
        url.addQueryItem('body', body)

        ret = QtGui.QDesktopServices.openUrl(url)
        if not ret:
            msg = self.tr('Unable to send the bug-report.\n'
                          'Please save the bug-report on file and send it '
                          'manually.')
            QtGui.QMessageBox.warning(self, self.tr('WARNING'), msg)

    def saveBugReport(self):
        if not self._excInfoSet():
            exctype, excvalue, tracebackobj = sys.exc_info()
        else:
            exctype = self.exctype
            excvalue = self.excvalue
            tracebackobj = self.tracebackobj

        lines = utils.foramt_bugreport(exctype, excvalue, tracebackobj)
        report = ''.join(lines)
        filename = QtGui.QFileDialog.getSaveFileName(self)
        if filename:
            fd = file(filename, 'w')
            try:
                fd.write(report)
            except Exception, e:
                msg = self.tr('Unable to save the bug-report:\n%s' % str(e))
                QtGui.QMessageBox.warning(self, self.tr('WARNING'), msg)
            finally:
                fd.close()


class GSDViewExceptionDialog(ExceptionDialog):
    def __init__(self, *args, **kwargs):
        super(GSDViewExceptionDialog, self).__init__(*args, **kwargs)
        text = ('Please file a bug report at '
            '<a href="%(website)s">%(website_label)s</a> '
            'or report the problem via email to '
            '<a href="mailto:$(author_email)s?subject=[gsdview] Bug report">'
                '%(author)s'
            '</a>.')
        text = text % info.__dict__
        self.setText(self.tr(text))
