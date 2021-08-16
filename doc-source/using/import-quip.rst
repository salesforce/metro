==========================
Converting a Quip Document
==========================

..
  * Copyright (c) 2018, salesforce.com, inc.
  * All rights reserved.
  * SPDX-License-Identifier: BSD-3-Clause
  * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

Converting a Quip document to a Confluence page is easy, because you can export Quip text as Markdown. 

1. Select *Document->Export->Markdown*. This copies Markdown text to your clipboard.
2. Paste the text to your favorite unicode-safe editor and save it to a file with an *.md* suffix.
3. If the Quip document has images and/or contents you'd like to attach to the page, download each image and attachment from Quip.
4. Now just follow the rules for :doc:`prepare-to-import-markdown`.
 
---------------------------
Importing Converted Content
---------------------------

To import a set of files associated with a manifest, use the following command:

```
./import_pages -m /path/to/manifest.json -u <username>
```
where `<username>` is the username for your Confluence account. If you're 
importing a page to our internal Confluence production server, this is just 
your SSO identity (just your username, not your email address).

This finds the files associated with the manifest (assuming they are in the same folder)
and imports them as child pages of their respective parents.
