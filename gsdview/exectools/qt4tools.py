### Copyright (C) 2006-2009 Antonio Valentino <a_valentino@users.sf.net>

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

'''Tools for running external processes in a QT4 GUI.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__revision__ = '$Revision$'
__date__     = '$Date$'

import re
import time
import logging

from PyQt4 import QtCore, QtGui

from exectools import BaseOStream, BaseOutputHandler, BaseToolController, EX_OK

import resources

class Qt4Blinker(QtGui.QLabel):
    def __init__(self, filename=None):
        QtGui.QLabel.__init__(self)
        if not filename:
            filename = ':/images/red-circle.svg'
        pixmap = QtGui.QPixmap()
        pixmap.load(filename)
        self.setPixmap(pixmap)

    def pulse(self):
        '''A blinker pulse'''

        sensitive = self.isEnabled()
        sensitive = not sensitive
        self.setEnabled(sensitive)

    def flush(self):
        #QtGui.qApp.processEvents() # @TODO: check
        pass

    def reset(self):
        self.setEnabled(True)


class Qt4OStream(BaseOStream):
    '''Qt4 Output Stream'''

    def __init__(self, textview=None):
        super(Qt4OStream, self).__init__(textview)
        if textview is None:
            textview = QtGui.QTextEdit()
        self.textview = textview

        # @TODO: improve formats handling add/remove/list/edit
        self._formats = self._setupFormats()

    def _setupFormats(self):
        '''Setup a different format for the different message types.'''

        fmap = {}

        fmt = QtGui.QTextCharFormat()
        fmt.setForeground(QtGui.QColor('red'))
        fmap['error'] = fmt

        fmt = QtGui.QTextCharFormat()
        fmt.setForeground(QtGui.QColor('orange'))
        fmap['warning'] = fmt

        fmt = QtGui.QTextCharFormat()
        fmt.setForeground(QtGui.QColor('blue'))
        fmap['info'] = fmt

        fmt = QtGui.QTextCharFormat()
        fmt.setForeground(QtGui.QColor('gray'))
        fmap['debug'] = fmt

        fmt = QtGui.QTextCharFormat()
        fmt.setFontWeight(QtGui.QFont.Bold)
        fmap['cmd'] = fmt

        return fmap

    def flush(self):
        #QtGui.qApp.processEvents()     # @TODO: check
        pass

    def write(self, data, format=None):
        '''Write data on the output stream'''

        data = self._fixencoding(data)

        if isinstance(format, basestring):
            format = self._formats.get(format, '')

        if format:
            oldFormat = self.textview.currentCharFormat()
            self.textview.setCurrentCharFormat(format)
            self.textview.insertPlainText(data)
            self.textview.setCurrentCharFormat(oldFormat)
        else:
            self.textview.insertPlainText(data)
        self.textview.ensureCursorVisible()


class Qt4OutputPlane(QtGui.QTextEdit):

    def __init__(self, *args):
        QtGui.QTextEdit.__init__(self, *args)
        self._setupActions()
        self.banner = None

    def _setupActions(self):
        # Setup actions
        self.actions = QtGui.QActionGroup(self)

        # Save As
        self.actionSaveAs = QtGui.QAction(QtGui.QIcon(':/images/save-as.svg'),
                                          self.tr('&Save As'), self)
        self.actionSaveAs.setShortcut(self.tr('Ctrl+S'))
        self.actionSaveAs.setStatusTip(self.tr('Save text to file'))
        self.connect(self.actionSaveAs, QtCore.SIGNAL('triggered()'),
                     self.save)
        self.actions.addAction(self.actionSaveAs)

        # Clear
        self.actionClear = QtGui.QAction(QtGui.QIcon(':/images/clear.svg'),
                                         self.tr('&Clear'), self)
        self.actionClear.setShortcut(self.tr('Shift+F5'));
        self.actionClear.setStatusTip(self.tr('Clear the text'))
        self.connect(self.actionClear, QtCore.SIGNAL('triggered()'),
                     self.clear)
        self.actions.addAction(self.actionClear)

        # Close
        self.actionHide = QtGui.QAction(QtGui.QIcon(':/images/close.svg'),
                                        self.tr('&Hide'), self)
        self.actionHide.setShortcut(self.tr('Ctrl+W'))
        self.actionHide.setStatusTip(self.tr('Hide the text plane'))
        self.connect(self.actionHide, QtCore.SIGNAL('triggered()'),
                     self.planeHideRequest)
        self.actions.addAction(self.actionHide)

    def contextMenuEvent(self, event):
        menu = QtGui.QTextEdit.createStandardContextMenu(self)
        menu.addSeparator()

        for action in self.actions.actions():
            menu.addAction(action)

        menu.exec_(event.globalPos())

    def _report(self):
        if callable(self.banner):
            header = self.banner()
        elif self.banner is not None:
            header = self.banner
        else:
            header = '# Output log generated on %s' % time.asctime()
        text = self.toPlainText()
        return '%s\n\n%s' % (header, text)

    # def clear(self): # it is a standard QtGui.QTextEdit method

    def save(self):
        '''Save a file'''

        filter_ = self.tr('Text files (*.txt)')
        filename = QtGui.QFileDialog.getSaveFileName(self, QtCore.QString(),
                                                     QtCore.QString(), filter_)
        if filename:
            text = self._report()
            logfile = open(filename, 'w')
            logfile.write(text)
            logfile.close()

    def planeHideRequest(self):
        self.emit(QtCore.SIGNAL('planeHideRequest()'))


class Qt4OutputHandler(BaseOutputHandler):
    '''Qt4 Output Handler'''

    _statusbar_timeout = 2000 # ms

    def __init__(self, textview=None, statusbar=None, progressbar=None,
                 blinker=None):
        if textview:
            stream = Qt4OStream(textview)
        else:
            stream = None

        BaseOutputHandler.__init__(self, stream)

        self.statusbar = statusbar

        if self.statusbar:
            if blinker is None:
                blinker = Qt4Blinker()
                statusbar.addPermanentWidget(blinker)
                blinker.hide()
            self.blinker = blinker

            if progressbar is None:
                progressbar = QtGui.QProgressBar(self.statusbar)
                progressbar.setTextVisible(True)
                statusbar.addPermanentWidget(progressbar) #, 1) # stretch = 1
                progressbar.hide()
            self.progressbar = progressbar
        else:
            self.progressbar = None
            self.blinker = None

    def feed(self, data):
        '''Feed some data to the parser

        It is processed insofar as it consists of complete elements;
        incomplete data is buffered until more data is fed or close()
        is called.

        '''

        if self.blinker:
            self.blinker.show()
        super(Qt4OutputHandler, self).feed(data)

    def close(self):
        '''Reset the instance'''

        if self.statusbar:
            self.statusbar.clearMessage()
        super(Qt4OutputHandler, self).close()

    def reset(self):
        '''Reset the handler instance

        Loses all unprocessed data. This is called implicitly at
        instantiation time.

        '''

        super(Qt4OutputHandler, self).reset()
        if self.progressbar:
            self.progressbar.setRange(0, 100)
            self.progressbar.reset()
            self.progressbar.hide()
        if self.blinker:
            self.blinker.reset()
            self.blinker.hide()

    def _handle_pulse(self, data=None):
        '''Handle a blinker pulse'''

        if self.blinker:
            if not self.blinker.isVisible():
                self.blinker.show()
            else:
                self.blinker.pulse()

    def _handle_percentage(self, data):
        '''Handle percentage of a precess execution

        :Parameters:

        - 'data' : percentage

        '''

        if self.progressbar:
            self.progressbar.show() # @TODO: check
            self.progressbar.setValue(data)

    def handle_progress(self, data):
        '''Handle progress data

        :Parameters:

        - `data`: a list containing an item for each named group in the
          "progress" regular expression: (pulse, percentage, text) for
          the default implementation.  Each item can be None.

        '''

        pulse, percentage, text = data
        if pulse:
            self._handle_pulse(pulse)
        if percentage is not None:
            self._handle_percentage(percentage)
        if text and not pulse and percentage is None:
            if self.statusbar:
                self.statusbar.showMessage(text, self._statusbar_timeout)
            self._handle_pulse()
        QtGui.qApp.processEvents() # might slow too mutch


class Qt4StreamLoggingHandler(logging.StreamHandler):
    '''Qt4 handler for the logging stream'''

    # @TODO: move to a bese class
    level2tag = {
        logging.CRITICAL: 'error',
        # FATAL = CRITICAL
        logging.ERROR: 'error',
        logging.WARNING: 'warning',
        # WARN = WARNING
        logging.INFO: 'info',
        logging.DEBUG: 'debug',
        logging.NOTSET: '',
    }

    def __init__(self, stream=None):
        if stream is None:
            stream = Qt4OStream()

        if isinstance(stream, QtGui.QTextEdit):
            stream = Qt4OStream(stream)

        assert isinstance(stream, Qt4OStream)
        logging.StreamHandler.__init__(self, stream)

    # @TODO: move to a bese class
    def emit(self, record):
        # @TODO: docstring

        try:
            msg = self.format(record)
            tag = self.level2tag.get(record.levelno, '')
            self.stream.write('%s\n' % msg, tag)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

class Qt4DialogLoggingHandler(logging.Handler):
    '''Qt4 handler for the logging dialog'''

    levelsmap = {
        logging.CRITICAL: QtGui.QMessageBox.Critical,
        # FATAL = CRITICAL
        logging.ERROR: QtGui.QMessageBox.Critical,
        logging.WARNING: QtGui.QMessageBox.Warning,
        # WARN = WARNING
        logging.INFO: QtGui.QMessageBox.Information,
        logging.DEBUG: QtGui.QMessageBox.Information,
        logging.NOTSET: QtGui.QMessageBox.Information,
    }

    def __init__(self, dialog=None, parent=None):
        logging.Handler.__init__(self)
        if dialog is None:
            # @TODO: check
            #~ if parent is None:
                #~ parent = QtGui.qApp.mainWidget()

            dialog = QtGui.QMessageBox(parent)
            dialog.addButton(QtGui.QMessageBox.Close)
            # @TODO: set dialog title
            dialog.setTextFormat(QtCore.Qt.AutoText)
        self.dialog = dialog
        self.formatter = None

    def emit(self, record):
        try:
            if self.dialog.isVisible():
                raise RuntimeError('trying to show again a dialog that is '
                                   'already visible.')

            msgtype = self.levelsmap[record.levelno]
            self.dialog.setIcon(msgtype)

            level = logging.getLevelName(record.levelno)
            level = level.upper()
            self.dialog.setWindowTitle(level)
            msg = ['<h1>%s</h1>' % level]
            if record.exc_info:
                msg.append('<p><b>%s<b></p><br>' %
                                        record.getMessage().capitalize())
                # @TODO: background-color="white"
                msg.append('<pre>%s</pre>' % self.format(record))
            else:
                msg.append('<p>%s</p>' % self.format(record).capitalize())

            msg = '\n'.join(msg)
            msg = msg.encode('UTF-8', 'replace') # @TODO: check

            self.dialog.setText(msg)
            self.dialog.exec_()
            self.dialog.hide()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class Qt4ToolController(QtCore.QObject, BaseToolController):
    '''Qt4 tool controller

    :signals:

    * externalToolStarted()
    * failedToStart(PyQt_PyObject tooldescriptor)
    * finished(PyQt_PyObject tooldescriptor, int exitCode)
    * planeHideRequest()

    '''

    _delay_after_stop = 200    #ms

    def __init__(self, logger=None, parent=None):
        QtCore.QObject.__init__(self, parent)
        BaseToolController.__init__(self, logger)
        # @TODO: check
        # It is important the subprocess has a parent
        #~ if not parent:
            #~ # @TODO: fix
            #~ parent = self.stdout_handler.stream.textview.topLevelWidget() # exists?
            #~ #parent = QtGui.qApp.topLevelWidgets()[0]
        self.subprocess = QtCore.QProcess(parent)
        self.subprocess.setProcessChannelMode(QtCore.QProcess.MergedChannels)

        # connect process handlers and I/O handlers
        QtCore.QObject.connect(
                        self.subprocess,
                        QtCore.SIGNAL('readyReadStandardOutput()'),
                        self.handle_stdout)
        QtCore.QObject.connect(
                        self.subprocess,
                        QtCore.SIGNAL('readyReadStandardError()'),
                        self.handle_stderr)
        QtCore.QObject.connect(
                        self.subprocess,
                        QtCore.SIGNAL('error(QProcess::ProcessError)'),
                        self.handle_error)
        QtCore.QObject.connect(
                        self.subprocess,
                        QtCore.SIGNAL('finished(int, QProcess::ExitStatus)'),
                        self.finalize_run)
        # @TODO: remove
        QtCore.QObject.connect(
                        self.subprocess,
                        QtCore.SIGNAL('error()'),
                        self.handle_error)

    def finalize_run(self, exitCode=None, exitStatus=None):
        '''Perform finalization actions

        This method is called when the controlled process terminates
        to perform finalization actions like:

        * read and handle residual data in buffers,
        * flush and close output handlers,
        * close subprocess file descriptors
        * run the "finalize_run_hook" method
        * reset the controller instance

        If one just needs to perfor some additional finalization action
        it should be better to use a custom "finalize_run_hook" instead
        of overriging "finalize_run".

        '''

        try:
            # retrieve residual data
            # @TODO: check id it is actualli needed
            if self.tool.stdout_handler:
                byteArray = self.subprocess.readAllStandardOutput()
                self.tool.stdout_handler.feed(byteArray.data())
            if self.tool.stderr_handler:
                byteArray = self.subprocess.readAllStandardError()
                self.tool.stderr_handler.feed(byteArray.data())

            # close the pipe and wait for the subprocess termination
            self.subprocess.close()
            if self.tool.stdout_handler:
                self.tool.stdout_handler.close()
            if self.tool.stderr_handler:
                self.tool.stderr_handler.close()

            if exitCode != EX_OK:
                if self._stopped:
                    self.logger.info('Execution stopped by the user.')
                else:
                    msg = ('Process (PID=%d) exited with return code %d.' %
                                           (self.subprocess.pid(),
                                            self.subprocess.exitCode()))
                    self.logger.warning(msg)

            # Call finalize hook is available
            self.finalize_run_hook()
        finally:
            # @TODO: check
            # Protect for unexpected errors in the feed and close methods of
            # the stdout_handler
            self.reset_controller()
            self.emit(QtCore.SIGNAL('finished()'))

    def reset_controller(self):
        if self.subprocess.state() != self.subprocess.NotRunning:
            self._stop(force=True)
            self.subprocess.waitForFinished()
            stopped = self.subprocess.state() == self.subprocess.NotRunning
            if not stopped:
                self.logger.warning('reset on running process')

        assert self.subprocess.state() == self.subprocess.NotRunning, \
                                                'the process is still running'
        self.subprocess.setProcessState(self.subprocess.NotRunning)

        if self.tool.stdout_handler:
            self.tool.stdout_handler.reset()
        if self.tool.stderr_handler:
            self.tool.stderr_handler.reset()

        self._stopped = False

    def handle_stdout(self, *args):
        '''Handle standard output'''

        byteArray = self.subprocess.readAllStandardOutput()
        if not byteArray.isEmpty():
            self.tool.stdout_handler.feed(byteArray.data())

    def handle_stderr(self, *args):
        '''Handle standard error'''

        byteArray = self.subprocess.readAllStandardError()
        if not byteArray.isEmpty():
            self.tool.stderr_handler.feed(byteArray.data())

    def handle_error(self, error):
        '''Handle a error in process execution

        Can be handle different types of errors:

        * starting failed
        * crashing after starts successfully
        * timeout elapsed
        * write error
        * read error
        * unknow error

        '''

        level = logging.DEBUG
        if error == QtCore.QProcess.FailedToStart:
            msg = ('The process failed to start. Either the invoked program '
                   'is missing, or you may have insufficient permissions to '
                   'invoke the program.')
            level = logging.ERROR
            self.reset_controller()
        elif error == QtCore.QProcess.Crashed:
            msg = 'The process crashed some time after starting successfully.'
            level = logging.ERROR
            #~ self.finalize() # @TODO: check
        elif error == QtCore.QProcess.Timedout:
            msg = ('The last waitFor...() function timed out. The state of '
                   'QProcess is unchanged, and you can try calling '
                   'waitFor...() again.')
            level = logging.DEBUG
        elif error == QtCore.QProcess.WriteError:
            msg = ('An error occurred when attempting to write to the process. '
                   'For example, the process may not be running, or it may '
                   'have closed its input channel.')
            #level = logging.ERROR # @TODO: check
        elif error == QtCore.QProcess.ReadError:
            msg = ('An error occurred when attempting to read from the '
                   'process. For example, the process may not be running.')
            #level = logging.ERROR # @TODO: check
        elif error == QtCore.QProcess.UnknownError:
            msg = ('An unknown error occurred. This is the default return '
                   'value of error().')
            #level = logging.ERROR # @TODO: check

        self.logger.log(level, msg)
        self.emit(QtCore.SIGNAL('finished()'))

    def run_tool(self, *args):
        '''Run an external tool in controlled way

        The output of the child process is handled by the controller
        and, optionally, notifications can be achieved at sub-process
        termination.

        '''

        assert self.subprocess.state() == self.subprocess.NotRunning

        if self.tool.stdout_handler:
            self.tool.stdout_handler.reset()
        # @TODO: check
        #if self.tool.stderr_handler:
        #    self.tool.stderr_handler.reset()
        cmd = self.tool.cmdline(*args)
        self.prerun_hook(cmd)
        cmd = ' '.join(cmd)

        #self.subprocess.setEnvironmet(...)         # <-- self.tool.env
        #self.subprocess.setWorkingDirectory(...)   # <-- self.tool.cwd

        self.subprocess.start(cmd)
        self.subprocess.closeWriteChannel()

    def _stop(self, force=True):
        if self.subprocess.state() == self.subprocess.NotRunning:
            return
        self.subprocess.terminate()
        self.subprocess.waitForFinished(self._delay_after_stop)
        stopped = self.subprocess.state() == self.subprocess.NotRunning
        if not stopped and force:
            self.subprocess.kill()

    def stop_tool(self, force=True):
        '''Stop the execution of controlled subprocess

        When this method is invoked the controller instance is always
        reset even if the controller is unable to stop the subprocess.

        When possible the controller try to kill the subprocess in a
        polite way.  If this fails it also tryes brute killing by
        default (force=True).  This behaviour can be controlled using
        the `force` parameter.

        '''

        if self.subprocess.state() != self.subprocess.NotRunning:
            self.logger.debug('Execution stopped by the user.')
            self._stopped = True
            self._stop(force)
            self.subprocess.waitForFinished()
            stopped = self.subprocess.state() == self.subprocess.NotRunning
            if not stopped:
                msg = ('Unable to stop the sub-process (PID=%d).' %
                                                        self.subprocess.pid())
                self.logger.warning(msg)

        QtGui.qApp.processEvents()
        self.reset_controller()
