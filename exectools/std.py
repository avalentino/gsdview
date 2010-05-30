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

'''Tools for running external processes using the subprocess module.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__revision__ = '$Revision$'
__date__     = '$Date$'

import sys

# @TODO: check
from exectools import BaseToolController

import subprocess2

class StdToolController(BaseToolController):
    '''Class for controlling command line tools.

    A tool controller runs an external tool in controlled way.
    The output of the child process is handled by the controller and,
    optionally, notifications can be achieved at sub-process
    termination.

    A tool controller also allow to stop the controlled process.

    '''

    def run_tool(self, tool, *args):
        '''Run an external tool in controlled way.

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
        cmd = self._tool.cmdline(*args)
        self.prerun_hook(*cmd)

        try:
            self.subprocess = subprocess2.Popen(cmd,
                                                stdin = subprocess2.PIPE,
                                                stdout = subprocess2.PIPE,
                                                stderr = subprocess2.STDOUT,
                                                cwd = self._tool.cwd,
                                                env = self._tool.env,
                                                close_fds = closefds,
                                                shell = self._tool.shell,
                                                startupinfo = startupinfo)
            self.subprocess.stdin.close()
            self.connect_output_handlers()
        except OSError:
            if not isinstance(args, basestring):
                args = ' '.join(args)
            msg = 'Unable to execute: "%s"' % args
            self.logger.error(msg, exc_info=True)
            self.reset_controller()
        except:
            self.reset_controller()
            raise

# @TODO: logging handler for progress
