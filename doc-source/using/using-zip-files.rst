=======================================
Using zip files (e.g. with Google Docs)
=======================================

..
  * Copyright (c) 2018, salesforce.com, inc.
  * All rights reserved.
  * SPDX-License-Identifier: BSD-3-Clause
  * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

Another easy way to import stuff into Confluence is to hand it a zip file with converted
documents and specify a parent page under which the documents will live. Each of these
documents becomes a Confluence page under the parent page.

.. code-block:: bash
		
   ./import_pages -z converted_stuff.zip -p <parent_page_id> -u <username>


You only need to provide a parent `page ID`_ if your manifest includes pages that don't have 
*parent_id* fields. If you specify a parent page with *-p*, the *parent_id* field in the 
manifest overrides the parent page you provide with this option.

To get a Confluence page ID, click *...* on that page's menu bar and select 
*Page Information*. The page ID is the last portion of the URL for the resulting page.

You can do a lot more with the importer. For details, get usage information from 
*import_pages* with 

.. code-block:: bash
		
   ./import_pages --help

.. _page ID: https://confluence.atlassian.com/confkb/how-to-get-confluence-page-id-648380445.html
