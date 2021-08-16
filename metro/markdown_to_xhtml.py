# Copyright (c) 2018, salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause

def markdown_to_xhtml(title, 
                      md_content, 
                      table_of_contents = None, 
                      auto_gen = None):
    """markdown_to_xhtml(md_content, table_of_contents = None, auto_gen = None) -> xhtml_content
Given a (UTF-8) string containing Markdown content, this function returns a
(UTF-8) string containing the Confluence XHTML version of the content."""
    # This code was pilfered from md2conf.py in
    # https://github.com/RittmanMead/md_to_conf.
    import re

    def convert_macros(xhtml):
        infoTag = '<p><ac:structured-macro ac:name="info"><ac:rich-text-body><p>'
        noteTag = infoTag.replace('info','note')
        warningTag = infoTag.replace('info','warning')
        closeTag = '</p></ac:rich-text-body></ac:structured-macro></p>\n'
    
        # Convert custom Info/Note/Warning tags into macros
        xhtml = xhtml.replace('<p>~?', infoTag).replace('?~</p>', closeTag)
        xhtml = xhtml.replace('<p>~!', noteTag).replace('!~</p>', closeTag)
        xhtml = xhtml.replace('<p>~%', warningTag).replace('%~</p>', closeTag)
        
        # Convert block quotes into macros
        quotes = re.findall('<blockquote>(.*?)</blockquote>', xhtml, re.DOTALL)
        cleaned_quotes = []
        if quotes:
            # Python's Markdown converter makes weird assumptions about stuff in the 
            # blockquote environment. Go through the quotes and remove erroneous <p>, </p> tags.
            # This is kludgey, but solving the real problem here is Hard.
            for i in range(len(quotes)):
                q = quotes[i]
                # Inspect each line. If we find a multi-line markup thingy, remove the paragraph
                # tags surrounding the first line.
                lines = q.split('\n')
                j = 0
                while j < len(lines):
                    line = lines[j]
                    if 'Panel:' in line or 'Expand:' in line:
                        lines[j] = line.replace('<p>', '')
                        lines[j+1] = lines[j+1].replace('</p>', '')
                        j += 2
                    else:
                        j += 1
                cleaned_quotes.append('\n'.join(lines))

            for i in range(len(cleaned_quotes)):
                q = cleaned_quotes[i]
                # Break the block quote chunk into separate paragraphs.
                if '</p>' in q:
                    paras = [p + '</p>' for p in q.split('</p>')][:-1]
                else:
                    paras = [q]
                macroTag = ''
                for p in paras:
                    info = re.search('^<.*>Info', p.strip(), re.IGNORECASE)
                    note = re.search('^<.*>Note', p.strip(), re.IGNORECASE)
                    warning = re.search('^<.*>Warning', p.strip(), re.IGNORECASE)
                    panel = re.search('Panel:', p.strip(), re.IGNORECASE)
                    expand = re.search('Expand:', p.strip(), re.IGNORECASE)
                    expand_all = re.search('ExpandAll', p.strip(), re.IGNORECASE)
                    livesearch = re.search('LiveSearch', p.strip(), re.IGNORECASE)
            
                    if info:
                        cleanTag = strip_type(p, 'Info')
                        macroTag += cleanTag.replace('<p>', infoTag).replace('</p>', closeTag).strip() + '\n'
                    elif note:
                        cleanTag = strip_type(p, 'Note')
                        macroTag += cleanTag.replace('<p>', noteTag).replace('</p>', closeTag).strip() + '\n'
                    elif warning:
                        cleanTag = strip_type(p, 'Warning')
                        macroTag += cleanTag.replace('<p>', warningTag).replace('</p>', closeTag).strip() + '\n'
                    elif panel:
                        cleanTag = strip_type(p, 'Panel')
                        lines = cleanTag.split('\n')
                        title = lines[0].replace('<p>', '')
                        body = '\n'.join(lines[1:]) + '\n'
                        cleanTag = '<p>' + body
                        panelTag = '<p><ac:structured-macro ac:name="panel">' + \
                                   '<ac:parameter ac:name="title">%s</ac:parameter>'%title + \
                                   '<ac:rich-text-body><p>\n'
                        macroTag += panelTag + body + closeTag
                    elif expand:
                        cleanTag = strip_type(p, 'Expand')
                        lines = cleanTag.split('\n')
                        title = lines[0].replace('<p>', '')
                        body = '\n'.join(lines[1:]) + '\n'
                        cleanTag = '<p>' + body
                        expandTag = '<p><ac:structured-macro ac:name="expand">' + \
                                    '<ac:parameter ac:name="title">%s</ac:parameter>'%title + \
                                    '<ac:rich-text-body><p>\n'
                        macroTag += expandTag + body + closeTag
                    elif expand_all:
                        macroTag += '<ac:structured-macro ac:name="expand-collapse-all"/>'
                    elif livesearch:
                        macroTag += '<p><ac:structured-macro ac:name="livesearch">' + \
                                    '<ac:parameter ac:name="spaceKey"><ri:space ri:space-key="@self"/></ac:parameter>' + \
                                    '<ac:parameter ac:name="placeholder">Search this space</ac:parameter>' + \
                                    '</ac:structured-macro></p>\n'
            
                if len(macroTag) > 0:
                    xhtml = xhtml.replace('<blockquote>%s</blockquote>'%quotes[i], macroTag)
        return xhtml
    
    def convert_code_blocks(xhtml):
        codeBlocks = re.findall('<pre><code.*?>.*?<\/code><\/pre>', xhtml, re.DOTALL)
        if codeBlocks:
            for tag in codeBlocks:
                confML = '<ac:structured-macro ac:name="code">'
