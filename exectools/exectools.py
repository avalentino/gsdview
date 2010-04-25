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

'''Tools for running external processes.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__revision__ = '$Revision$'
__date__     = '$Date$'

import re
import os
import sys
import locale
import logging
import subprocess2
from cStringIO import StringIO

if sys.platform[:3] == 'win':
    EX_OK = 0
else:
    EX_OK = os.EX_OK

class BaseOStream(object):
    '''Base class for the output stream'''

    def __init__(self, *args, **kwargs):
        super(BaseOStream, self).__init__()
        self.srcencoding = locale.getpreferredencoding()
        self.dstencoding = self.srcencoding
        self.formats = {}

    def _fixencoding(self, data):
        # @TODO: test on win32
        if self.srcencoding != self.dstencoding:
            try:
                data = data.decode(self.srcencoding, 'replace')
                data = data.encode(self.dstencoding, 'replace')
            except UnicodeDecodeError, e:
                data = str(e)
                logging.warning('unicode error.', exc_info=True)
        return data

    def flush(self):
        '''Flush the stream buffers'''

        pass

    def write(self, data, format_=None):
        '''Write data on the output stream'''

        pass


class OFStream(BaseOStream):
    '''Output file stream'''

    def __init__(self, fileobj=sys.stdout):
        super(OFStream, self).__init__(fileobj)
        self.fileobj = fileobj
        self.formats = {'progress': '\r%s'}

    def flush(self):
        '''Flush the file buffer'''

        self.fileobj.flush()

    def write(self, data, format_=None):
        '''Write data to file'''

        data = self._fixencoding(data)

        if isinstance(format_, basestring):
            format_ = self.formats.get(format_, '')

        if format_:
            data = format_ % data

        self.fileobj.write(data)


class BaseOutputHandler(object):
    '''Base class for output handlers'''

    def __init__(self, stream=None):
        super(BaseOutputHandler, self).__init__()
        self._buffer = StringIO()
        self._wpos  = self._buffer.tell()

        self.stream = stream

        self.percentage_fmt = '%5.1f %%'
        self.handlers = ['progress', 'line']

        # NOTE: pulse, percentage and text are all optional. The regexp
        #       consumes the '\r' character in any case.
        pattern = ('[ \t]'
                   '*\r+'
                   '[ \t]*'
                   '(?P<pulse>[\\\|/-])?'
                   '[ \t]*'
                   '((?P<percentage>\d{1,3}(\.\d*)?)[ \t]*%)?'
                   '[ \t]*'
                   '((?P<text>.*?)(?=\r|\n))')
        self._progress_pattern = re.compile(pattern)

        self._text_patterns = {
            'error': re.compile('error', re.IGNORECASE),
            'warning': re.compile('warning', re.IGNORECASE),
        }

    def reset(self):
        '''Reset the handler instance

        Loses all unprocessed data. This is called implicitly at
        instantiation time.

        '''

        self._buffer.close()
        self._buffer = StringIO()
        self._wpos = self._buffer.tell()

    def close(self):
        '''Force processing of all buffered data and reset the instance'''

        self._parse()
        data = self._buffer.read()
        if data:
            if not data.endswith('\n'):
                data += '\n'
            self.handle_line(data)
        self.reset()

    def feed(self, data):
        '''Feed some data to the parser

        It is processed insofar as it consists of complete elements;
        incomplete data is buffered until more data is fed or close()
        is called.

        '''

        rpos = self._buffer.tell()
        self._buffer.seek(self._wpos)
        self._buffer.write(data)
        self._wpos = self._buffer.tell()
        self._buffer.seek(rpos)
        self._parse()

    def get_progress(self):
        '''Search and decode progress patterns'''

        pos = self._buffer.tell()
        data = self._buffer.read()
        match = self._progress_pattern.match(data)
        if match:
            result = [match.group('pulse'),
                      match.group('percentage'),
                      match.group('text')]
            if result == [None, None, None]:
                result = None
        else:
            result = None

        if result:
            self._buffer.seek(pos+match.end())
        else:
            self._buffer.seek(pos)
            return None

        if result[1] is not None:
            result[1] = float(result[1])
        return result

    def get_line(self):
        '''Extract complete lines'''

        pos = self._buffer.tell()
        data = self._buffer.readline()
        if data and (data[-1] == '\n'):
            return data
        self._buffer.seek(pos)
        return None

    def _parse(self):
        while True:
            for name in self.handlers:
                data = getattr(self, 'get_' + name)()
                if data not in (None, ''):
                    getattr(self, 'handle_' + name)(data)
                    break
            else:
                # no pattern matches
                break

    def handle_progress(self, data):
        '''Handle progress data

        This method is not meant to be called by the user.

        The user, anyway, can provide a custom implementation in
        derived classes.

        :param data: a list containing an item for each named group in
                     the "progress" regular expression: (pulse,
                     percentage, text) for the default implementation.
                     Each item can be None.

        '''

        if self.stream:
            pulse, percentage, text = data
            result = []
            if pulse:
                result.append(pulse)
            if percentage is not None:
                result.append(self.percentage_fmt % percentage)
            if text:
                result.append(text)
            self.stream.write(' '.join(result), 'progress')
            self.stream.flush()

    def handle_line(self, data):
        '''Handle output lines

        This method is not meant to be directly called by the user.

        The user, anyway, can provide a custom implementation in
        derived classes.

        :param data: an entire output line (including the trailing
                     "end of line" character.

        '''

        if self.stream:
            for tag_name, pattern in self._text_patterns.items():
                match = pattern.search(data)
                if match:
                    self.stream.write(data, tag_name)
                    break
            else:
                self.stream.write(data)
            self.stream.flush()


class ToolDescriptor(object):
    '''Command line tool desctiptor

    :ivar executable:     full path of the tool executable or just the
                          tool program name if it is in the system
                          search path
    :ivar cwd:            program working directory
    :ivar env:            environment
    :ivar stdout_handler: the OutputHandler for the stdout of the tool
    :ivar stderr_handler: the OutputHandler for the stderr of the tool

    .. todo:: shell

    '''

    def __init__(self, executable, args=None, cwd=None, env=None,
                 stdout_handler=None, stderr_handler=None):
        super(ToolDescriptor, self).__init__()
        self.executable = executable
        self.args = args
        self.cwd = cwd
        self.env = env
        self.shell = False  # @WARNING: shell proceses can't be stopped

        self.stdout_handler = stdout_handler
        self.stderr_handler = stderr_handler

    def get_args(self, *args, **kwargs):
        # @TODO: quoting
        parts = ['%s=%s' % (key, value) for key, value in kwargs.items()]
        if self.args:
            parts.extend(str(arg) for arg in self.args)
        parts.extend(str(arg) for arg in args)
        return parts

    def cmdline(self, *args, **kwargs):
        parts = [self.executable]
        parts.extend(self.get_args(*args, **kwargs))
        return parts

    def __str__(self):
        return ' '.join(self.cmdline())

    # @TODO: fix
    #~ self._shell = None      # @TODO: check shell property

    #~ def _get_shell(self):
        #~ return self._shell is not None

    #~ def _set_shell(self, shell):
        #~ if not shell:
            #~ self._shell = None
        #~ else:
            #~ if sys.platform[:3] == 'win':
                #~ self._shell = 'cmd /C "%s"'
            #~ else:
                #~ self._shell = 'sh -c "%s"'

    #~ shell = property(_get_shell, _set_shell)

    #~ def set_shellcmd(self, cmd):
        #~ self._shell = cmd

    #~ def _shellcmd_eval(self, cmd):
        #~ if '%s' in self._shell:
            #~ return self._shell % cmd
        #~ else:
            #~ return '%s "%s"' % (self._shell, cmd)


class GenericToolDescriptor(ToolDescriptor):
    '''Generic tool descriptor

    The command line can be entirely defined by means of arguments
    passed to the `cmdline` method.

    '''

    def cmdline(self, *args, **kwargs):
        '''Generate the complete command-line for the tool

        This method is meant to be used together with "subprocess"
        so the "comman-line" actually is a list of strings.

        If the executable attribute is not set (evaluate false) then
        the first non-keyword argument is considered to be the
        executable tool  name.

        The command line is build as follows::

          executable keword-arguments args

        If you need a command-line in single string form use something
        like::

          ' '.join(tooldescriptorinstance.cmdline(arg1, arg2, arg3))

        '''

        return self.get_args(*args, **kwargs)


class BaseToolController(object):
    '''Base class for controlling command line tools

    A tool controller runs an external tool in controlled way.
    The output of the child process is handled by the controller and,
    optionally, notifications can be achieved at sub-process
    termination.

    A tool controller also allow to stop the controlled process.

    '''

    def __init__(self, logger=None):
        super(BaseToolController, self).__init__()
        self.subprocess = None
        self._stopped = False

        self.tool = None

        if not logger:
            self.logger = logging.getLogger()
        else:
            self.logger = logger

    def finalize_run_hook(self):
        '''Hook method for extra finalization tasks

        This method is always called after finalization and before
        controller reset.

        The user can provide a custom implementation in derived classes
        in order to perform extra finalization actions.

        This method is not meant to be called from the user.

        '''

        pass

    def finalize_run(self, *args, **kwargs):
        '''Perform finalization actions

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
                    if self.tool.stdout_handler:
                        data = self.subprocess.recv()
                        while data:
                            self.tool.stdout_handler.feed(data)
                            data = self.subprocess.recv()
                    if self.tool.stderr_handler:
                        data = self.subprocess.recv_err()
                        while data:
                            self.tool.stderr_handler.feed(data)
                            data = self.subprocess.recv_err()
                else:
                    try:
                        if self.tool.stdout_handler:
                            data = self.subprocess.stdout.read()
                            self.tool.stdout_handler.feed(data)
                    except ValueError:
                        # I/O operation on closed file.
                        pass

                    try:
                        if self.tool.stderr_handler:
                            data = self.subprocess.stderr.read()
                            self.tool.stderr_handler.feed(data)
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
                if self.tool.stdout_handler:
                    self.tool.stdout_handler.close()
                if self.tool.stderr_handler:
                    self.tool.stderr_handler.close()

                if self.subprocess.returncode != EX_OK:
                    if self._stopped:
                        self.logger.info('Execution stopped by the user.')
                    else:
                        msg = ('Process (PID=%d) exited with return code %d.' %
                                               (self.subprocess.pid,
                                                self.subprocess.returncode))
                        self.logger.warning(msg)

                # Call finalize hook is available
                self.finalize_run_hook()
        finally:
            # Protect for unexpected errors in the feed and close methods of
            # the outputhandler
            self.reset_controller()

    def reset_controller(self):
        '''Reset the tool controller instance

        Kill the controlled subprocess and reset the controller
        instance losing all unprocessed data.

        '''

        if self.subprocess:
            self.subprocess.stop(force=True)

        assert (self.subprocess is None or
                self.subprocess.returncode is not None), \
                                        'the process is still running'

        if self.tool.stdout_handler:
            self.tool.stdout_handler.reset()
        if self.tool.stderr_handler:
            self.tool.stderr_handler.reset()

        self.subprocess = None
        self._stopped = False

    def prerun_hook(self, cmd):
        '''Hook method for extra pre-run actions

        This method is always called before the controlled subprocess
        is actually started.  The user can provide its own custom
        implementation in derived classes in order to perform
        additional actions.

        This method is not meant to be called from the user.

        '''

        if sys.platform[:3] == 'win':
            prompt = 'cmd >'
        else:
            prompt = '$'

        if not isinstance(cmd, basestring):
            cmd = ' '.join(cmd)

        self.logger.info('%s %s' % (prompt, cmd))

    def connect_output_handlers(self):
        pass

    def handle_stdout(self, *args):
        '''Handle standard output data

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
                self.tool.stdout_handler.feed(data)
            return True

    def handle_stderr(self, *args):
        '''Handle standard  error

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
                self.tool.stderr_handler.feed(data)
            return True

    def run_tool(self, *args):
        '''Run an external tool in controlled way

        The output of the child process is handled by the controller
        and, optionally, notifications can be achieved at sub-process
        termination.

        '''

        assert self.subprocess is None
        if sys.platform[:3] == 'win':
            closefds = False
            startupinfo = subprocess2.STARTUPINFO()
            startupinfo.dwFlags |= subprocess2.STARTF_USESHOWWINDOW
        else:
            closefds = True
            startupinfo = None

        if self.tool.stdout_handler:
            self.tool.stdout_handler.reset()
        # @TODO: check
        #if self.tool.stderr_handler:
        #    self.tool.stderr_handler.reset()
        cmd = self.tool.cmdline(*args)
        self.prerun_hook(*cmd)

        try:
            self.subprocess = subprocess2.Popen(cmd,
                                                stdin = subprocess2.PIPE,
                                                stdout = subprocess2.PIPE,
                                                stderr = subprocess2.STDOUT,
                                                cwd = self.tool.cwd,
                                                env = self.tool.env,
                                                close_fds = closefds,
                                                shell = self.tool.shell,
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

    def stop_tool(self, force=True):
        '''Stop the execution of controlled subprocess

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
            self._stopped = True
            stopped = self.subprocess.stop(force)
            if not stopped:
                msg = ('Unable to stop the sub-process (PID=%d).' %
                                                        self.subprocess.pid)
                self.logger.warning(msg)
                self.reset_controller()
            # The subprocess is successfully stopped.
            # The output handler will provide to the finalization
            # NOTE: return without reset
        else:
            self.reset_controller()


if(__name__ == '__main__'):
    import time

    class DummyToolController(BaseToolController):

        def connect_output_handlers(self):
            while self.subprocess:
                self.handle_stdout()
                time.sleep(0.1)

    h = BaseOutputHandler(OFStream())
    h.feed('\rline\n')
    h.feed('\r-')
    h.feed(' \r/')
    h.feed('\r \\')
    h.feed('\r| ')
    h.feed(' \r - ')

    h.feed('\rline\n')
    h.feed('\r12%')
    h.feed(' \r13%')
    h.feed('\r 14%')
    h.feed('\r15 %')
    h.feed('\r16% ')
    h.feed(' \r 17 % ')

    h.feed('\rline\n')
    h.feed('\r17.1%')
    h.feed(' \r17.2%')
    h.feed('\r 17.3%')
    h.feed('\r17.4 %')
    h.feed('\r17.5% ')
    h.feed(' \r 17.6 % ')

    h.feed('\rline\n')
    h.feed('\r-18%')
    h.feed(' \r/18%')
    h.feed('\r |18% ')
    h.feed('\r\\ 18%')
    h.feed('\r-18 %')
    h.feed('\r/18% ')
    h.feed(' \r   |   18 % ')

    h.feed('\rline\n')
    h.feed('\r-19.0%')
    h.feed(' \r/19.1%')
    h.feed('\r |19.2%')
    h.feed('\r\\ 19.3%')
    h.feed('\r-19.4 %')
    h.feed('\r/19.5% ')
    h.feed(' \r   |   19.5 % ')

    h.feed('\rline\n')
    h.feed('\relapsed time: 1')
    h.feed('\relapsed time: 2')
    h.feed('\relapsed time: 3')

    h.feed('\rline\n')
    h.feed('\r- 1.0% completed.')
    h.feed('\r/ 2.0% completed.')
    h.feed('\r| 3.0% completed.')
    h.feed('\r\\ 4.0% completed.')

    h.feed('\rdone\n')
    h.close()

    #~ import doctest
    #~ doctest.testmod()
