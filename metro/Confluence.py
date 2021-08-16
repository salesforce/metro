# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

import logging
logger = logging.getLogger()

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class Page(object):
    """Page: an object representing a Confluence page as defined in a Metro manifest file."""

    def __init__(self, 
                 title = None, 
                 body = None, 
                 page_id = None, 
                 parent_id = None,
                 overwrite = False,
                 images = [],
                 attachments = [],
                 auto_gen = None):
        """Page(title = None, body = None, page_id = None, parent_id = None,
     overwrite = False, images = [], attachments = [], auto_gen = None) -> 
new Confluence page with the given content specified. Not all content is required: 
the data needed depend on what you want to do with the page. Content that is 
provided is validated according to these rules:
    * title, if given, must be a string.
    * body, if given, must be a string.
    * page_id, if given, must be a non-negative integer.
    * parent_id, if given, must be a non-negative integer or a dict referring
      to another page.
    * overwrite, if given, must be True or False. This attribute is only used 
      in creating pages.
    * images, if given, must be a list of names of image files (JPEG or PNG) 
      accessible to the filesystem.
    * attachments, if given, must be a list of names of files accessible to 
      the filesystem.
    * work"""

        if title is not None:
            if not isinstance(title, str):
                raise TypeError('Page title must be a string.')
        self.title = title

        if body is not None:
            if not isinstance(body, str):
                raise TypeError('Page body must be a string.')
        self.body = body

        if page_id is not None:
            self.id = int(page_id)
            if self.id < 0:
                raise ValueError('page_id must be non-negative.')
        else:
            self.id = None

        if parent_id is not None:
            if isinstance(parent_id, int):
                if parent_id < 0:
                    raise ValueError('parent_id must be non-negative.')
            elif not isinstance(parent_id, Page):
                raise ValueError('parent_id must be an integer or a Page.')
            self.parent_id = parent_id
        else:
            self.parent_id = None
        if not isinstance(overwrite, bool):
            raise TypeError('overwrite must be a boolean.')
        self.overwrite = overwrite

        import os.path  # for validating image paths.

        if not isinstance(images, list):
            raise TypeError('Page images must be a list of image filenames.')
        else:
            for image in images:
                if not image.lower().endswith('.png') and \
                   not image.lower().endswith('.jpg'):
                    raise TypeError('Page image %s is not a PNG or JPEG file.'%image)
                if not os.path.isfile(image):
                    raise FileNotFoundError('Page image %s not found.'%image)
        self.images = images

        if not isinstance(attachments, list):
            raise TypeError('Page attachments must be a list of filenames.')
        else:
            for attach in attachments:
                if not os.path.isfile(attach):
                    raise FileNotFoundError('Page attachment %s not found.'%attach)
        self.attachments = attachments

        if auto_gen is not None:
            if not isinstance(auto_gen, str):
                raise TypeError('Page working draft must be a string.')
            if 'https' not in auto_gen:
                raise TypeError('Page working draft must be a URI.')
        self.auto_gen = auto_gen

    def __str__(self):
        """String representation of a Page."""
        import os
        if self.title is not None:
            s = 'Page("%s")\n'%self.title
        else: # self.page_id is not None:
            s = 'Page(ID = %i)\n'%self.page_id
        if self.parent_id is not None:
            if isinstance(self.parent_id, int):
                s += ' Parent page ID: %i\n'%self.parent_id
            else:
                s += ' Parent page: %s\n'%self.parent_id['title']
        if self.images is not None:
            s += ' Images: %s\n'%repr([os.path.basename(im) for im in self.images])
        if self.attachments is not None:
            s += ' Attachments: %s\n'%repr([os.path.basename(im) for im in self.attachments])
        return s

