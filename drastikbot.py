#!/usr/bin/env python3
# coding=utf-8

import sys
import argparse
from pathlib import Path, PurePath
from config import Config
from irc.worker import Main

def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c" ,"--conf" ,nargs='?' ,type=str , help="Specify the configuration directory")
    parser.add_argument("--debug", help="Start in debug mode", action="store_true")
    args = parser.parse_args()

    # --conf
    if args.conf:
        path = Path(args.conf)
        if not path.is_dir():
            sys.exit("[Error] Config directory does not exist.")
        if '~/' in args.conf:
            conf_dir = str(path.expanduser())
        else:
            conf_dir = args.conf
    else: conf_dir = str(Path('~/.drastikbot').expanduser())

    # --debug
    if args.debug:
        debug = True
    else:
        debug = False

    startIRC(conf_dir,debug)
    
def startIRC(conf_dir, debug):
    c = Main(conf_dir, debug)
    c.main()

parser()

