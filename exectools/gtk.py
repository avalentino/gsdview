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

"""Tools for running external processes in a GTK GUI."""


import os
import sys
import time
import logging

from gi.repository import Gtk, Pango, GObject, GLib

from exectools import subprocess2
from exectools import BaseOutputHandler, level2tag
from exectools.std import StdToolController


class Popen(GObject.GObject, subprocess2.Popen):

    _timeout = 100  # ms

    __gsignals__ = {
        'stdout-ready': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (),),
        'stderr-ready': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (),),
        'io-error': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (),),
        'connection-broken': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (),),
        'finished': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (),),
    }

    def __init__(self, *args, **kwargs):
        GObject.GObject.__init__(self)
        subprocess2.Popen.__init__(self, *args, **kwargs)
        self._watch_tags = []

        id_ = GLib.timeout_add(self._timeout, self._check_finished)
        self._watch_tags.append(id_)

        self._setup_io_watch()

    def _check_finished(self):
        if self.poll() is not None:
            self.emit('finished')
            return False
        return True

    def close(self):
        # @NOTE: don't close system stdout and stderr
        # if self.stdout:
        #     self.stdout.close()
        # if self.stderr:
        #     self.stderr.close()

        for tag in set(self._watch_tags):
            GLib.source_remove(tag)
        self._watch_tags.clear()

    if sys.platform[:3] == 'win':
        import errno
        import msvcrt
        from win32pipe import PeekNamedPipe

        def _setup_io_watch(self):
            # @TODO: signal.set_wakeup_fd from Python 2.6
            if self.stdout:
                id_ = GLib.timeout_add(self._timeout, self._check_ready,
                                       self.stdout)
                self._watch_tags.append(id_)
            if self.stderr:
                id_ = GLib.timeout_add(self._timeout, self._check_ready,
                                       self.stderr)
                self._watch_tags.append(id_)

        def _check_ready(self, conn, maxsize=1024):
            if maxsize < 1:
                maxsize = 1

            if conn is None:
                return

            try:
                x = msvcrt.get_osfhandle(conn.fileno())
                (read, nAvail, nMessage) = PeekNamedPipe(x, 0)
                if maxsize < nAvail:
                    nAvail = maxsize
                if nAvail > 0:
                    if conn is self.stdout:
                        self.emit('stdout-ready')
                    elif conn is self.stderr:
                        self.emit('stderr-ready')
            except ValueError:
                return conn.close()
            except (WindowsError, Exception) as ex:
                if ex[0] in (109, errno.ESHUTDOWN):
                    return conn.close()
                raise

            return True

    else:   # POSIX

        def _setup_io_watch(self):
            cond = (GObject.IO_IN | GObject.IO_PRI | GObject.IO_ERR |
                    GObject.IO_HUP)
            if self.stdout:
                id_ = GLib.io_add_watch(self.stdout, GLib.PRIORITY_DEFAULT,
                                        cond, self._io_callback)
                self._watch_tags.append(id_)
            if self.stderr:
                id_ = GObject.io_add_watch(self.stderr, cond,
                                           self._io_callback)
                self._watch_tags.append(id_)

        def _io_callback(self, source, condition):
            if condition in (GObject.IO_IN, GObject.IO_PRI):
                if source == self.stdout:
                    self.emit('stdout-ready')
                elif source == self.stderr:
                    self.emit('stderr-ready')
                return True

            if condition == GObject.IO_ERR:
                self.emit('io-error')
            if condition == GObject.IO_HUP:
                self.emit('connection-broken')
            return False


class GtkBlinker(Gtk.Image):
    def __init__(self):
        Gtk.Image.__init__(self)
        self.set_from_stock(Gtk.STOCK_MEDIA_RECORD,
                            Gtk.IconSize.SMALL_TOOLBAR)

    def pulse(self):
        """A blinker pulse"""

        sensitive = self.get_property('sensitive')
        sensitive = not sensitive
        self.set_sensitive(sensitive)

    def flush(self):
        """Flush the blinker"""

        while Gtk.events_pending():
            Gtk.main_iteration(False)

    def reset(self):
        """Reset the blinker"""

        self.set_sensitive(True)