class Confluence(object):
    """Confluence: a proxy object for a Confluence server"""

    def __init__(self, url, username = None):
        """Confluence(url, username = None) -> new proxy for Confluence server at the given URL."""
        self.base_url = url
        self.user = username

        # Stash REST endpoint and viewing URIs in the options namespace.
        self.rest_url = "{base}/rest/api/content".format(base = self.base_url)
        self.view_url = "{base}/pages/viewpage.action?pageId=".format(base = self.base_url)

        # Authenticate.
        self._authenticate()

        # Get the server version number.
        logging.info('Connected to %s (v%s)'%(self.base_url, self.version))

        # Keep track of IDs of recently created pages.
        self.pages_created = {}

        # Cache children of pages.
        self._children_cache = {}

    def _authenticate(self):
        """Authenticates the user, returning a (username, password) tuple."""

        # Fetch our username and password.
        import keyring, getpass
        if self.user is None:
            self.user = getpass.getuser()
        key = 'confluence_{url}'.format(url = self.base_url)
        self.passwd = keyring.get_password(key, self.user)
        if self.passwd is None:
            self.passwd = getpass.getpass(prompt="Password for {user}@{url}: ".format(user = self.user, url = self.base_url))
            keyring.set_password(key, self.user, self.passwd)

        # Create a session to use for requests.
        import requests
        self.session = requests.Session()
        self.session.auth = (self.user, self.passwd)
        self.session.headers.update({'Content-Type' : 'application/json'})

        # FIXME: Turn off SSL certificate verification for now.
        # FIXME: We have to figure out SSL certificates for our Confluence 
        # FIXME: servers.
        import urllib3
        urllib3.disable_warnings()
        self.session.verify = False

        # We try to authenticate by asking Confluence for its version number.
        # If this fails, we re-prompt for a password and change it. 
        # Only prompt for a new password once.
        logging.info('Authenticating as %s'%self.user)
        version = self._get_version()
        if version == 'unauthorized':
            # Reset the password from the keyring, since it seems to be bad.
            self.passwd = getpass.getpass(prompt="Password for {user}@{url}: ".format(user = self.user, url = self.base_url))
            keyring.set_password(key, self.user, self.passwd)
            self.session.auth = (self.user, self.passwd)
        version = self._get_version()
        if version == 'unauthorized':
            print('Invalid password.')
            exit(1)
        else:
            self.version = version

        # Give our session a not-stupid retry policy. 
        # (From https://www.peterbe.com/plog/best-practice-with-retries-with-requests)
