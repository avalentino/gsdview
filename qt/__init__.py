# -*- coding: utf-8 -*-

# Copyright (c) 2006-2010 Enthought, Inc.
# Copyright (c) 2011-2015 Antonio Valentino <antonio.valentino@tiscali.it>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#  * Neither the name of copyright holder nor the names of its contributors may
#    be used to endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os


def prepare_pyqt4():
    # Set API version 2 (compatible with both PyQt5 and PySide)
    import sip

    sip.setapi('QDate', 2)
    sip.setapi('QDateTime', 2)
    sip.setapi('QString', 2)
    sip.setapi('QTextStream', 2)
    sip.setapi('QTime', 2)
    sip.setapi('QUrl', 2)
    sip.setapi('QVariant', 2)

qt_api = os.environ.get('QT_API')

if qt_api is None:
    try:
        import PyQt5
        qt_api = 'pyqt5'
    except ImportError:
        try:
            prepare_pyqt4()
            import PyQt4
            qt_api = 'pyqt4'
        except ImportError:
            try:
                import PySide
                qt_api = 'pyside'
            except ImportError:
                raise ImportError('Cannot import PyQt4 or PySide')

elif qt_api == 'pyqt4':
    prepare_pyqt4()

elif qt_api != 'pyside':
    raise RuntimeError('Invalid Qt API %r, valid values are: '
                       '"pyqt5", "pyqt4" or "pyside"' % qt_api)
