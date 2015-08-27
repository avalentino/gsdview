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


'''Utility functions and classes for GSDView.'''


import os
import sys
import stat
import locale
import platform
import traceback
import email.utils  # @TODO: check

try:
    import pkg_resources
except ImportError:
    import logging
    logging.getLogger(__name__).debug('"pkg_resources" not found.')

from gsdview import info
from gsdview import appsite


__all__ = [
    'which', 'isexecutable', 'isscript', 'scriptcmd', 'default_workdir',
    'getresource', 'format_platform_info', 'format_bugreport',
]


def default_workdir():
    '''Return the defaut workinhg directory.'''

    if sys.platform[:3] == 'win':
        return 'C:\\'
        #return QtGui.QDesktopServices.storageLocation(
        #                           QtGui.QDesktopServices.DocumentsLocation)
    else:
        return os.path.expanduser('~')


def _getresource(resource, package):
    try:
        return pkg_resources.resource_filename(package, resource)
    except NameError:
        # pkg_resources not available
        if '.' in package:
            fromlist = package.split('.')[:-1]
            # @WARNING: (pychecker) Function (__import__) doesn't
            #           support **kwArgs
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
    platform_info = [
        'architecture: %s %s\n' % platform.architecture(),
        'machine: %s\n' % platform.machine(),
        'platform: %s\n' % platform.platform(),
    ]
    libc_ver = '%s %s\n' % platform.libc_ver()
    if libc_ver.strip():
        platform_info.append(libc_ver)

    if platform.dist() != ('', '', ''):
        platform_info.append('GNU/Linux: %s\n' % ' '.join(platform.dist()))
    elif platform.mac_ver() != ('', ('', '', ''), ''):
        platform_info.append('Mac OS X: %s\n' % platform.mac_ver()[0])
    elif platform.win32_ver() != ('', '', '', ''):
        platform_info.append('Windows: %s\n' % platform.win32_ver()[0])

    platform_info.append('python_compiler: %s\n' % platform.python_compiler())
    platform_info.append(
        'python_implementation: %s\n' % platform.python_implementation())

    platform_info.append('locale: %s\n' % (locale.getlocale(),))
    platform_info.append('default encoding: %s\n' % sys.getdefaultencoding())
    platform_info.append('file system encoding: %s\n' % sys.getfilesystemencoding())

    return platform_info


def format_bugreport(exctype=None, excvalue=None, tracebackobj=None,
                     extra_info=None):
    if (exctype, excvalue, tracebackobj) == (None, None, None):
        exctype, excvalue, tracebackobj = sys.exc_info()

    separator = '-' * 80 + '\n'
    timestamp = email.utils.formatdate(localtime=True) + '\n'

    msg = [timestamp, separator]
    msg.extend(traceback.format_exception_only(exctype, excvalue))
    msg.append(separator)
    msg.append('Traceback:\n')
    msg.extend(traceback.format_tb(tracebackobj))
    msg.append(separator)
    msg.extend(info.all_versions_str().splitlines(True))
    msg[-1] = msg[-1] + '\n'
    msg.extend(format_platform_info())
    if extra_info:
        msg.extend(extra_info)

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
    '''Return the full path of the program (*cmd*) or None.

    >>> which('ls')
    '/bin/ls'

    '''

    if not env:
        env = os.environ

    for dir_ in env.get('PATH', '').split(os.pathsep):
        exe = os.path.join(dir_, cmd)
        if isexecutable(exe):
            return exe


def isscript(filename):
    '''Check if a file is a script.'''

    try:
        return open(filename, 'rb').read(2) == '#!'
    except IOError:
        return False


def scriptcmd(scriptname):
    '''Return the list of args for starting the script via subprocess.

    On unix platforms the shebang string is used so almost all
    scripting languages are recognized.

    On windows platforms this function only works with batch files and
    python scripts.

    .. note:: if the *scriptname* is not recognized to be a script
              it is assumed it is a binary executable so the only
              argument in the returned list will be *scriptname*
              itself.

    :param scriptname:
        the filename of the script
    :returns:
        a list of strings containing the command line arguments for
        startting the program via subprocess

    '''

    cmd = [scriptname]
    if sys.platform.startswith('win'):
        ext = os.path.splitext(scriptname)[-1]
        ext = ext.lower()
        if ext == '.bat':
            comspec = os.environ.get('COMSPEC', 'cmd.exe')
            cmd = [comspec, '/c', scriptname]
        elif ext in ('.py', '.pyc', '.pyo', '.pyw'):
            # @WARNING: this doesn't work in case of frozen executables
            #cmd = [sys.executable, '-u', scriptname] # no buffering
            cmd = [sys.executable, scriptname]
    else:
        with open(scriptname, 'rb') as fd:
            shebang = fd.readline().rstrip()
            if shebang.startswith('#!'):
                cmd = shebang[2:].split() + scriptname

    return cmd


# Geographic tools ##########################################################
# @TODO: support vectors
def geonormalize(x, angle_range=360.):
    '''Normalize angles to fit expected range

    Example: (-180, 180) --> (0, 360)

    '''

    halfrange = angle_range / 2.
    if -halfrange <= x <= halfrange:
        x = x % angle_range
    if x > halfrange:
        x -= angle_range

    return x
