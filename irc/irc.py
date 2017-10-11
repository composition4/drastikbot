#!/usr/bin/env python3
# coding=utf-8
#ayano from yuru yuri
import socket
import ssl
import re
import time
import errno
from config import Config

class Drastikbot():
    def __init__(self, conf_dir, debug):
        #self.irc_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.debug = debug
        self.cd = conf_dir
        conf = Config(conf_dir)
        config = conf.read()
        ### connection ###
        self.nickname       = config['irc']['connection']['nickname']
        self.username       = config['irc']['connection']['username']
        self.realname       = config['irc']['connection']['realname']
        self.authentication = config['irc']['connection']['authentication'] or 'None'
        self.auth_password  = config['irc']['connection']['auth_password']
        self.host           = config['irc']['connection']['network']
        self.port           = config['irc']['connection']['port']
        self.net_password   = config['irc']['connection']['net_password']
        self.ssl            = config['irc']['connection']['ssl']
        ### channels ###
        self.channels       = config['irc']['channels']['join']
        ### modules ###
        self.global_prefix = config['irc']['modules']['global_prefix']
        
    def textFix(self, line):
        if isinstance(line, bytes):
            try:
                line = line.decode('utf8')
            except: #catch UnicodeDecode errors
                pass
        line = line.replace('\n', '')
        line = line.replace('\r', '')
        return line 
        
    def send(self, cmds, text = None): #textFix stuff and send them
        cmds = [self.textFix(cmd) for cmd in cmds]
        if text:
            text = self.textFix(text)
            #https://tools.ietf.org/html/rfc2812.html#section-2.3
            #NOTE: 2) IRC messages are limited to 512 characters in length.
            #With CR-LF we are left with 510 characters to use, hence the [:510]
            toSend = (' '.join(cmds) + ' :' + text)[:510] + '\r\n' #for text with spaces
        else:
            toSend = ' '.join(cmds)[:510] + '\r\n' #for commands
        self.irc_sock.send(toSend.encode('utf-8'))
        if self.debug: print(toSend.encode('utf-8'))
        
    def privmsg(self, target, msg):
        self.send(('PRIVMSG', target), msg)

    def notice(self, target, msg):
        self.send(('NOTICE', target), msg)
                        
    def join(self, chanDict):
        for key, value in chanDict.items():
            self.send(('JOIN', key, value))
            print('Joined {}'.format(key))

    def part(self, channel, msg): #untested
        self.send(('PART', channel), msg)

    def invite(self, nick, channel): #untested
        self.send(('INVITE', nick, channel))

    def kick(self, channel, nick, msg): #untested
        self.send(('KICK', channel, nick, msg))
        
    def nick(self, nick):
        self.send(('NICK', '{}'.format(nick)))

    def quit(self, msg=None):
        self.send('QUIT', msg)

    def away(self, msg=None):
        self.send('AWAY', msg)

    def connect(self):
        try: # ConnectionResetError: [Errno 104] Connection reset by peer
            self.irc_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.ssl: # SSL enabled/disabled
                self.irc_sock = ssl.wrap_socket(self.irc_sock)
        except Exception as e:
            if e.errno != errno.ECONNRESET:
                raise
            self.connect()

        # SOCKET OPTIONS
        self.irc_sock.settimeout(300)
        self.irc_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        try: self.irc_sock.connect((self.host, self.port))
        except OSError: # OSError: [Errno 113] No route to host
            print('[ERROR] No route to host. Retrying...')
            self.irc_sock.close()
            time.sleep(5)
            return self.connect()
        
        if self.net_password: # Authenticate if the server is password protected
            self.send(('PASS', self.net_password))
