# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

class ManifestError(Exception):
    """Exception raised for errors in validating a Manifest.

Attributes: 
    message - The error message associated with the exception."""
    
    def __init__(self, message):
        self.message = message

class Manifest(object):
    """Manifest: an object representing the contents of a Metro manifest file."""

    def __init__(self, json_file):
        """Manifest(json_file) -> new Manifest object created from the 
given JSON file with the given absolute path."""
        import os.path
        if not isinstance(json_file, str):
            raise TypeError('json_file must be the name of a file containing a JSON manifest.')
        elif not os.path.isfile(json_file):
            raise FileNotFoundError('The JSON manifest file %s was not found.'%json_file)

        # Extract the prefix for all the files from the manifest filename.
        # We will prepend this prefix to all filenames in pages.
        self.prefix = os.path.dirname(json_file)
        # Parse the manifest into a big dictionary.
        import json
        with open(json_file, 'r') as f:
            manifest = json.loads(f.read())
        # Validate the dictionary and populate the Manifest with it.
        if 'pages' not in manifest.keys():
            raise ManifestError('The JSON manifest file has no "pages" entry.')
        pages = manifest['pages']
        if not isinstance(pages, list):
            raise ManifestError('The "pages" entry in the JSON manifest file is not a list.')
        import os
        for page in pages:
            if not isinstance(page, dict):
                raise ManifestError('Each page in the "pages" entry for the JSON manifest file must be a JSON object.')
            self.validate_page(page)

        # Now populate our page lists.
        self.pages_to_create = []
        self.pages_to_update = []
        self.pages_to_delete = []
        for page in pages:
            self._add_page(page)

    def _add_page(self, page):
        import os.path
        folder = os.path.join(self.prefix, page['folder']) or self.prefix

        # Do we want a table of contents?
        toc = None
        if 'table_of_contents' in page.keys():
            toc = page['table_of_contents']

        # Are we adding a badge explaining this is a work in progress?
        auto_gen = None
        if 'auto_gen' in page.keys():
            auto_gen = page['auto_gen']

        if page['operation'] == 'create':
            file_path = os.path.join(folder, page['file'])

            # Get the title and/or body from the file.
            (title, body) = self.parse_page_body(file_path, 
                                                 table_of_contents = toc,
                                                 auto_gen = auto_gen)

            # Get the front matter on markdown file
            front_matter = self._evaluate_front_matter(file_path)

            # Overwrite the title with any specified one.
            if 'title' in page.keys():
                title = page['title']
            else:
                title = front_matter['title']

            overwrite = False
            if 'overwrite' in page.keys():
                overwrite = bool(page['overwrite'])

            parent_id = None
            if 'parent_id' in page.keys():
                from metro.Confluence import Page
                # A parent ID can be either an integer or a Confluence Page object.
                parent_id = page['parent_id']
                if not isinstance(parent_id, int) and not isinstance(parent_id, Page):
                    raise ManifestError('The "parent_id" field must be an integer or a reference to another page.')

                # If the parent page has an ID, let's translate it here.
                if isinstance(parent_id, Page) and parent_id.id:
                    parent_id = parent_id.id

            images = []
            if 'images' in page.keys():
                images = [os.path.join(folder, im) for im in page['images']]

            attachments = []
            if 'attachments' in page.keys():
                attachments = [os.path.join(folder, a) for a in page['attachments']]

            # Append this page to our list.
            from metro.Confluence import Page
            new_page = Page(title = title, 
                            body = body, 
                            parent_id = parent_id,
                            overwrite = overwrite,
                            images = images,
                            attachments = attachments,
                            auto_gen = auto_gen)
            self.pages_to_create.append(new_page)

            # Are there child pages in here?
            children = []
            if 'children' in page.keys():
                children = page['children']

            # Handle the children.
            for child in children:
                # For now, 'parent_id' points to the new Page object. 
                child['parent_id'] = new_page
                self._add_page(child)

        elif page['operation'] == 'update':
            file_path = os.path.join(folder, page['file'])

            # Get the title and/or body from the file.
            (title, body) = self.parse_page_body(file_path,
                                                 table_of_contents = toc,
                                                 auto_gen = auto_gen)

            # Get the front matter on markdown file
            front_matter = self._evaluate_front_matter(file_path)

            # Overwrite the title with any specified one.
            if 'title' in page.keys():
                title = page['title']
            else:
                title = front_matter['title']

            images = []
            if 'images' in page.keys():
                images = [os.path.join(folder, im) for im in page['images']]

            attachments = []
            if 'attachments' in page.keys():
                attachments = [os.path.join(folder, a) for a in page['attachments']]

            # Append this page to our list.
            updated_page = Page(title = title, 
                                body = body, 
                                page_id = int(page['page_id']),
                                images = images,
                                attachments = attachments,
                                auto_gen = auto_gen)
            self.pages_to_update.append(updated_page)

            # Are there child pages in here?
            children = []
            if 'children' in page.keys():
                children = page['children']

            # Handle the children.
            for child in children:
                child['parent_id'] = page['page_id']
                self.add_page(child)

        else: # page['operation'] == 'delete'
            # Append this page to our delete list.
            page_to_delete = Page(page_id = int(page['page_id']))
            self.pages_to_delete.append(page_to_delete)

    def validate_page(self, page_dict):
        # Figure out the operation and use that to determine whether we have 
        # enough data to work with.
        if 'operation' not in page_dict.keys():
            raise ManifestError('A page in the manifest is missing the "operation" entry.')
        if page_dict['operation'] not in ['create', 'update', 'delete']:
            raise ManifestError('Invalid operation found for manifest page: %s'%page_dict['operation'])
        if page_dict['operation'] == 'create':
