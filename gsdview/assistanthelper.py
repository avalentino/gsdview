# -*- coding: utf-8 -*-

### Copyright (C) 2008-2014 Antonio Valentino <a_valentino@users.sf.net>

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


'''Qt Assistant helper.'''


import sys

from qt import QtCore, QtGui


class Assistant(object):
    '''Helper class controllig an external QAssistant proces.'''

    # @TODO: fix
    APP_DOC_PATH = "qthelp://com.trolltech.examples.simpletextviewer/doc/"

    def __init__(self):
        super(Assistant, self).__init__(self)

        #: external process controller (QProcess)
        self.proc = None

    def close(self):
        if self.proc and self.proc.state() == QtCore.QProcess.Running:
            self.proc.terminate()
            self.proc.waitForFinished(3000)
        self.proc = None

    def showDocumentation(self, page):
        if not self.startAssistant():
            return

        ba = QtCore.QByteArray("SetSource ")
        ba.append(self.APP_DOC_PATH)

        self.proc.write(ba + page + '\0')

    def startAssistant(self):
        if not self.proc:
            self.proc = QtCore.QProcess()

        if self.proc.state() != QtCore.QProcess.Running:
            app = QtCore.QLibraryInfo.location(
                QtCore.QLibraryInfo.BinariesPath)
            app += QtCore.QDir.separator()
            if sys.platform == 'darwin':
                app += QtCore.QLatin1String(
                    'Assistant.app/Contents/MacOS/Assistant')
            else:
                app += QtCore.QLatin1String('assistant')

            args = [
                QtCore.QLatin1String('-collectionFile'),
                QtCore.QLatin1String('path to .qhc'),
                QtCore.QLatin1String('-enableRemoteControl'),
            ]

            self.proc.start(app, args)

            if not self.proc.waitForStarted():
                if QtGui.aApp is not None:
                    tr = QtGui.qApp.tr
                else:
                    tr = str
                QtGui.QMessageBox.critical(
                    0, tr('Simple Text Viewer'),
                    tr('Unable to launch Qt Assistant (%s)') % app)
                return False

        return True
