# -*- coding: utf-8 -*-

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


'''Specialized MainWindow classes and mixins.'''

# @TODO: move this to widgets sub-package or qt4freesolutions subpackage

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import sys; sys.path.insert(0, '..')
from PyQt4 import QtCore, QtGui

from gsdview.qtwindowlistmenu import QtWindowListMenu


class MdiMainWindow(QtGui.QMainWindow):
    '''Base class for MDI applications.

    :attributes:

    - mdiarea
    - windowactions
    - windowmenu

    :signals:

    - subWindowClosed()     # @TODO: should this signal be emitted by mdiarea?

    '''
    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QMainWindow.__init__(self, parent, flags)

        self.mdiarea = QtGui.QMdiArea()
        self.setCentralWidget(self.mdiarea)
        self.mdiarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.windowmenu = QtWindowListMenu(self.menuBar())
        self.windowmenu.attachToMdiArea(self.mdiarea)

    ### SIGNALS ###############################################################
    def subWindowClosed(self):
        self.emit(QtCore.SIGNAL('subWindowClosed()'))

class ItemSubWindow(QtGui.QMdiSubWindow):

    def __init__(self, item, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QMdiSubWindow.__init__(self, parent, flags)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.item = item


class ItemModelMainWindow(MdiMainWindow):

    def __init__(self, parent=None):
        super(ItemModelMainWindow, self).__init__(parent)

        self.datamodel = QtGui.QStandardItemModel(self)

        # @TODO: custom treeview with "currentChanged" slot re-implemented
        self.treeview = QtGui.QTreeView()
        # @TODO self.treeview.setSelectionMode(QtGui.QTreeView.SingleSelection)
        self.treeview.setModel(self.datamodel)
        self.treeview.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.treeview.header().hide()

        self.connect(self.treeview,
                     QtCore.SIGNAL('clicked(const QModelIndex&)'),
                     self.setActiveWinFromIndex)
        self.connect(self.mdiarea,
                     QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                     self.setActiveIndexFromWin)

        # setup the treeview dock
        treeviewdock = QtGui.QDockWidget(self.tr('Data Browser'), self)
        treeviewdock.setWidget(self.treeview)
        treeviewdock.setObjectName('TreeViewPanel')
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, treeviewdock)

    def currentItem(self):
        modelindex = self.treeview.currentIndex()
        if not modelindex.isValid():
            return None
        return self.datamodel.itemFromIndex(modelindex)

    def setActiveWinFromIndex(self, index):
        # @TODO: find a better name
        item = self.datamodel.itemFromIndex(index)
        windowlist = self.mdiarea.subWindowList()
        window = self.mdiarea.activeSubWindow()
        if window:
            windowlist.remove(window)
            windowlist.insert(0, window)

        for window in windowlist:
            try:
                if window.item == item:
                    self.mdiarea.setActiveSubWindow(window)
            except AttributeError:
                # the window has not an associated item in the datamodel
                pass

    def setActiveIndexFromWin(self, window):
        # @TODO: find a better name
        # @TODO: check and, if the case, remove
        if not window:
            return

        try:
            index = window.item.index()
        except AttributeError:
            # the window has not an associated item in the datamodel
            pass
        else:
            self.treeview.setCurrentIndex(index)


