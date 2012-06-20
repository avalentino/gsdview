#!/usr/bin/env python
# -*- coding: utf-8 -*-

### Copyright (C) 2006-2012 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of exectools.

### This module is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### This module is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with this module; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA.

'''Simple interactive shell implementation using exectools and Qt4.'''


import time
import logging

try:
    from qt import QtCore, QtGui
except ImportError:
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
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot


import exectools
from exectools.qt4 import (Qt4OutputPlane, Qt4OutputHandler, Qt4ToolController,
                           Qt4DialogLoggingHandler, Qt4LoggingHandler)


__author__ = 'Antonio Valentino <antonio.valentino@tiscali.it>'
__date__ = '$Date: 2006/03/11 23:18:40 $'
__version__ = '$Revision: 1.15 $'


class Qt4Shell(QtGui.QMainWindow):
    '''Qt4 interactive shell using tool controller.

    :SLOTS:

        * :meth:`execute`

    '''

    historyfile = 'history.txt'

    def __init__(self, debug=False):
        QtGui.QMainWindow.__init__(self)

        ### Command box ###
        self.cmdbox = QtGui.QComboBox()
        self.cmdbox.setEditable(True)
        self.cmdbox.addItem('')
        self.cmdbox.setCurrentIndex(self.cmdbox.count() - 1)
        # @TODO: complete
        #self.entry.populate_popup.connect(self.on_populate_popup)

        self.cmdbutton = QtGui.QPushButton('Run')
        self.cmdbutton.clicked.connect(self.execute)

        lineedit = self.cmdbox.lineEdit()
        lineedit.returnPressed.connect(self.cmdbutton.clicked[''])

        hLayout = QtGui.QHBoxLayout()
        hLayout.addWidget(QtGui.QLabel('cmd > '))
        hLayout.addWidget(self.cmdbox, 1)
        hLayout.addWidget(self.cmdbutton)

        ### Output plane ###
        outputplane = Qt4OutputPlane()
        outputplane.setReadOnly(True)
        outputplane.actions.removeAction(outputplane.actionHide)
        vLayout = QtGui.QVBoxLayout()
        vLayout.addLayout(hLayout)
        vLayout.addWidget(outputplane)

        ### Main window ###
        centralWidget = QtGui.QWidget()
        centralWidget.setLayout(vLayout)
        self.setCentralWidget(centralWidget)

        # @TODO: complete
        #~ accelgroup = gtk.AccelGroup()
        #~ accelgroup.connect_group(ord('d'), gtk.gdk.CONTROL_MASK,
                                 #~ gtk.ACCEL_VISIBLE, self.quit)

        self.setWindowTitle('Qt4 Shell')
        self.setGeometry(0, 0, 800, 600)
        #~ self.mainwin.add_accel_group(accelgroup)
        #~ self.mainwin.destroy.connect(self.quit)

        ### Setup the log system ###
        if debug:
            level = logging.DEBUG
            logging.basicConfig(level=level)
        else:
            level = logging.INFO

        self.logger = logging.getLogger()

        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler = Qt4LoggingHandler(outputplane)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        formatter = logging.Formatter('%(message)s')
        handler = Qt4DialogLoggingHandler(parent=self, dialog=None)
        handler.setLevel(logging.WARNING)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.logger.setLevel(level)

        ### Setup high level components and initialize the parent classes ###
        handler = Qt4OutputHandler(self.logger, self.statusBar())
        self.tool = exectools.ToolDescriptor('', stdout_handler=handler)
        self.controller = Qt4ToolController(self.logger, parent=self)
        self.controller.finished.connect(lambda returncode: self.reset())

        ###
        #self.shell = True
        self._state = 'ready'   # or maybe __state

        self.logger.debug('qt4shell session started at %s.' % time.asctime())
        self.load_history()

    def closeEvent(self, event):
        try:
            self.save_history()
        finally:
            self.logger.debug('qt4shell session stopped at %s.' %
                                                                time.asctime())
        event.accept()  # @TODO: check

    def load_history(self):
        self.cmdbox.clear()
        try:
            for cmd in open(self.historyfile, 'rU'):
                self.cmdbox.addItem(cmd.rstrip())

            self.logger.debug('history file "%s" loaded.' % self.historyfile)
        except (OSError, IOError) as e:
            self.logger.debug('unable to read the history file "%s": %s.' %
                                                        (self.historyfile, e))
        self.cmdbox.addItem('')
        self.cmdbox.setCurrentIndex(self.cmdbox.count() - 1)

    def save_history(self):
        try:
            history = [str(self.cmdbox.itemText(index))
                                    for index in range(self.cmdbox.count())]
            history = '\n'.join(history)
            f = open(self.historyfile, 'w')
            f.write(history)
            f.close()
            self.logger.debug('history saved in %s' % self.historyfile)
        except (OSError, IOError) as e:
            self.logger.warning('unable to save the history file "%s": %s' %
                                                        (self.historyfile, e))

    def _reset(self):
        self.controller.reset()
        # @TOD: use icons here
        self.cmdbutton.setText('Run')
        self.cmdbox.setEnabled(True)
        try:
            self.cmdbutton.clicked.disconnect(self.controller.stop_tool)
        except TypeError:
            # signal already disconnected
            pass
        else:
            self.cmdbutton.clicked.connect(self.execute)

    def reset(self):
        self.state = 'ready'

    def _get_state(self):
        return self._state

    def _set_state(self, state):
        if(state == 'ready'):
            self._reset()
            self.statusBar().showMessage('Ready')  # , 2000) # ms
            self.cmdbox.setFocus()
        elif(state == 'running'):
            self.cmdbox.setEnabled(False)
            self.cmdbutton.setText('Stop')
            self.cmdbutton.clicked.disconnect(self.execute)
            self.cmdbutton.clicked.connect(self.controller.stop_tool)
            self.statusBar().showMessage('Running ...')  # , 2000) # ms
        else:
            raise ValueError('invalid status: "%s".' % state)
        self._state = state

    state = property(_get_state, _set_state)

    def get_command(self):
        cmd = str(self.cmdbox.currentText())
        if cmd:
            count = self.cmdbox.count()
            if self.cmdbox.currentIndex() != count - 1:
                self.cmdbox.insertItem(count - 1, cmd)
            else:
                self.cmdbox.removeItem(count - 2)
                self.cmdbox.addItem('')
            self.cmdbox.setCurrentIndex(self.cmdbox.count() - 1)
        return cmd

    @QtCore.Slot()
    def execute(self):
        '''Execute the command line using the tool controller.

        :C++ signature: `void execute()`

        '''

        cmd = self.get_command()
        if cmd:
            self.state = 'running'
            try:
                self.controller.run_tool(self.tool, cmd)
                #~ raise RuntimeError('simulated runtime error')
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                self.logger.exception(e)
                self.reset()

    #~ def on_cmdbutton_clicked(self, widget=None, data=None):
        #~ if self.state == 'ready':
            #~ self.execute()
        #~ elif self.state == 'running':
            #~ self.stop()

    #~ def on_entry_activate(self, widget=None, data=None):
        #~ if self.state == 'running':
            #~ return
        #~ self.execute()

    # @TODO: complete
    #~ def on_populate_popup(self, widget, menu, data=None):
        #~ # separator
        #~ item = gtk.SeparatorMenuItem()
        #~ item.show()
        #~ menu.append(item)

        #~ # Clear history
        #~ item = gtk.ImageMenuItem(gtk.STOCK_CLEAR)
        #~ item.set_name('clear_history')
        #~ item.activate.connect(self.on_clear_history)
        #~ item.activate.connect(self.on_clear_entry)
        #~ item.show()
        #~ menu.append(item)

    #~ def on_clear_history(self):
        #~ self.cmdbox.clear()

    #~ def on_clear_entry(self):
        #~ self.cmdbox.clearEdirText()

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    mainwin = Qt4Shell(debug=True)
    mainwin.show()
    sys.exit(app.exec_())
