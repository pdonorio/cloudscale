#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Experimenting tasks """

from invoke import task
from cloudscale.commander.machinery import TheMachine, Basher
from plumbum import colors


#####################################################
# TESTS with the Basher Class
@task
def machine(node='pymachine', driver=None):
    """ Launch openstack machine """
    TheMachine(driver).create(node)


#####################################################
# SSH with Paramiko

@task
def ssh(hosts='host', port=22, user='root', com='ls', path=None,
        pwd=None, kfile=None, timeout=5):
    """ Execute command to host via pythonic ssh (auth: passwork or key) """

    for host in hosts.split(','):
        bash = Basher()
        bash.remote(host=host, port=port, user=user,
                    pwd=pwd, kfile=kfile, timeout=timeout)
        bash.cd(path)
        bash.do(com)


#####################################################
# DOCKER MACHINE
@task
def new(node="dev", driver='virtualbox'):
    """ A task to add a docker machine """
    machine = TheMachine(driver)

    # Check that the requested node does not already exist
    if node in machine.list():
        print(colors.warn | "Failed:", colors.bold |
              "Machine '%s' Already exists" % node)
        return
    machine.create(node)

    # Create the machine
    print("Preparing machine", node)
    print(machine.create(node))
    print(colors.green | "Created!\n\n")


@task
def rm(node="dev", driver='virtualbox'):
    """ A task to remove an existing machine """
    machine = TheMachine(driver)

    # Check that the requested node does not already exist
    if node not in machine.list():
        print(colors.warn | "Failed:", colors.bold |
              "Machine '%s' does not exist" % node)
        return

    print(colors.bold | "Trying to remove '%s'" % node)
    print(machine.remove(node))
    print(colors.green | "Removed")
