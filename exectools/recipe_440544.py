# Recipe 440554 from the Python Cookbok online:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/440554

'''
Title:          Module to allow Asynchronous subprocess use on Windows and
                Posix platforms
Submitter:      Josiah Carlson
Last Updated:   2006/12/01
Version no:     1.9
Category:       System

Description:

The 'subprocess' module in Python 2.4 has made creating and accessing
subprocess streams in Python relatively convenient for all supported platforms,
but what if you want to interact with the started subprocess? That is, what if
you want to send a command, read the response, and send a new command based on
that response?

Now there is a solution. The included subprocess.Popen subclass adds three new
commonly used methods: recv(maxsize=None), recv_err(maxsize=None), and
send(input), along with a utility method: send_recv(input='', maxsize=None).

recv() and recv_err() both read at most maxsize bytes from the started
subprocess.
send() sends strings to the started subprocess.
send_recv() will send the provided input, and read up to maxsize bytes from
both stdout and stderr.

If any of the pipes are closed, the attributes for those pipes will be set to
None, and the methods will return None.

v. 1.3      fixed a few bugs relating to *nix support
v. 1.4,5    fixed initialization on all platforms, a few bugs relating to
            Windows support, added two utility functions, and added an example
            of how to use this module.
v. 1.6      fixed linux _recv() and test initialization thanks to Yuri
            Takhteyev at Stanford.
v. 1.7      removed _setup() and __init__() and fixed subprocess unittests
            thanks to Antonio Valentino. Added 4th argument 'tr' to
            recv_some(), which is, approximately, the number of times it will
            attempt to recieve data. Added 5th argument 'stderr' to
            recv_some(), where when true, will recieve from stderr.
            Cleaned up some pipe closing.
v. 1.8      Fixed missing self. parameter in non-windows _recv method thanks
            to comment.
v. 1.9      Fixed fcntl calls for closed handles.

'''

from __future__ import print_function

import os
import subprocess
import errno
import time
import sys

PIPE = subprocess.PIPE

if subprocess.mswindows:
    from win32file import ReadFile, WriteFile
    from win32pipe import PeekNamedPipe
    import msvcrt
else:
    import select
    import fcntl

class Popen(subprocess.Popen):
    def recv(self, maxsize=None):
        return self._recv('stdout', maxsize)

    def recv_err(self, maxsize=None):
        return self._recv('stderr', maxsize)

    def send_recv(self, input='', maxsize=None):
        return self.send(input), self.recv(maxsize), self.recv_err(maxsize)

    def get_conn_maxsize(self, which, maxsize):
        if maxsize is None:
            maxsize = 1024
        elif maxsize < 1:
            maxsize = 1
        return getattr(self, which), maxsize

    def _close(self, which):
        getattr(self, which).close()
        setattr(self, which, None)

    if subprocess.mswindows:
        def send(self, input):
            if not self.stdin:
                return None

            try:
                x = msvcrt.get_osfhandle(self.stdin.fileno())
                (errCode, written) = WriteFile(x, input)
            except ValueError:
                return self._close('stdin')
            except (subprocess.pywintypes.error, Exception) as why:
                if why[0] in (109, errno.ESHUTDOWN):
                    return self._close('stdin')
                raise

            return written

        def _recv(self, which, maxsize):
            conn, maxsize = self.get_conn_maxsize(which, maxsize)
            if conn is None:
                return None

            try:
                x = msvcrt.get_osfhandle(conn.fileno())
                (read, nAvail, nMessage) = PeekNamedPipe(x, 0)
                if maxsize < nAvail:
                    nAvail = maxsize
                if nAvail > 0:
                    (errCode, read) = ReadFile(x, nAvail, None)
            except ValueError:
                return self._close(which)
            except (subprocess.pywintypes.error, Exception) as why:
                if why[0] in (109, errno.ESHUTDOWN):
                    return self._close(which)
                raise

            if self.universal_newlines:
                read = self._translate_newlines(read)
            return read

    else:
        def send(self, input):
            if not self.stdin:
                return None

            if not select.select([], [self.stdin], [], 0)[1]:
                return 0

            try:
                written = os.write(self.stdin.fileno(), input)
            except OSError as why:
                if why[0] == errno.EPIPE:  # broken pipe
                    return self._close('stdin')
                raise

            return written

        def _recv(self, which, maxsize):
            conn, maxsize = self.get_conn_maxsize(which, maxsize)
            if conn is None:
                return None

            flags = fcntl.fcntl(conn, fcntl.F_GETFL)
            if not conn.closed:
                fcntl.fcntl(conn, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            try:
                if not select.select([conn], [], [], 0)[0]:
                    return ''

                r = conn.read(maxsize)
                if not r:
                    return self._close(which)

                if self.universal_newlines:
                    r = self._translate_newlines(r)
                return r
            finally:
                if not conn.closed:
                    fcntl.fcntl(conn, fcntl.F_SETFL, flags)

message = "Other end disconnected!"


def recv_some(p, t=.1, e=1, tr=5, stderr=0):
    if tr < 1:
        tr = 1
    x = time.time() + t
    y = []
    r = ''
    pr = p.recv
    if stderr:
        pr = p.recv_err
    while time.time() < x or r:
        r = pr()
        if r is None:
            if e:
                raise Exception(message)
            else:
                break
        elif r:
            y.append(r)
        else:
            time.sleep(max((x - time.time()) / tr, 0))
    return ''.join(y)


def send_all(p, data):
    while len(data):
        sent = p.send(data)
        if sent is None:
            raise Exception(message)
        try:
            data = buffer(data, sent)
        except Exception:
            data = data[sent:]

if __name__ == '__main__':
    if sys.platform == 'win32':
        shell, commands, tail = ('cmd', ('dir /w', 'echo HELLO WORLD'), '\r\n')
    else:
        shell, commands, tail = ('sh', ('ls', 'echo HELLO WORLD'), '\n')

    a = Popen(shell, stdin=PIPE, stdout=PIPE)
    print(recv_some(a), end=' ')
    for cmd in commands:
        send_all(a, cmd + tail)
        print(recv_some(a), end=' ')
    send_all(a, 'exit' + tail)
    print(recv_some(a, e=0))
    a.wait()
