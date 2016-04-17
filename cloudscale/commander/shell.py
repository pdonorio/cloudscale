#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Use shell commands in a more pythonic way.
Both local or remote.
"""

from __future__ import division, print_function, absolute_import
from .. import myself, lic, DLEVEL, logging
import os
import codecs
import paramiko
from plumbum import colors, FG, BG, NOHUP
from plumbum.machines.paramiko_machine import ParamikoMachine

__author__ = myself
__copyright__ = myself
__license__ = lic
_logger = logging.getLogger(__name__)
_logger.setLevel(DLEVEL)


#######################
class Basher(object):
    """
    Pythonic wrapper for execution of commands inside a shell.

    Will make it work both on local and ssh.
    """

    _shell = None
    _salt = None
    _pass = None
    _iip = None

    def __init__(self):
        self.init_shell()
        _logger.debug(colors.warn | "Internal shell initialized")
        super(Basher, self).__init__()

    def init_shell(self):
        # Load my personal list of commands based on my bash environment
        from plumbum import local
        self._shell = local

    def set_environment_var(self, name, value):
        self._shell.env[name] = value

    @staticmethod
    def pretty_print(string, success=True):
        mystring = str(string)
        if "the docker daemon running on this host" in mystring:
            return
        log = _logger.warning
        incipit = colors.warn | "Failed"
        if success:
            log = _logger.debug
            incipit = colors.green | "Success"
        log(incipit + (colors.blue | "\n==============") +
                      (colors.bold | "\n" + mystring))

    @staticmethod
    def join_command(command, parameters):
        """From a command string and dict of parameters to shell string"""

        _logger.debug("Composing command %s" % command)
        for key, value in parameters.items():
            command += " --%s %s" % (key, value)
        return command

    def make_command(self, command, parameters=[]):
        """ Use the plumbum pattern for executing a shell command """
        if self._shell is None:
            return False
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

    def execute(self, com, realtime=True, wait=True):
        """ Execute the command """
        try:
            if not wait:
                _logger.debug("Command in background %s" % com)
                return com & BG
                # return com & NOHUP(stdout=None)
                return com & NOHUP(stdout='/dev/null')
            elif realtime:
                _logger.debug("Realtime")
                return com & FG
        except Exception as e:
            print(colors.warn | "Failed")
            print(e)
            return False

        # Most advanced option
        return self.exec_command_advanced(com)

    def exec_command_advanced(self, com, retcodes=[0]):

        import plumbum.commands.processes as proc
        try:
            # THIS IS THE COMMAND
            (status, stdout, stderr) = com.run(retcode=retcodes)
        except proc.ProcessExecutionError as e:
            self.pretty_print(e, success=False)
            return False
        else:
            if status not in list(retcodes):
                self.pretty_print(stderr, success=False)
            else:
                self.pretty_print(stdout)
            return stdout
        return None

    def remote_bg(self, com, admin=True):
        """ With paramiko + plumbum there is no way to bg a sudo com """
        mycom = 'sudo ' + com
        bg = 'nohup %s >/dev/null 2>&1 &' % mycom
        s = self._shell.session()
        s.run('echo "%s" > /tmp/com' % bg)
        s.run('chmod +x /tmp/com')
        s.run('/tmp/com')
        _logger.info("BG remote for\n%s" % com)
        return True

    def get_salt(self, intrasalt=None, force=False, truncate=0):
        """ Create salt """
        if self._salt is None or force:
            string = os.urandom(16)
            if intrasalt is not None:
                string += intrasalt.encode()
            self._salt = codecs.encode(string, 'base_64').decode()
            _logger.info("Created an encrypted salt")

            if truncate > 4:
                _logger.debug("Salt truncated to %s chars" % truncate)
                if truncate >= len(self._salt):
                    truncate = len(self._salt) - 1
                self._salt = self._salt[0:truncate]

        return self._salt

    def get_cryptedp(self):
        return {'p': self._pass, 'salt': self._salt}

    def set_cryptedp(self, p=None, salt=None):
        self._pass = p
        self._salt = salt
        _logger.debug("ENCRYPTION\n*%s*%s*" % (self._pass, self._salt))

    def encrypt(self, obj):
        if not isinstance(obj, str) or len(obj) < 1:
            _logger.warning("Empty element")
            return False

        eobj = obj.encode()
        salt = self.get_salt().encode()
        return codecs.encode(salt + eobj + salt, 'base_64')

    def decrypt(self, obj):
        decrypt = codecs.decode(self._pass, 'base_64').decode()
        salt = self.get_salt()
        return decrypt.replace(salt, '')

    def passw(self):
        if self._pass is None:
            _logger.info("Account credentials required")
            import getpass
            self._pass = self.encrypt(getpass.getpass())

            if self._pass is False:
                _logger.critical("Failed to acquire valid password")
                exit(1)
            _logger.info("Pass received")

        return self.decrypt(self._pass)

    def cd(self, path="~"):
        """ Change current directory """
        if path is None or self._shell is None:
            return
        self._shell.cwd.chdir(path)
        _logger.debug("PWD:\t%s" % path)

    def do(self, command="ls", no_output=False,
           admin=False, die_on_fail=True, wait=True):
        """ The main function to be called """
        if self._shell is None:
            _logger.critical(colors.warn | "No working shell for command")
            exit(1)

        if admin:
            command = 'sudo ' + command

        totalcom = None

        for single_command in command.split('|'):
            (command, parameters) = self.command2string(single_command)
            _logger.debug("Executing %s" % command)
            # print("Parameters", parameters)

            tmpcom = self.make_command(command, parameters)
            if totalcom is None:
                totalcom = tmpcom
            else:
                totalcom = totalcom | tmpcom

        out = self.execute(totalcom, realtime=no_output, wait=wait)
        if out is False and die_on_fail:
            # Command has failed... i should stop, maybe
            exit(1)
        return out

    def remote(self, host='host', port=22, user='root',
               pwd=None, kfile=None, timeout=10):
        """ Make the shell a remote connection """

        if kfile is None and pwd is None:
            _logger.critical("No credentials provided")
            exit(1)

        _logger.info("Preparing connection to '%s'" % host)
        connect_params = {
            'host': host, 'port': port, 'user': user,
            'password': pwd, 'keyfile': kfile,
            'missing_host_policy': paramiko.AutoAddPolicy(),
            'connect_timeout': timeout,
        }

        import socket
        client = None
        try:
            client = ParamikoMachine(**connect_params)
            _logger.info(colors.green | "Connected")
        except socket.timeout:
            _logger.warn(colors.warn | "Connection timeout...")
        except OSError as e:
            _logger.critical(colors.warn | str(e))
            exit(1)
        self._shell = client
        return client

    def iip(self):
        """ Get the internal ip """
        if self._iip is None:
            out = self.do('ifconfig eth0')
            self._iip = out.split("\n")[1].split()[1].split(':')[1]
        _logger.info("Internal master ip is: '%s'" % self._iip)
        return self._iip

    def exit(self):
        _logger.info("Closing %s" % self._shell)
        self._shell.close()
        # Bring power back to local bash
        self.init_shell()
