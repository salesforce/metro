// Code.gs -- Converts a Google Doc to Markdown.
// Part of the Metro Confluence suite.
//

// Copyright (c) 2018, salesforce.com, inc.
// All rights reserved.
// SPDX-License-Identifier: BSD-3-Clause
// For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause


// This Google App script converts selected Google Docs to Markdown, placing 
// the output in a zip file that you can download from your Google Drive root 
// folder. Google App scripts use a language that is like Javascript, but 
// even more lame, so some basic Javascript types (strings, lists) don't have 
// some of the methods that you might expect.
//
// To use this script: 
// 
// 1. Navigate to script.google.com.
// 2. Create a new Google App Script project (named gdoc_to_md, say).
// 3. Copy/paste Code.gs into the empty script waiting in your project.
// 
// You can use this code in standalone fashion, or as part of a google sheet. For standalone,
// to select a document for conversion, "star" it by right-clicking it in Google Drive
// and selecting "Add Star". When you've selected all the docs you want to convert, 
// run the `convert_to_md()` function in the Script using the Script Editor's 
// play button. The first time you run this function, you'll have to give Google
// Drive access to your account.
// 
// When you run the function, it writes a file named Metro-<timestamp>.zip 
// to the root folder in your Google Drive. This file contains a folder with a 
// manifest.json file and converted documents in subfolders. Download this file.
// You can unzip the file to get the converted content, or you can use the zip file directly 
// with the importer.

// List of monospaced fonts in Google Apps.
var monospace_fonts = {"Anonymous Pro": true,
                       "Consolas": true,
                       "Courier": true, 
                       "Courier New": true, 
                       "Cousine": true, 
                       "Cutive Mono": true,
                       "Fira Mono": true,
                       "IBM Plex Mono": true,
                       "Inconsolata": true,
                       "Menlo": true,
                       "Monaco": true,
                       "Nanum Gothic Coding": true,
                       "Nova Mono": true,
                       "Overpass Mono": true,
                       "Oxygen Mono": true,
                       "PT Mono": true,  
                       "Roboto Mono": true,
                       "Share Tech Mono": true,
                       "Source Code Pro": true,
                       "Space Mono": true,
                       "Ubuntu Mono": true,
                       "VT323": true
                      };

