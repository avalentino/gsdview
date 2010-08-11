# -*- coding: utf-8 -*-

# Select the PyQt API 2
import sip
sip.setapi('QDate',       2)
sip.setapi('QDateTime',   2)
sip.setapi('QString',     2)
sip.setapi('QTextStream', 2)
sip.setapi('QTime',       2)
sip.setapi('QUrl',        2)
sip.setapi('QVariant',    2)

from gsdview.info import *
from gsdview.launch import main