# @TODO: check
class GtkOutputPane(Gtk.TextView):

    __gsignals__ = {
        'hide-request': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (),),
    }

    def __init__(self, buffer=None, hide_button=True, formats=None):
        super(GtkOutputPane, self).__init__()
        if buffer is not None:
            self.set_buffer(buffer)
        # self.stream = Gio.IOStream(self)
        self.hide_button = hide_button
        self.connect('populate-popup', self.on_populate_popup)
        self._filedialog = self._setup_filedialog()
        self.banner = None

        # @TODO: improve formats handling add/remove/list/edit
        if formats is None:
            formats = {
                'error': {'foreground': 'red'},
                'warning': {'foreground': 'orange'},
                'info': {'foreground': 'blue'},
                'debug': {'foreground': 'gray'},
                'cmd': {'weight': Pango.Weight.BOLD},
            }
            # 'message':{}

        buffer_ = self.get_buffer()
        for key, value in formats.items():
            buffer_.create_tag(key, **value)

    def _setup_filedialog(self):
        dialog = Gtk.FileChooserDialog(
            title='Save Output Log',
            # parent=self.textview.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK,
                           Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        patterns = [('*.txt', 'Text files'), ('*', 'All Files')]
        for pattern, name in patterns:
            filefilter = Gtk.FileFilter()
            filefilter.set_name(name)
            filefilter.add_pattern(pattern)
            dialog.add_filter(filefilter)

        dialog.set_current_name('outputlog.txt')
        dialog.set_select_multiple(False)
        dialog.set_default_response(Gtk.ResponseType.OK)

        return dialog

    def _report(self):
        if callable(self.banner):
            header = self.banner()
        elif self.banner is not None:
            header = self.banner
        else:
            header = '# Output log generated on %s' % time.asctime()

        buf = self.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)

        return '%s\n\n%s' % (header, text)

    def clear(self):
        buf = self.get_buffer()
        buf.set_text('')

    def save(self):
        dialog = self._filedialog
        dialog.set_transient_for(self.get_toplevel())
        filename = None
        while not filename:
            response = dialog.run()
            if response == Gtk.ResponseType.CANCEL:
                dialog.hide()
                return
            filename = dialog.get_filename()
            if filename and os.path.exists(filename):
                msg = ('File "%s" already exists.\n\n'
                       'Are you sure you want overwrite it?' % filename)
                msgdialog = Gtk.MessageDialog(
                    transient_for=dialog,
                    modal=True,
                    destroy_with_parent=True,
                    message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text=msg)
                msgdialog.set_default_response(Gtk.ResponseType.NO)
                response = msgdialog.run()
                msgdialog.destroy()
                if response != Gtk.ResponseType.YES:
                    filename = None

        dialog.hide()

        logfile = open(filename, 'w')
        text = self._report()
        logfile.write(text)
        logfile.close()

    def on_populate_popup(self, widget, menu):
        # Separator
        item = Gtk.SeparatorMenuItem()
        item.set_name('separator')
        item.show()
        menu.append(item)

        # Save As
        item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_SAVE_AS)
        item.set_name('save_as')
        item.connect('activate', lambda item, w: self.save(), None)
        item.show()
        menu.append(item)

        # Clear OutputLog
        item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_CLEAR)
        item.set_name('clear')
        item.connect('activate', lambda item, w: self.clear(), None)
        item.show()
        menu.append(item)

        # Hide OutputLog
        if self.hide_button:
            item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_CLOSE)
            item.set_name('close')
            item.connect('activate', lambda self, w: self.emit('hide-request'))
            item.show()
            menu.append(item)


