=======================================
Preparing to Import a Markdown Document
=======================================

..
  * Copyright (c) 2018, salesforce.com, inc.
  * All rights reserved.
  * SPDX-License-Identifier: BSD-3-Clause
  * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

1. Look over your document and make sure it's clean. If you see oddities in 
   converted content, you can help out metro by using some unambiguous 
   standards for Markdown in your input:
   
   * Use `_` instead of `*` for italic text.
   * Use `+` instead of `*` for unordered lists.
     
2. Place your document file into a folder.
   
3. In the same directory as that folder, create a `manifest.json` file with 
   contents like the following:

   .. code-block:: json
      :caption: manifest.json
      
      {
        "pages": [
          {
            "folder": "doc_folder",
            "file": "doc.md",
            "parent_id": 75199145,
            "operation": "create",
            "overwrite": true,
            "images": [],
            "attachments": []
          }
        ]
      }

   Here, we've assumed you created a file called `doc.md`, and that 
   you want to place it under the Confluence page with the ID 7519945.

4. Metro tries to guess the title of your document, using the first heading it finds.
   This title becomes the title of the imported Confluence page. If you want more control 
   over the Confluence page title, you can include a `title` field in the page entry. 
   This field overrides any title metro finds.

5. If the file has images and/or contents you'd like to attach to your Confluence
   page, place each image and attachment into your folder (`doc_folder` in this case)
   and add their filenames to the `images` and `attachments` fields. 

6. If you want to add child pages to any page, add a field called `children`
   to that page's entry. This field is a JSON list of page entries just like 
   the top-level list in the manifest.

7. For longer documents, you may want to add a table of contents at the top.
   You can do this by adding a `table_of_contents` field to your page's 
   entry in `manifest.json`. This field should be a JSON object with any 
   parameters you want to set in the Confluence table of contents macro. 
   See `this page`_ for details about the macro. Use lower-case text with underscores instead of camel case 
   for the parameter and values (e.g. `max_level` instead of `maxLevel`).

8. If you want to maintain the page content in Google Docs, Quip, or somewhere 
   else outside of Confluence, you can add a link to a working draft of the 
   doc in a `auto_gen` field in your page's entry. This adds a badge to 
   the top of the converted Confluence page with a link to the working draft
   so you can collect questions and comments in one place.

Now your document is ready to be imported.

..   _this page: https://confluence.atlassian.com/doc/table-of-contents-macro-182682099.html
