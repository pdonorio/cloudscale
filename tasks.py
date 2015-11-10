#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Experimenting tasks """

import paramiko
import getpass
from collections import OrderedDict
from invoke import task
from cloudscale.myshell import Basher, join_command
from plumbum import cmd as shell
from plumbum import colors
from plumbum.machines.paramiko_machine import ParamikoMachine

DRIVER = 'openstack'

oovar = {
    'OS_AUTH_URL': "http://cloud.pico.cineca.it:5000/v2.0",
    'OS_USERNAME': "pdonorio",
    'OS_PASSWORD': "",
    'OS_REGION_NAME': "RegionOne",
    'OS_TENANT_NAME': "mw",
}


#####################################################
# TESTS with the Basher Class

def get_oomachine_com():
    com = "docker-machine"
    # Operation 'create', with debug
    opts = OrderedDict({'debug': 'create'})
    # Choose driver
    opts["driver"] = DRIVER
    # Remaining
    otheropts = {
        DRIVER + "-image-name": "ubuntu-trusty-server",
        DRIVER + "-ssh-user": "ubuntu",
        DRIVER + "-sec-groups": "default",
        DRIVER + "-net-name": "mw-net",
        DRIVER + "-floatingip-pool": "ext-net",
        DRIVER + "-flavor-name": "m1.small",
    }
    for key, value in otheropts.items():
        opts[key] = value
    return join_command(com, opts)


@task
def test(node='pymachine'):
    """ just a test """
    pwd = getpass.getpass()
    oovar['OS_PASSWORD'] = pwd

    bash = Basher()

    for key, value in oovar.items():
        bash.set_environment_var(key, value)
    # print(bash._shell.env['OS_TENANT_NAME'])

    bash.do(get_oomachine_com() + " " + node)


#####################################################
# SSH with Paramiko

@task
def ssh(hosts='host', port=22, user='root', com='ls',
        pwd=None, kfile=None, timeout=5):
    """ Execute command to host via pythonic ssh (auth: passwork or key) """

    for host in hosts.split(','):
        print(colors.title | "Prepare host '%s'" % host)
        connect_params = {
            'host': host, 'port': port, 'user': user,
            'password': pwd, 'keyfile': kfile,
            'missing_host_policy': paramiko.AutoAddPolicy(),
            'connect_timeout': timeout,
        }

        try:
            with ParamikoMachine(**connect_params) as client:
                print("Connected")
                c = com.split()
                command = c[0]
                args = []
                if len(c) > 1:
                    args = c[1:len(c)]

                handle = client[command]
                import plumbum.commands.processes as proc
                import socket
                try:
                    out = handle[args]()
                except proc.ProcessExecutionError as e:
                    print(colors.warn | "Command failed:")
                    print(str(e))
                else:
                    print(colors.green | "Command executed")
                    print("Command output:\t", out)
        except socket.timeout as e:
            print(colors.warn | "Connection timeout...")


#####################################################
# DOCKER MACHINE

def machine_list(machine):
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
    machine = getattr(shell, 'docker-machine')

    # Check that the requested node does not already exist
    if node in machine_list(machine):
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
    machine = getattr(shell, 'docker-machine')

    # Check that the requested node does not already exist
    if node not in machine_list(machine):
        print(colors.warn | "Failed:", colors.bold |
              "Machine '%s' does not exist" % node)
        return

    print(colors.bold | "Trying to remove '%s'" % node)
    args = ["rm", node]
    print(machine[args]())
    print(colors.green | "Removed")
