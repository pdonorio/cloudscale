#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Experimenting tasks """

import paramiko
from invoke import task
from plumbum import cmd as shell
from plumbum import colors

#####################################################
# SSH via PARAMIKO

hostname = 'host'
username = 'root'
port = 22
command = 'ls /tmp'


@task
def ssh():
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


#####################################################
# DOCKER MACHINE
machine = getattr(shell, 'docker-machine')


def machine_list():
    """ Get all machine list """
    machines = []
    print(colors.yellow | "Checking machine list")
    for line in machine["ls"]().split('\n'):
        if line.strip() == '':
            continue
        machines.append(line.split()[0])
    return machines


@task
def new(node="dev", driver='virtualbox'):
    """ A task to add a docker machine """

    # Check that the requested node does not already exist
    if node in machine_list():
        print(colors.warn | "Failed:", colors.bold |
              "Machine '%s' Already exists" % node)
        return

    # Create the machine
    print("Preparing machine", node)
    args = ["create", "-d", driver, node]
    print(machine[args]())
    print(colors.green | "Created!\n\n")


@task
def rm(node="dev"):
    """ A task to remove an existing machine """

    # Check that the requested node does not already exist
    if node not in machine_list():
        print(colors.warn | "Failed:", colors.bold |
              "Machine '%s' does not exist" % node)
        return

    print(colors.bold | "Trying to remove '%s'" % node)
    args = ["rm", node]
    print(machine[args]())
    print(colors.green | "Removed")
