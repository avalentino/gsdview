# -*- coding: utf-8 -*-

### Copyright (C) 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>

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

'''Python 2/3 compatibility module

Replicates some of the features of six.

'''

import sys


PY2 = sys.version_info < (3, 0)
PY3 = not PY2

# strings
if PY2:
    string_types = (basestring,)
else:
    string_types = (str,)

# callable
try:
    callable = callable
except NameError:
    from collections import Callable as _Callable

    def callable(obj):
        return isinstance(obj, _Callable)