// Converts the given Text element to Markdown, appending to the text in doc.
function convert_text(text_elem, doc)
{
  // Get a list of character indices at which distinct formatting changes occur.
  var format_indices = text_elem.getTextAttributeIndices();
  var text = text_elem.getText();
  var text_len = text.length;
  var linkified_formatted_text = '';

  // Tags
  var bold_open_tag = '**', bold_close_tag = '**';
  var ital_open_tag = '_', ital_close_tag = '_';
  var del_open_tag = '_', del_close_tag = '_';
  var code_open_tag = '`', code_close_tag = '`';
  if (doc.format == 'html')
  {
    bold_open_tag = '<b>', bold_close_tag = '</b>';
    ital_open_tag = '<i>', ital_close_tag = '</i>';
    del_open_tag = '<del>', del_close_tag = '</del>';
    code_open_tag = '<code>', code_close_tag = '</code>';
  }

  var num_segments = format_indices.length;
  for (var i = 0; i < num_segments; ++i)
  {
    var formatted_text = '';

    // Get the current formatted chunk.
    var index = format_indices[i];

    // Get the formatting for this chunk.
    var is_bold = text_elem.isBold(index);
    var is_ital = text_elem.isItalic(index);
    var is_del = text_elem.isStrikethrough(index);
    var link_url = text_elem.getLinkUrl(index);
    var is_link = (link_url != null);

    // We ignore fonts except for monospace fonts, which indicate code markup.
    var is_code = (text_elem.getFontFamily(index) in monospace_fonts);

    // Check the previous chunk to see if its formatting is identical to 
    // this one, in which case we skip the opening format tag.
    var skip_bold_tag = false, skip_ital_tag = false, skip_del_tag = false,
        skip_code_tag = false;
    if (i > 0)
    {
      var prev_index = format_indices[i-1];
      var was_bold = text_elem.isBold(prev_index);
      var was_ital = text_elem.isItalic(prev_index);
      var was_del = text_elem.isStrikethrough(prev_index);
      var was_code = (text_elem.getFontFamily(prev_index) == 'Courier New');
      skip_bold_tag = (was_bold == is_bold);
      skip_ital_tag = (was_ital == is_ital);
      skip_del_tag = (was_del == is_del);
      skip_code_tag = (was_code == is_code);
    }

    // Add the opening tag.
    if (is_bold && !skip_bold_tag)
      formatted_text += bold_open_tag;
    if (is_ital && !skip_ital_tag)
      formatted_text += ital_open_tag;
    if (is_del && !skip_del_tag)
      formatted_text += del_open_tag;
    if (is_code && !skip_code_tag)
      formatted_text += code_open_tag;
  
    // Here's the chunk itself.
    var next_index = text_len;
    if (i < num_segments-1)
      next_index = format_indices[i+1];
    var chunk = text_elem.getText().substring(index, next_index);

    // If the chunk ends in whitespace, we save the whitespace for after the closers.
    // Evidently, Google App Script doesn't deal in Javascript Strings, cuz trimEnd() doesn't
    // work. :-( So we have to do this the stupid way.
    var j = chunk.length-1;
    while (chunk.charAt(j) == ' ')
      --j;
    formatted_text += chunk.substring(0, j+1);
    var ws = chunk.substring(j+1, chunk.length);

    // Check the next chunk to see if its formatting is identical to 
    // this one, in which case we skip the closing format tag.
    skip_bold_tag = false; 
    skip_ital_tag = false; 
    skip_del_tag = false;
    if (i < (num_segments-1))
    {
      var next_index = format_indices[i+1];
      var will_bold = text_elem.isBold(next_index);
      var will_ital = text_elem.isItalic(next_index);
      var will_del = text_elem.isStrikethrough(next_index);
      skip_bold_tag = (will_bold == is_bold);
      skip_ital_tag = (will_ital == is_ital);
      skip_del_tag = (will_del == is_del);
    }

    // Close those tags.
    if (is_bold && !skip_bold_tag)
      formatted_text += bold_close_tag;
    if (is_ital && !skip_ital_tag)
      formatted_text += ital_close_tag;
    if (is_del && !skip_del_tag)
      formatted_text += del_close_tag;
    if (is_code)
      formatted_text += code_close_tag;

    // Re-add any whitespace.
    formatted_text += ws;

    // If this was a link, linkify it and add it to our final text.
    if (is_link)
    {
      if (doc.format == 'md')
        linkified_formatted_text += '[' + formatted_text + '](' + link_url + ')';
      else
        linkified_formatted_text += '<a href="' + link_url + '">' + formatted_text + '</a>';
    }
    else
      linkified_formatted_text += formatted_text;
  }

  // Emit the text of the paragraph.
  doc.text += linkified_formatted_text;
}

// Converts the given InlineImage element to Markdown, inserting its link and 
// image data into the doc dictionary.
function convert_image(image, doc)
{
  // Get image data/metadata.
  var width = image.getWidth();
  var height = image.getHeight();
  var alt_desc = image.getAltDescription();
  var blob = image.getBlob();
  var type = blob.getContentType();
  var extension = "";
  if (/\/png$/.test(type)) 
    extension = ".png";
  else if (/\/gif$/.test(type)) 
    extension = ".gif";
  else if (/\/jpe?g$/.test(type)) 
    extension = ".jpg";
  else 
    throw "Unsupported image type: " + type;

  // Generate a filename.
  var filename = doc.prefix + '_' + doc.image_counter + extension;
  ++doc.image_counter;
  
  // Get out of any paragraph environment.
  doc.text += '\n';

  // Stick a link to the image in the text. Use HTML to preserve all the 
  // image attributes.
  if (alt_desc === null)
    alt_desc = filename;
  doc.text += '<img src="images/' + filename + '" alt="' + alt_desc + '" width="' + width + '" height="' + height + '"/>\n';

  // Add the blob to our list of images.
  blob.setName(filename);
  doc.image_blobs.push(blob);
}

