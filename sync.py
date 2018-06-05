#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import paramiko
import logging
import time
from watchdog.observers import Observer
from configparser import SafeConfigParser
from fileEvent import FileEventHandler


def getConfig(sectionName='default'):
    config = SafeConfigParser()
    config.read_file(open('config.conf'))
    return dict(config.items(sectionName))


def getIgnore():
    with open("ignore.conf") as f:
        return [line.strip('\n') for line in f.readlines() if line]


def addServer(configName):
    config = getConfig(configName)
    ignore = getIgnore()
    watch_path = config['watch_path']
    host = config['host']
    port = config['port']
    ssh_key_path = config['ssh_key_path']
    username = config['username']
    dest_path = config['dest_path']
    private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    transport = paramiko.Transport(host, int(port))
    transport.connect(username=username, pkey=private_key)
    sftp = paramiko.SFTPClient.from_transport(transport)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, username)

    observer = Observer()
    event_handler = FileEventHandler(sftp, ssh, watch_path, dest_path, ignore)
    observer.schedule(event_handler, watch_path, recursive=True)
    return observer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    serverList = getConfig('servers')
    serverName = serverList['name'].split(" ")
    observers = []
    for server in serverName:
        observer = addServer(server)
        observer.start()
        observers.append(observer)


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
