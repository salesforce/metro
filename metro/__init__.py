# Copyright (c) 2019, salesforce.com, inc.
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
# use this section to test authenticated connection to confluence
#  and the ability to travel the confluence hierarchy
if __name__ == "__main__": 
    server = "https://confluence.internal.mynonprofit.org" # your confluence server, for example 'https://confluence.internal.mynonprofit.org'
    user = "somedude" # a user account authenticated on the server 'somedude'
    conf = Confluence(server, user)
    some_page_id = ""# the confluence ID of a page to test, example 75199145 (no quotes)
    some_page_with_child_pages_id = ""# the confluence ID of a page with child pages, example 24281616 
    info = conf.info(some_page_id) 
    children = conf.children(some_page_with_child_pages_id)
    print(children)
