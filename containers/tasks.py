#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Experimenting tasks """

import paramiko
from invoke import task
from plumbum import cmd as shell
from plumbum import colors

hostname = 'host'
username = 'root'
port = 22
command = 'ls /tmp'


@task
def connect():
    print("Prepare")
    kfile = 'insecure_key'
    k = paramiko.RSAKey.from_private_key_file(kfile)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # client.load_system_host_keys()

    client.connect(hostname, port=port, username=username, pkey=k)
    print("Connected")
    stdin, stdout, stderr = client.exec_command(command)
    print(colors.green | "Success")
    print("Command output")
    print(stdout.read())
    client.close()


@task
def newnode():
    node = "test"
    driver = 'virtualbox'

    # Getting machine
    machine = getattr(shell, 'docker-machine')
    print("Preparing machine", node)

    # Check that the requested node does not already exist
    machines = machine["ls"]()
    for line in machines.split('\n'):
        if line.strip() == '':
            continue
        if line.split()[0] == node:
            print(colors.red | "Failed:", colors.bold |
                  "Machine '%s' Already exists" % node)
            return

    # Create the machine
    args = ["create", "-d", driver, node]
    print(machine[args]())
    print(colors.green | "Created")
