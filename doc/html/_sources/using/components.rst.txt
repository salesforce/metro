==========
Components
==========
..
  * Copyright (c) 2018, salesforce.com, inc.
  * All rights reserved.
  * SPDX-License-Identifier: BSD-3-Clause
  * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

Importing a document into Confluence involves two Metro components:

1. A **converter** for getting the document into the intermediate representation.
2. An **importer** for getting the intermediate representation into Confluence.

Metro has a converter for each type of document supported. type of document you want to convert. All 
conversion tools produce a zip file with a JSON manifest, `manifest.json`, at the top 
level of the zipped folder tree. This manifest contains information about any pages, 
images, and attachments that have been converted, and how they relate to each other.

There's only one importer: `import_pages`. This Python script takes a manifest and a set of 
files (or a zip file containing the manifest and those files) and imports the content into 
Confluence. The manifest is a JSON file that tells `import_pages` where to place the imported
content, what images and attachments to upload, and so on.