class GtkOutputHandler(GObject.GObject, BaseOutputHandler):
    """GTK progress handler"""

    __gsignals__ = {
        'pulse': (
            GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_STRING,),
        ),
        'percentage-changed': (
            GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_FLOAT,),
        ),
    }

    def __init__(self, logger=None, statusbar=None, progressbar=None,
                 blinker=None):
        GObject.GObject.__init__(self)
        BaseOutputHandler.__init__(self, logger)

        self.statusbar = statusbar
        if self.statusbar:
            self.context_id = statusbar.get_context_id('progress')

            if blinker is None:
                blinker = GtkBlinker()
                statusbar.pack_end(
                    blinker, expand=False, fill=False, padding=0)
                blinker.hide()
            self.connect('pulse', lambda obj, text: blinker.show())
            self.connect('pulse', lambda obj, text: blinker.pulse())
            self.connect('pulse', self._update_statusbar)

            if progressbar is None:
                progressbar = Gtk.ProgressBar()
                statusbar.pack_end(
                    progressbar, expand=False, fill=False, padding=0)
                progressbar.hide()
            self.connect(
                'percentage-changed', lambda obj, perc: progressbar.show())
            self.connect(
                'percentage-changed',
                lambda obj, value: progressbar.set_text(
                    self.percentage_fmt % value))
            self.connect(
                'percentage-changed',
                lambda obj, value: progressbar.set_fraction(value / 100.))
        else:
            self.context_id = None

        self.progressbar = progressbar
        self.blinker = blinker

    def _update_statusbar(self, obj, text=''):
        assert self.statusbar
        if text:
            self.statusbar.pop(self.context_id)
            self.statusbar.push(self.context_id, text)

    def feed(self, data):
        """Feed some data to the parser.

        It is processed insofar as it consists of complete elements;
        incomplete data is buffered until more data is fed or close()
        is called.

        """

        if self.blinker:
            self.blinker.show()
            # self.progressbar.show()
        super(GtkOutputHandler, self).feed(data)

    def close(self):
        """Force processing of all buffered data and reset the instance"""

        if self.statusbar:
            self.statusbar.pop(self.context_id)
        super(GtkOutputHandler, self).close()

    def reset(self):
        """Reset the handler instance.

        Loses all unprocessed data. This is called implicitly at
        instantiation time.

        """

        super(GtkOutputHandler, self).reset()
        if self.progressbar:
            self.progressbar.set_text('%.0f %%' % 0)
            self.progressbar.hide()
            self.progressbar.set_fraction(0)
        if self.blinker:
            self.blinker.hide()

    def handle_progress(self, data):
        """Handle progress data.

        :param data:
            a list containing an item for each named group in the
            "progress" regular expression: (pulse, percentage, text)
            for the default implementation.
            Each item can be None.

        """

        # pulse = data.get('pulse')
        percentage = data.get('percentage')
        text = data.get('text')

        if text:
            self.emit('pulse', text)
        else:
            self.emit('pulse', '')
        if percentage is not None:
            self.emit('percentage-changed', percentage)

        # Flush events
        # while Gtk.events_pending():
        #     Gtk.main_iteration(False)


class GtkLoggingHandler(logging.Handler):
    """Custom handler for logging on GTK+ textviews"""

    def __init__(self, textview):
        assert textview is not None
        self.textview = textview
        logging.Handler.__init__(self)

    def _write(self, data, format=None):
        buf = self.textview.get_buffer()
        textiter = buf.get_end_iter()

        if format:
            tagtable = buf.get_tag_table()
            tag = tagtable.lookup(format)
        else:
            tag = None

        if data and not data.endswith('\n'):
            data += '\n'

        if tag:
            buf.insert_with_tags(textiter, data, tag)
        else:
            buf.insert(textiter, data)

        buf.place_cursor(buf.get_end_iter())
        self.textview.scroll_mark_onscreen(buf.get_mark('insert'))

    def _flush(self):
        while Gtk.events_pending():
            Gtk.main_iteration(False)

    def emit(self, record):
        try:
            msg = self.format(record)
            tag = getattr(record, 'tag', level2tag(record.levelno))
            self._write('%s' % msg, tag)
            # @TODO: check
            # self._flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


class GtkDialogLoggingHandler(logging.Handler):
    """GTK handler for logging message dialog"""

    levelsmap = {
        logging.CRITICAL: Gtk.MessageType.ERROR,
        # FATAL = CRITICAL
        logging.ERROR: Gtk.MessageType.ERROR,
        logging.WARNING: Gtk.MessageType.WARNING,
        # WARN = WARNING
        logging.INFO: Gtk.MessageType.INFO,
        logging.DEBUG: Gtk.MessageType.INFO,
        logging.NOTSET: Gtk.MessageType.INFO,
    }

    def __init__(self, dialog=None, parent=None):
        logging.Handler.__init__(self)
        if dialog is None:
            if parent is None:
                try:
                    parent = Gtk.window_list_toplevels()[0]
                except IndexError:
                    pass
            dialog = Gtk.MessageDialog(transient_for=parent,
                                       buttons=Gtk.ButtonsType.CLOSE)
        self.dialog = dialog
        self.formatter = None

    def emit(self, record):
        try:
            msgtype = self.levelsmap[record.levelno]
            self.dialog.set_property('message-type', msgtype)

            msg = self.format(record)
            msg = msg.encode('UTF-8', 'replace')

            self.dialog.format_secondary_markup(msg)
            if record.exc_info:
                msg = record.getMessage()
                msg = msg.encode('UTF-8', 'replace')
                # @TODO: check
                # self.dialog.set_markup('<b>%s</b>' % msg)
                self.dialog.set_markup(msg)
            else:
                msg = logging.getLevelName(record.levelno)
                # @TODO: check
                # self.dialog.set_markup('<b>%s</b>' % msg)
                self.dialog.set_markup(msg)

            self.dialog.run()
            self.dialog.hide()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


