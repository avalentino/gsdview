### Copyright (C) 2008-2009 Antonio Valentino <a_valentino@users.sf.net>

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

'''Custom exectools components for GDAL.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import re

import exectools
from exectools.qt4tools import Qt4OutputHandler

from PyQt4 import QtGui


class GdalAddOverviewDescriptor(exectools.ToolDescriptor):

    def __init__(self, cwd=None, env=None,
                 stdout_handler=None, stderr_handler=None):


        executable = 'gdaladdo'
        args = []
        #args.extend(['--config', 'USE_RRD', 'YES'])
        args.extend(['-r', 'average'])
        super(GdalAddOverviewDescriptor, self).__init__(
                    executable, args, cwd, env, stdout_handler, stderr_handler)

class GdalOutputHandler(Qt4OutputHandler):
    '''Handler for the GDAL simple progress report to terminal.

    This progress reporter prints simple progress report to the terminal
    window.  The progress report generally looks something like this:

      "0...10...20...30...40...50...60...70...80...90...100 - done."

    Every 2.5% of progress another number or period is emitted.

    '''

    def __init__(self, textview=None, statusbar=None, progressbar=None,
                 blinker=None):
        super(GdalOutputHandler, self).__init__(textview, statusbar,
                                                progressbar, blinker)
        #pattern = '(?P<percentage>\d{1,3})|(?P<pulse>\.)|((?P<text> - done\.?)$)'
        pattern = '(?P<percentage>\d{1,3})|(?P<pulse>\.)|( - (?P<text>done\.?)\n)'
        self._progress_pattern = re.compile(pattern)
        self.percentage = 0.    # @TODO: remove.  Set the progressbar maximum
                                #        to 1000 instead.

    def handle_progress(self, data):
        pulse, percentage, text = data
        if pulse:
            if self.progressbar:
                self.percentage = min(100, self.percentage + 2.5)
                self._handle_percentage(self.percentage)
        if percentage is not None:
            assert percentage >= self.percentage, 'percentage = %d, ' \
                        'self.percentage = %f' % (percentage, self.percentage)

            self.percentage = percentage
            self._handle_percentage(percentage)
        if text and not pulse and percentage is None:
            self.percentage = 0.
            if self.statusbar:
                self.statusbar.showMessage(text, self._statusbar_timeout)
        self._handle_pulse(pulse)
        QtGui.qApp.processEvents() # might slow too mutch

    def reset(self):
        super(GdalOutputHandler, self).reset()
        self.percentage = 0.

if __name__ == '__main__':
    def test_GdalOutputHandler_re():
        s = '0...10...20...30...40...50...60...70...80...90...100 - done.\n'
        import exectools
        h = exectools.BaseOutputHandler(exectools.OFStream())
        h._progress_pattern = GdalOutputHandler()._progress_pattern
        h.feed(s)
        h.close()
        print 'done.'

    def test_GdalOutputHandler1():
        s = '0...10...20...30...40...50...60...70...80...90...100 - done.\n'
        import exectools
        class C(GdalOutputHandler):
            def __init__(self):
                exectools.BaseOutputHandler.__init__(self, exectools.OFStream())
            def feed(self, data):
                return exectools.BaseOutputHandler.feed(self, data)
            def close(self):
                return exectools.BaseOutputHandler.close(self)
            def reset(self):
                return exectools.BaseOutputHandler.reset(self)
            def handle_progress(self, data):
                return exectools.BaseOutputHandler.handle_progress(self, data)
        h = C()
        h.feed(s)
        h.close()
        print 'done.'

    def test_GdalOutputHandler2():
        s = '0...10...20...30...40...50...60...70...80...90...100 - done.\n'
        import exectools
        h = exectools.BaseOutputHandler(exectools.OFStream())
        h._progress_pattern = GdalOutputHandler()._progress_pattern
        for c in s:
            h.feed(c)
        h.close()

    #~ test_GdalOutputHandler_re()
    #~ test_GdalOutputHandler1()
    test_GdalOutputHandler2()
