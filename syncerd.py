#!/usr/bin/python

from __future__ import print_function
import signal
import getopt
import sys
import plistlib
import logging
import logging.handlers
import traceback
from syncer import WatchFiles
import daemon
from version import * # pylint: disable=wildcard-import,import-error

def shutdown(sig, frame): # pylint: disable=unused-argument
    WatchFiles.keepgoing = False

def print_version():
    print("%s version %s " % ('syncerd', SYNCER_VERSION)) # pylint: disable=undefined-variable

def default_config_filename():
    return  "%s/syncer.conf" % (SYNCER_RCPATH) # pylint: disable=undefined-variable

def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    syncerd_config = default_config_filename()
    daemonize = True
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "f:p:Dv")
    except getopt.GetoptError as exc:
        print(exc)
        sys.exit(1)

    for opt, arg in opts:
        if opt == "-f":
            syncerd_config = arg
        if opt == "-p":
            syncerd_pidfile = arg
        if opt == "-D":
            daemonize = False
        if opt == "-v":
            print_version()
            sys.exit()

    consolelog = logging.StreamHandler(sys.stdout)
    syslog = logging.handlers.SysLogHandler(address='/dev/log')
    formatter = logging.Formatter('%(filename)s[%(process)s]: - %(levelname)s - %(message)s')
    consolelog.setFormatter(formatter)
    syslog.setFormatter(formatter)

    if daemonize:
        daemon.daemon(nochdir=True)
        WatchFiles.jnxlog.addHandler(syslog)
    else:
        WatchFiles.jnxlog.addHandler(consolelog)

    WatchFiles.jnxlog.info("Starting up syncer version %s", SYNCER_VERSION) # pylint: disable=undefined-variable

    pidfile = daemon.PidFile(syncerd_pidfile)
    try:
        pidfile.open(0644)
    except daemon.DaemonAlreadyRunning as exc:
        WatchFiles.jnxlog.error("Daemon already running, pid: %d", exc.otherpid)
        sys.exit(1)
    except Exception:
        WatchFiles.jnxlog.critical("Can not open or create pidfile")
        sys.exit(1)
    pidfile.write()

    try:
        WatchFiles.plist = plistlib.readPlist(syncerd_config)
        WatchFiles.jnxlog.info("Start watching the files")
        dump = WatchFiles()
        dump.start()
    except Exception as exc:
        WatchFiles.jnxlog.error("Aborting..., %s", exc)
        traceback.print_exc()
        sys.exit(1)

    WatchFiles.jnxlog.info("Ready")
    while WatchFiles.keepgoing:
        signal.pause()

    dump.stop()
    WatchFiles.jnxlog.info("Shutting down...")

if __name__ == '__main__':
    main()
