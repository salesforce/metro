==========
Overview
==========

..
  * Copyright (c) 2018, salesforce.com, inc.
  * All rights reserved.
  * SPDX-License-Identifier: BSD-3-Clause
  * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

Metro is a system for reducing friction in the process of publishing long-lived technical documentation at Salesforce. Confluence, our publishing environment, ships without any reasonable way to import content from other sources: as it is, you can import files directly in its cute XHTML pidgin tongue, or you can hamfistedly shove a PDF or a Word document into it. Great job onboarding your users, Confluence!

You'd think that third-party solutions would step up and solve this problem. Unfortunately, the third-party Confluence ecosystem seems a little moribund these days. Many products haven't been touched in years, and those that are maintained often don't seem like they've been thought through properly.

Metro solves this problem by choosing an intermediate representation for all of the docs we want to publish, and providing tools to 

- convert our docs to that intermediate representation
- import that representation into Confluence directly and systematically

Metro can interpret information in a JSON manifest file to decide how a given page or set of pages is published.