// Converts the given Paragraph element to Markdown, updating the given document.
function convert_paragraph(para, doc)
{
  // Handle the paragraph's heading, if it has one.
  var heading = para.getHeading()
  var tag = '';
  if (heading != DocumentApp.ParagraphHeading.NORMAL)
  {
    if (heading == DocumentApp.ParagraphHeading.TITLE)
      tag = '\n# ';
    else if (heading == DocumentApp.ParagraphHeading.HEADING1)
      tag = '\n# ';
    else if (heading == DocumentApp.ParagraphHeading.HEADING2)
      tag = '\n## ';      
    else if (heading == DocumentApp.ParagraphHeading.HEADING3)
      tag = '\n### ';      
    else if (heading == DocumentApp.ParagraphHeading.HEADING4)
      tag = '\n#### ';      
    else if (heading == DocumentApp.ParagraphHeading.HEADING5)
      tag = '\n##### ';     
    else if (heading == DocumentApp.ParagraphHeading.HEADING6)
      tag = '\n###### ';
    doc.text += tag;

    // Since we're in a heading, we can reset our prior list items.
    doc.prior_list_items = [];
  }

  // Traverse the children of this paragraph element.
  var num_children = para.getNumChildren()
  for (var i = 0; i < num_children; ++i)
  {
    var elem = para.getChild(i);
    if (elem.getType() == DocumentApp.ElementType.TEXT)
      convert_text(elem, doc);
    else if (elem.getType() == DocumentApp.ElementType.INLINE_IMAGE)
      convert_image(elem, doc);
    else if (elem.getType() == DocumentApp.ElementType.LIST_ITEM)
      convert_list_item(elem, doc);
    else if (elem.getType() == DocumentApp.ElementType.TABLE)
      convert_table(elem, doc);
  }
  
  // Close the paragraph with an extra newline.
  doc.text += '\n';
}

// Converts the given ListItem element to Markdown, updating the
//  given document. 
function convert_list_item(list_item, doc)
{
  // I can't believe how dumb list items are. There seems to be no way to 
  // traverse a list without duplicates. So we keep a list of strings that we 
  // use to identify list items that we've already traversed. And since Google
  // App Script is even lamer than Javascript, it doesn't have Javascript's
  // List or array objects.
  
  // Make sure we're not in a paragraph environment.
  doc.text += '\n';

  // Traverse the list items.
  var item = list_item;
  var i = 1;
  while ((item != null) && (item.getType() == DocumentApp.ElementType.LIST_ITEM))
  {
    // Have we seem this before?
    var item_text = item.getText();
    var seen_it = false;
    for (var j = 0; j < doc.prior_list_items.length; ++j)
    {
      if (doc.prior_list_items[j] == item_text)
      {
        seen_it = true;
        break;
      }
    }

    if (seen_it)
      break;
    else
    {
      // What glyph type does this list item use?
      var glyph_type = item.getGlyphType();

      if (doc.format == 'md')
      {
        // We use '+' for unordered list elements to avoid the confusion 
        // surrounding '*' in open-source Markdown parsers.
        var glyph = '+'; 
        if (glyph_type == DocumentApp.GlyphType.NUMBER)
          glyph = i + '.';

        // Indent according to the nesting level.
        var level = item.getNestingLevel();
        for (var j = 0; j < level; ++j)
          doc.text += '    ';

        doc.text += glyph + ' ';
      }
      else
      {
        if (i == 1)
        {
          if (glyph_type == DocumentApp.GlyphType.NUMBER)
            doc.text += '<ol>\n';
          else
            doc.text += '<ul>\n';
        }
        doc.text += ' <li>\n';
      }

      convert_paragraph(item, doc);
      if (doc.format == 'html')
        doc.text += ' </li>\n';

      item = item.getNextSibling();

      // Add it to the "done" list.
      doc.prior_list_items.push(item_text);

      ++i;
    }
  }
  if ((i > 1) && (doc.format == 'html'))
  {
    if (glyph_type == DocumentApp.GlyphType.NUMBER)
      doc.text += '</ol>\n';
    else
      doc.text += '</ul>\n';
  }
}

