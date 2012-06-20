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

'''Enhanced version of the subprocess module.

The Popen class provides a cross-platform stop method for stopping the child
sub-process and allow asynchronous I/O both on Windows and Posix platforms.

'''

# @TODO: use ctypes instead of pywin32
# @TODO: update to the new subprocess API (signal, kill, terminate)


import os
import time
import errno
import warnings
import subprocess

import recipe_440544

if subprocess.mswindows:
    from win32api import OpenProcess, TerminateProcess, CloseHandle
else:
    import signal

from subprocess import list2cmdline

try:
    from subprocess import PIPE, STDOUT, call, check_call, CalledProcessError
    __all__ = ["Popen", "PIPE", "STDOUT", "call", "check_call",
               "CalledProcessError", "list2cmdline"]
except ImportError:
    # @COMPATIBILITY with python 2.4
    from subprocess import PIPE, STDOUT, call
    __all__ = ["Popen", "PIPE", "STDOUT", "call", "list2cmdline"]


__author__ = 'Antonio Valentino <a_valentino@users.sf.net>'
__revision__ = '$Revision$'
__date__ = '$Date$'


class Popen(recipe_440544.Popen):
    # @TODO: see subprocess.Popen.terminate(), subprocess.Popen.kill(), and
    #        subprocess.Popen.send_signal() from Python 2.6
    delay_after_stop = 0.2

    if subprocess.mswindows:

        def stop(self, force=True):
            if self.poll() is not None:
                return True

            try:
                PROCESS_TERMINATE = 1
                handle = OpenProcess(PROCESS_TERMINATE, False, self.pid)
                TerminateProcess(handle, -1)
                CloseHandle(handle)
            except subprocess.pywintypes.error as e:
                # @TODO: check error code
                warnings.warn(e)

            time.sleep(self.delay_after_stop)
            if self.poll() is not None:
                return True
            else:
                return False

    else:

        def _kill(self, sigid):
            '''Ignore the exception when the process doesn't exist.'''
            try:
                os.kill(self.pid, sigid)
            except OSError as e:
                if e.errno != errno.ESRCH:
                    raise

        def stop(self, force=True):
            '''This forces a child process to terminate.

            It starts nicely with SIGTERM.
            If "force" is True then moves onto SIGKILL.
            This returns True if the child was terminated.
            This returns False if the child could not be terminated.
            '''

            # Stop shell dependent sub-procsses
            # @TODO: check
            if self.poll() is not None:
                return True
            self._kill(signal.SIGINT)
            if self.poll() is None:
                time.sleep(self.delay_after_stop)

            if self.poll() is not None:
                return True
            self._kill(signal.SIGTERM)
            if self.poll() is None:
                time.sleep(self.delay_after_stop)
            if self.poll() is not None:
                return True
            if force:
                self._kill(signal.SIGKILL)
                if self.poll() is None:
                    time.sleep(self.delay_after_stop)
                if self.poll() is not None:
                    return True
                else:
                    return False
            return False
