# -*- coding: utf-8 -*-

### Copyright (C) 2006-2014 Antonio Valentino <a_valentino@users.sf.net>

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

import sys

from exectools import BaseToolController, EX_OK
from exectools import subprocess2


class StdToolController(BaseToolController):
    '''Class for controlling command line tools.

    A tool controller runs an external tool in controlled way.
    The output of the child process is handled by the controller and,
    optionally, notifications can be achieved at sub-process
    termination.

    A tool controller also allow to stop the controlled process.

    '''

    @property
    def isbusy(self):
        '''If True then the controller is already running a subprocess.'''

        return self.subclasses is not None

    def run_tool(self, tool, *args, **kwargs):
        '''Run an external tool in controlled way.

        The output of the child process is handled by the controller
        and, optionally, notifications can be achieved at sub-process
        termination.

        '''

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
        self.prerun_hook(*cmd)

        try:
            self.subprocess = subprocess2.Popen(cmd,
                                                stdin=subprocess2.PIPE,
                                                stdout=subprocess2.PIPE,
                                                stderr=subprocess2.STDOUT,
                                                cwd=self._tool.cwd,
                                                env=self._tool.env,
                                                close_fds=closefds,
                                                shell=self._tool.shell,
                                                startupinfo=startupinfo)
            self.subprocess.stdin.close()
            self.connect_output_handlers()
        except OSError:
            if not isinstance(args, basestring):
                args = ' '.join(args)
            msg = 'Unable to execute: "%s"' % args
            self.logger.error(msg, exc_info=True)
            self._reset()
        except:
            self._reset()
            raise

    def finalize_run(self, *args, **kwargs):
        '''Perform finalization actions.

        This method is called when the controlled process terminates
        to perform finalization actions like:

        * read and handle residual data in buffers,
        * flush and close output handlers,
        * close subprocess file descriptors
        * run the "finalize_run_hook" method
        * reset the controller instance

        This method is not meant to be called by the user but the user
        can provide custom implementations in subclasses.

        If one just needs to perfor some additional finalization action
        it should be better to use a custom "finalize_run_hook" instead
        of overriging "finalize_run".

        '''

        try:
            if self.subprocess:
                # retrieve residual data
                if sys.platform[:3] == 'win':
                    # using read() here hangs on win32
                    if self._tool.stdout_handler:
                        data = self.subprocess.recv()
                        while data:
                            data = data.decode(self._tool.output_encoding)
                            self._tool.stdout_handler.feed(data)
                            data = self.subprocess.recv()
                    if self._tool.stderr_handler:
                        data = self.subprocess.recv_err()
                        while data:
                            data = data.decode(self._tool.output_encoding)
                            self._tool.stderr_handler.feed(data)
                            data = self.subprocess.recv_err()
                else:
                    try:
                        if self._tool.stdout_handler:
                            data = self.subprocess.stdout.read()
                            data = data.decode(self._tool.output_encoding)
                            self._tool.stdout_handler.feed(data)
                    except ValueError:
                        # I/O operation on closed file.
                        pass

                    try:
                        if self._tool.stderr_handler:
                            data = self.subprocess.stderr.read()
                            data = data.decode(self._tool.output_encoding)
                            self._tool.stderr_handler.feed(data)
                    except ValueError:
                        # I/O operation on closed file.
                        pass

                # close the pipes
                # NOTE: recipe_440544.Popen closes the stdout if no more
                #       output is available
                if self.subprocess.stdout:
                    self.subprocess.stdout.close()
                if self.subprocess.stderr:
                    self.subprocess.stderr.close()

                # wait for the subprocess termination
                self.subprocess.wait()
                if self._tool.stdout_handler:
                    self._tool.stdout_handler.close()
                if self._tool.stderr_handler:
                    self._tool.stderr_handler.close()

                if self._userstop:
                    self.logger.info('Execution stopped by the user.')
                elif self.subprocess.returncode != EX_OK:
                    msg = ('Process (PID=%d) exited with return code %d.' % (
                        self.subprocess.pid, self.subprocess.returncode))
                    self.logger.warning(msg)

                # Call finalize hook is available
                self.finalize_run_hook()
        finally:
            # Protect for unexpected errors in the feed and close methods of
            # the outputhandler
            self._reset()

    def _reset(self):
        '''Internal reset.

        Kill the controlled subprocess and reset I/O channels loosing
        all unprocessed data.

        '''

        if self.subprocess:
            self.subprocess.stop(force=True)

        assert (self.subprocess is None or
                self.subprocess.returncode is not None), \
            'the process is still running'

        super(StdToolController, self)._reset()

    def reset(self):
        '''Reset the tool controller instance.

        Kill the controlled subprocess and reset the controller
        instance loosing all unprocessed data.

        '''

        super(StdToolController, self).reset()
        self.subprocess = None

    def handle_stdout(self, *args):
        '''Handle standard output data.

        This method is not meant to be directly called by the user.

        The user, anyway, can provide a custom implementation in
        derived classes.

        '''

        if self.subprocess is None or self.subprocess.poll() is not None:
            # NOTE: 'self.subprocess is None' should never happen at this point
            #self.finalize_run() # @TODO: check
            return False
        else:
            data = self.subprocess.recv()
            if data:
                data = data.decode(self._tool.output_encoding)
                self._tool.stdout_handler.feed(data)
            return True

    def handle_stderr(self, *args):
        '''Handle standard  error.

        This method is not meant to be directly called by the user.

        The user, anyway, can provide a custom implementation in
        derived classes.

        '''

        if self.subprocess is None or self.subprocess.poll() is not None:
            # NOTE: 'self.subprocess is None' should never happen ar this point
            #self.finalize_run() # @TODO: check
            return False
        else:
            data = self.subprocess.recv_err()
            if data:
                data = data.decode(self._tool.output_encoding)
                self._tool.stderr_handler.feed(data)
            return True

    def stop_tool(self, force=True):
        '''Stop the execution of controlled subprocess.

        When this method is invoked the controller instance is always
        reset even if the controller is unable to stop the subprocess.

        When possible the controller try to kill the subprocess in a
        polite way.  If this fails it also tryes brute killing by
        default (force=True).  This behaviour can be controlled using
        the `force` parameter.

        '''

        # @TODO: fix stop function with shell=True
        if self.subprocess:
            self.logger.debug('Execution stopped by the user.')
            self._userstop = True
            stopped = self.subprocess.stop(force)
            if not stopped:
                msg = ('Unable to stop the sub-process (PID=%d).' %
                       self.subprocess.pid)
                self.logger.warning(msg)
                self._reset()
            # The subprocess is successfully stopped.
            # The output handler will provide to the finalization
            # NOTE: return without reset
        else:
            self._reset()


# @TODO: logging handler for progress
