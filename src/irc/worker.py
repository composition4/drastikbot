#!/usr/bin/env python3
# coding=utf-8

'''
This file handles registering, reconnecting, pinging,
and other methods and functions required for the bot
to operate.
Copyright (C) 2017 drastik.org

This file is part of drastikbot.

Drastikbot is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Drastikbot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Drastikbot. If not, see <http://www.gnu.org/licenses/>.
'''

from threading import Thread
from queue import Queue
import re
import time
import errno
import base64
from config import Config
from irc.irc import Drastikbot
from irc.modules import Modules


class Main():

    def __init__(self, conf_dir, debug):
        self.ircv3_ver = '302'  # IRCv3 version supported by the bot
        self.connected = False  # True: when connected to the server and registered.
        self.ircv3 = False  # True: IRCv3 supported by the server
        self.cap_list = []    # List of the IRC Server Capabilities
        self.cap_req = ('sasl')  # Tuple of CAPabilities used by the bot
        self.cap_ack = []
            # List of capabilities ACKnowledged by the server

        self.irc = Drastikbot(conf_dir, debug)
        self.mod = Modules(conf_dir, debug)
        self.servqueue = Queue()
        self.debug = debug

    def recieve(self):
        while True:
            try:
                msg_raw = self.irc.irc_sock.recv(4096)
            except:
                self.conn_lost()
                break

            if len(msg_raw) == 0:
                self.conn_lost()

            msg = self.irc.textFix(msg_raw)
            self.servqueue.put(msg)
            if self.debug:
                print(msg)

    def text_work(self):  # ^^^consider rewriting and using regex (tho it may be slower)
        self.buff = self.servqueue.get()
        config = Config(self.irc.cd).read()
        self.bufflist = self.buff.split(' :', 1)
        self.usernick = self.bufflist[0].split('!', 1)[0][1:]
        self.irc_cmd_list = self.bufflist[0].split(' ')
        try:
            self.irc_cmd = self.irc_cmd_list[1]  # PRIVMSG, NOTICE, MODE etc.
        except IndexError:
            self.irc_cmd = self.irc_cmd_list[0]  # PING etc.
        try:
            self.channel = self.irc_cmd_list[2]  # IRC channel or bot nickname
        except IndexError:
            self.channel = ''
        if self.channel == self.irc.nickname:
            self.channel = self.usernick  # for PMs
        try:
            self.txtmsg = self.bufflist[1]
        except IndexError:
            self.txtmsg = ''
        try:
            self.msg_nocmd = self.txtmsg.split(' ', 1)[1].strip()
        except IndexError:
            self.msg_nocmd = ''
        try:
            self.prefix = config['irc']['channels'][
                'settings'][self.channel]['prefix']
        except KeyError:
            self.prefix = config['irc']['modules']['global_prefix']
        self.info = [self.channel, self.usernick,
                     self.txtmsg, self.msg_nocmd, self.prefix, self.buff]
        self.command = self.txtmsg.split(' ')[0]

    def conn_lost(self):
        print('[WARNING] Connection Lost...')
        self.irc.irc_sock.close()
        self.connected = False
        time.sleep(5)
        print(' - Reconnecting')
        self.main()

    def service(self):
        while self.connected:
            self.text_work()
            if 'PRIVMSG' == self.irc_cmd:
                self.thread_make(
                    self.mod.mod_main, (self.irc, self.info, self.command))
            if 'PING' == self.irc_cmd:
                self.irc.send(('PONG', self.txtmsg))
            if self.nickname_:
                if self.irc_cmd == 'QUIT' and self.usernick == self.irc.nickname:
                    self.irc.nick(self.irc.nickname)
                    self.nickname_ = False
                elif time.time() - self.nickchange_time > 300:
                    self.irc.nick(self.irc.nickname)
                    self.nickname_ = False

    def sasl(self):  # ^^^change to use self.text_work() for more precision
        self.irc.send(('AUTHENTICATE', 'PLAIN'))
        while True:
            buff = self.servqueue.get()
            if 'AUTHENTICATE +' in buff:
                sasl_pass = '{}\0{}\0{}'.format(
                    self.irc.username, self.irc.username, self.irc.auth_password)
                self.irc.send(
                    ('AUTHENTICATE', base64.b64encode(sasl_pass.encode('utf-8'))))
            elif 'SASL authentication failed' in buff:
                return False
            elif 'SASL authentication successful' in buff:
                return True

    def nickserv_id(self):
        self.irc.privmsg(
            'NickServ', 'IDENTIFY {} {}'.format(self.irc.nickname, self.auth_pass))

    def register(self):
        self.irc.send(('CAP', 'LS', self.ircv3_ver))
        self.irc.send(
            ('USER', self.irc.username, '0', '*', ':{}'.format(self.irc.realname)))
        self.irc.nick(self.irc.nickname)

        while True:
            self.text_work()
            if ' LS :' in self.buff:
                self.ircv3 = True
                self.cap_list = re.search(
                    r"(?:CAP .* LS :)(.*)", self.buff).group(1).split(' ')
                cap_req = [i for i in self.cap_list if i in self.cap_req]
                self.irc.send(('CAP', 'REQ', ':{}'.format(' '.join(cap_req))))
            if 'CAP {} ACK'.format(self.irc.nickname) in self.buff:
                ack = re.search(r"(?:CAP .* ACK :)(.*)", self.buff).group(1)
                self.cap_ack = ack.split()
                if self.irc.authentication.lower() == 'sasl' and 'sasl' in self.cap_ack:
                    sasl = self.sasl()
                    if not sasl:
                        print(' - SASL authentication failed. Exiting...')
                    self.irc.send(('CAP', 'END'))
                else:
                    self.irc.send(('CAP', 'END'))
            if 'Nickname is already in use' in self.buff:  # ^^^replace self.buff with more specific
                self.nickname_ = self.irc.nickname + '_'
                self.irc.nick(self.nickname_)
                self.nickchange = time.time()
                if self.auth and self.auth_pass:
                    self.irc.privmsg('NickServ', 'GHOST {} {}'.format(
                        self.irc.nickname, self.irc.auth_password))
                    # self.irc.nick(self.irc.nickname) ^^^maybe removing makes
                    # it work, investigate
            else:
                self.nickname_ = False
                self.nickchange_time = False

            if 'PING' == self.irc_cmd:
                self.irc.send(('PONG', txtmsg))

            if 'End of /MOTD' in self.buff or 'End of message of the day' in self.buff:
                if self.irc.authentication.lower() == 'nickserv':
                    self.nickserv_id()
                self.irc.join(self.irc.channels)
                self.connected = True
                break

        if not self.ircv3:
            print(' - This server does not support IRCv3')
        if (self.irc.authentication.lower() == 'sasl' and not self.ircv3) or (self.irc.authentication.lower() == 'sasl' and 'sasl' not in self.cap_list):
            print(
                ' - [WARNING] SASL is not supported by the server, use NickServ instead. Exiting...')

    def thread_make(self, target, args='', daemon=False):
        thread = Thread(target=target, args=(args))
        thread.daemon = daemon
        thread.start()
        return thread

    def main(self):
        print('\nDrastikbot v2 is starting.\n')
        self.irc.connect()
        self.thread_make(self.recieve)  # recieve thread, always running
        self.mod.mod_import()
        regiT = self.thread_make(self.register)
        regiT.join()
        self.thread_make(self.service)  # control server input