#            if 'parent_id' not in page_dict.keys():
#                raise ManifestError('The "create" operation for a page requires a parent_id.')
            if 'file' not in page_dict.keys():
                raise ManifestError('The "create" operation for a page requires a file.')
        elif page_dict['operation'] == 'update':
            if 'page_id' not in page_dict.keys():
                raise ManifestError('The "update" operation for a page requires a page_id.')
            if 'file' not in page_dict.keys():
                raise ManifestError('The "update" operation for a page requires a file.')
        else: # page_dict['operation'] == 'delete'
            # We need the page_id attribute to delete a page.
            if 'page_id' not in page_dict.keys():
                raise ManifestError('The "delete" operation for a page requires a page_id.')

        # Now that we know whether we have all the data we need, validate 
        # each datum.

        # Page ID
        try:
            page_id = int(page_dict['page_id'])
            if page_id < 0:
                raise ValueError()
        except ValueError:
            raise ManifestError('The "page_id" attribute for a page must be a non-negative integer.')
        except:
            pass

        # Parent page ID
        try:
            parent_id = int(page_dict['parent_id'])
            if parent_id < 0:
                raise ValueError()
        except ValueError:
            raise ManifestError('The "parent_id" attribute for a page must be a non-negative integer.')
        except:
            pass

        # Title (if given)
        if 'title' in page_dict.keys():
            title = page_dict['title']
            if not isinstance(title, str):
                raise ManifestError('The "title" attribute for a page must be a string.')

        # Folder (if given)
        import os.path
        folder = self.prefix
        if 'folder' in page_dict.keys():
            folder_name = page_dict['folder']
            if not isinstance(folder_name, str):
                raise ManifestError('The "folder" attribute for a page must be a string.')
            folder = os.path.join(self.prefix, folder_name) 
            if not os.path.isdir(folder):
                raise ManifestError('The page folder %s is not a valid directory.'%folder)

        # File (if given)
        if 'file' in page_dict.keys():
            file_name = page_dict['file']
            if not isinstance(file_name, str):
                raise ManifestError('The "file" attribute for a page must be a string.')
            file_path = os.path.join(folder, file_name) 
            if not os.path.isfile(file_path):
                raise ManifestError('The page file %s is not a valid file.'%file_path)

        # Overwrite directive (only used for create operation)
        if 'overwrite' in page_dict.keys():
            overwrite = page_dict['overwrite']
            if not isinstance(overwrite, bool) and overwrite not in ['true', 'false']:
                raise ManifestError('The "overwrite" page attribute must be true or false.')
            overwrite = (overwrite == True) or (overwrite == 'true')

        # Images (if given)
        if 'images' in page_dict.keys():
            images = page_dict['images']
            if not isinstance(images, list):
                raise ManifestError('The "images" attribute for a page must be a list.')
            for image in images:
                if not image.lower().endswith('.png') and \
                   not image.lower().endswith('.jpg'):
                    raise TypeError('Page image %s is not a PNG or JPEG file.'%image)
                im_file = os.path.join(folder, image)
                if not os.path.isfile(im_file):
                    raise FileNotFoundError('Page image %s not found.'%image)

        # Attachments (if given)
        if 'attachments' in page_dict.keys():
            attachments = page_dict['attachments']
            if not isinstance(attachments, list):
                raise ManifestError('The "attachments" attribute for a page must be a list.')
            for attach in attachments:
                a_file = os.path.join(folder, attach)
                if not os.path.isfile(a_file):
                    raise FileNotFoundError('Page attachment %s not found.'%attach)

    def parse_page_body(self, page_file, 
                        table_of_contents = None, 
                        auto_gen = None):
        """manifest.parse_page_body(page_file, table_of_contents = None, auto_gen = None) -> (title, body)
Parse the page file and extract the page's title and body separately."""
        lines = self._read_lines(page_file)

        # Fetch the title from the lines.
        title = 'Untitled'
        for i in range(len(lines)):
            if lines[i].startswith('# '):
                title = lines[i].replace('# ', '').strip()
                break

        # Removing a part between '---' from Jekyll-formatted markdown file.
        # Otherwise, throws an exception and print out a message
        try:
            first_occurrence = lines.index('---\n')
            last_occurrence = len(lines) - lines[::-1].index('---\n') - 1
            for index in range(first_occurrence, last_occurrence + 1):
                lines.pop(first_occurrence)
        except ValueError as e:
            print(e)

        # Now convert the Markdown content to Confluence XHTML.
        from metro.markdown_to_xhtml import markdown_to_xhtml
        body = markdown_to_xhtml(title, ''.join(lines), 
                                 table_of_contents = table_of_contents, 
                                 auto_gen = auto_gen)
        return (title, body)

    def __str__(self):
        """String representation of a Manifest."""
        s = 'Metro Manifest:\n\n'

        if len(self.pages_to_create) > 0:
            s += '------------------------------------\n'
            s += 'The following pages will be created:\n'
            s += '------------------------------------\n\n'
            for page in self.pages_to_create:
                s += str(page) + '\n'

        if len(self.pages_to_update) > 0:
            s += '------------------------------------\n'
            s += 'The following pages will be updated:\n'
            s += '------------------------------------\n\n'
            for page in self.pages_to_update:
                s += str(page) + '\n'

        if len(self.pages_to_delete) > 0:
            s += '------------------------------------\n'
            s += 'The following pages will be deleted:\n'
            s += '------------------------------------\n\n'
            for page in self.pages_to_delete:
                s += str(page) + '\n'
 
        return s
	

    def _evaluate_front_matter(self, markdown_file):
        # Jekyll-formatted markdown documents have a section of front matter at the top with three dashes.
        # ---
        # title: SQL Support Summary
        # excerpt: SDB SQL support as compared to PostgreSQL
        # toc: false
        # tags: [dml,ddl,queries]
        # ---
        # We want to recognize each value inside dashes.
        inside_dash = False
        lines = self._read_lines(markdown_file)
        
        front_matter = {}
        for i in range(len(lines)):
            if lines[i].startswith('---'):
                inside_dash = not inside_dash
            elif lines[i].startswith('title: '):
                front_matter['title'] = lines[i].replace('title: ', '').strip()
            elif lines[i].startswith('excerpt: '):
                front_matter['excerpt'] = lines[i].replace('excerpt: ', '').strip()
            elif lines[i].startswith('toc: '):
                front_matter['toc'] = lines[i].replace('toc: ', '').strip()
            elif lines[i].startswith('tags: '):
                front_matter['tags'] = lines[i].replace('tags: ', '').strip()
            elif lines[i].startswith('---') and inside_dash:
                break
        return front_matter
        
    def _read_lines(self, file_to_read):
        # Try utf-8 encoding first.
        with open(file_to_read, mode='r', encoding='utf-8') as f:
            try:
                lines = f.readlines()
            except UnicodeDecodeError:
                # Drat. Must be regular ASCII. Quip does this.
                f.close()
                with open(file_to_read, mode='r', encoding='latin-1') as f:
                    lines = f.readlines()
        return lines

