# Copyright (c) 2006, 2007, 2008, 2009, 2010, 2011, 2012  Andrey Golovizin
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import re

from pybtex.style.formatting import toplevel
from pybtex.style.formatting.unsrt import Style as UnsrtStyle
from pybtex.style.template import (
    join, words, field, optional, first_of,
    names, sentence, tag, optional_field
)
from pybtex.richtext import Text, Symbol

def dashify(text):
    dash_re = re.compile(r'-+')
    return Text(Symbol('ndash')).join(dash_re.split(text))

pages = field('pages', apply_func=dashify)

date = words [optional_field('month'), field('year')]



class Style(UnsrtStyle):
    name = 'andreash'
    default_sorting_style = 'invyear_author_title'

    def format_names(self, role, as_sentence=True):
        formatted_names = names(role, sep=', ', sep2 = ' and ', last_sep=', and ')
        if as_sentence:
            return sentence(capfirst=False, add_period=":") [formatted_names]
        else:
            return formatted_names


    def format_author_or_editor(self, e):
        return first_of [
            optional[ self.format_names('author') ],
            self.format_editor(e),
        ]

    def format_article(self, e):
        volume_and_pages = first_of [
            # volume and pages, with optional issue number
            optional [
                join [
                    tag('bold') [field('volume')],
                    optional['(', field('number'),')'],
                    ':', pages
                ],
            ],
            # pages only
            words ['pages', pages],
        ]
        template = toplevel [
            self.format_names('author'),
            self.format_title(e, 'title'),
            sentence(capfirst=False) [
                tag('emph') [field('journal')],
                optional[ volume_and_pages ],
                date],
            sentence(capfirst=False) [ optional_field('note') ],
        ]
        return template.format_data(e)