if __name__ == "__main__":
    from qt4support import geticon
    ### Test MdiMainWindow ####################################################
    def test_mdimainwin():
        class MdiChild(QtGui.QTextEdit):
            sequenceNumber = 1

            def __init__(self):
                QtGui.QTextEdit.__init__(self, None)
                self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                self.isUntitled = True
                #self.resize(600, 500) # doesn't work

                self.connect(self.document(),
                             QtCore.SIGNAL("contentsChanged()"),
                             self.documentWasModified)

            def newFile(self):
                self.isUntitled = True
                self.curFile = self.tr("document%1.txt").arg(MdiChild.sequenceNumber)
                MdiChild.sequenceNumber += 1
                self.setWindowTitle(self.curFile+"[*]")

            def loadFile(self, fileName):
                file = QtCore.QFile(fileName)
                if not file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
                    QtGui.QMessageBox.warning(self, self.tr("MDI"),
                                self.tr("Cannot read file %1:\n%2.")
                                .arg(fileName)
                                .arg(file.errorString()))
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
                fileName = QtGui.QFileDialog.getSaveFileName(
                                                self, self.tr("Save As"),
                                                self.curFile)
                if fileName.isEmpty:
                    return False

                return self.saveFile(fileName)

            def saveFile(self, fileName):
                file = QtCore.QFile(fileName)

                if not file.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
                    QtGui.QMessageBox.warning(self, self.tr("MDI"),
                            self.tr("Cannot write file %1:\n%2.")
                            .arg(fileName)
                            .arg(file.errorString()))
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

            def documentWasModified(self):
                self.setWindowModified(self.document().isModified())

            def maybeSave(self):
                if self.document().isModified():
                    ret = QtGui.QMessageBox.warning(self, self.tr("MDI"),
                            self.tr("'%1' has been modified.\n"\
                                    "Do you want to save your changes?")
                            .arg(self.userFriendlyCurrentFile()),
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
                self.setWindowTitle(self.userFriendlyCurrentFile() + "[*]")

            def strippedName(self, fullFileName):
                return QtCore.QFileInfo(fullFileName).fileName()


        class TestMdiMainWindow(MdiMainWindow):
            def __init__(self, parent=None):
                super(TestMdiMainWindow, self).__init__(parent)
                self.connect(self.mdiarea,
                             QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                             self.updateActions)

                self.createActions()
                self.createMenus()
                self.createToolBars()
                self.updateActions()

                self.setWindowTitle(self.tr("MDI"))
                self.statusBar().showMessage(self.tr("Ready"))

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

            def newFile(self):
                child = self.createMdiChild()
                child.newFile()
                child.show()

            def open(self):
                fileName = QtGui.QFileDialog.getOpenFileName(self)
                if not fileName.isEmpty():
                    existing = self.findMdiChild(fileName)
                    if existing:
                        self.mdiarea.setActiveSubWindow(existing)
                        return

                    child = self.createMdiChild()
                    if child.loadFile(fileName):
                        self.statusBar().showMessage(self.tr("File loaded"),
                                                     2000)
                        child.show()
                    else:
                        child.close()

            def save(self):
                if self.activeMdiChild().save():
                    self.statusBar().showMessage(self.tr("File saved"), 2000)

            def saveAs(self):
                if self.activeMdiChild().saveAs():
                    self.statusBar().showMessage(self.tr("File saved"), 2000)

            def cut(self):      self.activeMdiChild().cut()
            def copy(self):     self.activeMdiChild().copy()
            def paste(self):    self.activeMdiChild().paste()

            def about(self):
                QtGui.QMessageBox.about(self, self.tr("About MDI"),
                    self.tr("The <b>MDI</b> example demonstrates how to write multiple "
                            "document interface applications using Qt."))

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
                self.connect(child,
                             QtCore.SIGNAL("copyAvailable(bool)"),
                             self.cutAct.setEnabled)
                self.connect(child,
                             QtCore.SIGNAL("copyAvailable(bool)"),
                             self.copyAct.setEnabled)
                window.resize(600, 400)
                return child

            def createActions(self):
                style = QtGui.qApp.style()

                icon = style.standardIcon(style.SP_FileIcon)
                self.newAct = QtGui.QAction(icon, self.tr("&New"), self)
                self.newAct.setShortcut(self.tr("Ctrl+N"))
                self.newAct.setStatusTip(self.tr("Create a new file"))
                self.connect(self.newAct, QtCore.SIGNAL("triggered()"),
                             self.newFile)

                icon = style.standardIcon(style.SP_DialogOpenButton)
                self.openAct = QtGui.QAction(icon, self.tr("&Open..."), self)
                self.openAct.setShortcut(self.tr("Ctrl+O"))
                self.openAct.setStatusTip(self.tr("Open an existing file"))
                self.connect(self.openAct, QtCore.SIGNAL("triggered()"),
                             self.open)

                icon = style.standardIcon(style.SP_DialogSaveButton)
                self.saveAct = QtGui.QAction(icon, self.tr("&Save"), self)
                self.saveAct.setShortcut(self.tr("Ctrl+S"))
                self.saveAct.setStatusTip(self.tr("Save the document to disk"))
                self.connect(self.saveAct, QtCore.SIGNAL("triggered()"),
                             self.save)

                self.saveAsAct = QtGui.QAction(self.tr("Save &As..."), self)
                self.saveAsAct.setStatusTip(self.tr("Save the document under "
                                                    "a new name"))
                self.connect(self.saveAsAct, QtCore.SIGNAL("triggered()"),
                             self.saveAs)

                self.exitAct = QtGui.QAction(self.tr("E&xit"), self)
                self.exitAct.setShortcut(self.tr("Ctrl+Q"))
                self.exitAct.setStatusTip(self.tr("Exit the application"))
                self.connect(self.exitAct, QtCore.SIGNAL("triggered()"),
                             self.close)

                icon = geticon('cut.svg', 'gsdview')
                self.cutAct = QtGui.QAction(icon, self.tr("Cu&t"), self)
                self.cutAct.setShortcut(self.tr("Ctrl+X"))
                self.cutAct.setStatusTip(self.tr("Cut the current selection's "
                                                 "contents to the clipboard"))
                self.connect(self.cutAct, QtCore.SIGNAL("triggered()"), self.cut)

                icon = geticon('copy.svg', 'gsdview')
                self.copyAct = QtGui.QAction(icon, self.tr("&Copy"), self)
                self.copyAct.setShortcut(self.tr("Ctrl+C"))
                self.copyAct.setStatusTip(self.tr("Copy the current selection's "
                                                  "contents to the clipboard"))
                self.connect(self.copyAct, QtCore.SIGNAL("triggered()"),
                             self.copy)

                icon = geticon('paste.svg', 'gsdview')
                self.pasteAct = QtGui.QAction(icon, self.tr("&Paste"), self)
                self.pasteAct.setShortcut(self.tr("Ctrl+V"))
                self.pasteAct.setStatusTip(self.tr("Paste the clipboard's contents "
                                                   "into the current selection"))
                self.connect(self.pasteAct, QtCore.SIGNAL("triggered()"),
                             self.paste)

                self.aboutAct = QtGui.QAction(self.tr("&About"), self)
                self.aboutAct.setStatusTip(self.tr("Show the application's "
                                                   "About box"))
                self.connect(self.aboutAct, QtCore.SIGNAL("triggered()"),
                             self.about)

                self.aboutQtAct = QtGui.QAction(self.tr("About &Qt"), self)
                self.aboutQtAct.setStatusTip(self.tr("Show the Qt library's "
                                                     "About box"))
                self.connect(self.aboutQtAct, QtCore.SIGNAL("triggered()"),
                             QtGui.qApp, QtCore.SLOT("aboutQt()"))

            def createMenus(self):
                self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
                self.fileMenu.addAction(self.newAct)
                self.fileMenu.addAction(self.openAct)
                self.fileMenu.addAction(self.saveAct)
                self.fileMenu.addAction(self.saveAsAct)
                self.fileMenu.addSeparator()
                self.fileMenu.addAction(self.exitAct)

                self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
                self.editMenu.addAction(self.cutAct)
                self.editMenu.addAction(self.copyAct)
                self.editMenu.addAction(self.pasteAct)

                self.menuBar().addMenu(self.windowmenu)

                self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
                self.helpMenu.addAction(self.aboutAct)
                self.helpMenu.addAction(self.aboutQtAct)

            def createToolBars(self):
                self.fileToolBar = self.addToolBar(self.tr("File"))
                self.fileToolBar.addAction(self.newAct)
                self.fileToolBar.addAction(self.openAct)
                self.fileToolBar.addAction(self.saveAct)

                self.editToolBar = self.addToolBar(self.tr("Edit"))
                self.editToolBar.addAction(self.cutAct)
                self.editToolBar.addAction(self.copyAct)
                self.editToolBar.addAction(self.pasteAct)

            def findMdiChild(self, fileName):
                canonicalFilePath = QtCore.QFileInfo(fileName).canonicalFilePath()

                for window in self.mdiarea.subWindowList():
                    if window.widget().currentFile() == canonicalFilePath:
                        return window
                return None

        import sys
        app = QtGui.QApplication(sys.argv)
        mainwindow = TestMdiMainWindow()
        mainwindow.show()
        sys.exit(app.exec_())
    ### Test MdiMainWindow END ################################################

    test_mdimainwin()
