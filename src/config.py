#!/usr/bin/env python3
# coding=utf-8

'''
Class methods for reading and writing the configuration file.
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

import json

# The Config() class needs to be passed a variable with the path to
# the configuration directory


class Config:

    def __init__(self, conf_dir):
        self.config_file = '{}/config.json'.format(conf_dir)

    def read(self):  # read the configuration file
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def write(self, value):  # write to the configuration file
        with open(self.config_file, 'w') as f:
            json.dump(value, f, indent=4)
