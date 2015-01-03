#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2015 Antonio Valentino <antonio.valentino@tiscali.it>
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

'''Simple interactive shell implementation using exectools and GTK+.'''


import time
import logging

from gi.repository import Gtk, Gdk

import exectools
from exectools.gtk import (GtkOutputPane, GtkOutputHandler,
                           GtkToolController, GtkDialogLoggingHandler,
                           GtkLoggingHandler)


class GtkShell(object):
    historyfile = 'history.txt'

    def __init__(self, debug=False):
        # Command box
        cmdlabel = Gtk.Label(label='cmd >')
        cmdlabel.set_padding(5, 0)

        self.cmdbox = Gtk.ComboBoxText.new_with_entry()
        self.cmdbox.set_active(0)
        self.cmdbox.set_focus_on_click(False)
        self.cmdbox.connect('changed', self.on_item_selected)

        completion = Gtk.EntryCompletion()
        completion.set_model(self.cmdbox.get_model())
        completion.set_text_column(0)

        self.entry = self.cmdbox.get_child()
        self.entry.set_completion(completion)
        self.entry.connect('activate', self.on_entry_activate)
        self.entry.connect('key-press-event', self.on_key_pressed)
        self.entry.connect('populate-popup', self.on_populate_popup)

        #self.cmdbutton = Gtk.Button.new_with_mnemonic('_Execute')
        self.cmdbutton = Gtk.Button(stock=Gtk.STOCK_EXECUTE)
        self.cmdbutton.connect('clicked', self.on_cmdbutton_clicked)
        # @COMPATIBILITY: set_always_show_image is new in Gtk 3.6
        try:
            self.cmdbutton.set_always_show_image(True)
        except AttributeErrror:
            pass

        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, spacing=3)
        hbox.pack_start(cmdlabel, expand=False, fill=False, padding=0)
        hbox.pack_start(self.cmdbox, expand=True, fill=True, padding=0)
        hbox.pack_start(self.cmdbutton, expand=False, fill=False, padding=0)

        # Output pane
        outputpane = GtkOutputPane(hide_button=False)
        outputpane.set_editable(False)
        scrolledwin = Gtk.ScrolledWindow()
        scrolledwin.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolledwin.add(outputpane)

        # Status bar
        self.statusbar = Gtk.Statusbar()
        id_ = self.statusbar.get_context_id('ready')
        self.statusbar.push(id_, 'Ready.')

        # Main window
        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, spacing=3)
        vbox.set_border_width(3)
        vbox.pack_start(hbox, expand=False, fill=True, padding=0)
        vbox.pack_start(scrolledwin, expand=True, fill=True, padding=0)
        vbox.pack_start(self.statusbar, expand=False, fill=True, padding=0)

        accelgroup = Gtk.AccelGroup()
        accelgroup.connect(ord('d'), Gdk.ModifierType.CONTROL_MASK,
                           Gtk.AccelFlags.VISIBLE, self.quit)

        self.mainwin = Gtk.Window()
        self.mainwin.set_title('GTK Shell')
        theme = Gtk.IconTheme.get_default()
        icon = theme.load_icon(Gtk.STOCK_EXECUTE,
                               Gtk.IconSize.LARGE_TOOLBAR,
                               Gtk.IconLookupFlags(0))
        self.mainwin.set_icon(icon)
        self.mainwin.add(vbox)
        self.mainwin.set_default_size(650, 500)
        self.mainwin.add_accel_group(accelgroup)
        self.mainwin.connect('destroy', self.quit)
        self.mainwin.show_all()

        # Setup the log system
        if debug:
            level = logging.DEBUG
            logging.basicConfig(level=level)
        else:
            level = logging.INFO

        self.logger = logging.getLogger()

        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler = GtkLoggingHandler(outputpane)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        formatter = logging.Formatter('%(message)s')
        handler = GtkDialogLoggingHandler(parent=self.mainwin, dialog=None)
        handler.setLevel(logging.WARNING)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.logger.setLevel(level)

        # Setup high level components and initialize the parent classes
        handler = GtkOutputHandler(self.logger, self.statusbar)
        self.tool = exectools.ToolDescriptor('', stdout_handler=handler)
        self.controller = GtkToolController(logger=self.logger)
        self.controller.connect('finished', self.on_finished)

        # Final setup
        self._state = 'ready'   # or maybe __state

        self.logger.debug('gtkshell session started at %s.' % time.asctime())
        self.load_history()

    def main(self):
        Gtk.main()

    def quit(self, *data):
        try:
            self.save_history()
        finally:
            self.logger.debug(
                'gtkshell session stopped at %s.' % time.asctime())
            Gtk.main_quit()

    def load_history(self):
        try:
            for cmd in open(self.historyfile, 'r'):
                self.cmdbox.append_text(cmd.rstrip())
            self.logger.debug('history file "%s" loaded.' % self.historyfile)
        except (OSError, IOError) as e:
            self.logger.debug('unable to read the history file "%s": %s.' %
                              (self.historyfile, e))

    def save_history(self):
        try:
            liststore = self.cmdbox.get_model()
            history = '\n'.join([item[0] for item in liststore])
            f = open(self.historyfile, 'w')
            f.write(history)
            f.close()
            self.logger.debug('history saved in %s' % self.historyfile)
        except (OSError, IOError) as e:
            self.logger.warning('unable to save the history file "%s": %s' %
                                (self.historyfile, e))

    def _reset(self):
        self.controller._reset()
        self.cmdbutton.set_label(Gtk.STOCK_EXECUTE)
        self.cmdbox.set_sensitive(True)
        self.entry.grab_focus()

    def reset(self):
        self._reset()
        self.state = 'ready'

    def get_state(self):
        return self._state

    def set_state(self, state):
        if(state == 'ready'):
            self._reset()
            id_ = self.statusbar.get_context_id('running')
            self.statusbar.pop(id_)
        elif(state == 'running'):
            self.cmdbox.set_sensitive(False)
            id_ = self.statusbar.get_context_id('running')
            self.statusbar.push(id_, 'Running ...')
            self.cmdbutton.set_label(Gtk.STOCK_STOP)
        else:
            raise ValueError('invalid status: "%s".' % state)
        self._state = state

    state = property(get_state, set_state)

    def execute(self):
        cmd = self.entry.get_text()
        if cmd:
            self.entry.set_text('')
            self.cmdbox.append_text(cmd)
            cmd = cmd.split()

            try:
                self.state = 'running'
                self.controller.run_tool(self.tool, *cmd)
                #raise RuntimeError('simulated runtime error')
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                self.logger.error(e, exc_info=True)
                self.state = 'ready'

    def on_key_pressed(self, widget, event):
        key = Gdk.keyval_name(event.keyval)
        if key in ('Up', 'Down', 'Page_Up', 'Page_Down'):
            self.cmdbox.popup()
            return True

    def on_cmdbutton_clicked(self, widget=None):
        if self.state == 'ready':
            self.execute()
        elif self.state == 'running':
            self.controller.stop_tool()

    def on_entry_activate(self, widget=None):
        if self.state == 'running':
            return
        self.execute()

    def on_item_selected(self, widget):
        self.entry.set_position(-1)

    def on_populate_popup(self, widget, menu):
        # separator
        item = Gtk.SeparatorMenuItem()
        item.show()
        menu.append(item)

        # Clear history
        item = Gtk.ImageMenuItem(Gtk.STOCK_CLEAR)
        item.set_name('clear_history')
        item.connect('activate', self.on_clear_history, None)
        item.connect('activate', self.on_clear_entry, None)
        item.show()
        menu.append(item)

    def on_clear_history(self, widget=None):
        liststore = self.cmdbox.get_model()
        liststore.clear()

    def on_clear_entry(self, widget=None):
        self.entry.set_text('')

    def on_finished(self, widget=None, returncode=0):
        self.reset()

if __name__ == '__main__':
    GtkShell(debug=True).main()
