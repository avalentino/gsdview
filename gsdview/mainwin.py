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

'''Specialized MainWindow classes and mixins.'''

# @TODO: move this to widgets sub-package or qt4freesolutions subpackage

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date: 2009-01-12 22:46:23 +0100 (lun, 12 gen 2009) $'
__revision__ = '$Revision: 324 $'

import sys

from PyQt4 import QtCore, QtGui

'''Sub-window menu

http://doc.trolltech.com/solutions/4/qtwindowlistmenu/

Inherits QMenu.

Public Functions

    * QtWindowListMenu(QWorkspace* workspace, QWidget* parent=0, const char* name=0)
    * QAction *addTo(const QString& text, QMenuBar* menubar, int idx=-1)
    * void removeWindow(QWidget* w, bool windowDestroyed=false)
    * void setCascadeIcon(const QIcon& icon)
    * void setCloseAllIcon(const QIcon& icon)
    * void setCloseIcon(const QIcon & icon)
    * void setDefaultIcon(const QIcon& icon)
    * void setTileIcon(const QIcon& icon)
    * void setWindowIcon(QWidget* widget, const QIcon& icon)

Public Slots

    * void addWindow(QWidget* w)
    * void addWindow(QWidget* widget, const QIcon& icon)
    * virtual void setEnabled(bool b)

'''

