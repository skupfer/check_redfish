#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  Copyright (c) 2020 - 2025 Ricardo Bartels. All rights reserved.
#
#  check_redfish.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

description = """
This is a monitoring/inventory plugin to check components and
health status of systems which support Redfish.
It will also create a inventory of all components of a system.

R.I.P. IPMI
"""

__version__ = "1.11.0"
__version_date__ = "2025-02-21"
__author__ = "Ricardo Bartels <ricardo@bitchbrothers.com>"
__description__ = "Check Redfish Plugin"
__license__ = "MIT"

# check for a virtual environment
import os
ACTIVATE_THIS = False
venv_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.venv')
if os.path.exists(venv_path):
    ACTIVATE_THIS = os.path.join(venv_path, 'bin/activate_this.py')
if ACTIVATE_THIS and os.path.isfile(ACTIVATE_THIS):
    exec(open(ACTIVATE_THIS).read(), {'__file__': ACTIVATE_THIS})
# end virtual environment check

import logging

from cr_module.classes.plugin import PluginData
from cr_module.system_chassi import get_system_info, get_chassi_data, get_system_data
from cr_module.nic import get_network_interfaces
from cr_module.storage import get_storage
from cr_module.bmc import get_bmc_info
from cr_module.firmware import get_firmware_info
from cr_module.event import get_event_log
from cr_module.args import parse_command_line

from cr_module.classes.inventory import Fan, PowerSupply, Temperature, Memory, Processor


if __name__ == "__main__":
    # start here
    args = parse_command_line(description, __version__, __version_date__)

    if args.verbose:
        # initialize logger
        logging.basicConfig(level="DEBUG", format='%(asctime)s - %(levelname)s: %(message)s')

    # initialize plugin object
    plugin = PluginData(args, plugin_version=__version__)

    # try to get systems, managers and chassis IDs
    plugin.rf.discover_system_properties()

    # get basic information
    plugin.rf.determine_vendor()

    if any(x in args.requested_query for x in ['power', 'all']):    get_chassi_data(PowerSupply)
    if any(x in args.requested_query for x in ['temp', 'all']):     get_chassi_data(Temperature)
    if any(x in args.requested_query for x in ['fan', 'all']):      get_chassi_data(Fan)
    if any(x in args.requested_query for x in ['proc', 'all']):     get_system_data(Processor)
    if any(x in args.requested_query for x in ['memory', 'all']):   get_system_data(Memory)
    if any(x in args.requested_query for x in ['nic', 'all']):      get_network_interfaces()
    if any(x in args.requested_query for x in ['storage', 'all']):  get_storage()
    if any(x in args.requested_query for x in ['bmc', 'all']):      get_bmc_info()
    if any(x in args.requested_query for x in ['info', 'all']):     get_system_info()
    if any(x in args.requested_query for x in ['firmware', 'all']): get_firmware_info()
    if any(x in args.requested_query for x in ['mel', 'all']):      get_event_log("Manager")
    if any(x in args.requested_query for x in ['sel', 'all']):      get_event_log("System")

    plugin.do_exit()

# EOF
