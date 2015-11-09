#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Experimenting tasks """

import paramiko
from invoke import task
from plumbum import cmd as shell

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
    print("Command output")
    print(stdout.read())
    client.close()


@task
def newnode():
    node = "test"
    print("Preparing machine", node)

    # Getting machine
    machine = getattr(shell, 'docker-machine')

    # Check that the requested node does not already exist
    machines = machine["ls"]()
    for line in machines.split('\n'):
        if line.strip() == '':
            continue
        if line.split()[0] == node:
            print("Already exists")
# // TO FIX:
# i may import colors if i update plumbum
            return

    # Create the machine
    args = ["create", "-d", "virtualbox", "test"]
    print(machine[args]())
    print("Created")
