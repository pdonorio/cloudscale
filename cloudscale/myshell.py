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


class Basher(object):
    """ Wrapper for execution of commands in a bash shell """

    _shell = None

    def __init__(self):
        # Load my personal list of commands based on my bash environment
        from plumbum import cmd as myshell
        self._shell = myshell

        super(Basher, self).__init__()
        _logger.debug(colors.title | "Internal shell initialized")

    def make_command(self, command, parameters=[]):
        """ Use the plumbum pattern for executing a shell command """
        command_handle = getattr(self._shell, command)
        return command_handle[parameters]

    def exec_command_advanced(self, command, parameters=[], retcodes=()):
        """ Advanced command: handling errors, skipping some status """
        command_handle = getattr(self._shell, command)
        (status, stdout, stderr) = \
            command_handle[parameters].run(retcode=retcodes)
        return (status, stdout, stderr)

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
            com & FG
        else:
            out = com()
            print("Output is:\n=================\n", colors.green | "\n" + out)

    def do(self, command="ls", ssh=False):
        """ The main function to be called """

        totalcom = None

        for single_command in command.split('|'):
            (command, parameters) = self.command2string(single_command)
            print("Command", command)
            print("Parameters", parameters)

            tmpcom = self.make_command(command, parameters)
            if totalcom is None:
                totalcom = tmpcom
            else:
                totalcom = totalcom | tmpcom

        self.execute(totalcom)
