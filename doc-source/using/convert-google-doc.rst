=======================
Converting a Google Doc
=======================

..
  * Copyright (c) 2018, salesforce.com, inc.
  * All rights reserved.
  * SPDX-License-Identifier: BSD-3-Clause
  * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

The Google Doc converter is a spreadsheet-based user interface for selecting
Google documents with some simple metadata. To use it:

1. Create a google sheet that has the format depicted in this figure:

   .. figure:: ../images/gsheet-example.png
	:scale: 50%
	:alt: Use a simple Google Sheet to list your docs and folders.

2. Create a google script project and attach it to the google sheet.

3. Include the content from the *code.gs* file (in this repo root) as the code for your script project.

4. Add to the script project a new html source file, *download.html*. For its content, add the html contained in the download.html file (in this repo root). Save the project and sheet.

5. In each row of the spreadsheet:
   
  * In the Resource column, fill in the Google Doc name of a document or a folder containing documents that you want to publish.
  * In the File or Folder column, select File or Folder, depending on the type of the resource you specified.
  * In the Confluence Parent Page ID column, specify the [page ID](https://confluence.atlassian.com/confkb/how-to-get-confluence-page-id-648380445.html) of the Confluence page under which this resource is to be published.
  * In the Working Draft column, check the box if you want a badge at the top of your published Confluence page that links to your document in Google Drive.
  * Finally, in the Table of Contents column, select the appropriate option. The TOC will be at the top of the finished page. If you want no TOC, select *None*.

6. Delete any extra rows that contain only partial information.

7. Now check the box in the first column of each resource you'd like to publish.

8. Editing the spreadsheet should reveal the *Metro* menu at the top of the sheet. Click it and select *Show Selected Files*
   to bring up a dialog box of the documents you're publishing.

9. In the *Metro* menu, select *Convert to Markdown* to convert the selected resources to Markdown. The conversion process can take a while, depending on the number and complexity of the documents you're converting. The process produces a .zip file that you can download by clicking the link in the resulting dialogue.

10. After downloading the zip file, you can unzip it to inspect or modify its contents if you like. When you're ready to publish it to confluence, you can use the *import_pages* script with the *-z* option. You don't need to supply a parent page ID, since you've already specified one for each page in the spreadsheet.