#                confML += '<ac:parameter ac:name="theme">Midnight</ac:parameter>'
                confML += '<ac:parameter ac:name="linenumbers">true</ac:parameter>'
            
                lang = re.search('code class="(.*)"', tag)
                if lang:
                    lang = lang.group(1)
                else:
                    lang = 'none'
                
                confML = confML + '<ac:parameter ac:name="language">' + lang + '</ac:parameter>'
                content = re.search('<pre><code.*?>(.*?)<\/code><\/pre>', tag, re.DOTALL).group(1)
                content = '<ac:plain-text-body><![CDATA[' + content + ']]></ac:plain-text-body>'
                confML = confML + content + '</ac:structured-macro>'
                confML = confML.replace('&lt;', '<').replace('&gt;', '>')
                confML = confML.replace('&quot;', '"').replace('&amp;', '&')
            
                xhtml = xhtml.replace(tag, confML)
    
        return xhtml

    def convert_images(xhtml):
        import os.path
        image_tags = re.findall('<img.*?>', xhtml, re.DOTALL)
        if image_tags:
            for tag in image_tags:
                # Get the important attributes.
                src = re.search('src="(.*?)"', tag)
                if src:
                    src = src.group(1)
                filename = os.path.basename(src)

                alt = re.search('alt="(.*?)"', tag)
                if alt:
                    alt = alt.group(1)

                width = re.search('width="(.*?)"', tag)
                if width:
                    width = width.group(1)
                
                height = re.search('height="(.*?)"', tag)
                if height:
                    height = height.group(1)
                
                # Open an ac:image tag and shove the attributes in.
                confML = '<ac:image ac:queryparams="effects=border-simple,blur-border" '
                if alt:
                    confML += 'ac:alt="%s" ac:title="%s" '%(alt, alt)
                if width:
                    confML += 'ac:width="%s" '%width
                if height:
                    confML += 'ac:height="%s" '%height
                confML += '>'

                # Point to the attached image.
                confML += '<ri:attachment ri:filename="%s"/>'%filename

                # Close the ac:image tag.
                confML += '</ac:image>'
            
                xhtml = xhtml.replace(tag, confML)
    
        return xhtml

    def strip_type(tag, type):
        tag = re.sub('%s:\s' % type, '', tag.strip(), re.IGNORECASE)
        tag = re.sub('%s\s:\s' % type, '', tag.strip(), re.IGNORECASE)
        tag = re.sub('<.*?>%s:\s<.*?>' % type, '', tag, re.IGNORECASE)
        tag = re.sub('<.*?>%s\s:\s<.*?>' % type, '', tag, re.IGNORECASE)
        tag = re.sub('<(em|strong)>%s:<.*?>\s' % type, '', tag, re.IGNORECASE)
        tag = re.sub('<(em|strong)>%s\s:<.*?>\s' % type, '', tag, re.IGNORECASE)
        tag = re.sub('<(em|strong)>%s<.*?>:\s' % type, '', tag, re.IGNORECASE)
        tag = re.sub('<(em|strong)>%s\s<.*?>:\s' % type, '', tag, re.IGNORECASE)
        stringStart = re.search('<.*?>', tag)
        tag = upper_chars(tag, [stringStart.end()])
        return tag
    
    def upper_chars(string, indices):
        upperString = "".join(c.upper() if i in indices else c for i, c in enumerate(string))
        return upperString

    def process_refs(xhtml):
        refs = re.findall('\n(\[\^(\d)\].*)|<p>(\[\^(\d)\].*)', xhtml)
        if len(refs) > 0:
            for ref in refs:
                if ref[0]:
                    fullRef = ref[0].replace('</p>', '').replace('<p>', '')
                    refID = ref[1]
                else:
                    fullRef = ref[2]
                    refID = ref[3]
        
                fullRef = fullRef.replace('</p>', '').replace('<p>', '')
                xhtml = xhtml.replace(fullRef, '')
                href = re.search('href="(.*?)"', fullRef).group(1)

                superscript = '<a id="test" href="%s"><sup>%s</sup></a>' % (href, refID)
                xhtml = xhtml.replace('[^%s]' % refID, superscript)
    
        return xhtml

    def add_table_of_contents(xhtml, table_of_contents):
        # See https://confluence.atlassian.com/doc/table-of-contents-macro-182682099.html
        # for macro parameter descriptions.
        min_level = 1
        if 'min_level' in table_of_contents.keys():
            min_level = int(table_of_contents['min_level'])
        max_level = 7
        if 'max_level' in table_of_contents.keys():
            max_level = int(table_of_contents['max_level'])
        type = 'list'
        if 'type' in table_of_contents.keys():
            type = table_of_contents['type']
        style = 'disc'
        if 'style' in table_of_contents.keys():
            style = table_of_contents['style']
        toc = '<ac:structured-macro ac:name="toc">\n<ac:parameter ac:name="printable">true</ac:parameter>\n<ac:parameter ac:name="style">disc</ac:parameter>'
        toc += '<ac:parameter ac:name="maxLevel">%i</ac:parameter>\n<ac:parameter ac:name="minLevel">%i</ac:parameter>'%(max_level, min_level)
        toc += '<ac:parameter ac:name="class">rm-contents</ac:parameter>\n<ac:parameter ac:name="exclude"></ac:parameter>\n<ac:parameter ac:name="type">%s</ac:parameter><ac:parameter ac:name="type">%s</ac:parameter>'%(type, style)
        toc += '<ac:parameter ac:name="outline">false</ac:parameter>\n<ac:parameter ac:name="include"></ac:parameter>\n</ac:structured-macro>'
        return toc + '\n' + xhtml

    def add_auto_gen(xhtml, draft_link):
        badge = '<ac:structured-macro ac:name="panel">\n<ac:parameter ac:name="title">This page is auto-generated. Please do not Edit directly.</ac:parameter>\n'
        badge += '<ac:rich-text-body>Make a suggestion or Pull Request to <a href="%s"><b>the source file.</b></a></ac:rich-text-body>\n'%draft_link
        badge += '</ac:structured-macro>'
        return badge + '\n' + xhtml


    # this bleach cleaner doesn't work for some of xhtml format.
    def convert_html_to_xhtml(xhtml):
        xhtml = re.sub(r'(<col(?:>|\s.*?>))', r'\1</col>', xhtml)
        return xhtml
    
    # Convert to XHTML.
    import markdown
    xhtml = markdown.markdown(md_content, 
                              extensions = ['markdown.extensions.tables', 
                                            'markdown.extensions.fenced_code'])
    # Sanitize HTML within. (Yes, we're kind of abusing bleach here.)
    from bleach.sanitizer import Cleaner
    allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'col', 'colgroup', 'pre', 'code', 'em', 
                    'i', 'li', 'ol', 'strong', 'ul', 'p', 'h1', 'h2', 'h3', 
                    'h4', 'h5', 'h6', 'img', 'table', 'th', 'thead', 'tbody', 'tr', 'td']
    allowed_attrs = {'a': ['href', 'title', 'id'], 
                     'abbr': ['title'], 
                     'acronym': ['title'],
                     'col': ['width'],
                     'colgroup': ['valign'],
                     'img': ['alt', 'src', 'width', 'height'],
                     '*': ['style'],
                     'th': ['id'],
                     'td': ['headers']}
                     #'td': ['style', 'headers']}
    allowed_styles = ['color', 'font-family', 'width']
    cleaner = Cleaner(tags=allowed_tags, attributes = allowed_attrs, styles = allowed_styles)
    xhtml = cleaner.clean(xhtml)
    # Toss the first line if it matches our title.
    xhtml_lines = xhtml.split('\n')
    if title in xhtml_lines[0]:
        xhtml_lines = xhtml_lines[1:]
    # Now handle Confluence-specific stuff.
    xhtml = '\n'.join(xhtml_lines)
    xhtml = convert_macros(xhtml)
    xhtml = convert_code_blocks(xhtml)
    xhtml = convert_html_to_xhtml(xhtml)
    xhtml = convert_images(xhtml)
    xhtml = process_refs(xhtml)

    if table_of_contents:
        xhtml = add_table_of_contents(xhtml, table_of_contents)
    if auto_gen:
        xhtml = add_auto_gen(xhtml, auto_gen)
    return xhtml

