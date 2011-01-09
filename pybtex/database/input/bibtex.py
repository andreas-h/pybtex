# Copyright (c) 2006, 2007, 2008, 2009, 2010, 2011  Andrey Golovizin
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

"""BibTeX parser

>>> import StringIO
>>> parser = Parser()
>>> bib_data = parser.parse_stream(StringIO.StringIO('''
... @String{SCI = "Science"}
... 
... @String{JFernandez = "Fernandez, Julio M."}
... @String{HGaub = "Gaub, Hermann E."}
... @String{MGautel = "Gautel, Mathias"}
... @String{FOesterhelt = "Oesterhelt, Filipp"}
... @String{MRief = "Rief, Matthias"}
... 
... @Article{rief97b,
...   author =       MRief #" and "# MGautel #" and "# FOesterhelt
...                  #" and "# JFernandez #" and "# HGaub,
...   title =        "Reversible Unfolding of Individual Titin
...                  Immunoglobulin Domains by {AFM}",
...   journal =      SCI,
...   volume =       276,
...   number =       5315,
...   pages =        "1109--1112",
...   year =         1997,
...   doi =          "10.1126/science.276.5315.1109",
...   URL =          "http://www.sciencemag.org/cgi/content/abstract/276/5315/1109",
...   eprint =       "http://www.sciencemag.org/cgi/reprint/276/5315/1109.pdf",
... }
... '''))
>>> rief97b = parser.data.entries['rief97b']
>>> authors = rief97b.persons['author']
>>> for author in authors:
...     print unicode(author)
Rief, Matthias
Gautel, Mathias
Oesterhelt, Filipp
Fernandez, Julio M.
Gaub, Hermann E.

"""

import re
from string import ascii_letters, digits

import pybtex.io
from pybtex.core import Entry, Person
from pybtex.database.input import BaseParser
from pybtex.bibtex.utils import split_name_list
from pybtex.exceptions import PybtexError
from pybtex import textutils

month_names = {
    'jan': 'January',
    'feb': 'February',
    'mar': 'March',
    'apr': 'April',
    'may': 'May',
    'jun': 'June',
    'jul': 'July',
    'aug': 'August',
    'sep': 'September',
    'oct': 'October',
    'nov': 'November',
    'dec': 'December'
}


def normalize_whitespace(value_parts):
    return textutils.normalize_whitespace(''.join(value_parts))


class Token(object):
    def __init__(self, value, pattern):
        self.value = value
        self.pattern = pattern

    def __repr__(self):
        return repr(self.value)


class SkipEntry(Exception):
    pass


class BibTeXSyntaxError(PybtexError):
    def __init__(self, message, parser):
        super(BibTeXSyntaxError, self).__init__(message)
        self.parser = parser
        self.lineno = parser.lineno
        self.error_context_info = parser.get_error_context_info()

    def __unicode__(self):
        base_message = super(BibTeXSyntaxError, self).__unicode__()
        return 'Syntax error in {parser.filename}, line {parser.lineno}: {message}'.format(
            parser=self.parser,
            message=base_message,
        )


class TokenRequired(BibTeXSyntaxError):
    def __init__(self, tokens, context):
        message = 'Token required: ' + ', '.join(tokens)
        super(TokenRequired, self).__init__(message, context)

    def __unicode__(self):
        self.context, self.lineno, self.colno = self.parser.get_error_context(self.error_context_info)
        message = super(TokenRequired, self).__unicode__()
        if self.context is None:
            return message
        if self.colno == 0:
            marker = '^^'
        else:
            marker = ' ' * (self.colno - 1) + '^^^'
        return '\n'.join((message, self.context, marker))


class PrematureEOF(BibTeXSyntaxError):
    def __init__(self, parser):
        message = 'premature end of file'
        super(PrematureEOF, self).__init__(message, parser)


def literal(s):
    return re.compile(re.escape(s))


