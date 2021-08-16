=====================================
Metro-Specific Extensions to Markdown
=====================================

..
  * Copyright (c) 2018, salesforce.com, inc.
  * All rights reserved.
  * SPDX-License-Identifier: BSD-3-Clause
  * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

Because Markdown is so spartan in terms of markup features, and because Confluence has some 
nifty macros we like to use, we have added some metro-specific stuff to Markdown. 

- Info
  
  - Use *> Info: text* to place text into a grey `Confluence Info`_ block.
  - Alternatively, use *~?text?~*.
    
- Notes
  
  - Use *> Note: text* to place text into a yellow `Confluence Note`_ block.
  - Alternatively, use *~!text!~*.
    
- Warnings

  - Use *> Warning: text* to place text into a red `Confluence Warning`_ block.
  - Alternatively, use *~%text%~*.
    
- Panels
  
  - Use *> Panel: title* to create a `Confluence Panel`_  with the given title. Use *> text* on subsequent lines
    to put text into the body of the Panel. The Panel is closed with the first line not beginning with *>*.
      
- Collapsible content
  
  - Use *> Expand: title* to create a `Confluence Expand`_ 
      macro with the given title. Use `> *text*` on subsequent lines to put text into the collapsible portion. The 
      Expand environment is closed with the first line not beginning with *>*.
  - The *title* must be text and not a link. You click the title to expand the collapsed content, not to go somewhere.
    
    .. Note:: Currently, Metro doesn't support the use of nested Expand macros.

  - If you want a button that expands all Expand macros on your page, you can add one with *> ExpandAll*.
    
- Other HTMLisms (as allowed by standard Markdown):
  
    - HTML tables
    - HTML anchors. Use `<a id="anchorName"></a>` to make one, and make sure you use the 
      `Confluence Anchor syntax`_ to link to it (it's more complicated than you might think).
    - HTML images, links, etc

Let us know if you have problems with anything that you'd expect to work.

.. _Confluence Info: https://confluence.atlassian.com/doc/info-tip-note-and-warning-macros-51872369.html
.. _Confluence Note: https://confluence.atlassian.com/doc/info-tip-note-and-warning-macros-51872369.html
.. _Confluence Warning: https://confluence.atlassian.com/doc/info-tip-note-and-warning-macros-51872369.html
.. _Confluence Panel: https://confluence.atlassian.com/doc/panel-macro-51872380.html
.. _Confluence Expand: https://confluence.atlassian.com/doc/expand-macro-223222352.html
.. _Confluence Anchor syntax: https://confluence.atlassian.com/doc/anchors-139442.html
