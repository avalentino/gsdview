# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2019 Antonio Valentino <antonio.valentino@tiscali.it>
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

"""Tools for running external processes in a Qt GUI."""


from __future__ import absolute_import

import time
import logging

from qtpy import QtCore, QtWidgets, QtGui

from exectools import (
    BaseOutputHandler, BaseToolController, EX_OK, level2tag, string_types,
    callable,
)


__all__ = ['QtBlinker', 'QtOutputPane', 'QtOutputHandler',
           'QtLoggingHandler', 'QtDialogLoggingHandler', 'QtToolController']


class QtBlinker(QtWidgets.QLabel):
    """Qt linker.

    :SLOTS:

        * :meth:`pulse`

    """

    def __init__(self, parent=None, flags=QtCore.Qt.WindowFlags(0), **kwargs):
        super(QtBlinker, self).__init__(parent, flags, **kwargs)
        #qstyle = QtWidgets.QApplication.style()
        #pixmap = qstyle.standardPixmap(QtWidgets.QStyle.SP_MediaStop)
        pixmap = QtGui.QPixmap(
            ':/trolltech/styles/commonstyle/images/standardbutton-no-32.png')
        self.setPixmap(pixmap)

    @QtCore.Slot()
    def pulse(self):
        """A blinker pulse.

        :C++ signature: `void pulse()`

        """

        sensitive = self.isEnabled()
        sensitive = not sensitive
        self.setEnabled(sensitive)

    def flush(self):
        #QtWidgets.qApp.processEvents() # @TODO: check
        pass

    def reset(self):
        """Reset the blinker."""

        self.setEnabled(True)


class QtOutputPane(QtWidgets.QTextEdit):

    #: SIGNAL: emits a hide request.
    #:
    #: :C++ signature: `void paneHideRequest()`
    paneHideRequest = QtCore.Signal()

    def __init__(self, parent=None, **kwargs):
        super(QtOutputPane, self).__init__(parent, **kwargs)
        self._setupActions()
        self.banner = None

    def _setupActions(self):
        qstype = QtWidgets.QApplication.style()

        # Setup actions
        self.actions = QtWidgets.QActionGroup(self)

        # Save As
        icon = qstype.standardIcon(QtWidgets.QStyle.SP_DialogSaveButton)
        self.actionSaveAs = QtWidgets.QAction(
            icon, self.tr('&Save As'), self,
            shortcut=self.tr('Ctrl+S'),
            statusTip=self.tr('Save text to file'),
            triggered=self.save)
        self.actions.addAction(self.actionSaveAs)

        # Clear
        icon = QtGui.QIcon(':/trolltech/styles/commonstyle/images/'
                           'standardbutton-clear-32.png')
        self.actionClear = QtWidgets.QAction(
            icon, self.tr('&Clear'), self,
            shortcut=self.tr('Shift+F5'),
            statusTip=self.tr('Clear the text'),
            triggered=self.clear)
        self.actions.addAction(self.actionClear)

        # Close
        icon = qstype.standardIcon(QtWidgets.QStyle.SP_DialogCloseButton)
        self.actionHide = QtWidgets.QAction(
            icon, self.tr('&Hide'), self,
            shortcut=self.tr('Ctrl+W'),
            statusTip=self.tr('Hide the text pane'),
            triggered=self.paneHideRequest)
        self.actions.addAction(self.actionHide)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QTextEdit.createStandardContextMenu(self)
        menu.addSeparator()
        menu.addActions(self.actions.actions())
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

    # def clear(self): # it is a standard QtWidgets.QTextEdit method

    def save(self):
        """Save a file."""

        filter_ = self.tr('Text files (*.txt)')
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '', '', filter_)
        if filename:
            text = self._report()
            logfile = open(filename, 'w')
            logfile.write(text)
            logfile.close()


