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


from . import qt_api

__all__ = [
    #'QAbstractOpenGLFunctions',
    'QAbstractTextDocumentLayout',
    'QActionEvent',
    #'QBackingStore',
    'QBitmap',
    'QBrush',
    'QClipboard',
    'QCloseEvent',
    'QColor',
    'QConicalGradient',
    'QContextMenuEvent',
    'QCursor',
    'QDesktopServices',
    'QDoubleValidator',
    'QDrag',
    'QDragEnterEvent',
    'QDragLeaveEvent',
    'QDragMoveEvent',
    'QDropEvent',
    #'QEnterEvent',
    #'QExposeEvent',
    'QFileOpenEvent',
    'QFocusEvent',
    'QFont',
    'QFontDatabase',
    'QFontInfo',
    'QFontMetrics',
    'QFontMetricsF',
    #'QGlyphRun',               # not available in pyside
    'QGradient',
    #'QGuiApplication',
    'QHelpEvent',
    'QHideEvent',
    'QHoverEvent',
    'QIcon',
    'QIconDragEvent',
    'QIconEngine',
    'QImage',
    'QImageIOHandler',
    'QImageReader',
    'QImageWriter',
    'QInputEvent',
    #'QInputMethod',
    'QInputMethodEvent',
    #'QInputMethodQueryEvent',
    'QIntValidator',
    'QKeyEvent',
    'QKeySequence',
    'QLinearGradient',
    'QMatrix2x2',
    'QMatrix2x3',
    'QMatrix2x4',
    'QMatrix3x2',
    'QMatrix3x3',
    'QMatrix3x4',
    'QMatrix4x2',
    'QMatrix4x3',
    'QMatrix4x4',
    'QMouseEvent',
    'QMoveEvent',
    'QMovie',
    #'QNativeGestureEvent',
    #'QOffscreenSurface',
    #'QOpenGLBuffer',
    #'QOpenGLContext',
    #'QOpenGLContextGroup',
    #'QOpenGLDebugLogger',
    #'QOpenGLDebugMessage',
    #'QOpenGLFramebufferObject',
    #'QOpenGLFramebufferObjectFormat',
    #'QOpenGLPaintDevice',
    #'QOpenGLPixelTransferOptions',
    #'QOpenGLShader',
    #'QOpenGLShaderProgram',
    #'QOpenGLTexture',
    #'QOpenGLTimeMonitor',
    #'QOpenGLTimerQuery',
    #'QOpenGLVersionProfile',
    #'QOpenGLVertexArrayObject',
    #'QPageLayout',
    #'QPageSize',
    #'QPagedPaintDevice',
    'QPaintDevice',
    'QPaintEngine',
    'QPaintEngineState',
    'QPaintEvent',
    'QPainter',
    'QPainterPath',
    'QPainterPathStroker',
    'QPalette',
    #'QPdfWriter',
    'QPen',
    'QPicture',
    'QPictureIO',
    'QPixmap',
    'QPixmapCache',
    'QPolygon',
    'QPolygonF',
    'QQuaternion',
    'QRadialGradient',
    #'QRawFont',                # not available in pyside
    'QRegExpValidator',
    'QRegion',
    #'QRegularExpressionValidator',
    'QResizeEvent',
    #'QScreen',
    #'QScrollEvent',
    #'QScrollPrepareEvent',
    'QSessionManager',
    'QShortcutEvent',
    'QShowEvent',
    'QStandardItem',
    'QStandardItemModel',
    #'QStaticText',             # not available in pyside
    'QStatusTipEvent',
    #'QStyleHints',
    #'QSurface',
    #'QSurfaceFormat',
    'QSyntaxHighlighter',
    'QTabletEvent',
    'QTextBlock',
    'QTextBlockFormat',
    'QTextBlockGroup',
    'QTextBlockUserData',
    'QTextCharFormat',
    'QTextCursor',
    'QTextDocument',
    'QTextDocumentFragment',
    #'QTextDocumentWriter',     # not available in pyside
    'QTextFormat',
    'QTextFragment',
    'QTextFrame',
    'QTextFrameFormat',
    'QTextImageFormat',
    'QTextInlineObject',
    'QTextItem',
    'QTextLayout',
    'QTextLength',
    'QTextLine',
    'QTextList',
    'QTextListFormat',
    'QTextObject',
    'QTextObjectInterface',
    'QTextOption',
    'QTextTable',
    'QTextTableCell',
    'QTextTableCellFormat',
    'QTextTableFormat',
    #'QTouchDevice',
    'QTouchEvent',
    'QTransform',
    'QValidator',
    'QVector2D',
    'QVector3D',
    'QVector4D',
    'QWhatsThisClickedEvent',
    'QWheelEvent',
    #'QWindow',
    'QWindowStateChangeEvent',
    'qAlpha',
    'qBlue',
    #'qFuzzyCompare',           # not available in pyside
    'qGray',
    'qGreen',
    'qIsGray',
    #'qPremultiply',
    'qRed',
    'qRgb',
    'qRgba',
    #'qUnpremultiply',
]

if qt_api == 'pyqt5':
    from PyQt5.QtGui import *

elif qt_api == 'pyqt4':
    import PyQt4.QtGui as _QtGui
    locals().update(dict((name, getattr(_QtGui, name)) for name in __all__))
    del _QtGui

elif qt_api == 'pyside':
    import PySide.QtGui as _QtGui
    locals().update(dict((name, getattr(_QtGui, name)) for name in __all__))
    del _QtGui
