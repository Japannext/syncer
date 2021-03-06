# Copyright 2021 Japannext Co., Ltd. <https://www.japannext.co.jp/>
# SPDX-License-Identifier: GPL-2.0-or-later

import os
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
        mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO
        self.notifier = pyinotify.Notifier(w_man, RsyncInFiles(self.plist['SFTP']))
        for watchdirectory in self.plist['WatchDirectory']:
            w_man.add_watch(watchdirectory, mask, do_glob=True, rec=True, auto_add=True)

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
    def __init__(self, sftp_options):
        self.sftphosts = sftp_options['Hosts']
        self.user = sftp_options['user']
        self.rsync_options = sftp_options['rsync_options']
        pyinotify.ProcessEvent.__init__(self)

    def process_IN_MOVED_TO(self, event):
        self.rsync_file(event)

    def process_IN_CLOSE_WRITE(self, event):
        self.rsync_file(event)

    def rsync_file(self, event):
        if event.name.startswith('.'):
            return
        new_file = event.pathname
        time.sleep(1)
        if not os.path.exists(new_file):
            return
        WatchFiles.jnxlog.info("New file %s is detected in %s", event.name, event.path)
        my_hostname = socket.gethostname()
        for sftp in self.sftphosts:
            if sftp in (my_hostname, my_hostname.split('.')[0]):
                continue
            cmd = shlex.split("rsync %s %s %s" % (self.rsync_options, new_file, self.get_dest_string(sftp, new_file)))
            rsync = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            err = rsync.communicate()[1]
            while rsync.poll() is None:
                time.sleep(1)
            if rsync.returncode == 0:
                WatchFiles.jnxlog.info("Successfully rsynced %s into %s host", new_file, sftp)
            else:
                WatchFiles.jnxlog.error("Could not rsync %s into %s host\n%s", new_file, sftp, err)

    def get_dest_string(self, host, filename):
        prefix = ''
        if self.user:
            prefix += "%s@" % (self.user)
        return "%s%s:%s" % (prefix, host, filename)
