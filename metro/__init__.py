# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause


import sys
if sys.version_info[0] != 3:
    print("The metro module requires Python version 3.")
    sys.exit(1)

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from metro.Manifest import Manifest
from metro.Confluence import Confluence

# metro module test
if __name__ == "__main__": 
    server = 'https://confluence.internal.salesforce.com'
    user = 'jeffreyjohnson'
#    server = 'https://sfm-confl-lp004.internal.salesforce.com'
#    user = 'jeffreyjohnson.local'
    conf = Confluence(server, user)
    core_ent_fw_id = 75199145 # Core Entity Framework page
    core_plat_id = 24281616 # Core Platform page
    info = conf.info(core_ent_fw_id) 
    children = conf.children(core_plat_id)
    print(children)
