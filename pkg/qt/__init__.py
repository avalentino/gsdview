def _prepare_pyqt4():
    # Set PySide compatible APIs.
    import sip

    sip.setapi('QDate', 2)
    sip.setapi('QDateTime', 2)
    sip.setapi('QString', 2)
    sip.setapi('QTextStream', 2)
    sip.setapi('QTime', 2)
    sip.setapi('QUrl', 2)
    sip.setapi('QVariant', 2)

_prepare_pyqt4()
import PyQt4

qt_api = 'pyqt'
