syncer
======

Utility to automatically synchronize directories between hosts.

It uses inotify to detect files which are added or removed, and will
automatically copy them over to the specified remoted hosts.

Its purpose is to keep multiple hosts in sync, without introducing moving parts
like shared filesystems or databases.