class QtOutputHandler(QtCore.QObject, BaseOutputHandler):
    """Qt Output Handler.

    :SIGNALS:

        * :attr:`pulse`
        * :attr:`percentageChanged`

    """

    _statusbar_timeout = 2000  # ms

    #: SIGNAL: it is emitted to signal some kind of activity of the external
    #: process
    #:
    #: :param str text:
    #:     an optional text describing the kind activity of the external
    #:     process
    #:
    #: :C++ signature: `void pulse(QString)`
    pulse = QtCore.Signal([], [str])

    #: SIGNAL: it is emitted when the progress percentage changes
    #:
    #: :param float percentage:
    #:     the new completion percentage [0, 100]
    #:
    #: :C++ signature: `void percentageChanged(float)`
    percentageChanged = QtCore.Signal([int], [])

    def __init__(self, logger=None, statusbar=None, progressbar=None,
                 blinker=None, parent=None, **kwargs):
        QtCore.QObject.__init__(self, parent, **kwargs)
        BaseOutputHandler.__init__(self, logger)

        self.statusbar = statusbar
        if self.statusbar:
            if blinker is None:
                blinker = QtBlinker()
                statusbar.addPermanentWidget(blinker)
                blinker.hide()
            self.pulse.connect(blinker.show)
            self.pulse.connect(blinker.pulse)
            self.pulse[str].connect(
                lambda text: statusbar.showMessage(
                    text, self._statusbar_timeout))

            if progressbar is None:
                progressbar = QtWidgets.QProgressBar(self.statusbar)
                progressbar.setTextVisible(True)
                statusbar.addPermanentWidget(progressbar)  # , 1) # stretch=1
                progressbar.hide()
            self.progressbar = progressbar
            #self.percentageChanged[()].connect(progressbar.show)
            self.percentageChanged.connect(progressbar.show)
            self.percentageChanged.connect(progressbar.setValue)

        self.progressbar = progressbar
        self.blinker = blinker

    def feed(self, data):
        """Feed some data to the parser.

        It is processed insofar as it consists of complete elements;
        incomplete data is buffered until more data is fed or close()
        is called.

        """

        if self.blinker:
            self.blinker.show()
        super(QtOutputHandler, self).feed(data)

    def close(self):
        """Reset the instance."""

        if self.statusbar:
            self.statusbar.clearMessage()
        super(QtOutputHandler, self).close()

    def reset(self):
        """Reset the handler instance.

        Loses all unprocessed data. This is called implicitly at
        instantiation time.

        """

        super(QtOutputHandler, self).reset()
        if self.progressbar:
            self.progressbar.setRange(0, 100)
            self.progressbar.reset()
            self.progressbar.hide()
        if self.blinker:
            self.blinker.reset()
            self.blinker.hide()

    def handle_progress(self, data):
        """Handle progress data.

        :param data:
            a list containing an item for each named group in the
            "progress" regular expression: (pulse, percentage, text)
            for the default implementation.
            Each item can be None.

        """

        #pulse = data.get('pulse')
        percentage = data.get('percentage')
        text = data.get('text')

        self.pulse.emit()
        if text:
            self.pulse[str].emit(text)
        if percentage is not None:
            self.percentageChanged.emit(int(percentage))


