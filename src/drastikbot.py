#!/usr/bin/env python3
# coding=utf-8

'''
This file parses command line arguments and starts the bot.
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

import sys
import argparse
from pathlib import Path, PurePath
from config import Config
from irc.worker import Main


def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf", nargs='?',
                        type=str, help="Specify the configuration directory")
    parser.add_argument(
        "--debug", help="Start in debug mode", action="store_true")
    args = parser.parse_args()
    if args.conf:
        path = Path(args.conf)
        if not path.is_dir():
            sys.exit("[Error] Config directory does not exist.")
        if '~/' in args.conf:
            conf_dir = str(path.expanduser())
        else:
            conf_dir = args.conf
    else:
        conf_dir = str(Path('~/.drastikbot').expanduser())
    if args.debug:
        debug = True
    else:
        debug = False
    startIRC(conf_dir, debug)


def startIRC(conf_dir, debug):
    c = Main(conf_dir, debug)
    c.main()

parser()
