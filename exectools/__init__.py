# -*- coding: utf-8 -*-

### Copyright (C) 2006-2011 Antonio Valentino <a_valentino@users.sf.net>

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


import re
import os
import sys
import logging
from cStringIO import StringIO


__author__ = 'Antonio Valentino <a_valentino@users.sf.net>'
__revision__ = '$Revision$'
__date__ = '$Date$'
__version__ = (0, 6, 5)

__all__ = ['EX_OK', 'PROGRESS', 'TAGS', 'level2tag',
           'BaseOutputHandler', 'BaseToolController', 'ToolDescriptor']

version = '.'.join(map(str, __version__)) + '+'

if sys.platform[:3] == 'win':
    EX_OK = 0
else:
    EX_OK = os.EX_OK

PROGRESS = 15
TAGS = ['error', 'warning', 'info', 'progress', 'debug', 'cmd']

_LEVEL2TAG = {
    logging.CRITICAL: 'error',
    logging.ERROR: 'error',
    logging.WARNING: 'warning',
    logging.INFO: 'info',
    PROGRESS: 'progress',
    logging.DEBUG: 'debug',
    logging.NOTSET: '',
}


def level2tag(level):
    # @TODO: intermediate levels
    return _LEVEL2TAG.get(level, '')


class BaseOutputHandler(object):
    '''Base class for output handlers'''

    def __init__(self, logger=None):
        super(BaseOutputHandler, self).__init__()
        self._buffer = StringIO()
        self._wpos = self._buffer.tell()

        if logger is None or isinstance(logger, basestring):
            self.logger = logging.getLogger(logger)
        else:
            # @TODO: remove assertion
            assert isinstance(logger, logging.Logger)
            self.logger = logger

        self.percentage_fmt = '%5.1f %%'
        self.handlers = ['progress', 'line']

        # NOTE: pulse, percentage and text are all optional. The regexp
        #       consumes the '\r' character in any case.
        pattern = ('[ \t]*'
                   '\r+'
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
        '''Reset the handler instance.

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
        '''Feed some data to the parser.

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
            result = {
                'pulse': match.group('pulse'),
                'percentage': match.group('percentage'),
                'text': match.group('text'),
                'rawdata': data,
            }
        else:
            result = None

        if result:
            self._buffer.seek(pos + match.end())
        else:
            self._buffer.seek(pos)
            return None

        if result['percentage'] is not None:
            result['percentage'] = float(result['percentage'])

        return result

    def get_line(self):
        '''Extract complete lines'''

        pos = self._buffer.tell()
        data = self._buffer.readline()
        if data and (data[-1] == '\n'):
            return data[:-1]  # remove '\n'
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
        '''Handle progress data.

        This method is not meant to be called by the user.

        The user, anyway, can provide a custom implementation in
        derived classes.

        :param data:
            a list containing an item for each named group in the
            "progress" regular expression: (pulse, percentage, text)
            for the default implementation.
            Each item can be None.

        '''

        pulse = data.get('pulse')
        percentage = data.get('percentage')
        text = data.get('text')

        result = []
        if pulse:
            result.append(pulse)
        if percentage is not None:
            result.append(self.percentage_fmt % percentage)
        if text:
            result.append(text)

        extra = {
            'tag': 'progress',
            'pulse': pulse,
            'percentage': percentage,
            'text': text,
        }

        self.logger.log(PROGRESS, ' '.join(result), extra=extra)

    def handle_line(self, data):
        '''Handle output lines.

        This method is not meant to be directly called by the user.

        The user, anyway, can provide a custom implementation in
        derived classes.

        :param data:
            an entire output line (including the trailing "end of line"
            character.

        '''

        for tag_name, pattern in self._text_patterns.items():
            match = pattern.search(data)
            if match:
                self.logger.info(data, extra={'tag': tag_name})
                break
        else:
            self.logger.info(data)


class ToolDescriptor(object):
    '''Command line tool desctiptor.

    A :class:`ToolDescriptor` instance describes a command line tool
    (:attr:`executable`), how to run it (:attr:`args`, :attr:`cwd`,
    :attr:`env`) and how to handle its output (:attr:`stdout_handler`,
    :attr:`stderr_handler`).

    Example::

        handler = BaseOutputHandler()
        ll = ToolDescriptor(executable='ls', args=['-l'],
                            stdout_handler=handler)
        controller.run_tool(ll)

        # In this case no executabe is set in the descriptor.
        cmd = ToolDescriptor(stdout_handler=handler)

        # The executable name is passed at execution time (first argument)
        controller.run_tool(cmd, 'ls', '-l')

    '''

    def __init__(self, executable, args=None, cwd=None, env=None,
                 stdout_handler=None, stderr_handler=None):
        '''
        :param executable:
            full path of the tool executable or just the tool program
            name if it is in the system search path
        :param args:
            default args for command (list of strings)
        :type args:
            list
        :param cwd:
            program working directory
        :param env:
            environment dictionary
        :param envmerge:
            if set to True (default) it is the :attr:`env` dictionaty is
            used to update the system environment
        :param stdout_handler:
            *OutputHandler* for the stdout of the tool
        :param stderr_handler:
            *OutputHandler* for the stderr of the tool

        .. seealso:: :class:`BaseOutputHandler`

        '''

        super(ToolDescriptor, self).__init__()

        #: full path of the tool executable or just the tool program name
        #  if it is in the system search path
        self.executable = executable

        #: default args for command
        self.args = args

        #: program working directory
        self.cwd = cwd

        #: if set to True (default) then the :attr:`env` dictionaty is used
        #: to update the system environment
        self.envmerge = True
        self._env = env

        #: is set to true the external too is executed in a system shell
        #:
        #: .. warning:: some implementation don't allow to stop a subprocess
        #:              executed via shell
        self.shell = False

        #: the *OutputHandler* for the stdout of the tool
        #:
        #: .. seealso:: :class:`BaseOutputHandler`
        self.stdout_handler = stdout_handler

        #: the *OutputHandler* for the stderr of the tool
        self.stderr_handler = stderr_handler

    def _getenv(self):
        if self.envmerge:
            env = os.environ.copy()
            if self._env:
                env.update(self._env)
            return env
        else:
            return self._env

    def _setenv(self, env):
        self._env = env

    env = property(_getenv, _setenv, doc='the tool environment')

    ## @COMPATIBILITY: property.setter nedds Python >= 2.6
    #@property
    #def env(self):
    #    if self.envmerge:
    #        env = os.environ.copy()
    #        if self._env:
    #            env.update(self._env)
    #        return env
    #    else:
    #        return self._env
    #
    #@env.setter
    #def env(self, env):
    #    self._env = env

    def cmdline(self, *args, **kwargs):
        '''Generate the complete command-line for the tool.

        This method is meant to be used together with "subprocess"
        so the "comman-line" actually is a list of strings.

        If the executable attribute is not set (evaluate false) then
        the first non-keyword argument is considered to be the
        executable tool name.

        The command line is build as follows::

          executable keyword-arguments args

        If you need a command-line in single string form use something
        like::

          ' '.join(tool.cmdline(arg1, arg2, arg3))

        '''

        if self.args is not None:
            args = list(self.args) + list(args)

        executable = self.executable
        if not executable:
            try:
                executable = args[0]
                args = args[1:]
            except IndexError:
                raise ValueError('"executable" not set')

        if isinstance(executable, basestring):
            parts = [executable]
        else:
            # handle cases like: executable = ['python', '-u', 'script.py']
            parts = list(executable)

        parts.extend('%s=%s' % (key, value) for key, value in kwargs.items())
        parts.extend(str(arg) for arg in args)

        return parts

    def __str__(self):
        return ' '.join(self.cmdline())


class BaseToolController(object):
    '''Base class for controlling command line tools.

    A tool controller runs an external tool in controlled way.
    The output of the child process is handled by the controller and,
    optionally, notifications can be achieved at sub-process
    termination.

    A tool controller also allows to stop the controlled process.

    .. note:: after the process termination the user can still query
              both :attr:`subprocess` and :attr:`stopped` for getting
              info about the executed process.

              The user should have care of calling :meth:`reset` when
              info n executed process are no more needed or before
              executing a new process.

    '''

    def __init__(self, logger=None):
        super(BaseToolController, self).__init__()

        #: the subprocess instance
        self.subprocess = None
        self._userstop = False

        self._tool = None

        if logger is None or isinstance(logger, basestring):
            self.logger = logging.getLogger(logger)
        else:
            assert isinstance(logger, logging.Logger)
            self.logger = logger

    @property
    def isbusy(self):
        '''If True then the controller is already running a subprocess.'''

        raise NotImplementedError('BaseToolController.busy')

    @property
    def userstop(self):
        '''If True the process has been stopped by the user.'''

        return self._userstop

    def finalize_run_hook(self):
        '''Hook method for extra finalization tasks.

        This method is always called after finalization and before
        controller reset.

        The user can provide a custom implementation in derived classes
        in order to perform extra finalization actions.

        This method is not meant to be called from the user.

        '''

        pass

    def finalize_run(self, *args, **kwargs):
        raise NotImplementedError('finalize_run')

    def _reset(self):
        '''Internal reset.

        Kill the controlled subprocess and reset I/O channels loosing
        all unprocessed data.

        '''

        if self._tool:
            if self._tool.stdout_handler:
                self._tool.stdout_handler.reset()
            if self._tool.stderr_handler:
                self._tool.stderr_handler.reset()

    def reset(self):
        '''Reset the tool controller instance'''

        self._reset()
        self._userstop = False
        self._tool = None

    def prerun_hook(self, cmd):
        '''Hook method for extra pre-run actions.

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

        self.logger.info('%s %s' % (prompt, cmd), extra={'tag': 'cmd'})

    def connect_output_handlers(self):
        pass

    def handle_stdout(self, *args):
        raise NotImplementedError('handle_stdout')

    def handle_stderr(self, *args):
        raise NotImplementedError('handle_stderr')

    def run_tool(self, tool, *args, **kwargs):
        raise NotImplementedError('run_tool')

    def stop_tool(self, force=True):
        raise NotImplementedError('stop_tool')


if(__name__ == '__main__'):
    import time

    logging.basicConfig(level=logging.DEBUG)

    class DummyToolController(BaseToolController):

        def connect_output_handlers(self):
            while self.subprocess:
                self.handle_stdout()
                time.sleep(0.1)

    h = BaseOutputHandler()
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
