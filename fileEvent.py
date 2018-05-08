import os
import logging
from watchdog.events import PatternMatchingEventHandler


class FileEventHandler(PatternMatchingEventHandler):
    def __init__(self, sftp, ssh, watch_path, dest_path, ignore=None):
        self.watch_path = watch_path
        self.dest_path = dest_path
        self.sftp = sftp
        self.ssh = ssh
        PatternMatchingEventHandler.__init__(self, ignore_patterns=ignore)

    def on_created(self, event):
        dest_path = event.src_path.replace(self.watch_path, self.dest_path)
        print(dest_path)
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
        if not event.is_directory:
            dest_path = event.src_path.replace(self.watch_path, self.dest_path)
            self.sftp.put(event.src_path, dest_path)
            logging.info('Modified: %s', dest_path)

    def on_moved(self, event):
        from_path = event.src_path.replace(self.watch_path, self.dest_path)
        dest_path = event.dest_path.replace(self.watch_path, self.dest_path)
        try:
            self.sftp.rename(from_path, dest_path)
        except:
            pass
        logging.info('Moved: %s', dest_path)

    def on_deleted(self, event):
        src_path = event.src_path.replace(self.watch_path, self.dest_path)
        self.ssh.exec_command('rm -rf ' + src_path)
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
        return True
