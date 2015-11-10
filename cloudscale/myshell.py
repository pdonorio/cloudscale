#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Use shell commands in a more pythonic way.
Both local or remote.
"""

from __future__ import division, print_function, absolute_import
import logging
from . import myself  # , __version__
from plumbum import colors

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

    def execute_command(self, command, parameters=[]):
        """ Use the plumbum pattern for executing a shell command """
        command_handle = getattr(self._shell, command)
        out = command_handle[parameters]()
        return out

    def execute_command_advanced(self, command, parameters=[], retcodes=()):
        """ Advanced command: handling errors, skipping some status """
        command_handle = getattr(self._shell, command)
        (status, stdout, stderr) = \
            command_handle[parameters].run(retcode=retcodes)
        return (status, stdout, stderr)

    def command2string(self, string):
        """ Convert a whole string into a single plumbum command """
        pieces = string.split()
        command = pieces[0]
        args = []
        if len(c) > 1:
            args = command[1:len(c)]
        return (command, args)

    def pipelining(self, string):
        """ Convert a whole string of pipelines into a plumbum pipeline """
        pass

    def do(self, command="ls", ssh=False):
        """ The main function to be called """

        for single_command in command.split('|'):
            (command, parameters) = command2string(single_command)
            print("Command", command)
            print("Parameters", parameters)
            # DO SOME
