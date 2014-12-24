# -*- coding: utf-8 -*-

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