class QtLoggingHandler(logging.Handler):
    """Custom handler for logging on Qt textviews."""

    def __init__(self, textview):
        logging.Handler.__init__(self)
        self.textview = textview
        self._formats = self._setupFormats()

    def _setupFormats(self):
        """Setup a different format for the different message types."""

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

    def _flush(self):
        QtWidgets.qApp.processEvents()

    def _write(self, data, format_=None):
        """Write data on the textview."""

        if isinstance(format_, string_types):
            format_ = self._formats.get(format_, '')

        if data and not data.endswith('\n'):
            data += '\n'

        if format_:
            oldFormat = self.textview.currentCharFormat()
            self.textview.setCurrentCharFormat(format_)
            self.textview.insertPlainText(data)
            self.textview.setCurrentCharFormat(oldFormat)
        else:
            self.textview.insertPlainText(data)
        self.textview.ensureCursorVisible()

    def emit(self, record):
        try:
            msg = self.format(record)
            tag = getattr(record, 'tag', level2tag(record.levelno))
            self._write('%s' % msg, tag)
            # @TODO: check
            #self._flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class QtDialogLoggingHandler(logging.Handler):
    """Qt handler for the logging dialog."""

    levelsmap = {
        logging.CRITICAL: QtWidgets.QMessageBox.Critical,
        # FATAL = CRITICAL
        logging.ERROR: QtWidgets.QMessageBox.Critical,
        logging.WARNING: QtWidgets.QMessageBox.Warning,
        # WARN = WARNING
        logging.INFO: QtWidgets.QMessageBox.Information,
        logging.DEBUG: QtWidgets.QMessageBox.Information,
        logging.NOTSET: QtWidgets.QMessageBox.Information,
    }

    def __init__(self, dialog=None, parent=None):
        logging.Handler.__init__(self)
        if dialog is None:
            # @TODO: check
            #~ if parent is None:
                #~ parent = QtWidgets.qApp.mainWidget()

            dialog = QtWidgets.QMessageBox(parent)
            dialog.addButton(QtWidgets.QMessageBox.Close)
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
                msg.append(
                    '<p><b>%s<b></p><br>' % record.getMessage().capitalize())
                # @TODO: background-color="white"
                msg.append('<pre>%s</pre>' % self.format(record))
            else:
                msg.append('<p>%s</p>' % self.format(record).capitalize())

            msg = '\n'.join(msg)

            self.dialog.setText(msg)
            self.dialog.exec_()
            self.dialog.hide()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class QtToolController(QtCore.QObject, BaseToolController):
    """Qt tool controller.

    :SIGNALS:

        * :attr:`finished`

    :SLOTS:

        * :meth:`stop_tool`
        * :meth:`finalize_run`
        * :meth:`handle_stdout`
        * :meth:`handle_stderr`
        * :meth:`handle_error`

    """

    _delay_after_stop = 200    # ms

    #: SIGNAL: it is emitted when the processing is finished.
    #:
    #: :param int exitcode:
    #:     the external proces exit code
    #:
    #: :C++ signature: `void finished(int exitCode)`
    finished = QtCore.Signal(int)

    def __init__(self, logger=None, parent=None, **kwargs):
        QtCore.QObject.__init__(self, parent, **kwargs)
        BaseToolController.__init__(self, logger)
        self.subprocess = QtCore.QProcess(parent)
        self.subprocess.setProcessChannelMode(QtCore.QProcess.MergedChannels)

        # connect process handlers and I/O handlers
        self.subprocess.readyReadStandardOutput.connect(self.handle_stdout)
        self.subprocess.readyReadStandardError.connect(self.handle_stderr)
        self.subprocess.error.connect(self.handle_error)
        self.subprocess.finished.connect(self.finalize_run)

    @property
    def isbusy(self):
        """If True then the controller is already running a subprocess."""

        return self.subprocess.state() != self.subprocess.NotRunning

    @QtCore.Slot(int, QtCore.QProcess.ExitStatus)
    def finalize_run(self, exitCode=None, exitStatus=None):
        """Perform finalization actions.

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

        :C++ signature: `finalize_run(int, QProcess::ExitStatus)`

        """

        if not self._tool:
            return

        out_encoding = self._tool.output_encoding

        try:
            # retrieve residual data
            # @TODO: check if it is actually needed
            if self._tool.stdout_handler:
                byteArray = self.subprocess.readAllStandardOutput()
                data = byteArray.data().decode(out_encoding)
                self._tool.stdout_handler.feed(data)
            if self._tool.stderr_handler:
                byteArray = self.subprocess.readAllStandardError()
                data = byteArray.data().decode(out_encoding)
                self._tool.stderr_handler.feed(data)

            # close the pipe and wait for the subprocess termination
            self.subprocess.close()
            if self._tool.stdout_handler:
                self._tool.stdout_handler.close()
            if self._tool.stderr_handler:
                self._tool.stderr_handler.close()

            if self._userstop:
                self.logger.info('Execution stopped by the user.')
            elif exitCode != EX_OK:
                msg = ('Process (PID=%d) exited with return code %d.' % (
                    self.subprocess.pid(), self.subprocess.exitCode()))
                self.logger.warning(msg)

            # Call finalize hook if available
            self.finalize_run_hook()
        finally:
            # @TODO: check
            # Protect for unexpected errors in the feed and close methods of
            # the stdout_handler
            self._reset()
            self.finished.emit(exitCode)

    def _reset(self):
        """Internal reset."""

        if self.subprocess.state() != self.subprocess.NotRunning:
            self._stop(force=True)
            self.subprocess.waitForFinished()
            stopped = self.subprocess.state() == self.subprocess.NotRunning
            if not stopped:
                self.logger.warning(
                    'reset running process (PID=%d)' % self.subprocess.pid())

        assert self.subprocess.state() == self.subprocess.NotRunning, \
            'the process is still running'
        self.subprocess.setProcessState(self.subprocess.NotRunning)
        # @TODO: check
        self.subprocess.closeReadChannel(QtCore.QProcess.StandardOutput)
        self.subprocess.closeReadChannel(QtCore.QProcess.StandardError)
        self.subprocess.closeWriteChannel()

        super(QtToolController, self)._reset()
        self.subprocess.close()

    @QtCore.Slot()
    def handle_stdout(self):
        """Handle standard output.

        :C++ signature: `void handle_stdout()`

        """

        byteArray = self.subprocess.readAllStandardOutput()
        if not byteArray.isEmpty():
            data = byteArray.data().decode(self._tool.output_encoding)
            self._tool.stdout_handler.feed(data)

    @QtCore.Slot()
    def handle_stderr(self):
        """Handle standard error.

        :C++ signature: `void handle_stderr()`

        """

        byteArray = self.subprocess.readAllStandardError()
        if not byteArray.isEmpty():
            data = byteArray.data().decode(self._tool.output_encoding)
            self._tool.stderr_handler.feed(data)

    @QtCore.Slot(QtCore.QProcess.ProcessError)
    def handle_error(self, error):
        """Handle a error in process execution.

        Can be handle different types of errors:

        * starting failed
        * crashing after starts successfully
        * timeout elapsed
        * write error
        * read error
        * unknow error

        :C++ signature: `void handle_error(QProcess::ProcessError)`

        """

        msg = ''
        level = logging.DEBUG
        if self.subprocess.state() == self.subprocess.NotRunning:
            logging.debug('NotRunning')
            exit_code = self.subprocess.exitCode()
        else:
            exit_code = 0

        if error == QtCore.QProcess.FailedToStart:
            msg = ('The process failed to start. Either the invoked program '
                   'is missing, or you may have insufficient permissions to '
                   'invoke the program.')
            level = logging.ERROR
            # @TODO: check
            #self._reset()
        elif error == QtCore.QProcess.Crashed:
            if not self._userstop and self.subprocess.exitCode() == EX_OK:
                msg = ('The process crashed some time after starting '
                       'successfully.')
                level = logging.ERROR
        elif error == QtCore.QProcess.Timedout:
            msg = ('The last waitFor...() function timed out. The state of '
                   'QProcess is unchanged, and you can try calling '
                   'waitFor...() again.')
            level = logging.DEBUG
        elif error == QtCore.QProcess.WriteError:
            msg = ('An error occurred when attempting to write to the process.'
                   ' For example, the process may not be running, or it may '
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

        if msg:
            self.logger.log(level, msg)

        self.finished.emit(exit_code)

    #QtCore.Slot() # @TODO: check how to handle varargs
    def run_tool(self, tool, *args, **kwargs):
        """Run an external tool in controlled way.

        The output of the child process is handled by the controller
        and, optionally, notifications can be achieved at sub-process
        termination.

        """

        assert self.subprocess.state() == self.subprocess.NotRunning
        self.reset()
        self._tool = tool

        if self._tool.stdout_handler:
            self._tool.stdout_handler.reset()
        if self._tool.stderr_handler:
            self._tool.stderr_handler.reset()

        cmd = self._tool.cmdline(*args, **kwargs)
        self.prerun_hook(cmd)
        cmd = ' '.join(cmd)

        if self._tool.env:
            qenv = QtCore.QProcessEnvironment()
            for key, val in self._tool.env.items():
                qenv.insert(key, str(val))
            self.subprocess.setProcessEnvironment(qenv)

        if self._tool.cwd:
            self.subprocess.setWorkingDirectory(self._tool.cwd)

        self.logger.debug('"shell" flag set to %s.' % self._tool.shell)
        self.logger.debug('Starting: %s' % cmd)
        self.subprocess.start(cmd)
        self.subprocess.closeWriteChannel()

    def _stop(self, force=True):
        if self.subprocess.state() == self.subprocess.NotRunning:
            return
        self.subprocess.terminate()
        self.subprocess.waitForFinished(self._delay_after_stop)
        stopped = self.subprocess.state() == self.subprocess.NotRunning
        if not stopped and force:
            self.logger.info(
                'Force process termination (PID=%d).' % self.subprocess.pid())
            self.subprocess.kill()

    @QtCore.Slot()
    @QtCore.Slot(bool)
    def stop_tool(self, force=True):
        """Stop the execution of controlled subprocess.

        When this method is invoked the controller instance is always
        reset even if the controller is unable to stop the subprocess.

        When possible the controller try to kill the subprocess in a
        polite way.  If this fails it also tryes brute killing by
        default (force=True).  This behaviour can be controlled using
        the `force` parameter.

        :C++ signature: `void stop_tool(bool)`

        """

        if self._userstop:
            return

        if self.subprocess.state() != self.subprocess.NotRunning:
            self.logger.debug('Execution stopped by the user.')
            self._userstop = True
            self._stop(force)
            self.subprocess.waitForFinished()
            stopped = self.subprocess.state() == self.subprocess.NotRunning
            if not stopped:
                msg = ('Unable to stop the sub-process (PID=%d).' %
                       self.subprocess.pid())
                self.logger.warning(msg)