// Converts the given Table element to Markdown, updating the given document.
function convert_table(table, doc)
{
  // We can use 1x1 tables with Courier New to indicate code blocks. Other 1x1 tables with 
  // text just get treated like normal content.
  var is_code_block = false;
  var is_single_cell = false;
  var num_rows = table.getNumRows();
  if (num_rows == 1)
  {
    var row = table.getRow(0);
    var num_cells = row.getNumCells();
    if (num_cells == 1)
    {
      is_code_block = true;
      is_single_cell = true;
      // Okay, we're in a single-cell table. If it contains only paragraphs and 
      // if the text in those paragraphs is in Courier New font, it's a code block.
      // Otherwise, it's "just text".
      var cell = row.getCell(0);
      var num_children = cell.getNumChildren();
      for (var i = 0; i < num_children; ++i)
      {
        var elem = cell.getChild(i);
        if (elem.getType() == DocumentApp.ElementType.PARAGRAPH)
        {
          var num_children = elem.getNumChildren();
          for (var j = 0; j < num_children; ++j)
          {
            var child = elem.getChild(j);
            if (child.getType() == DocumentApp.ElementType.TEXT)
            {
              var is_code = (child.getFontFamily() in monospace_fonts);
              if (!is_code)
              {
                is_code_block = false;
                break;
              }
            }
            else
              is_code_block = false;
            if (!is_code_block)
              break;
          }
        }
        else
          is_code_block = false;
        if (!is_code_block)
          break;
      }
    }
  }

  if (is_code_block)
  {
    // We just extract the text, since that's all there is.
    var cell = table.getRow(0).getCell(0);
    var num_children = cell.getNumChildren();
    doc.text += '```\n';
    for (var i = 0; i < num_children; ++i)
    {
      var elem = cell.getChild(i);
      if (elem.getType() == DocumentApp.ElementType.PARAGRAPH)
      {
        var num_subelems = elem.getNumChildren();
        for (var j = 0; j < num_subelems; ++j)
        {
          var child = elem.getChild(j);
          if (child.getType() == DocumentApp.ElementType.TEXT)
            doc.text += child.getText() + '\n';
        }
      }
    }
    doc.text += '```\n';
  }
  else if (is_single_cell)
  {
    // Convert the cell as we would normal content.
    var cell = table.getRow(0).getCell(0);
    var num_children = cell.getNumChildren();
    for (var i = 0; i < num_children; ++i)
    {
      var elem = cell.getChild(i);
      if (elem.getType() == DocumentApp.ElementType.LIST_ITEM)
        convert_list_item(elem, doc);
      else if (elem.getType() == DocumentApp.ElementType.PARAGRAPH)
        convert_paragraph(elem, doc);
      else if (elem.getType() == DocumentApp.ElementType.TABLE)
        convert_table(elem, doc);
    }
  }
  else
  {
    // Switch to HTML format.
    var old_format = doc.format;
    doc.format = 'html';

    // Since Markdown doesn't directly support tables, we use inline HTML.
    doc.text += '<table class="wrapped">\n';

    // Process each row in the table.
    for (var r = 0; r < num_rows; ++r)
    {
      doc.text += ' <tr>\n';
      var row = table.getRow(r);
      var num_cells = row.getNumCells();

      // Process each cell in the table row.
      for (var c = 0; c < num_cells; ++c)
      {
        if (r == 0)
          doc.text += '  <th>\n';
        else
          doc.text += '  <td>\n';

        var cell = row.getCell(c);

        // A table cell can contain list items, paragraphs, and/or tables(!).
        var num_children = cell.getNumChildren();
        for (var i = 0; i < num_children; ++i)
        {
          var elem = cell.getChild(i);
          if (elem.getType() == DocumentApp.ElementType.LIST_ITEM)
            convert_list_item(elem, doc);
          else if (elem.getType() == DocumentApp.ElementType.PARAGRAPH)
            convert_paragraph(elem, doc);
          else if (elem.getType() == DocumentApp.ElementType.TABLE)
            convert_table(elem, doc);
        }

        if (r == 0)
          doc.text += '  </th>\n';
        else
          doc.text += '  </td>\n';
      }
      doc.text += ' </tr>\n';
    }
    doc.text += '</table>\n';

    // Restore the original format.
    doc.format = old_format;
  }
}

