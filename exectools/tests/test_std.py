#!/usr/bin/env python

import logging
import exectools, exectools.std


logging.basicConfig(level=logging.DEBUG, format='%(message)s')

echo = exectools.ToolDescriptor(
    'echo', stdout_handler=exectools.BaseOutputHandler())

c = exectools.std.StdToolController()
c.run_tool(echo, 'ciao', 'ciao2')
c.finalize_run()
print(c.isbusy)
