==========================
Frequently Asked Questions
==========================

..
  * Copyright (c) 2018, salesforce.com, inc.
  * All rights reserved.
  * SPDX-License-Identifier: BSD-3-Clause
  * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

1. **Does `import_pages` update pages with no changes?**

   Nope! If a page's content hasn't 
   changed since the last import, no update is performed. The same goes for 
   images and attachments: they are only updated if they've changed. Metro 
   accomplishes this by computing MD5 checksums for new content and storing 
   them as metadata on Confluence for comparison during updates.

2. **What kinds of markup does Metro support?**

   Anything in basic Markdown is fair game:

   * Headings (1-6)
   * **Bold**, _italic_, and `monospace` text
   * Ordered and unordered lists (try to use + instead of \*)
   * Code blocks
   * Links
   * Inlined images (in HTML, for simplicity)
   * Tables (in HTML, to preserve image attributes)

3. **If a page entry in the manifest contains a `parent_id` field and I specify a `parent_id`
   on the command line, which parent ID "wins"?**
   
   A parent ID specified in a manifest always overrides a parent ID specified from the 
   command line.

-----------
Google Docs
-----------

1. **How do I make a "code block" in a Google Doc?**

   Make a single-cell 
   (1x1) table and use `Courier New` for the text inside. That table will 
   be converted to a code block.

2. **Some of the headings in the Confluence page for my Google Doc are... off.
   What's going on?**

   Check the type of headings you used. Metro doesn't pay 
   attention to font sizes, so if you sized up a smaller heading, that won't 
   translate.
