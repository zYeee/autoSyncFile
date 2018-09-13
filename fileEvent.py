import os
import logging
import paramiko
from watchdog.events import PatternMatchingEventHandler


class FileEventHandler(PatternMatchingEventHandler):
    def __init__(self, serverInfo, watch_path, dest_path, ignore=None):
        self.sftp = None
        self.serverInfo = serverInfo
        self.connect()

        self.watch_path = watch_path
        self.dest_path = dest_path
        PatternMatchingEventHandler.__init__(self, ignore_patterns=ignore)
    
    def connect(self):
        logging.info("-------connect-------")
        transport = paramiko.Transport(
                self.serverInfo['host'], self.serverInfo['port'])
        username = self.serverInfo['username']
        private_key = self.serverInfo['private_key']
        transport.connect(username=username, pkey=private_key)
        self.sftp = paramiko.SFTPClient.from_transport(transport)

    def on_created(self, event):
        dest_path = event.src_path.replace(self.watch_path, self.dest_path)
        self.create_path(os.path.dirname(dest_path))

        if event.is_directory:
            if self.is_exsit(dest_path) is False:
                self.sftp.mkdir(dest_path)
        else:
            try:
                self.sftp.put(event.src_path, dest_path)
            except:
                pass
        logging.info('Created: %s', dest_path)

    def on_modified(self, event):
        try:
            if not event.is_directory:
                dest_path = event.src_path.replace(self.watch_path, self.dest_path)
                self.sftp.put(event.src_path, dest_path)
                logging.info('Modified: %s', dest_path)
        except paramiko.ssh_exception.SSHException:
            self.connect()
            self.sftp.put(event.src_path, dest_path)
            logging.info('Modified: %s', dest_path)

    def on_moved(self, event):
        try:
            from_path = event.src_path.replace(self.watch_path, self.dest_path)
            dest_path = event.dest_path.replace(self.watch_path, self.dest_path)
            self.sftp.rename(from_path, dest_path)
        except paramiko.ssh_exception.SSHException:
            self.connect()
            self.sftp.rename(from_path, dest_path)
        except:
            pass
        logging.info('Moved: %s', dest_path)

    def on_deleted(self, event):
        try:
            src_path = event.src_path.replace(self.watch_path, self.dest_path)
            if event.is_directory is False:
                self.sftp.remove(src_path)
        except FileNotFoundError:
            pass
        except paramiko.ssh_exception.SSHException:
            self.connect()
            self.sftp.remove(src_path)
        logging.info('deleted: %s', src_path)

    def create_path(self, path):
        if self.is_exsit(path) is False:
            self.create_path(os.path.dirname(path))
            self.sftp.mkdir(path)

    def is_exsit(self, path):
        try:
            self.sftp.lstat(path)
        except FileNotFoundError:
            return False
        except paramiko.ssh_exception.SSHException:
            self.connect()
            self.is_exsit(path)
        return True