class Parser(BaseParser):
    name = 'bibtex'
    suffixes = '.bib',
    unicode_io = True

    text = None
    lineno = None
    pos = None
    end_pos = None
    command_start = None
    macros = None

    NAME_CHARS = ascii_letters + '!$&*+-./:;<>?[\\]^_`|~\x7f'
    NAME = re.compile(r'[{0}][{1}]+'.format(re.escape(NAME_CHARS), re.escape(NAME_CHARS + digits)))
    NUMBER = re.compile(r'[{0}]+'.format(digits))
    LBRACE = literal('{')
    RBRACE = literal('}')
    LPAREN = literal('(')
    RPAREN = literal(')')
    QUOTE = literal('"')
    COMMA = literal(',')
    EQUALS = literal('=')
    HASH = literal('#')
    AT = literal('@')
    WHITESPACE = re.compile(r'\s+')
    NEWLINE = re.compile(r'[\r\n]')

    def __init__(self, encoding=None, macros=month_names, person_fields=Person.valid_roles, **kwargs):
        BaseParser.__init__(self, encoding)

        self.default_macros = dict(macros)
        self.person_fields = person_fields

    def skip_to(self, *patterns):
        end = None
        winning_pattern = None
        for pattern in patterns:
            match = pattern.search(self.text, self.pos)
            if match and (not end or match.end() < end):
                end = match.end()
                winning_pattern = pattern
        if winning_pattern:
            value = self.text[self.pos : end]
            self.pos = end
            #print '>>', value
            self.update_lineno(value)
            return Token(value, winning_pattern)

    def update_lineno(self, value):
        num_newlines = len(self.NEWLINE.findall(value))
        self.lineno += num_newlines

    def eat_whitespace_and_check_eof(self):
        whitespace = self.WHITESPACE.match(self.text, self.pos)
        if whitespace:
            self.pos = whitespace.end()
            self.update_lineno(whitespace.group())
        if self.pos == self.end_pos:
            raise PrematureEOF(self)

    def get_token(self, patterns):
        self.eat_whitespace_and_check_eof()
        for i, pattern in enumerate(patterns):
            match = pattern.match(self.text, self.pos)
            if match:
                value = match.group()
                self.pos = match.end()
                #print '->', value
                return Token(value, pattern)

    def optional(self, patterns, **kwargs):
        if not isinstance(patterns, (list, tuple)):
            patterns = [patterns]
        return self.get_token(patterns)

    def required(self, patterns, **kwargs):
        if not isinstance(patterns, (list, tuple)):
            patterns = [patterns]
        token =  self.get_token(patterns, **kwargs)
        if token is None:
            raise TokenRequired([pattern.pattern for pattern in patterns], self)
        else:
            return token

    def get_error_context_info(self):
        return self.command_start, self.pos

    def get_error_context(self, context_info):
        error_start, error_pos  = context_info
        before_error = self.text[error_start:error_pos]
        if not before_error.endswith('\n'):
            eol = self.NEWLINE.search(self.text, error_pos)
            error_end = eol.end() if eol else self.end_pos
        else:
            error_end = error_pos
        context = self.text[error_start:error_end].rstrip('\r\n')
        colno = len(before_error.splitlines()[-1])
        return context, self.lineno, colno

    def parse_bibliography(self):
        while True:
            if not self.skip_to(self.AT):
                return
            self.command_start = self.pos - 1
            try:
                self.parse_command()
            except TokenRequired as token_required:
                print unicode(token_required)
                #raise
            except SkipEntry:
                pass

    def parse_command(self):
        name = self.required(self.NAME)
        body_start = self.required([self.LPAREN, self.LBRACE])
        body_end = self.RBRACE if body_start.pattern == self.LBRACE else self.RPAREN

        entry_type = name.value.lower()
        if entry_type == 'string':
            self.parse_string_body(body_end)
        elif entry_type == 'preamble':
            self.parse_preamble_body(body_end)
        elif entry_type == 'comment':
            raise SkipEntry
        else:
            self.parse_entry_body(entry_type, body_end)

    def parse_preamble_body(self, body_end):
        self.data.add_to_preamble(normalize_whitespace(self.parse_value()))
        self.required(body_end)

    def parse_string_body(self, body_end):
        name = self.required(self.NAME).value
        self.required(self.EQUALS)
        value = normalize_whitespace(self.parse_value())
        self.required(body_end)
        self.process_macro(name, value)

    def parse_entry_body(self, entry_type, body_end):
        key = self.required(self.NAME).value
        fields = dict(self.parse_entry_fields(body_end))
        self.process_entry(entry_type, key, fields)

    def parse_entry_fields(self, body_end):
        while True:
            comma_or_body_end = self.required([self.COMMA, body_end])
            if comma_or_body_end.pattern is self.COMMA:
                field = list(self.parse_field())
                if field:
                    yield field
            else:
                return

    def parse_field(self):
        name = self.optional(self.NAME)
        if not name:
            return
        yield name.value
        self.required(self.EQUALS)
        yield normalize_whitespace(self.parse_value())

    def parse_value(self):
        start = True
        concatenation = False
        while True:
            if not start:
                concatenation = self.optional(self.HASH)
            if not (start or concatenation):
                break
            yield self.parse_value_part()
            start = False

    def parse_value_part(self):
        token = self.required([self.QUOTE, self.LBRACE, self.NUMBER, self.NAME])
        if token.pattern is self.QUOTE:
            return self.flatten_string(self.parse_string(string_end=self.QUOTE))
        elif token.pattern is self.LBRACE:
            return self.flatten_string(self.parse_string(string_end=self.RBRACE))
        elif token.pattern is self.NUMBER:
            return token.value
        else:
            return self.substitute_macro(token.value)

    def flatten_string(self, parts):
        return ''.join(part.value for part in parts)[:-1]

    def parse_string(self, string_end, level=0):
        special_chars = [self.RBRACE, self.LBRACE]
        if string_end is self.QUOTE:
            special_chars = [self.QUOTE] + special_chars
        while True:
            part = self.skip_to(*special_chars)
            if not part:
                raise PrematureEOF(self)
            if part.pattern is string_end:
                yield part
                break
            elif part.pattern is self.LBRACE:
                yield part
                for subpart in self.parse_string(self.RBRACE, level + 1):
                    yield subpart
            elif part.pattern is self.RBRACE and level == 0:
                raise SyntaxError('unbalanced brace')

    def process_entry(self, entry_type, key, fields):
        entry = Entry(entry_type)

        if key is None:
            key = 'unnamed-%i' % self.unnamed_entry_counter
            self.unnamed_entry_counter += 1

        for field_name, field_value in fields.items():
            if field_name in self.person_fields:
                for name in split_name_list(field_value):
                    entry.add_person(Person(name), field_name)
            else:
                entry.fields[field_name] = field_value
#        return (key, entry)
        self.data.add_entry(key, entry)

    def substitute_macro(self, name):
        try:
            return self.macros[name.lower()]
        except KeyError:
            raise PybtexError('undefined macro %s' % name)

    def process_macro(self, name, value):
        self.macros[name.lower()] = value

    def parse_stream(self, stream):
        text = stream.read()
        self.text = text
        self.lineno = 1
        self.pos = 0
        self.end_pos = len(text)
        self.command_start = 0
        self.macros = dict(self.default_macros)

        self.parse_bibliography()
        return self.data
