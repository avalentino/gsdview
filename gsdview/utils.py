# -*- coding: utf-8 -*-

### Copyright (C) 2008-2010 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of GSDView.

### GSDView is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### GSDView is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with GSDView; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA.


'''Utility functions and classes for GSDView.'''

__author__   = '$Author$'
__date__     = '$Date$'
__revision__ = '$Revision$'

__all__ = ['getresource']

import os
import sys
import stat
import platform
import traceback
import email.utils

try:
    import pkg_resources
except ImportError:
    import logging
    logging.getLogger('gsdview').debug('"pkg_resources" not found.')

from gsdview import info
from gsdview import appsite

def default_workdir():
    if sys.platform[:3] == 'win':
        return 'C:\\'
    else:
        return os.path.expanduser('~')

def _getresource(resource, package):
    try:
        return pkg_resources.resource_filename(package, resource)
    except NameError:
        # pkg_resources not available
        if '.' in package:
            fromlist = package.split('.')[:-1]
            # @WARNING: (pychecker) Function (__import__) doesn't support **kwArgs
            m = __import__(package, fromlist=fromlist)
        else:
            m = __import__(package)
        datadir = os.path.dirname(os.path.abspath(m.__file__))
        return os.path.join(datadir, resource)


def getresource(resource, package=None):
    '''Return the resurce path.

    If `package` is specified (usually passing `__name__` of the called
    modile) the package resource name is returned.

    If no `package` is specified then it is assumed that resource is
    located in the common resource directory (e.g.
    `/usr/share/<PROJECTNAME>` on UNIX-like systems.

    .. note:: it is safe to use this function also if the package is
              distributed as a compressed *egg* or as standalon package
              generated using `pyinstaller <http://www.pyinstaller.org>`_.

    '''

    if package:
        if not hasattr(sys, 'frozen'):   # not packed
            return _getresource(resource, package)
        else:
            m = __import__(package)
            #if '.pyz' not in m.__file__:
            if os.path.exists(m.__file__):
                return _getresource(resource, package)
            else:
                datadir = appsite.DATADIR
    else:
        datadir = appsite.DATADIR

    return os.path.join(datadir, resource)


def format_platform_info():
    platform_info = ['architecture: %s %s\n' % platform.architecture()]
    platform_info.append('platform: %s' % platform.platform())
    libc_ver = '%s %s\n' % platform.libc_ver()
    if libc_ver.strip():
        platform_info.append(libc_ver)

    #~ mac_ver(): ('', ('', '', ''), '')
    #~ win32_ver(): ('', '', '', '')

    platform_info.append('python_compiler: %s\n' % platform.python_compiler())
    platform_info.append('python_implementation: %s\n' %
                                            platform.python_implementation())

    return platform_info


def foramt_bugreport(exctype=None, excvalue=None, tracebackobj=None):
    if (exctype, excvalue, tracebackobj) == (None, None, None):
        exctype, excvalue, tracebackobj = sys.exc_info()

    separator = '-' * 80 + '\n'
    timestamp = email.utils.formatdate(localtime=True)+'\n'

    msg = [timestamp, separator]
    msg.extend(traceback.format_exception_only(exctype, excvalue))
    msg.append(separator)
    msg.append('Traceback:\n')
    msg.extend(traceback.format_tb(tracebackobj))
    msg.append(separator)
    msg.extend(info.all_versions_str().splitlines(True))
    msg[-1] = msg[-1] + '\n'
    msg.extend(format_platform_info())

    return msg


if sys.platform[:3] == 'win':
    def isexecutable(cmd):
        '''Check if "cmd" actually is an executable program.'''

        cmd = cmd.lower()
        if os.path.isfile(cmd) and cmd.endswith(('.exe', '.bat')):
            return True
        for ext in '.exe', '.bat':
            if os.path.isfile(cmd + ext):
                return True
        return False
else:
    def isexecutable(cmd):
        '''Check if "cmd" actually is an executable program.'''

        if os.path.isfile(cmd):
            mode = os.stat(cmd)[stat.ST_MODE]
            if ((mode & stat.S_IXUSR) or (mode & stat.S_IXGRP) or
                                                    (mode & stat.S_IXOTH)):
                return True
        return False


def which(cmd, env=None):
    '''Return the full path of the program (cnd) or None.

    >>> which('ls')
    '/bin/ls'

    '''

    if not env:
        env = os.environ

    for dir_ in env.get('PATH', '').split(os.pathsep):
        exe = os.path.join(dir_, cmd)
        if isexecutable(exe):
            return exe
