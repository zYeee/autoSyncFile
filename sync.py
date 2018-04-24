#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import time
import paramiko
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from configparser import SafeConfigParser


def getConfig(sectionName='env'):
    config = SafeConfigParser()
    config.readfp(open('config.conf'))
    return dict(config.items(sectionName))


def getIgnore():
    with open("ignore.conf") as f:
        return [line.strip('\n') for line in f.readlines() if line]


class FileEventHandler(PatternMatchingEventHandler):
    def __init__(self, sftp, watch_path, dest_path, ignore=None):
        self.watch_path = watch_path
        self.dest_path = dest_path
        self.sftp = sftp
        PatternMatchingEventHandler.__init__(self, ignore_patterns=ignore)

    def on_created(self, event):
        dest_path = event.src_path.replace(self.watch_path, self.dest_path)
        if event.is_directory:
            self.sftp.mkdir(dest_path)
        else:
            self.sftp.put(event.src_path, dest_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            dest_path = event.src_path.replace(self.watch_path, self.dest_path)
            self.sftp.put(event.src_path, dest_path)

    def on_moved(self, event):
        from_path = event.src_path.replace(self.watch_path, self.dest_path)
        dest_path = event.dest_path.replace(self.watch_path, self.dest_path)
        try:
            self.sftp.rename(from_path, dest_path)
        except:
            pass


if __name__ == "__main__":
    config = getConfig()
    ignore = getIgnore()
    watch_path = config['watch_path']
    host = config['host']
    port = config['port']
    ssh_key_path = config['ssh_key_path']
    username = config['username']
    dest_path = config['dest_path']
    private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    ssh = paramiko.Transport(host, int(port))
    ssh.connect(username=username, pkey=private_key)
    sftp = paramiko.SFTPClient.from_transport(ssh)

    observer = Observer()
    event_handler = FileEventHandler(sftp, watch_path, dest_path, ignore)
    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