// Writes the converted Markdown document and its images to the given folder.
function write_converted_doc(doc)
{
  // Write the Markdown document itself to the doc's folder.
  var file = doc.folder.createFile(doc.filename, doc.text, 'text/plain');

  // Write the images to the document's image folder.
  for (var i = 0; i < doc.image_blobs.length; ++i)
    doc.image_folder.createFile(doc.image_blobs[i]);
}

function get_blobs(folder, path)
{
  var blobs = [];
  var files = folder.getFiles();
  while (files.hasNext()) 
  {
    var file = files.next().getBlob();
    file.setName(path + '/' + file.getName());
    blobs.push(file);
  }
  var folders = folder.getFolders();
  while (folders.hasNext()) 
  {
    var f = folders.next();
    var f_path = path + '/' + f.getName() +'/';
    blobs.push(Utilities.newBlob([]).setName(f_path));
    blobs = blobs.concat(get_blobs(f, f_path));
  }
  return blobs;
}

// Zips up the given folder and its contents, adding .zip to its name and returning the file.
function zip_folder(folder)
{
  // Create a list of blobs for the folder.
  var blobs = get_blobs(folder, folder.getName());

  var zip = Utilities.zip(blobs, folder.getName() + '.zip');
  return DriveApp.createFile(zip);
}

// Converts the given document to Markdown, placing the output in 
// the given folder. Returns a dictionary holding manifest data.
function convert_file(file_data, folder)
{
  // Access the file as a document.
  var doc = DocumentApp.openById(file_data['id']);
  Logger.log('Converting ' + doc.getName() + '.')

  // This dictionary holds all the data for the converted doc.
  conv_doc = {};

  // Get the title of the document.
  conv_doc.title = doc.getName();

  // Create a file prefix for this doc, replacing spaces with underscores.
  conv_doc.prefix = doc.getName().replace(/ /g, '_');

  // Create a folder that holds all the doc's stuff, and an images folder 
  // within it.
  conv_doc.folder = folder.createFolder(conv_doc.prefix);
  conv_doc.image_folder = conv_doc.folder.createFolder('images');

  // Point at the generated file within the folder.
  conv_doc.filename = conv_doc.prefix + '.md';

  // Reset the blobs list and counter.
  conv_doc.image_counter = 0;
  conv_doc.image_blobs = [];

  // Doc text.
  conv_doc.text = '';

  // An array of list items, because Stupid.
  conv_doc.prior_list_items = [];

  // Formatting can be Markdown ("md") or HTML ("html"). We switch while
  // in tables.
  conv_doc.format = 'md';

  // Access the document's body and convert each element.
  var body = doc.getBody();
  var num_children = body.getNumChildren();
  for (var i = 0; i < num_children; ++i)
  {
    var elem = body.getChild(i);
    if (elem.getType() == DocumentApp.ElementType.LIST_ITEM)
      convert_list_item(elem, conv_doc);
    else if (elem.getType() == DocumentApp.ElementType.PARAGRAPH)
      convert_paragraph(elem, conv_doc);
    else if (elem.getType() == DocumentApp.ElementType.TABLE)
      convert_table(elem, conv_doc);
    else if (elem.getType() == DocumentApp.ElementType.INLINE_IMAGE)
      convert_image(elem, conv_doc);
  }
  
  // Write out the converted doc.
  write_converted_doc(conv_doc);

  // Generate a manifest entry for the doc.
  manifest = {};
  manifest.folder = conv_doc.prefix;
  manifest.file = conv_doc.filename;
  manifest.parent_id = file_data['parent_id'];
  manifest.title = conv_doc.title;
  manifest.operation = 'create';
  manifest.overwrite = true;
  image_files = [];
  for (var i = 0; i < conv_doc.image_blobs.length; ++i)
    image_files.push('images/' + conv_doc.image_blobs[i].getName());

  manifest.images = image_files;
  manifest.attachments = [];

  // If this file is a working draft, add a link to the Google doc.
  if (file_data['auto_gen'])
    manifest.auto_gen = doc.getUrl();
  
  // Do we need a table of contents?
  if (file_data['table_of_contents'] != false)
    manifest.table_of_contents = file_data['table_of_contents'];

  return manifest;
}

