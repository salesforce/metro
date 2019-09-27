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
// 3. Copy/paste gdoc_to_md.gs into the empty script waiting in your project.
// 
// To select a document for conversion, "star" it by right-clicking it in Google Drive
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
  ++
