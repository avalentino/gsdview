#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GSDView - Geo-Spatial Data Viewer
# Copyright (C) 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>
#
# This module is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 2 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this module if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  US

from __future__ import print_function

import os
import sys
import time
import signal
import optparse
import warnings

# register the signal handlers
sigmap = dict()
for signame in ('SIGINT', 'SIGQUIT', 'SIGTERM'):
    if hasattr(signal, signame):
        sigmap[getattr(signal, signame)] = signame


def handler(signum, frame):
    print()
    print('%s (%d) signal trapped' % (sigmap[signum], signum))
    print('Now exit the program.')
    sys.exit(signum)

for sig_id in sigmap:
    signal.signal(sig_id, handler)

# parse the command line arguments
parser = optparse.OptionParser()
parser.add_option('-m', '--mode', dest='mode', default='percentage',
                  choices=['elapsed', 'percentage', 'pulse', 'mixed'],
                  help='select the execution mode (elapsed, percentage, '
                  'pulse, mixed)')
parser.add_option('-d', '--duration', action='store', type='float',
                  dest='duration', default=3.,
                  help='specify the duration of the run')
parser.add_option('-r', '--refresh-rate', action='store', type='float',
                  dest='refresh_rate', default=None,
                  help='specify the refresh rate')
parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                  help='set the verbose mode')
(options, args) = parser.parse_args()

mode = options.mode
duration = options.duration
if duration < 0:
    if mode in ('percentage', 'mixed'):
        warnings.warn('mode "%s" not supported for infinite loop' % mode)
        mode = 'elapsed'

refresh_rate_defaults = {
    'elapsed': .5,
    'percentage': .05,
    'pulse': .05,
    'mixed': .05,
}
refresh_rate = options.refresh_rate
if refresh_rate is None:
    refresh_rate = refresh_rate_defaults[mode]
assert(refresh_rate > 0), 'invalid refresh_rate'

verbose = options.verbose

print('PID =', os.getpid())
print('mode = "%s"' % mode)
if duration < 0:
    print('duration = infinite')
else:
    print('duration =', duration)

pulses = '-/|\\'
t0 = time.time()
elapsed = 0.
percentage = 0.
index = 0
while duration < 0 or elapsed < duration:
    if mode == 'percentage':
        print('\r  %6.2f%%' % percentage, end=' ')
    elif mode == 'pulse':
        print('\r%s' % pulses[index % len(pulses)], end=' ')
    elif mode == 'mixed':
        if (index % 4) == 0:
            print('\r%s %6.2f%%' % (pulses[index % len(pulses)], percentage),
                  end=' ')
        else:
            print('\r%s' % pulses[index % len(pulses)], end=' ')
    else:  # 'elapsed'
        print('\r%.2f' % elapsed, end=' ')
    if verbose:
        print()
    index += 1
    time.sleep(refresh_rate)
    elapsed = time.time() - t0
    percentage = min(100., 100. * elapsed / duration)
    sys.stdout.flush()

if mode in ('percentage', 'mixed'):
    print('\r  %6.2f%%' % 100.)
elif not verbose:
    if mode == 'elapsed':
        print()
    elif mode == 'pulse':
        sys.stdout.write('\r')

print('done.')
