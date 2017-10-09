#!/usr/bin/env python3
# coding=utf-8

import json

# Class methods for fetching values from the configuration file
# The class needs to be passed a variable linking to the Configuration Directory

import sys


class Config:
    def __init__(self, conf_dir):
        self.config_file = '{}/config.json'.format(conf_dir)
        
    def read(self): # read the configuration file
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def write(self, value): # write to the configuration file
        with open(self.config_file, 'w') as f:
            json.dump(value, f, indent=4)
