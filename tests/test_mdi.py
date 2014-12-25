#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>
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


import os
import sys


# Fix sys path
GSDVIEWROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, GSDVIEWROOT)


from qt import QtCore, QtWidgets

from gsdview.mdi import MdiMainWindow
from gsdview.qtsupport import geticon


class MdiChild(QtWidgets.QTextEdit):
    sequenceNumber = 1

    def __init__(self):
        super(MdiChild, self).__init__(None)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.isUntitled = True
        #self.resize(600, 500) # doesn't work

        self.document().contentsChanged.connect(self.documentWasModified)

    def newFile(self):
        self.isUntitled = True
        self.curFile = self.tr('document%d.txt') % MdiChild.sequenceNumber
        MdiChild.sequenceNumber += 1
        self.setWindowTitle(self.curFile + '[*]')

    def loadFile(self, fileName):
        qfile = QtCore.QFile(fileName)
        if not qfile.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            QtWidgets.QMessageBox.warning(
                self, self.tr('MDI'),
                self.tr('Cannot read file %s:\n%s.') % (fileName,
                                                        qfile.errorString()))
            return False

        instr = QtCore.QTextStream(qfile)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.setPlainText(instr.readAll())
        QtWidgets.QApplication.restoreOverrideCursor()

        self.setCurrentFile(fileName)
        return True

    def save(self):
        if self.isUntitled:
            return self.saveAs()
        else:
            return self.saveFile(self.curFile)

    def saveAs(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr('Save As'), self.curFile)
        if filename.isEmpty:
            return False

        return self.saveFile(filename)

    def saveFile(self, fileName):
        qfile = QtCore.QFile(fileName)

        if not qfile.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            QtWidgets.QMessageBox.warning(
                self, self.tr('MDI'),
                self.tr('Cannot write file %s:\n%s.') % (fileName,
                                                         qfile.errorString()))
            return False

        outstr = QtCore.QTextStream(qfile)
        QtCore.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        outstr << self.toPlainText()
        QtCore.QApplication.restoreOverrideCursor()

        self.setCurrentFile(fileName)
        return True

    def userFriendlyCurrentFile(self):
        return self.strippedName(self.curFile)

    def currentFile(self):
        return self.curFile

    def closeEvent(self, event):
        if self.maybeSave():
            event.accept()
        else:
            event.ignore()

    @QtCore.Slot()
    def documentWasModified(self):
        self.setWindowModified(self.document().isModified())

    def maybeSave(self):
        if self.document().isModified():
            ret = QtWidgets.QMessageBox.warning(
                self, self.tr('MDI'),
                self.tr("'%s' has been modified.\n"
                        "Do you want to save your changes?") %
                self.userFriendlyCurrentFile(),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Default,
                QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Escape)
            if ret == QtWidgets.QMessageBox.Yes:
                return self.save()
            elif ret == QtWidgets.QMessageBox.Cancel:
                return False

        return True

    def setCurrentFile(self, fileName):
        self.curFile = QtCore.QFileInfo(fileName).canonicalFilePath()
        self.isUntitled = False
        self.document().setModified(False)
        self.setWindowModified(False)
        self.setWindowTitle(self.userFriendlyCurrentFile() + '[*]')

    def strippedName(self, fullFileName):
        return QtCore.QFileInfo(fullFileName).fileName()