class MdiMainWindow(QtGui.QMainWindow):
    '''Base class for MDI applications.

    :attributes:

    - mdiarea
    . windowactions
    - windowmenu

    :signals:

    - subWindowClosed()     # @TODO: should this signal be emitted by mdiarea?

    '''

    # See /usr/share/doc/python-qt4-doc/examples/mainwindows/mdi/mdi.py

    def __init__(self, parent=None):
        super(MdiMainWindow, self).__init__(parent)

        self.mdiarea = QtGui.QMdiArea()
        self.setCentralWidget(self.mdiarea)
        self.mdiarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.connect(self.mdiarea,
                     QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                     self.updateWindowActions)
        self._windowmapper = QtCore.QSignalMapper(self)
        self.connect(self._windowmapper, QtCore.SIGNAL('mapped(QWidget*)'),
                     self.mdiarea.setActiveSubWindow)
                     #self.mdiarea, QtCore.SLOT('setActiveSubWindow(QWidget*)')

        self.windowactions = self._createWindowActions()
        self.updateWindowActions()
        self.windowmenu = self._createWindowMenu()

    #~ def closeEvent(self, event):
        #~ self.mdiarea.closeAllWindows()
        #~ if self.mdiarea.activeWindow():
            #~ event.ignore()
        #~ else:
            #~ self.writeSettings()
            #~ event.accept()

    def _createWindowActions(self):
        actionsgroup = QtGui.QActionGroup(self)

        action = QtGui.QAction(self.tr('Cl&ose'), actionsgroup)
        action.setObjectName('close')
        action.setShortcut(self.tr('Ctrl+W'))
        action.setStatusTip(self.tr('Close the active window'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.mdiarea.closeActiveSubWindow)

        action = QtGui.QAction(self.tr('Close &All'), actionsgroup)
        action.setObjectName('closeAll')
        action.setStatusTip(self.tr('Close all the windows'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.mdiarea.closeAllSubWindows)

        QtGui.QAction(actionsgroup).setSeparator(True)  # unnamed separator

        action = QtGui.QAction(self.tr('&Tile'), actionsgroup)
        action.setObjectName('tile')
        action.setStatusTip(self.tr('Tile the windows'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.mdiarea.tileSubWindows)

        action = QtGui.QAction(self.tr('&Cascade'), actionsgroup)
        action.setObjectName('cascade')
        action.setStatusTip(self.tr('Cascade the windows'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.mdiarea.cascadeSubWindows)

        QtGui.QAction(actionsgroup).setSeparator(True)  # unnamed separator

        action = QtGui.QAction(self.tr('Ne&xt'), actionsgroup)
        action.setObjectName('next')
        action.setShortcut(self.tr('Ctrl+F6'))
        action.setStatusTip(self.tr('Move the focus to the next window'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.mdiarea.activateNextSubWindow)

        action = QtGui.QAction(self.tr('Pre&vious'), actionsgroup)
        action.setObjectName('previous')
        action.setShortcut(self.tr('Ctrl+Shift+F6'))
        action.setStatusTip(self.tr('Move the focus to the previous window'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.mdiarea.activatePreviousSubWindow)

        action = QtGui.QAction(actionsgroup)
        action.setObjectName('separator')
        action.setSeparator(True)

        return actionsgroup

    def updateWindowActions(self):
        hasMdiChild = self.mdiarea.activeSubWindow() is not None
        for action in self.windowactions.actions():
            action.setEnabled(hasMdiChild)

    def _createWindowMenu(self):
        menu = QtGui.QMenu(self.tr('&Window'), self.menuBar())
        self.connect(menu, QtCore.SIGNAL('aboutToShow()'),
                     self.updateWindowMenu)
        return menu

    def updateWindowMenu(self):
        self.windowmenu.clear()
        for action in self.windowactions.actions():
            self.windowmenu.addAction(action)

        windows = self.mdiarea.subWindowList()

        separator = self.windowactions.findChild(QtGui.QAction, 'separator')
        separator.setVisible(len(windows) != 0)

        for index, child in enumerate(windows):
            title = str(child.windowTitle())
            if title.endswith('[*]'):
                title = title[:-3]
            if index < 9:
                text = self.tr('&%1 %2').arg(index + 1).arg(title)
            else:
                text = self.tr('%1 %2').arg(index + 1).arg(title)

            action = self.windowmenu.addAction(text)
            action.setCheckable(True)
            action.setChecked(child == self.mdiarea.activeSubWindow())
            self.connect(action, QtCore.SIGNAL('triggered()'),
                         self._windowmapper, QtCore.SLOT('map()'))
            self._windowmapper.setMapping(action, child)

    #~ def findMdiChild(self, fileName):
        #~ canonicalFilePath = QtCore.QFileInfo(fileName).canonicalFilePath()

        #~ for window in self.mdiarea.windowList():
            #~ if window.currentFile() == canonicalFilePath:
                #~ return window
        #~ return None

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
        self.treeview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self.treeview,
                     QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'),
                     self.itemContextMenu)
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
                self.newAct = QtGui.QAction(QtGui.QIcon(":/images/new.png"),
                                    self.tr("&New"), self)
                self.newAct.setShortcut(self.tr("Ctrl+N"))
                self.newAct.setStatusTip(self.tr("Create a new file"))
                self.connect(self.newAct, QtCore.SIGNAL("triggered()"),
                             self.newFile)

                self.openAct = QtGui.QAction(QtGui.QIcon(":/images/open.png"),
                                self.tr("&Open..."), self)
                self.openAct.setShortcut(self.tr("Ctrl+O"))
                self.openAct.setStatusTip(self.tr("Open an existing file"))
                self.connect(self.openAct, QtCore.SIGNAL("triggered()"),
                             self.open)

                self.saveAct = QtGui.QAction(QtGui.QIcon(":/images/save.png"),
                                self.tr("&Save"), self)
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

                self.cutAct = QtGui.QAction(QtGui.QIcon(":/images/cut.png"),
                                self.tr("Cu&t"), self)
                self.cutAct.setShortcut(self.tr("Ctrl+X"))
                self.cutAct.setStatusTip(self.tr("Cut the current selection's "
                                                 "contents to the clipboard"))
                self.connect(self.cutAct, QtCore.SIGNAL("triggered()"), self.cut)

                self.copyAct = QtGui.QAction(QtGui.QIcon(":/images/copy.png"),
                                self.tr("&Copy"), self)
                self.copyAct.setShortcut(self.tr("Ctrl+C"))
                self.copyAct.setStatusTip(self.tr("Copy the current selection's "
                                                  "contents to the clipboard"))
                self.connect(self.copyAct, QtCore.SIGNAL("triggered()"),
                             self.copy)

                self.pasteAct = QtGui.QAction(QtGui.QIcon(":/images/paste.png"),
                                self.tr("&Paste"), self)
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

        app = QtGui.QApplication(sys.argv)
        mainwindow = TestMdiMainWindow()
        mainwindow.show()
        sys.exit(app.exec_())
    ### Test MdiMainWindow END ################################################


    test_mdimainwin()
