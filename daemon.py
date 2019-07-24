import os
import fcntl
import errno
import time

__all__ = ["DaemonAlreadyRunning", "PidFile", "daemon"]

class DaemonAlreadyRunning(Exception):
    def __init__(self, otherpid):
        Exception.__init__(self)
        self.otherpid = otherpid

class PidFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.opened = False
        self.fd = None

    def __del__(self):
        pass

    def open(self, mode):
        fd = os.open(self.filename, os.O_WRONLY | os.O_CREAT, mode)
        if fd == -1:
            raise OSError()
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError as e:
                if e.errno == errno.EWOULDBLOCK:
                    for _ in range(3):
                        otherpid = self._read(self.filename)
                        if otherpid:
                            raise DaemonAlreadyRunning(otherpid)
                        time.sleep(0.005)
                raise
            os.ftruncate(fd, 0)
        except Exception as e:
            os.close(fd)
            raise
        self.fd = fd
        self.opened = True

    def write(self):
        os.ftruncate(self.fd, 0)
        os.write(self.fd, "%d" % (os.getpid(),))

    def close(self):
        if not self.opened:
            return
        os.close(self.fd)
        self.opened = False

    def remove(self):
        if not self.opened:
            return
        os.unlink(self.filename)
        os.close(self.fd)
        self.opened = False

    @staticmethod
    def _read(filename):
        f = file(filename, "r")
        s = f.read()
        return int(s) if s else None

def daemon(nochdir=False, noclose=False):
    if os.fork():
        os._exit(0) # pylint: disable=protected-access
    os.setsid()
    if os.fork():
        os._exit(0) # pylint: disable=protected-access
    if not nochdir:
        os.chdir('/')
    if not noclose:
        null = os.open('/dev/null', os.O_RDWR)
        for i in range(3):
            try:
                os.dup2(null, i)
            except OSError as e:
                if e.errno != errno.EBADF:
                    raise
        os.close(null)
