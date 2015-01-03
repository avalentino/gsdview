# -*- coding: utf-8 -*-

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


from . import qt_api

if qt_api == 'pyqt5':
    from PyQt5.uic import *

elif qt_api == 'pyqt4':
    from PyQt4.uic import *

elif qt_api == 'pyside':
    from pysideuic import *

    # Credit:
    # http://stackoverflow.com/questions/7144313/loading-qtdesigners-ui-files-in-pyside
    def loadUi(uifilename, parent=None):
        '''Load a Qt Designer .ui file and return an instance of
        the user interface.'''

        from PySide import QtCore, QtUiTools

        loader = QtUiTools.QUiLoader()
        uifile = QtCore.QFile(uifilename)
        uifile.open(QtCore.QFile.ReadOnly)
        ui = loader.load(uifile, parent)
        uifile.close()

        return ui

    # Credit:
    # http://stackoverflow.com/questions/4442286/python-code-genration-with-pyside-uic/14195313#14195313
    def loadUiType(uifile):
        """Load a Qt Designer .ui file and return the generated form
        class and the Qt base class.

        Pyside "loadUiType" command like PyQt4 has one, so we have to
        convert the ui file to py code in-memory first and then
        execute it in a special frame to retrieve the form_class.

        """

        # @COMPATIBILITY: Python 2
        import sys
        if sys.version_info >= (3, 0):
            from io import StringIO
        else:
            from io import BytesIO as StringIO
        import xml.etree.ElementTree as xml
        from PySide import QtGui    # NOQA

        parsed = xml.parse(uifile)
        widget_class = parsed.find('widget').get('class')
        form_class = parsed.find('class').text

        with open(uifile, 'r') as f:
            o = StringIO()
            frame = {}

            compileUi(f, o, indent=0)
            pyc = compile(o.getvalue(), '<string>', 'exec')
            exec(pyc, frame)

            # Fetch the base_class and form class based on their type in the
            # xml from designer
            form_class = frame['Ui_%s' % form_class]
            base_class = eval('QtGui.%s' % widget_class)

        return form_class, base_class