// Makes a list of documents referenced in our spreadsheet, either directly or 
// by their parent folder.
function gather_docs()
{
  // Access our "Metro" spreadsheet.
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheets()[0];
  
  // Loop over the rows in the spreadsheet and build a dictionary of file data.
  var data = sheet.getDataRange().getValues();
  var file_data = {};
  for (var row = 1; row < data.length; ++row)
  {
    var publish = data[row][0]; // selected for publication?
    var resource = data[row][1]; // resource name
    if (publish && (resource.length > 0))
    {
      var type = data[row][2]; // 'File' or 'Folder'
      var parent_page_id = parseInt(data[row][3], 10); // Confluence parent page ID
      var auto_gen = false;
      if (data[row][4] == true)
        auto_gen = true;
      var table_of_contents = false;
      if ((data[row][5] != '') && (data[row][5] != 'None'))
      {
        var max_level = null;
        var substr = data[row][5].substring(9, 10);
        if (substr != null)
          max_level = parseInt(substr, 10);
        if (max_level != null)
          table_of_contents = {'max_level': max_level};
      }
      Logger.log(resource + ': ' + type + ', ' + parent_page_id + ', ' + auto_gen + ', ' + table_of_contents);
    
      // If we're dealing with a folder, traverse the folder and add all its contents to our dictionary.
      if (type == 'Folder')
      {
        var folders = DriveApp.getFoldersByName(resource);
        while (folders.hasNext())
        {
          var folder = folders.next();
          var files = folder.getFilesByType('application/vnd.google-apps.document');
          while (files.hasNext())
          {
            var file = files.next();
            file_data[file.getName()] = {'id': file.getId(),
                                         'parent_id': parent_page_id,
                                         'auto_gen': auto_gen,
                                         'table_of_contents': table_of_contents};
          }
        }
      }
      // Otherwise, just add the data for this file.
      else
      {
        var files = DriveApp.getFilesByName(resource);
        while (files.hasNext())
        {
          var file = files.next();
          file_data[file.getName()] = {'id': file.getId(),
                                       'parent_id': parent_page_id,
                                       'auto_gen': auto_gen,
                                       'table_of_contents': table_of_contents};
        }
      }
    }
  }
  
  return file_data;
}

