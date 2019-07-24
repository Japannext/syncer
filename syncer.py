import shlex
import subprocess
import time
import plistlib
import socket
from threading import Thread, Event
import logging
import pyinotify

class WatchFiles(Thread):
    plist = None
    keepgoing = True
    jnxlog = logging.getLogger()
    jnxlog.setLevel(level=logging.INFO)

    def process_plist(self, plist_config):
        self.plist = plistlib.readPlist(plist_config)

    def __init__(self):
        Thread.__init__(self)
        self.doexit = Event()
        w_man = pyinotify.WatchManager()
        mask = pyinotify.IN_CLOSE_WRITE
        sftp = self.plist['SFTP']
        self.notifier = pyinotify.Notifier(w_man, RsyncInFiles(sftp['Hosts'], sftp['user']))
        for watchdirectory in self.plist['WatchDirectory']:
            w_man.add_watch(watchdirectory, mask, do_glob=True)

    def stop(self):
        self.doexit.set()
        self.join()

    def keep_going(self):
        return not self.doexit.isSet()

    def run(self):
        while self.keep_going():
            try:
                self.notifier.process_events()
                if self.notifier.check_events(timeout=10):
                    self.notifier.read_events()
            except KeyboardInterrupt:
                self.notifier.stop()
                break

class RsyncInFiles(pyinotify.ProcessEvent):
    def __init__(self, sftphosts, user=''):
        self.sftphosts = sftphosts
        self.user = user
        pyinotify.ProcessEvent.__init__(self)

    def process_IN_CLOSE_WRITE(self, event):
        new_file = event.pathname
        WatchFiles.jnxlog.info("New file %s is detected in %s", event.name, event.path)
        my_hostname = socket.gethostname()
        for sftp in self.sftphosts:
            if sftp in (my_hostname, my_hostname.split('.')[0]):
                continue
            cmd = shlex.split("rsync -v %s %s" % (new_file, self.get_dest_string(sftp, new_file)))
            rsync = subprocess.Popen(cmd)
            while rsync.poll() is None:
                time.sleep(1)
            if rsync.returncode == 0:
                WatchFiles.jnxlog.info("Successfully rsynced %s into %s host", new_file, sftp)
            else:
                WatchFiles.jnxlog.critical("Could not rsync %s", sftp)

    def get_dest_string(self, host, filename):
        prefix = ''
        if self.user:
            prefix += "%s@" % (self.user)
        return "%s%s:%s" % (prefix, host, filename)