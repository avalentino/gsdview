# -*- coding: utf-8 -*-

### Copyright (C) 2008-2012 Antonio Valentino <a_valentino@users.sf.net>

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


'''Site configuration module.

:DATADIR: system configuration, auxdata, images, etc.
:DOCSDIR: doumentation
:LICENSEFILE: license file
:SYSPLUGINSDIR: system plugins directory
:USERCONFIGDIR: user configuration directory (default `~/.gsdview`)

'''


import os
import sys


__all__ = ['DATADIR', 'DOCSDIR', 'LICENSEFILE', 'SYSPLUGINSDIR',
           'USERCONFIGDIR']


if not hasattr(sys, 'frozen'):
    # Source schema
    LIBDIR = os.path.abspath(os.path.dirname(__file__))
    GSDVIEWROOT = os.path.normpath(os.path.join(LIBDIR, os.pardir))
    SYSPLUGINSDIR = os.path.join(LIBDIR, 'plugins')
    del LIBDIR
else:
    if '_MEIPASS2' in os.environ:   # one-file temp's directory
        # @WARNING: this also happend in one-dir case
        GSDVIEWROOT = os.path.abspath(os.environ['_MEIPASS2'])
    else:   # one-dir
        GSDVIEWROOT = os.path.dirname(os.path.abspath(sys.executable))
    SYSPLUGINSDIR = os.path.join(GSDVIEWROOT, 'plugins')

DATADIR = GSDVIEWROOT
DOCSDIR = os.path.join(GSDVIEWROOT, 'doc')
LICENSEFILE = os.path.join(GSDVIEWROOT, 'LICENSE.txt')
USERCONFIGDIR = os.path.expanduser(os.path.join('~', '.gsdview'))

# @NOTE: Needed to locate GDAL executables in case of frozen app
# del GSDVIEWROOT