class GtkToolController(GObject.GObject, StdToolController):
    """GTK tool controller"""

    __gsignals__ = {
        'finished': (
            GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (GObject.TYPE_INT,),),
    }

    def __init__(self, logger=None):
        GObject.GObject.__init__(self)
        StdToolController.__init__(self, logger)
        self._handlers = []

    def finalize_run(self, *args, **kwargs):
        """Perform finalization actions.

        This method is called when the controlled process terminates
        to perform finalization actions like:

        * read and handle residual data in buffers,
        * flush and close output handlers,
        * close subprocess file descriptors
        * run the "finalize_run_hook" method
        * reset the controller instance

        Additional finalization actions are performed using a custom
        "finalize_run_hook" instead of overriging "finalize_run".

        """

        returncode = self.subprocess.returncode
        super(GtkToolController, self).finalize_run()
        self.emit('finished', returncode)

    def _reset(self):
        """Internal reset.

        Kill the controlled subprocess and reset I/O channels loosing
        all unprocessed data.

        """

        for handler_id in self._handlers:
            self.disconnect(handler_id)
        if self.subprocess:
            self.subprocess.close()

        super(GtkToolController, self)._reset()

    def connect_output_handlers(self):
        """Connect output handlers"""

        for handler_id in self._handlers:
            self.subprocess.disconnect(handler_id)

        self.subprocess.connect('stdout-ready', self.handle_stdout)
        self.subprocess.connect('stderr-ready', self.handle_stderr)
        self.subprocess.connect('io-error', self.handle_ioerror)
        self.subprocess.connect('connection-broken',
                                self.handle_connection_broken)
        self.subprocess.connect('finished', self.handle_finished)

    def run_tool(self, tool, *args, **kwargs):
        """Run an external tool in controlled way

        The output of the child process is handled by the controller
        and, optionally, notifications can be achieved at sub-process
        termination.

        """

        self.reset()
        self._tool = tool

        if sys.platform[:3] == 'win':
            closefds = False
            startupinfo = subprocess2.STARTUPINFO()
            startupinfo.dwFlags |= subprocess2.STARTF_USESHOWWINDOW
        else:
            closefds = True
            startupinfo = None

        if self._tool.stdout_handler:
            self._tool.stdout_handler.reset()
        if self._tool.stderr_handler:
            self._tool.stderr_handler.reset()

        cmd = self._tool.cmdline(*args, **kwargs)
        self.prerun_hook(cmd)
        self.logger.debug('"shell" flag set to %s.' % self._tool.shell)

        try:
            self.subprocess = Popen(cmd,
                                    stdin=subprocess2.PIPE,
                                    stdout=subprocess2.PIPE,
                                    stderr=subprocess2.STDOUT,
                                    close_fds=closefds,
                                    shell=self._tool.shell,
                                    startupinfo=startupinfo)
            self.subprocess.stdin.close()
            self.connect_output_handlers()
        except OSError:
            if not isinstance(cmd, str):
                cmd = ' '.join(cmd)
            msg = 'Unable to execute: "%s"' % cmd
            self.logger.error(msg, exc_info=True)
            self._reset()

            # ..seealso:: http://tldp.org/LDP/abs/html/exitcodes.html
            self.emit('finished', 126)   # @TODO: check
        except Exception:
            self._reset()
            raise

    def handle_finished(self, *args):
        """Handle process termination"""

        if not self._userstop:
            self.logger.debug('finished PID=%d' % self.subprocess.pid)

        self.finalize_run()

    def handle_ioerror(self, *args):
        """Handle a IO error while process execution"""

        if not self._userstop:
            msg = 'I/O error from sub-process PID=%d' % self.subprocess.pid
            # self.logger.error(msg)
            self.logger.debug(msg)

    def handle_connection_broken(self, *args):
        """Handle a connection broken"""

        if not self._userstop:
            msg = ('Connection broken with sub-process PID=%d' %
                   self.subprocess.pid)
            # self.logger.error(msg)
            self.logger.debug(msg)
