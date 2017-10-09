#!/usr/bin/env python3
# coding=utf-8

import sys
from pathlib import Path, PurePath
import importlib
import traceback
import sqlite3
from config import Config

class Modules():
    def __init__(self, conf_dir, debug):
        self.conf_dir = conf_dir
        self.debug    = debug
        self.modules   = {} # contains {Module Name : Module Callable}
        self.cmd_dict  = {} # contains {Module Name : [module, commands]}
        ### config ###
        conf = Config(conf_dir)
        self.config = conf.read()
        self.load     = self.config['irc']['modules']['load']
        ### initiate the databases ###
        self.dbmem    = sqlite3.connect(':memory:', check_same_thread=False)
        self.dbdisk   = sqlite3.connect('{}/drastikbot.db'.format(self.conf_dir), check_same_thread=False)
        ### module settings ###
        self.mod_settings = {} # contains {Module Name : {setting : value}}
        
    def mod_import(self): # import modules specified in the config
        importlib.invalidate_caches()
        moduleDir = self.conf_dir + '/modules'
        path = Path(moduleDir)
        init = Path(moduleDir + '/__init__.py')
        config  = Config(self.conf_dir).read()
        load = config['irc']['modules']['load']
        if not path.is_dir(): # check if /module exists and make it if not
            print('[WARNING] Module directory does not exist. Making it now...')
            path.mkdir(exist_ok=True)
            print(' --- Module directory created at: {}'.format(moduleDir))
        elif not init.is_file(): # check if __init__.py exists in /module | MIGHT NOT BE NEEDED
            init.touch(exist_ok=True)
            
        sys.path.insert(0, moduleDir) # insert the module directory in the project
  
        files = [f for f in path.iterdir() if Path(PurePath(moduleDir).joinpath(f)).is_file()]
        for f in files:
            suffix = PurePath(f).suffix
            prefix = PurePath(f).stem
            if (suffix == '.py') and (prefix in load):                
                try: # import the module and it's requested functionality
                    modimp = importlib.import_module(prefix) #import the module
                    self.modules[prefix] = modimp
                    mod = modimp.Module()
                    commands = mod.commands # get the requested commands by the module
                    sysmode = getattr(mod, 'system', False) # check if its a system module
                    self.cmd_dict[prefix] = [commands, sysmode]
                    print('- Loaded module: {}'.format(prefix))
                except Exception as e:
                    print('[WARNING] Module "{}" failed to load: "{}"'.format(prefix, e))

    def mod_reload(self):
        for value in self.modules.values():
            importlib.reload(value)
                    
    def mod_main(self, irc, info, command):
        self.mod_reload() # on the fly module reloading
        config = Config(self.conf_dir).read()
        botsys = [self.modules, self.mod_import] # Bot system functions 
        database = [self.dbmem, self.dbdisk]
        
        for key, value in self.cmd_dict.items(): #iterate over each module
            for v in value[0]:
                # iterate over the module's commands | commands = value[0], sysmode = value[1]

                try: blacklist = config['irc']['modules']['settings'][key]['blacklist']
                except KeyError: blacklist = ''
                try: whitelist = config['irc']['modules']['settings'][key]['whitelist']
                except KeyError: whitelist = ''
                if 'blacklist' in locals():
                    if info[0] in blacklist: break
                elif 'whitelist' in locals():
                    if info[0] in whitelist: break
                    
                try:
                    if '#auto#' == v : # code to always call that module
                        self.modules[key].main(v, info, database, irc)
                    elif command == info[4] + v and not value[1]: # .command
                        self.modules[key].main(v, info, database, irc)
                    elif command == info[4] + v and value[1]: # .command for system modules
                        self.modules[key].main(v, info, database, irc, botsys)
                except:
                    print('[WARNING] Module "{}" exitted with error: '.format(key))
                    traceback.print_exc()
