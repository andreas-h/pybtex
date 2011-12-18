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

"""Base parser class
"""

import re

from pybtex.exceptions import PybtexError


class Token(object):
    def __init__(self, value, pattern):
        self.value = value
        self.pattern = pattern

    def __repr__(self):
        return repr(self.value)


class Pattern(object):
    def __init__(self, regexp, description, flags=0):
        self.description = description
        compiled_regexp = re.compile(regexp, flags=flags)
        self.search = compiled_regexp.search
        self.match = compiled_regexp.match
        self.findall = compiled_regexp.findall


class Literal(Pattern):
    def __init__(self, literal):
        pattern = re.compile(re.escape(literal))
        description = "'{0}'".format(literal)
        super(Literal, self).__init__(pattern, description)


class Scanner(object):
    text = None
    lineno = None
    pos = None
    end_pos = None
    WHITESPACE = Pattern(ur'\s+', 'whitespace')
    NEWLINE = Pattern(ur'[\r\n]', 'newline')

    def __init__(self, text):
        self.text = text
        self.lineno = 1
        self.pos = 0
        self.end_pos = len(text)

    def skip_to(self, patterns):
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

    def eat_whitespace(self):
        whitespace = self.WHITESPACE.match(self.text, self.pos)
        if whitespace:
            self.pos = whitespace.end()
            self.update_lineno(whitespace.group())

    def eof(self):
        return self.pos == self.end_pos

    def get_token(self, patterns, allow_eof=False):
        self.eat_whitespace()
        if self.eof():
            if allow_eof:
                raise EOFError
            else:
                raise PrematureEOF(self)
        for i, pattern in enumerate(patterns):
            match = pattern.match(self.text, self.pos)
            if match:
                value = match.group()
                self.pos = match.end()
                #print '->', value
                return Token(value, pattern)

    def optional(self, patterns, allow_eof=False):
        return self.get_token(patterns, allow_eof=allow_eof)

    def required(self, patterns, description=None, allow_eof=False):
        token =  self.get_token(patterns, allow_eof=allow_eof)
        if token is None:
            if not description:
                description = ' or '.join(pattern.description for pattern in patterns)
            raise TokenRequired(description, self)
        else:
            return token

    def get_error_context_info(self):
        return self.lineno, self.pos

    def get_error_context(self, context_info):
        error_lineno, error_pos  = context_info
        error_lineno0 = error_lineno - 1
        lines = self.text.splitlines(True)
        before_error = ''.join(lines[:error_lineno0])
        colno = error_pos - len(before_error)
        context = lines[error_lineno0].rstrip('\r\n')
        return context, error_lineno, colno


class PybtexSyntaxError(PybtexError):
    def __init__(self, message, parser):
        super(PybtexSyntaxError, self).__init__(message)
        self.lineno = parser.lineno
        self.parser = parser
        self.error_context_info = parser.get_error_context_info()

    def __unicode__(self):
        base_message = super(PybtexSyntaxError, self).__unicode__()
        return 'Syntax error in line {lineno}: {message}'.format(
            lineno=self.lineno,
            message=base_message,
        )


class PrematureEOF(PybtexSyntaxError):
    def __init__(self, parser):
        message = 'premature end of file'
        super(PrematureEOF, self).__init__(message, parser)


class TokenRequired(PybtexSyntaxError):
    def __init__(self, description, parser):
        message = '{0} expected'.format(description)
        super(TokenRequired, self).__init__(message, parser)

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
