===================
System Requirements
===================

..
  * Copyright (c) 2018, salesforce.com, inc.
  * All rights reserved.
  * SPDX-License-Identifier: BSD-3-Clause
  * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

Metro is implemented as a Python module (`metro`) and a few utility programs. To use it, you 
need Python 3 and the following modules:

- `keyring` - A portable keyring for storing passwords
- `requests` - A module for making HTTP/REST requests
- `markdown` - Support for converting Markdown to (X)HTML
- `bleach` - An HTML sanitizer module

If you have a linux or mac, you probably have python already. You can grab the extra modules using the pyton `pip` or `pip3` installers. (This is all standard python functionality. If you are new to python, check out the Beginner's Guide on the `python wiki`_.

---------------------------------------
Installing Trusted SSL/TLS Certificates
---------------------------------------

.. note::
   Currently, metro doesn't validate certificates, so you can ignore this section. Just make sure you are connected via VPN when you use metro.

Because metro uses Confluence's REST API to connect to our internal Confluence
servers, you must install Salesforce's internal Confluence TLS certificates
on your machine before you use it. This enables us to verify that connections
to the Confluence server aren't intercepted.

Installing these certificates is so tricky under some circumstances that one of 
our own has written a `Python module`_ that appends the certificates to those shipped with Python. Arguably not the most 
elegant approach, but it's pretty foolproof.

If that's not your style, you can follow the `official instructions`_ for installing the Salesforce Confluence TLS root certificates to your machine.

.. _python wiki: https://wiki.python.org/moin/BeginnersGuide
.. _Python module: https://git.soma.salesforce.com/python-at-sfdc/sfdc_certs_patch
.. _official instructions: https://sites.google.com/a/salesforce.com/how-to-add-a-trusted-certificate-authority/?pli=1
