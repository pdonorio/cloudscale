#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Use shell commands in a more pythonic way.
Both local or remote.
"""

from __future__ import division, print_function, absolute_import
import logging
from . import myself  # , __version__
from plumbum import colors, FG

__author__ = myself
__copyright__ = myself
__license__ = "MIT"

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


#######################
def join_command(command, parameters):
    """From a command string and a dictionary of parameters to shell string"""

    for key, value in parameters.items():
        command += " --%s %s" % (key, value)
    print("Command", command)
    return command


#######################
class Basher(object):
    """
    Pythonic wrapper for execution of commands inside a shell.

    Will make it work both on local and ssh.
    """

    _shell = None

    def __init__(self):
        # Load my personal list of commands based on my bash environment
        from plumbum import local
        self._shell = local

        super(Basher, self).__init__()
        _logger.debug(colors.title | "Internal shell initialized")

    def set_environment_var(self, name, value):
        self._shell.env[name] = value

    def make_command(self, command, parameters=[]):
        """ Use the plumbum pattern for executing a shell command """
        # Works with 'local'
        command_handle = self._shell[command]
        # Works with 'cwd'
        # command_handle = getattr(self._shell, command)
        return command_handle[parameters]

    def command2string(self, string):
        """ Convert a whole string into a single plumbum command """
        pieces = string.split()
        num = len(pieces)
        command = pieces[0]
        args = []
        if num > 1:
            args = pieces[1:num]
        return (command, args)

    def execute(self, com, realtime=True):
        """ Execute the command """
        if realtime:
            try:
                com & FG
            except Exception:
                print(colors.warn | "Failed")
        else:
            self.exec_command_advanced(com, (0))

    def exec_command_advanced(self, com, retcodes=(0, 1)):

        import plumbum.commands.processes as proc
        try:
            # THIS IS THE COMMAND
            (status, stdout, stderr) = com.run(retcode=retcodes)
        except proc.ProcessExecutionError as e:
            print(colors.warn | "Failed",
                  colors.blue | "\n==============",
                  colors.bold | "\n" + str(e))

        if status not in retcodes:
            print(colors.warn | "Failed",
                  colors.blue | "\n==============",
                  colors.bold | "\n" + stderr)
            print(stderr)
        else:
            print(colors.green | "Success",
                  colors.blue | "\n==============",
                  colors.bold | "\n" + stdout)

    def do(self, command="ls", ssh=False):
        """ The main function to be called """

        totalcom = None

        for single_command in command.split('|'):
            (command, parameters) = self.command2string(single_command)
            print("Command", command)
            # print("Parameters", parameters)

            tmpcom = self.make_command(command, parameters)
            if totalcom is None:
                totalcom = tmpcom
            else:
                totalcom = totalcom | tmpcom

        self.execute(totalcom)