#        num_retries=3
#        backoff_factor=0.3
#        status_forcelist=(500, 502, 504)
#        from requests.packages.urllib3.util.retry import Retry
#        retry = Retry(total=num_retries,
#                      read=num_retries,
#                      connect=num_retries,
#                      backoff_factor=backoff_factor,
#                      status_forcelist=status_forcelist)
#        from requests.adapters import HTTPAdapter
#        adapter = HTTPAdapter(max_retries=retry)
#        self.session.mount('http://', adapter)
#        self.session.mount('https://', adapter)

    def _get_version(self):
        url = '{base}/rest/applinks/1.0/manifest'.format(base = self.base_url)
        r = self.session.get(url,
                             verify=self.session.verify) # :-( shouldn't need this
        if r.status_code == 200:
            # The manifest is an XML document. We're looking for 
            # manifest->version.
            import xml.etree.ElementTree as et
            root = et.fromstring(r.text) 
            version = None
            for v in root.findall('version'):
                version = v.text
            return version
        elif r.status_code == 401: # Unauthorized!
            logging.info('Could not connect to Confluence server (unauthorized)')
            return 'unauthorized'
        else:
            details = 'details not available'
            try:
                details = r.json()['message']
            except:
                pass
            logging.info('Could not get version for Confluence server: %s (%s)'%(r.reason, details))
            return '??.??.??'

    def _error(self, message):
        raise RuntimeError("Confluence: {m}".format(m = message))

    def _update_page_checksum(self, page):

        # Get the page's existing checksum if it exists.
        checksum, checksum_version = self._get_page_checksum(page.id)

        # Create a new checksum for the page.
        import hashlib, json
        content = page.title + page.body
        page.checksum = hashlib.md5(content.encode('utf-8')).hexdigest()
        prop = {'key': 'checksum',
                'value': page.checksum}
        if checksum_version is not None:
            prop['version'] = {'number': checksum_version + 1}
        data = json.dumps(prop)

        # Store the page's title and checksum as page properties.
        url = '{rest}/{pageid}/property/checksum'.format(rest = self.rest_url, pageid = page.id)
        if checksum is not None: # checksum already exists
            r = self.session.put(url, data = data)
            if r.status_code != 200: 
                logging.info('Could not update checksum for page "%s": %s (%s)'%(page.title, r.reason, r.json()['message']))
                return None
        else: #checksum doesn't exist yet
            # We need to create this property.
            data = json.dumps(prop)
            r = self.session.post(url, data = data)
            if r.status_code != 200:
                logging.info('Could not create checksum for page "%s": %s (%s)'%(page.title, r.reason, r.json()['message']))
                return None
        return page.checksum

    def _get_page_checksum(self, page_id):
        # Get the properties associated with this page.
        import json
        url = '{rest}/{pageid}/property/checksum'.format(rest = self.rest_url, 
                                                         pageid = page_id)
        r = self.session.get(url)
        if r.status_code != 200:
            if r.status_code == 404:
                return None, None
            else:
                logging.info('Could not retrieve checksum for page %i: %s (%s)'%(page_id, r.reason, json()['message']))
                return None, None
        return (r.json()['value'], r.json()['version']['number'])

    def info(self, page_id):
        """conf.info(page_id) -> a dict containing information for the page with the given ID,
or None if no such page exists."""

        url = '{rest}/{pageid}?expand=title,version,space,body.view.value,metadata'.format(rest = self.rest_url, pageid = page_id)
        r = self.session.get(url, 
                             verify=self.session.verify) # :-( shouldn't need this
        if r.status_code == 200:
            return r.json()
        else:
            details = 'details not available'
            try:
                details = r.json()['message']
            except:
                pass
            logging.info('Could not retrieve info for page %i: %s (%s)'%(page_id, r.reason, details))
            return None

    def ancestors(self, page_id):
        """conf.ancestors(page_id) -> a dict of ancestors of the page with the given ID."""

        # Get basic page information plus the ancestors properties
        url = '{rest}/{pageid}?expand=ancestors'.format(rest = self.rest_url, pageid = page_id)
        r = self.session.get(url)
        if r.status_code != 200:
            logging.info('Could not retrieve ancestors for page %i: %s (%s)'%(page.id, r.reason, r.json()['message']))
            return None
        return r.json()['ancestors']

    def children(self, page_id):
        """conf.children(page_id) -> a dict mapping child page IDs to their titles, 
for the page with the given ID, or None if no such ID exists."""

        if page_id in self._children_cache.keys():
            return self._children_cache[page_id]
        else: 
            # Confluence seems to limit us to 200 results max. But it does 
            # let us specify which results to start at, so we can keep going 
            # back till we exhaust the results.
            limit = 200
            url = '{rest}/{pageid}/child?expand=page&limit={limit}'.format(rest = self.rest_url, pageid = page_id, limit = limit)
            r = self.session.get(url)
            if r.status_code == 200:
                children = {}
                results = r.json()['page']['results']
                for r in results:
                    children[r['title']] = int(r['id'])
                # Keep going back for more until there are fewer than 
                # Confluence's undocumented results limit.
                start = limit
                while len(results) == limit:
                    url = '{rest}/{pageid}/child?expand=page&start={start}&limit={limit}'.format(rest = self.rest_url, pageid = page_id, start = start, limit = limit)
                    r = self.session.get(url)
                    if r.status_code == 200:
                        results = r.json()['page']['results']
                        for r in results:
                            children[r['title']] = int(r['id'])
                    start += len(results)
                self._children_cache[page_id] = children
                return children
            else:
                return None

    def create_page(self, parent_id, page):
        """conf.create_page(parent_id, page) -> Creates a new page under a parent page with the given ID.
Returns True if the page is successfully created. If a page with the same title exists under that parent page, 
nothing happens, and the function returns False."""

        # Make sure the page is well-formed.
        assert(page.title is not None)
        assert(page.body is not None)

        # Override the parent_id with the page's entry.
        pid = parent_id
        if page.parent_id:
            pid = page.parent_id

        # If our parent ID is another Page (because this is a child of a page 
        # created in the same manifest), convert it to an ID.
        if isinstance(pid, Page):
            if pid.parent_id:
                pid = pid.id
            else:
                pid = int(self.pages_created[pid.title])

        # Get information about the parent page.
        info = self.info(pid)
        if info is None:
            logging.info('Could not create new page "%s" under nonexistent parent %i.'%(page.title, pid))
            return False
        space_key = info['space']['key']
        parent_title = info['title']

        # See if we already have a page in this set.
        children = self.children(pid)
        if page.title in children.keys():
            page.id = int(children[page.title])
            # If we're allowed to overwrite the page, we update it.
            if page.overwrite:
                self.update_page(page.id, page)
                return True
            else:
                return False

        # There's no page, so we make a new one.
        data = {
            'type': 'page',
            'title': page.title,
            'ancestors': [{'type': 'page', 'id': str(pid)}],
            'space': {'key': space_key},
            'body': {'storage': {'representation': 'storage',
                                 'value': page.body}}
        }
        import json
        r = self.session.post(self.rest_url, data = json.dumps(data))

        # Flesh out the page object with some details from the transaction.
        if r.status_code == 200:
            data = r.json()
            page.space_key = data['space']['key']
            page.id = int(data['id'])
            page.version = int(data['version']['number'])
            page.view_url = '%s%s'%(self.view_url, page.id)
            logging.info('Created new page "%s" (id = %i) under parent "%s"'%(page.title, page.id, parent_title))
            self._update_page_checksum(page)

            # Invalidate the children cache for this page.
            del self._children_cache[pid]
        else:
            logging.info('Could not create new page "%s" under parent "%s": %s (%s)'%(page.title, parent_title, r.reason, r.json()['message']))
            return False

        # Now upload images if need be.
        import os.path
        for image in page.images:
            self.upload_attachment(page.id, 
                                   os.path.basename(image), 
                                   image, 
                                   overwrite = page.overwrite)

        # Update attachments if need be.
        for attachment in page.attachments:
            self.upload_attachment(page.id, 
                                   os.path.basename(attachment), 
                                   attachment, 
                                   overwrite = page.overwrite)

        # Stash the ID of the newly created page.
        self.pages_created[page.title] = page.id

        return True

    def update_page(self, page_id, page):
        """conf.update(page) -> Updates the page the given ID using the content 
of the given page. Returns True if the update succeeds or False if it fails."""

        # Create a checksum for the new page.
        import hashlib
        content = page.title + page.body
        page.checksum = hashlib.md5(content.encode('utf-8')).hexdigest()

        # Get the page's properties.
        checksum, checksum_version = self._get_page_checksum(page_id)

        # We only update the page itself if its title or checksum has changed.
        if checksum is None or page.checksum != checksum:
            # Retrieve and bump the version number.
            info = self.info(page_id)
            ver = int(info['version']['number']) + 1

            # Figure out the parent page.
            ancestors = self.ancestors(page_id)
            anc = ancestors[-1]
            del anc['_links']
            del anc['_expandable']
            del anc['extensions']

            # Assemble our request.
            data = {
                'id': page.id,
                'type': 'page',
                'title': page.title,
                'version': {'number' : ver},
                'ancestors': [anc],
                'body': {'storage': {'representation' : 'storage',
                                     'value' : page.body}}
            }

            # Do it.
            import json
            data = json.dumps(data)
            url = '{rest}/{pageid}'.format(rest = self.rest_url, pageid = page.id)
            r = self.session.put(url, data = data)

            if r.status_code == 200:
                # Flesh out the page object with some details from the transaction.
                data = r.json()
                page.space_key = data['space']['key']
                page.id = int(data['id'])
                page.version = data['version']['number']
                page.view_url = '%s%s'%(self.view_url, page.id)
                logging.info('Updated content for page "%s" (id = %i)'%(page.title, page.id))

                # Update the page's checksum.
                self._update_page_checksum(page)
            else:
                logging.info('Could not update content for page "%s" (id = %i): %s (%s)'%(page.title, page.id, r.reason, r.json()['message']))
                return False
        else:
            logging.info('Did not update content for page "%s" (identical)'%(page.title))

        # Now upload images if need be.
        import os.path
        for image in page.images:
            self.upload_attachment(page.id, 
                                   os.path.basename(image), 
                                   image, 
                                   overwrite = True)

        # Update attachments if need be.
        for attachment in page.attachments:
            self.upload_attachment(page.id, 
                                   os.path.basename(attachment), 
                                   attachment, 
                                   overwrite = True)

        return True

    def delete_page(self, page_id):
        """conf.delete_page(page_id)
Deletes the page with the given ID, returning True on success and False otherwise."""
        url = '{rest}/{pageid}'.format(rest = self.rest_url, pageid = page_id)
        r = self.session.delete(url)
        if r.status_code == 204:
            logging.info('Deleted page (id = %i)'%page.id)
            return True
        else:
            logging.info('Could not delete page (id = %i): %s (%s)'%(page.id, r.reason, r.json()['message']))
            return False

    def upload_attachment(self, page_id, attachment_filename, 
                          local_filename, comment = None, 
                          overwrite = False):
        """conf.upload_attachment(page_id, attachment_filename, local_filename, comment = None, overwrite = False)
Uploads the given local file as an attachment to the page with the given ID. 
If an attachment already exists with the same filename, it is overwritten if:
  * the overwrite flag is set to True
  * the contents of the existing attachment differ from the file being uploaded
Otherwise, this method has no effect. The same rules apply to the comment 
for the attachment."""
        attach_url = '{rest}/{pageid}/child/attachment'.format(rest = self.rest_url, pageid = page_id)
        # First we find out whether the page with the given ID already has 
        # an attachment with the given name.
        url = '{attach}?filename={file}'.format(attach = attach_url, file = attachment_filename)
        r = self.session.get(url)
        if r.status_code == 200:
            attach_info = r.json()
            attachment_exists = len(attach_info['results']) > 0
        else: 
            logging.info('Could not query attachment "%s" on page %i: %s (%s)'%(attachment_filename, page_id, r.reason, r.json()['message']))
            return False # Attachments not allowed on this page?

        # If this page has no such attachment, we create a new one.
        import requests, os.path, mimetypes
        if not attachment_exists:
            # The Confluence REST API requires a multipart-encoded POST 
            # for creating new attachments.
            headers = {'X-Atlassian-Token': 'no-check'}
            content_type, encoding = mimetypes.guess_type(local_filename)
            if content_type is None:
                content_type = 'multipart/form-data'
            files = {'file': (os.path.basename(attachment_filename), open(local_filename, 'rb'), content_type)}
            if comment is not None:
                files['comment'] = str(comment)

            # For some reason, this POST doesn't work when we use our usual
            # session (headers not set up properly?). So we just open a new session 
            # for the upload.
            r = requests.post(attach_url, 
                              files = files,
                              headers = headers,
                              auth=self.session.auth,
                              verify=self.session.verify)
            if r.status_code == 200:
                logging.info('Uploaded new attachment %s'%attachment_filename)
                return True
            else:
                logging.info('Could not upload new attachment "%s" to page %i: %s (%s)'%(attachment_filename, page_id, r.reason, r.json()['message']))
                return False

        elif overwrite:
            attach_info = attach_info['results'][0]
            attach_id = attach_info['id']

            # If we're told to overwrite the existing attachment, 
            # we get the current content so that we can compare it to 
            # what we're uploading.

            # Download the existing attachment.
            download_url = '{base}{dl}'.format(base = self.base_url, dl = attach_info['_links']['download'])
            r = requests.get(download_url, 
                             stream=True, 
                             auth=self.session.auth,
                             verify=self.session.verify)
            if r.status_code == 200:
                # Compare its contents to the file we're uploading, a chunk at a time.
                files_are_identical = True
                chunk_size = 1024
                with open(local_filename, 'rb') as f:
                    for old_bytes in r.iter_content(chunk_size = chunk_size):
                        new_bytes = f.read(chunk_size)
                        if new_bytes[:] != old_bytes[:]:
                            files_are_identical = False
                            break
            elif r.status_code == 500:
                logging.info('Got internal server error from Confluence for attachment "%s" on page %i.'%(attachment_filename, page_id))
                files_are_identical = False
            else:
                logging.info('Could not download existing attachment "%s" on page %i for comparison: %s (%s)'%(attachment_filename, page_id, r.reason, r.json()['message']))
                files_are_identical = False

            # If they're different, we upload the file.
            if not files_are_identical:
                update_url = attach_url + '/' + attach_id + '/data'
                headers = {'X-Atlassian-Token': 'no-check'}
                content_type, encoding = mimetypes.guess_type(local_filename)
                if content_type is None:
                    content_type = 'multipart/form-data'
                files = {'file': (os.path.basename(attachment_filename), open(local_filename, 'rb'), content_type)}

                r = requests.post(update_url, 
                                  files = files,
                                  headers = headers,
                                  auth=self.session.auth,
                                  verify=self.session.verify)
                if r.status_code == 200:
                    logging.info('Updated attachment %s'%attachment_filename)
                    updated = True
                else:
                    logging.info('Could not update existing attachment "%s" on page %i: %s (%s)'%(attachment_filename, page_id, r.reason, r.json()['message']))
                    updated = False
            else:
                updated = False
                logging.info('Did not update attachment %s (identical content)'%attachment_filename)

            # Does the comment need updating?
            old_comment = None
            if 'metadata' in attach_info.keys():
                md = attach_info['metadata']
                if 'comment' in md.keys():
                    old_comment = md['comment']
            if (comment != old_comment):
                comment_url = attach_url + '/' + attach_id
                data = {'comment': comment}
                r = self.session.put(url, data=data)
                if r.status_code == 200:
                    logging.info('Updated comment for attachment %s'%attachment_filename)
                    updated = True
                else:
                    logging.info('Could not update comment for attachment "%s" on page %i: %s (%s)'%(attachment_filename, page.id, r.reason, r.json()['message']))
                    updated = False
            return updated

