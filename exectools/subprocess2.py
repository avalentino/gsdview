# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2020 Antonio Valentino <antonio.valentino@tiscali.it>
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

"""Enhanced version of the subprocess module.

The Popen class provides a cross-platform stop method for stopping the child
sub-process and allow asynchronous I/O both on Windows and Posix platforms.

"""

import time
import errno
import warnings
import subprocess
from subprocess import *

__all__ = subprocess.__all__

from exectools import recipe_440544

if not subprocess.mswindows:
    import signal


class Popen(recipe_440544.Popen):
    delay_after_stop = 0.2

    if subprocess.mswindows:

        def stop(self, force=True):
            if self.poll() is not None:
                return True

            try:
                self.terminate()
            except WindowsError as e:
                # @TODO: check error code
                warnings.warn(e)

            time.sleep(self.delay_after_stop)
            if self.poll() is not None:
                return True
            else:
                return False

    else:

        def stop(self, force=True):
            """This forces a child process to terminate.

            It starts nicely with SIGTERM.
            If "force" is True then moves onto SIGKILL.
            This returns True if the child was terminated.
            This returns False if the child could not be terminated.
            """

            if self.poll() is not None:
                return True

            try:
                # Stop shell dependent sub-processes
                # @TODO: check
                self.send_signal(signal.SIGINT)
                if self.poll() is None:
                    time.sleep(self.delay_after_stop)

                if self.poll() is not None:
                    return True

                self.terminate()
                if self.poll() is None:
                    time.sleep(self.delay_after_stop)

                if force:
                    if self.poll() is not None:
                        return True

                    self.kill()
                    if self.poll() is None:
                        time.sleep(self.delay_after_stop)
            except OSError as e:
                if e.errno != errno.ESRCH:
                    raise
                return True

            if self.poll() is not None:
                return True

            return False
