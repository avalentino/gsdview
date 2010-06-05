# -*- coding: utf-8 -*-

### Copyright (C) 2006-2010 Antonio Valentino <a_valentino@users.sf.net>

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

'''Tools for running external processes in a GTK GUI.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__revision__ = '$Revision$'
__date__     = '$Date$'

import os
import sys
import time
import logging

import gtk
import pango
import gobject

import subprocess2

from exectools import BaseOutputHandler, level2tag
from exectools.std import StdToolController

class Popen(gobject.GObject, subprocess2.Popen):

    _timeout = 100 # ms

    __gsignals__ = {
        'stdout-ready': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (),),
        'stderr-ready': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (),),
        'io-error': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (),),
        'connection-broken': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (),),
        'finished': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (),),
    }

    def __init__(self, *args, **kwargs):
        gobject.GObject.__init__(self)
        subprocess2.Popen.__init__(self, *args, **kwargs)
        self._watch_tags = []

        id_ = gobject.timeout_add(self._timeout, self._check_finished)
        self._watch_tags.append(id_)

        self._setup_io_watch()

    def _check_finished(self):
        if self.poll() is not None:
            self.emit('finished')
            return False
        return True

    def close(self):
        if self.stdout:
            self.stdout.close()
        if self.stderr:
            self.stderr.close()

        for tag in self._watch_tags:
            gobject.source_remove(tag)

    if sys.platform[:3] == 'win':
        import errno
        import msvcrt
        from subprocess import pywintypes
        from win32pipe import PeekNamedPipe

        def _setup_io_watch(self):
            # @TODO: signal.set_wakeup_fd from Python 2.6
            if self.stdout:
                id_ = gobject.timeout_add(self._timeout, self._check_ready,
                                          self.stdout)
                self._watch_tags.append(id_)
            if self.stderr:
                id_ = gobject.timeout_add(self._timeout, self._check_ready,
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
            except (pywintypes.error, Exception), why:
                if why[0] in (109, errno.ESHUTDOWN):
                    return conn.close()
                raise

            return True

    else:   # POSIX

        def _setup_io_watch(self):
            cond = gobject.IO_IN|gobject.IO_PRI|gobject.IO_ERR|gobject.IO_HUP
            if self.stdout:
                id_ = gobject.io_add_watch(self.stdout, cond,
                                           self._io_callback)
                self._watch_tags.append(id_)
            if self.stderr:
                id_ = gobject.io_add_watch(self.stderr, cond,
                                           self._io_callback)
                self._watch_tags.append(id_)

        def _io_callback(self, source, condition):
            if condition in (gobject.IO_IN, gobject.IO_PRI):
                if source == self.stdout:
                    self.emit('stdout-ready')
                elif source == self.stderr:
                    self.emit('stderr-ready')
                return True

            if condition  == gobject.IO_ERR:
                self.emit('io-error')
            if condition  == gobject.IO_HUP:
                self.emit('connection-broken')
            return False


class GtkBlinker(gtk.Image):
    def __init__(self):
        gtk.Image.__init__(self)
        self.set_from_stock(gtk.STOCK_MEDIA_RECORD, gtk.ICON_SIZE_SMALL_TOOLBAR)

    def pulse(self):
        '''A blinker pulse'''

        sensitive = self.get_property('sensitive')
        sensitive = not sensitive
        self.set_sensitive(sensitive)

    def flush(self):
        '''Flush the blinker'''

        while gtk.events_pending():
            gtk.main_iteration(False)

    def reset(self):
        '''Reset the blinker'''

        self.set_sensitive(True)


# @TODO: check
class GtkOutputPlane(gtk.TextView):

    __gsignals__ = {
        'hide-request': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (),),
    }

    def __init__(self, buffer=None, hide_button=True, formats=None):
        super(GtkOutputPlane, self).__init__(buffer)
        #self.stream = GtkOStream(self)
        self.hide_button = hide_button
        self.connect('populate-popup', self.on_populate_popup)
        self._filedialog = self._setup_filedialog()
        self.banner = None

        # @TODO: improve formats handling add/remove/list/edit
        if formats is None:
            formats = {
                'error':     {'foreground': 'red'},
                'warning':   {'foreground': 'orange'},
                'info':      {'foreground': 'blue'},
                'debug':     {'foreground': 'gray'},
                'cmd':       {'weight':     pango.WEIGHT_BOLD},
            }
            #'message':{}

        buffer_ = self.get_buffer()
        for key, value in formats.iteritems():
            buffer_.create_tag(key, **value)

    def _setup_filedialog(self):
        dialog = gtk.FileChooserDialog(
                        title   = 'Save Output Log',
                        #parent  = self.textview.get_toplevel(),
                        action  = gtk.FILE_CHOOSER_ACTION_SAVE,
                        buttons = (gtk.STOCK_OK,     gtk.RESPONSE_OK,
                                   gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        patterns = [('*.txt', 'Text files'), ('*', 'All Files')]
        for pattern, name in patterns:
            filefilter = gtk.FileFilter()
            filefilter.set_name(name)
            filefilter.add_pattern(pattern)
            dialog.add_filter(filefilter)

        dialog.set_current_name('outputlog.txt')
        dialog.set_select_multiple(False)
        dialog.set_default_response(gtk.RESPONSE_OK)

        return dialog

    def _report(self):
        if callable(self.banner):
            header = self.banner()
        elif self.banner is not None:
            header = self.banner
        else:
            header = '# Output log generated on %s' % time.asctime()

        buf = self.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter())

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
            if response == gtk.RESPONSE_CANCEL:
                dialog.hide()
                return
            filename = dialog.get_filename()
            if filename and os.path.exists(filename):
                msg = ('File "%s" already exists.\n\n'
                       'Are you sure you want overwrite it?' % filename)
                msgdialog = gtk.MessageDialog(
                                    parent  = dialog,
                                    flags   = gtk.DIALOG_MODAL |
                                              gtk.DIALOG_DESTROY_WITH_PARENT,
                                    type    = gtk.MESSAGE_QUESTION ,
                                    buttons = gtk.BUTTONS_YES_NO,
                                    message_format = msg)
                msgdialog.set_default_response(gtk.RESPONSE_NO)
                response = msgdialog.run()
                msgdialog.destroy()
                if(response != gtk.RESPONSE_YES):
                    filename = None

        dialog.hide()

        logfile = open(filename, 'w')
        text = self._report()
        logfile.write(text)
        logfile.close()

    def on_populate_popup(self, widget, menu):
        # Separator
        item = gtk.SeparatorMenuItem()
        item.set_name('separator')
        item.show()
        menu.append(item)

        # Save As
        item = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS)
        item.set_name('save_as')
        item.connect('activate', lambda item, w: self.save(), None)
        item.show()
        menu.append(item)

        # Clear OutputLog
        item = gtk.ImageMenuItem(gtk.STOCK_CLEAR)
        item.set_name('clear')
        item.connect('activate', lambda item, w: self.clear(), None)
        item.show()
        menu.append(item)

        # Hide OutputLog
        if self.hide_button:
            item = gtk.ImageMenuItem(gtk.STOCK_CLOSE)
            item.set_name('close')
            item.connect('activate', lambda self, w: self.emit('hide-request'))
            item.show()
            menu.append(item)


class GtkOutputHandler(BaseOutputHandler):
    '''GTK progress handler'''

    def __init__(self, logger=None, statusbar=None, progressbar=None,
                 blinker=None):
        super(GtkOutputHandler, self).__init__(logger)

        self.statusbar = statusbar
        if self.statusbar:
            self.context_id = statusbar.get_context_id('progress')

            if blinker is None:
                blinker = GtkBlinker()
                statusbar.pack_end(blinker, expand=False)
                blinker.hide()

            if progressbar is None:
                progressbar = gtk.ProgressBar()
                statusbar.pack_end(progressbar)
                progressbar.hide()

        else:
            self.context_id = None

        self.progressbar = progressbar
        self.blinker = blinker

    def feed(self, data):
        '''Feed some data to the parser.

        It is processed insofar as it consists of complete elements;
        incomplete data is buffered until more data is fed or close()
        is called.

        '''

        if self.blinker:
            self.blinker.show()
            #self.progressbar.show()
        super(GtkOutputHandler, self).feed(data)

    def close(self):
        '''Force processing of all buffered data and reset the instance'''

        if self.statusbar:
            self.statusbar.pop(self.context_id)
        super(GtkOutputHandler, self).close()

    def reset(self):
        '''Reset the handler instance.

        Loses all unprocessed data. This is called implicitly at
        instantiation time.

        '''

        super(GtkOutputHandler, self).reset()
        if self.progressbar:
            self.progressbar.set_text('%.0f %%' % 0)
            self.progressbar.hide()
            self.progressbar.set_fraction(0)
        if self.blinker:
            self.blinker.hide()

    def _handle_pulse(self, data):
        '''Handle a blinker pulse'''

        if self.blinker:
            if not self.blinker.get_property('visible'):
                self.blinker.show()
            else:
                self.blinker.pulse()

    def _handle_percentage(self, data):
        '''Handle percentage of a precess execution.

        :param data: percentage

        '''

        if self.progressbar:
            self.progressbar.show()
            self.progressbar.set_text(self.percentage_fmt % data)
            self.progressbar.set_fraction(data / 100.)

    def handle_progress(self, data):
        '''Handle progress data.

        :param data: a list containing an item for each named group in
                     the "progress" regular expression: (pulse,
                     percentage, text) for the default implementation.
                     Each item can be None.

        '''

        pulse = data.get('pulse')
        percentage = data.get('percentage')
        text = data.get('text')

        if pulse:
            self._handle_pulse(pulse)
        if percentage is not None:
            self._handle_percentage(percentage)
        if text and not pulse and percentage is None:
            if self.statusbar:
                self.statusbar.pop(self.context_id)
                self.statusbar.push(self.context_id, text)
            self._handle_pulse(pulse)

        # Flush events
        # @TODO: check (might slow too mutch the app)
        while gtk.events_pending():
            gtk.main_iteration(False)


class GtkLoggingHandler(logging.Handler):
    '''Custom handler for logging on GTK+ textviews'''

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
        while gtk.events_pending():
            gtk.main_iteration(False)

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

class GtkDialogLoggingHandler(logging.Handler):
    '''GTK handler for logging message dialog'''

    levelsmap = {
        logging.CRITICAL: gtk.MESSAGE_ERROR,
        # FATAL = CRITICAL
        logging.ERROR: gtk.MESSAGE_ERROR,
        logging.WARNING: gtk.MESSAGE_WARNING,
        # WARN = WARNING
        logging.INFO: gtk.MESSAGE_INFO,
        logging.DEBUG: gtk.MESSAGE_INFO,
        logging.NOTSET: gtk.MESSAGE_INFO,
    }

    def __init__(self, dialog=None, parent=None):
        logging.Handler.__init__(self)
        if dialog is None:
            if parent is None:
                try:
                    parent = gtk.window_list_toplevels()[0]
                except IndexError:
                    pass
            dialog = gtk.MessageDialog(parent, buttons=gtk.BUTTONS_CLOSE)
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
                #self.dialog.set_markup('<b>%s</b>' % msg)
                self.dialog.set_markup(msg)
            else:
                msg = logging.getLevelName(record.levelno)
                # @TODO: check
                #self.dialog.set_markup('<b>%s</b>' % msg)
                self.dialog.set_markup(msg)

            self.dialog.run()
            self.dialog.hide()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class GtkToolController(gobject.GObject, StdToolController):
    '''GTK tool controller'''

    __gsignals__ = {
        'finished': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                                    (gobject.TYPE_INT,),),
    }

    def __init__(self, logger=None):
        gobject.GObject.__init__(self)
        StdToolController.__init__(self, logger)
        self._handlers = []

    def finalize_run(self, *args, **kwargs):
        '''Perform finalization actions.

        This method is called when the controlled process terminates
        to perform finalization actions like:

        * read and handle residual data in buffers,
        * flush and close output handlers,
        * close subprocess file descriptors
        * run the "finalize_run_hook" method
        * reset the controller instance

        Additional finalization actions are performed using a custom
        "finalize_run_hook" instead of overriging "finalize_run".

        '''

        returncode = self.subprocess.returncode
        super(GtkToolController, self).finalize_run()
        self.emit('finished', returncode)

    def reset_controller(self):
        '''Reset the tool controller instance.

        Kill the controlled subprocess and reset the controller
        instance losing all unprocessed data.

        '''

        for handler_id in self._handlers:
            self.disconnect(handler_id)
        if self.subprocess:
            self.subprocess.close()
        super(GtkToolController, self).reset_controller()

    def connect_output_handlers(self):
        '''Connect output handlers'''

        for handler_id in self._handlers:
            self.subprocess.disconnect(handler_id)

        self.subprocess.connect('stdout-ready', self.handle_stdout)
        self.subprocess.connect('stderr-ready', self.handle_stderr)
        self.subprocess.connect('io-error', self.handle_ioerror)
        self.subprocess.connect('connection-broken',
                                self.handle_connection_broken)
        self.subprocess.connect('finished', self.handle_finished)

    def run_tool(self, tool, *args, **kwargs):
        '''Run an external tool in controlled way

        The output of the child process is handled by the controller
        and, optionally, notifications can be achieved at sub-process
        termination.

        '''

        assert self.subprocess is None

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
                                    stdin  = subprocess2.PIPE,
                                    stdout = subprocess2.PIPE,
                                    stderr = subprocess2.STDOUT,
                                    close_fds = closefds,
                                    shell = self._tool.shell,
                                    startupinfo = startupinfo)
            self.subprocess.stdin.close()
            self.connect_output_handlers()
        except OSError:
            if not isinstance(cmd, basestring):
                cmd = ' '.join(cmd)
            msg = 'Unable to execute: "%s"' % cmd
            self.logger.error(msg, exc_info=True)
            self.reset_controller()
            self.emit('finished')
        except:
            self.reset_controller()
            raise

    def handle_finished(self, *args):
        '''Handle process termination'''

        if not self._stopped:
            self.logger.debug('finished PID=%d' % self.subprocess.pid)

        self.finalize_run()

    def handle_ioerror(self, *args):
        '''Handle a IO error while process execution'''

        if not self._stopped:
            msg = 'I/O error from sub-process PID=%d' % self.subprocess.pid
            #self.logger.error(msg)
            self.logger.debug(msg)

    def handle_connection_broken(self, *args):
        '''Handle a connection broken'''

        if not self._stopped:
            msg = ('Connection broken with sub-process PID=%d' %
                                                        self.subprocess.pid)
            #self.logger.error(msg)
            self.logger.debug(msg)