// Shows a list of files selected for publication in a nice table.
function show_selected_files()
{
  var ui = SpreadsheetApp.getUi();

  // Gather all documents identified in the spreadsheet.
  var file_data = gather_docs();

  // If there are no files selected for publication, pop up an alert and return.
  if (Object.keys(file_data).length == 0)
  {
    ui.alert("There are no files selected for publication. Select a row in the spreadsheet and make sure its information matches one of your files or folders.", ui.ButtonSet.OK);
    return;
  }
  
  // Assemble an HTML table to display the selected files.
  var text = '<style>\ntable, th, td {\n border: 1px solid black;\n}\n</style>\n<table>\n<tr><th>Title</th><th>Parent Page ID</th><th>Working draft?</th><th>Table of contents?</th></tr>\n';
  for (var filename in file_data)
  {
    var data = file_data[filename];
    var doc = DocumentApp.openById(data['id']);
    var url = doc.getUrl();
    var draft = 'No';
    if (data['auto_gen'])
      draft = 'Yes';
    var toc = 'No';
    if (data['table_of_contents'] != false)
      toc = 'Yes';
    text += '<tr><td><a href="' + url + '" target="_blank">' + filename + '</a></td><td>' + data['parent_id'] + '</td><td>' + draft + '</td><td>' + toc + '</td></tr>\n';
  }
  text += '</table>\n<br>\n';
  text += '<input type="button" value="Close" onclick="google.script.host.close()"/>\n';
  
  // Pop up a dialog with the table.
  var html = HtmlService.createHtmlOutput(text);
  ui.showModalDialog(html, 'Files Selected for Publication');
}

// Converts the contents of our Confluence conversion folder to a folder named
// Metro-<timestamp.zip with files written in Markdown.
function convert_to_md() 
{
  var ui = SpreadsheetApp.getUi();

  // Create a timestamp.
  var timestamp = Utilities.formatDate(new Date(), "GMT", "yyyy-MM-dd'T'HHmmss'Z'");

  // Gather all documents identified in the spreadsheet.
  var file_data = gather_docs();

  // If there are no files selected for publication, pop up an alert and return.
  if (Object.keys(file_data).length == 0)
  {
    ui.alert("There are no files selected for publication. Select a row in the spreadsheet and make sure its information matches one of your files or folders.", ui.ButtonSet.OK);
    return;
  }
  
  // Make a folder that will hold converted documents.
  var conv_folder_name = 'Metro-' + timestamp;
  var conv_folder = DriveApp.createFolder(conv_folder_name);
  
  // Pages for the manifest.
  pages = [];

  for (var filename in file_data)
  {
    var data = file_data[filename];

    // Convert the doc to Markdown.
    doc_manifest = convert_file(data, conv_folder);

    // Append this doc to our list of pages.
    pages.push(doc_manifest);
  }

  // Write the manifest file.
  var manifest = {};
  manifest.pages = pages;
  conv_folder.createFile('manifest.json', JSON.stringify(manifest, null, 2));

  // Create a zipfile containing the folder and remove the original.
  var zip = zip_folder(conv_folder);
  DriveApp.removeFolder(conv_folder);
  
  // Get our SSO username.
  var user_email = Session.getActiveUser().getEmail();
  var username = user_email.substring(0, user_email.indexOf('@'));
  
  // Pop up a dialog with a link to the zip file.
  var zip_url = 'https://docs.google.com/uc?export=download&id=' + zip.getId();
  var text = '<p>Your documents have been converted to Markdown and zipped up here: <a href="' + zip_url + '">' + zip.getName() + '</a>.</p>\n';
  text += '<code>./import_pages -z ' + zip.getName() + ' -u ' + username + '</code>\n';
  text += '<br><input type="button" value="Close" onclick="google.script.host.close()"/>\n';
  var html = HtmlService.createHtmlOutput(text).setWidth(400).setHeight(300);
  ui.showModalDialog(html, 'Conversion completed');
}

// This function displays help for Metro.
function help()
{
  var page = "https://metro.readthedocs.io/en/latest/using/convert-google-doc.html";
  var text = "<script>window.open('" + page + "');google.script.host.close();</script>";
  var html = HtmlService.createHtmlOutput(text);
  SpreadsheetApp.getUi().showModalDialog(html, 'Metro Help');
}

// This function runs when the Metro spreadsheet is opened.
function onOpen() 
{
  SpreadsheetApp.getUi()
      .createMenu('Metro')
      .addItem('Show Selected Files', 'show_selected_files')
      .addItem('Convert to Markdown', 'convert_to_md')
      .addItem('Metro Help (SFM Required)', 'help')
      .addToUi();
}