class TestMdiMainWindow(MdiMainWindow):
    def __init__(self, parent=None):
        super(TestMdiMainWindow, self).__init__(parent)
        self.mdiarea.subWindowActivated.connect(self.updateActions)

        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.updateActions()

        self.setWindowTitle(self.tr('MDI'))
        self.statusBar().showMessage(self.tr('Ready'))

    def closeEvent(self, event):
        self.mdiarea.closeAllSubWindows()
        if self.mdiarea.activeSubWindow():
            event.ignore()
        else:
            event.accept()

    def activeMdiChild(self):
        subwindow = self.mdiarea.activeSubWindow()
        if subwindow:
            return subwindow.widget()
        return None

    @QtCore.Slot()
    def newFile(self):
        child = self.createMdiChild()
        child.newFile()
        child.show()

    @QtCore.Slot()
    def open(self):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self)
        if not fileName.isEmpty():
            existing = self.findMdiChild(fileName)
            if existing:
                self.mdiarea.setActiveSubWindow(existing)
                return

            child = self.createMdiChild()
            if child.loadFile(fileName):
                self.statusBar().showMessage(self.tr('File loaded'), 2000)
                child.show()
            else:
                child.close()

    @QtCore.Slot()
    def save(self):
        if self.activeMdiChild().save():
            self.statusBar().showMessage(self.tr('File saved'), 2000)

    @QtCore.Slot()
    def saveAs(self):
        if self.activeMdiChild().saveAs():
            self.statusBar().showMessage(self.tr('File saved'), 2000)

    @QtCore.Slot()
    def cut(self):
        self.activeMdiChild().cut()

    @QtCore.Slot()
    def copy(self):
        self.activeMdiChild().copy()

    @QtCore.Slot()
    def paste(self):
        self.activeMdiChild().paste()

    @QtCore.Slot()
    def about(self):
        QtWidgets.QMessageBox.about(
            self, self.tr('About MDI'),
            self.tr('The <b>MDI</b> example demonstrates how to write '
                    'multiple document interface applications using Qt.'))

    @QtCore.Slot(QtWidgets.QMdiSubWindow)
    def updateActions(self, window=None):
        hasMdiChild = (window is not None)
        self.saveAct.setEnabled(hasMdiChild)
        self.saveAsAct.setEnabled(hasMdiChild)
        self.pasteAct.setEnabled(hasMdiChild)

        hasSelection = (hasMdiChild and
                        window.widget().textCursor().hasSelection())
        self.cutAct.setEnabled(hasSelection)
        self.copyAct.setEnabled(hasSelection)

    def createMdiChild(self):
        child = MdiChild()
        window = self.mdiarea.addSubWindow(child)
        child.copyAvailable.connect(self.cutAct.setEnabled)
        child.copyAvailable.connect(self.copyAct.setEnabled)
        window.resize(600, 400)
        return child

    def createActions(self):
        style = QtWidgets.QApplication.style()

        icon = style.standardIcon(style.SP_FileIcon)
        self.newAct = QtWidgets.QAction(
            icon, self.tr('&New'), self,
            shortcut=self.tr('Ctrl+N'),
            statusTip=self.tr('Create a new file'),
            triggered=self.newFile)

        icon = style.standardIcon(style.SP_DialogOpenButton)
        self.openAct = QtWidgets.QAction(
            icon, self.tr('&Open...'), self,
            shortcut=self.tr('Ctrl+O'),
            statusTip=self.tr('Open an existing file'),
            triggered=self.open)

        icon = style.standardIcon(style.SP_DialogSaveButton)
        self.saveAct = QtWidgets.QAction(
            icon, self.tr('&Save'), self,
            shortcut=self.tr('Ctrl+S'),
            statusTip=self.tr('Save the document to disk'),
            triggered=self.save)

        self.saveAsAct = QtWidgets.QAction(
            self.tr('Save &As...'), self,
            statusTip=self.tr('Save the document under a new name'),
            triggered=self.saveAs)

        self.exitAct = QtWidgets.QAction(
            self.tr('E&xit'), self,
            shortcut=self.tr('Ctrl+Q'),
            statusTip=self.tr('Exit the application'),
            triggered=self.close)

        icon = geticon('cut.svg', 'gsdview')
        self.cutAct = QtWidgets.QAction(
            icon, self.tr('Cu&t'), self,
            shortcut=self.tr('Ctrl+X'),
            statusTip=self.tr("Cut the current  selection's contents  to the "
                              "clipboard"),
            triggered=self.cut)

        icon = geticon('copy.svg', 'gsdview.gdalbackend')
        self.copyAct = QtWidgets.QAction(
            icon, self.tr('&Copy'), self,
            shortcut=self.tr("Ctrl+C"),
            statusTip=self.tr("Copy the current selection's contents to the "
                              "clipboard"),
            triggered=self.copy)

        icon = geticon('paste.svg', 'gsdview')
        self.pasteAct = QtWidgets.QAction(
            icon, self.tr('&Paste'), self,
            shortcut=self.tr("Ctrl+V"),
            statusTip=self.tr("Paste the clipboard's contents into the "
                              "current selection"),
            triggered=self.paste)

        self.aboutAct = QtWidgets.QAction(
            self.tr('&About'), self,
            statusTip=self.tr("Show the application's About box"),
            triggered=self.about)

        self.aboutQtAct = QtWidgets.QAction(
            self.tr('About &Qt'), self,
            statusTip=self.tr("Show the Qt library's About box"),
            triggered=QtWidgets.QApplication.aboutQt)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu(self.tr('&File'))
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.editMenu = self.menuBar().addMenu(self.tr('&Edit'))
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)

        self.menuBar().addMenu(self.windowmenu)

        self.helpMenu = self.menuBar().addMenu(self.tr('&Help'))
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

    def createToolBars(self):
        self.fileToolBar = self.addToolBar(self.tr('File'))
        self.fileToolBar.addAction(self.newAct)
        self.fileToolBar.addAction(self.openAct)
        self.fileToolBar.addAction(self.saveAct)

        self.editToolBar = self.addToolBar(self.tr('Edit'))
        self.editToolBar.addAction(self.cutAct)
        self.editToolBar.addAction(self.copyAct)
        self.editToolBar.addAction(self.pasteAct)

    def findMdiChild(self, fileName):
        canonicalFilePath = QtCore.QFileInfo(fileName).canonicalFilePath()

        for window in self.mdiarea.subWindowList():
            if window.widget().currentFile() == canonicalFilePath:
                return window
        return None


def test_mdimainwin():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainwindow = TestMdiMainWindow()
    mainwindow.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    test_mdimainwin()
