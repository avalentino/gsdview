#!/usr/bin/env python

import os
import sys

# Select the PyQt API 2
import sip
sip.setapi('QDate',       2)
sip.setapi('QDateTime',   2)
sip.setapi('QString',     2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime',       2)
sip.setapi('QUrl',        2)
sip.setapi('QVariant',    2)

from PyQt4 import QtCore, QtGui

# Fix sys path
from os.path import abspath, dirname
GSDVIEWROOT = abspath(os.path.join(dirname(__file__), os.pardir, os.pardir))
sys.path.insert(0, GSDVIEWROOT)


from gsdview.mainwin import *
from gsdview.qt4support import geticon


class MdiChild(QtGui.QTextEdit):
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
        file = QtCore.QFile(fileName)
        if not file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, self.tr('MDI'),
                        self.tr('Cannot read file %s:\n%s.') % (
                                                fileName, file.errorString()))
            return False

        instr = QtCore.QTextStream(file)
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.setPlainText(instr.readAll())
        QtGui.QApplication.restoreOverrideCursor()

        self.setCurrentFile(fileName)
        return True

    def save(self):
        if self.isUntitled:
            return self.saveAs()
        else:
            return self.saveFile(self.curFile)

    def saveAs(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, self.tr('Save As'),
                                                     self.curFile)
        if fileName.isEmpty:
            return False

        return self.saveFile(fileName)

    def saveFile(self, fileName):
        file = QtCore.QFile(fileName)

        if not file.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, self.tr('MDI'),
                    self.tr('Cannot write file %s:\n%s.') % (
                                                fileName, file.errorString()))
            return False

        outstr = QtCore.QTextStream(file)
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

    @QtCore.pyqtSlot()
    def documentWasModified(self):
        self.setWindowModified(self.document().isModified())

    def maybeSave(self):
        if self.document().isModified():
            ret = QtGui.QMessageBox.warning(self, self.tr('MDI'),
                    self.tr("'%s' has been modified.\n"
                            "Do you want to save your changes?") %
                                            self.userFriendlyCurrentFile(),
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
                    QtGui.QMessageBox.No,
                    QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)
            if ret == QtGui.QMessageBox.Yes:
                return self.save()
            elif ret == QtGui.QMessageBox.Cancel:
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

    @QtCore.pyqtSlot()
    def newFile(self):
        child = self.createMdiChild()
        child.newFile()
        child.show()

    @QtCore.pyqtSlot()
    def open(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self)
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

    @QtCore.pyqtSlot()
    def save(self):
        if self.activeMdiChild().save():
            self.statusBar().showMessage(self.tr('File saved'), 2000)

    @QtCore.pyqtSlot()
    def saveAs(self):
        if self.activeMdiChild().saveAs():
            self.statusBar().showMessage(self.tr('File saved'), 2000)

    @QtCore.pyqtSlot()
    def cut(self):
        self.activeMdiChild().cut()

    @QtCore.pyqtSlot()
    def copy(self):
        self.activeMdiChild().copy()

    @QtCore.pyqtSlot()
    def paste(self):
        self.activeMdiChild().paste()

    @QtCore.pyqtSlot()
    def about(self):
        QtGui.QMessageBox.about(self, self.tr('About MDI'),
            self.tr('The <b>MDI</b> example demonstrates how to write multiple '
                    'document interface applications using Qt.'))

    @QtCore.pyqtSlot(QtGui.QMdiSubWindow)
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
        style = QtGui.qApp.style()

        icon = style.standardIcon(style.SP_FileIcon)
        self.newAct = QtGui.QAction(icon, self.tr('&New'), self,
                                    shortcut=self.tr('Ctrl+N'),
                                    statusTip=self.tr('Create a new file'),
                                    triggered=self.newFile)

        icon = style.standardIcon(style.SP_DialogOpenButton)
        self.openAct = QtGui.QAction(icon, self.tr('&Open...'), self,
                                     shortcut=self.tr('Ctrl+O'),
                                     statusTip=self.tr('Open an existing file'),
                                     triggered=self.open)

        icon = style.standardIcon(style.SP_DialogSaveButton)
        self.saveAct = QtGui.QAction(icon, self.tr('&Save'), self,
                                     shortcut=self.tr('Ctrl+S'),
                                     statusTip=self.tr('Save the document to '
                                                       'disk'),
                                     triggered=self.save)

        self.saveAsAct = QtGui.QAction(self.tr('Save &As...'), self,
                                       statusTip=self.tr('Save the document '
                                                          'under a new name'),
                                       triggered=self.saveAs)

        self.exitAct = QtGui.QAction(self.tr('E&xit'), self,
                                     shortcut=self.tr('Ctrl+Q'),
                                     statusTip=self.tr('Exit the application'),
                                     triggered=self.close)

        icon = geticon('cut.svg', 'gsdview')
        self.cutAct = QtGui.QAction(icon, self.tr('Cu&t'), self,
                                    shortcut=self.tr('Ctrl+X'),
                                    statusTip=self.tr("Cut the current "
                                                      "selection's contents "
                                                      "to the clipboard"),
                                    triggered=self.cut)

        icon = geticon('copy.svg', 'gsdview.gdalbackend')
        self.copyAct = QtGui.QAction(icon, self.tr('&Copy'), self,
                                     shortcut=self.tr("Ctrl+C"),
                                     statusTip=self.tr("Copy the current "
                                                       "selection's contents "
                                                       "to the clipboard"),
                                     triggered=self.copy)

        icon = geticon('paste.svg', 'gsdview')
        self.pasteAct = QtGui.QAction(icon, self.tr('&Paste'), self,
                                      shortcut=self.tr("Ctrl+V"),
                                      statusTip=self.tr("Paste the clipboard's "
                                                        "contents into the "
                                                        "current selection"),
                                      triggered=self.paste)

        self.aboutAct = QtGui.QAction(self.tr('&About'), self,
                                      statusTip=self.tr("Show the application's "
                                                        "About box"),
                                      triggered=self.about)

        self.aboutQtAct = QtGui.QAction(self.tr('About &Qt'), self,
                                        statusTip=self.tr("Show the Qt "
                                                          "library's About box"),
                                        triggered=QtGui.qApp.aboutQt)

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
    app = QtGui.QApplication(sys.argv)
    mainwindow = TestMdiMainWindow()
    mainwindow.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    test_mdimainwin()
