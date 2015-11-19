#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Experimenting tasks """

import logging
from invoke import task
from cloudscale.commander.machinery import TheMachine, Basher
from plumbum import colors

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


#####################################################
# TESTS with the Basher Class
@task
def machine(node='pymachine', driver=None):
    """ Launch openstack machine """
    mach = TheMachine(driver)
    mach.create(node)
    mach.connect(node)
    # Do something to test
    print(mach.do("docker pull busybox"))
    print(mach.do("docker images"))


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
    """ A task to add a docker machine - on virtualbox """
    machine = TheMachine(driver)

    # Check that the requested node does not already exist
    if node in machine.list():
        print(colors.warn | "Failed:", colors.bold |
              "Machine '%s' Already exists" % node)
        return
    machine.create(node)

    # Create the machine
    _logger.info("Preparing machine", node)
    print(machine.create(node))
    _logger.info(colors.green | "Created!\n\n")


@task
def rm(node="dev", driver='virtualbox'):
    """ A task to remove an existing machine - on virtualbox """
    machine = TheMachine(driver)

    # Check that the requested node does not already exist
    if node not in machine.list():
        print(colors.warn | "Failed:", colors.bold |
              "Machine '%s' does not exist" % node)
        return

    _logger.info(colors.bold | "Trying to remove '%s'" % node)
    print(machine.remove(node))
    _logger.info(colors.green | "Removed")
