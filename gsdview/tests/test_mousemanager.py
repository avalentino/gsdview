#!/usr/bin/env python

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                                os.pardir, os.pardir)))

from PyQt4 import QtCore, QtGui

from gsdview.mousemanager import MouseManager


class MainWin(QtGui.QMainWindow):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget):
        QtGui.QMainWindow.__init__(self, parent, flags)

        self.mousemanager = MouseManager(self)

        self.scene = QtGui.QGraphicsScene(self)
        self.graphicsview = QtGui.QGraphicsView(self.scene, self)
        self.setCentralWidget(self.graphicsview)

        self.mousemanager.register(self.graphicsview)

        # File Actions
        self.fileactions = self._setupFileActions()

        menu = QtGui.QMenu('File', self)
        menu.addActions(self.fileactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('File', self)
        toolbar.addActions(self.fileactions.actions())
        self.addToolBar(toolbar)

        # Mouse Actions
        menu = QtGui.QMenu('Mouse')
        menu.addActions(self.mousemanager.actions.actions())
        self.menuBar().addMenu(menu)
        
        toolbar = QtGui.QToolBar('Mouse')
        toolbar.addActions(self.mousemanager.actions.actions())
        self.addToolBar(toolbar)

        # Help action
        self.helpactions = self._setupHelsActions()

        menu = QtGui.QMenu('Help', self)
        menu.addActions(self.helpactions.actions())
        self.menuBar().addMenu(menu)

        toolbar = QtGui.QToolBar('Help', self)
        toolbar.addActions(self.helpactions.actions())
        self.addToolBar(toolbar)

        self.resize(700, 500)

    def _setupFileActions(self):
        style = self.style()

        actions = QtGui.QActionGroup(self)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogOpenButton)
        action = QtGui.QAction(icon, 'Open', actions)
        self.connect(action, QtCore.SIGNAL('triggered()'), self.openfile)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogCloseButton)
        action = QtGui.QAction(icon, 'Close', actions)
        self.connect(action, QtCore.SIGNAL('triggered()'), self.scene.clear)

        QtGui.QAction(actions).setSeparator(True)

        icon = style.standardIcon(QtGui.QStyle.SP_DialogCancelButton)
        action = QtGui.QAction(icon, 'Exit', actions)
        self.connect(action, QtCore.SIGNAL('triggered()'), self.close)

        return actions

    def _setupHelsActions(self):
        style = self.style()

        actions = QtGui.QActionGroup(self)

        icon = QtGui.QIcon(':/trolltech/styles/commonstyle/images/fileinfo-32.png')
        action = QtGui.QAction(icon, 'About', actions)
        self.connect(action, QtCore.SIGNAL('triggered()'), self.about)

        icon = QtGui.QIcon(':/trolltech/qmessagebox/images/qtlogo-64.png')
        action = QtGui.QAction(icon, 'About Qt', actions)
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     QtGui.QApplication.aboutQt)

        return actions

    def openfile(self):
        self.scene.clear()
        self.graphicsview.setMatrix(QtGui.QMatrix())
        filename = QtGui.QFileDialog.getOpenFileName()
        if filename:
            pixmap = QtGui.QPixmap(filename)
            item = self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(item.boundingRect())

    def about(self):
        title = self.tr('MouseManager Example')
        text = ['<h1>Mouse Manager</h1>'
                '<p>Example program for the Mouse manager component.</p>',
                '<p>Copyright (C): 2009 '
                '<a href="mailto:a_valentino@users.sf.net">'
                    'Antonio Valentino'
                '<a>.</p>']
        text = self.tr('\n'.join(text))
        QtGui.QMessageBox.about(self, title, text)


def test_mousemanager():
    import sys
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('MouseManager')
    mainwin = MainWin()
    mainwin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    test_mousemanager()
