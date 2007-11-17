import re

import exectools
from exectools.qt4tools import Qt4OutputHandler

from PyQt4 import QtGui

class GdalAddOverviewDescriptor(exectools.ToolDescriptor):

    def __init__(self, cwd=None, env=None,
                 stdout_handler=None, stderr_handler=None):


        executable = 'gdaladdo'
        args = ['--config', 'USE_RRD', 'YES']
        super(GdalAddOverviewDescriptor, self).__init__(
                    executable, args, cwd, env, stdout_handler, stderr_handler)

class GdalOutputHandler(Qt4OutputHandler):
    '''int GDALTermProgress(double dfComplete,
                            const char *pszMessage,
                            void *pProgressArg)

    Simple progress report to terminal.

    This progress reporter prints simple progress report to the terminal
    window.
    The progress report generally looks something like this:

      "0...10...20...30...40...50...60...70...80...90...100 - done."

    Every 2.5% of progress another number or period is emitted.
    Note that GDALTermProgress() uses internal static data to keep track of
    the last percentage reported and will get confused if two terminal based
    progress reportings are active at the same time.

    The GDALTermProgress() function maintains an internal memory of the last
    percentage complete reported in a static variable, and this makes it
    unsuitable to have multiple GDALTermProgress()'s active eithin a single
    thread or across multiple threads.

    Parameters:
        dfComplete      completion ratio from 0.0 to 1.0.
        pszMessage      optional message.
        pProgressArg    ignored callback data argument.

    Returns:
        Always returns TRUE indicating the process should continue.

    '''

    def __init__(self, textview=None, statusbar=None, progressbar=None,
                 blinker=None):
        super(GdalOutputHandler, self).__init__(textview, statusbar,
                                                progressbar, blinker)
        #pattern = '(?P<percentage>\d{1,2})|(?P<pulse>\.)|((?P<text> - done\.?)$)'
        pattern = '(?P<percentage>\d{1,3})|(?P<pulse>\.)|((?P<text> - done\.?)$)'
        #pattern = '(?P<percentage>\d{2})|(?P<pulse>\.)|((?P<text>100 - done\.?)$)'
        self._progress_pattern = re.compile(pattern)
        self.percentage = 0.

    #~ def get_progress(self):
        #~ pos = self._buffer.tell()
        #~ data = self._buffer.read()
        #~ match = self._progress_pattern.match(data)
        #~ if match:
            #~ print match.groups()        # @TODO: remove
            #~ result = [match.group('pulse'),
                      #~ match.group('percentage'),
                      #~ match.group('text')]
            #~ if result == [None, None, None]:
                #~ result = None
        #~ else:
            #~ result = None

        #~ if result:
            #~ self._buffer.seek(pos+match.end())
        #~ else:
            #~ self._buffer.seek(pos)
            #~ return None

        #~ if result[1] is not None:
            #~ result[1] = float(result[1])
        #~ return result

    def handle_progress(self, data):
        pulse, percentage, text = data
        if pulse:
            if self.progressbar:
                assert percentage is None
                percentage = self.progressbar.value()
                percentage = min(100, percentage + 2.5)
        if percentage is not None:
            self._handle_percentage(percentage)
        if text and not pulse and percentage is None:
            if self.statusbar:
                self.statusbar.showMessage(text, self._statusbar_timeout)
        self._handle_pulse(pulse)
        QtGui.qApp.processEvents() # might slow too mutch

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
        print 'done.'

    #~ test_GdalOutputHandler_re()
    #~ test_GdalOutputHandler1()
    test_GdalOutputHandler2()
