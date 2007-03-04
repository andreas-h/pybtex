# Copyright 2007 Andrey Golovizin
#
# This file is part of pybtex.
#
# pybtex is free software; you can redistribute it and/or modify
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# pybtex is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pybtex; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA

"""Built-in functions for BibTeX interpreter.

CAUTION: functions should PUSH results, not RETURN
"""

import interpreter
from pybtex.database.input.bibtex import split_name_list

class Builtin(object):
    def __init__(self, f):
        self.f = f
    def execute(self, interpreter):
        self.f(interpreter)
    def __repr__(self):
        return '<builtin %s>' % self.f.__name__

def builtin(f):
    return Builtin(f)

@builtin
def operator_more(i):
    arg1 = i.pop()
    arg2 = i.pop()
    if arg2 > arg1:
        i.push(1)
    else:
        i.push(0)

@builtin
def operator_less(i):
    arg1 = i.pop()
    arg2 = i.pop()
    if arg2 < arg1:
        i.push(1)
    else:
        i.push(0)

@builtin
def operator_equals(i):
    arg1 = i.pop()
    arg2 = i.pop()
    if arg2 == arg1:
        i.push(1)
    else:
        i.push(0)

@builtin
def operator_asterisk(i):
    arg1 = i.pop()
    arg2 = i.pop()
    i.push(arg2 + arg1)

@builtin
def operator_assign(i):
    var = i.pop()
    value = i.pop()
    var.set(value)

@builtin
def operator_plus(i):
    arg1 = i.pop()
    arg2 = i.pop()
    i.push(arg2 + arg1)

@builtin
def operator_minus(i):
    arg1 = i.pop()
    arg2 = i.pop()
    i.push(arg2 - arg1)

@builtin
def add_period(i):
    s = i.pop()
    if s and not s.rstrip('}')[-1] in '.?!':
        s += '.'
    i.push(s)

@builtin
def call_type(i):
    type = i.current_entry.type
    i.vars[type].execute(i)

@builtin
def change_case(i):
    mode = i.pop()
    s = i.pop()
    #FIXME stub
    i.push(s)


@builtin
def cite(i):
    i.push(i.current_entry_key)

@builtin
def duplicate(i):
    tmp = i.pop()
    i.push(tmp)
    i.push(tmp)

@builtin
def empty(i):
    #FIXME error checking
    s = i.pop()
    if s and not s.isspace():
        i.push(0)
    else:
        i.push(1)

@builtin
def format_name(i):
    #FIXME stub
    format = i.pop()
    n = i.pop()
    names = i.pop()
    name = split_name_list(names)[n - 1]
    i.push(name)


@builtin
def if_(i):
    f1 = i.pop()
    f2 = i.pop()
    p = i.pop()
    if p > 0:
        f2.execute(i)
    else:
        f1.execute(i)

@builtin
def int_to_str(i):
    i.push(str(i.pop()))

@builtin
def missing(i):
    f = i.pop()
    if isinstance(f, interpreter.MissingField):
        i.push(1)
    else:
        i.push(0)

@builtin
def newline(i):
    # FIXME bibtex does some automatic line breaking
    # needs more investigation
    i.output('\n')

@builtin
def num_names(i):
    names = i.pop()
    i.push(len(split_name_list(names)))

@builtin
def pop(i):
    i.pop()

@builtin
def preamble(i):
    #FIXME stub
    i.push('')

@builtin
def skip(i):
    pass

@builtin
def substring(i):
    len = i.pop()
    start = i.pop()
    s = i.pop()
    if start > 0:
        i.push(s[start - 1:start - 1 + len])
    elif start < 0:
        i.push(s[-start - len:-start])
    else:
        raise BibTeXError('start=0 passed to substring$')


@builtin
def swap(i):
    tmp1 = i.pop()
    tmp2 = i.pop()
    i.push(tmp1)
    i.push(tmp2)

@builtin
def text_length(i):
    # FIXME special characters and braces
    s = i.pop()
    i.push(len(s))

@builtin
def warning(i):
    #FIXME stub
    msg = i.pop()
    print 'WARNING:', msg

@builtin
def while_(i):
    f = i.pop()
    p = i.pop()
    while True:
        p.execute(i)
        if i.pop() <= 0:
            break
        f.execute(i)

@builtin
def width(i):
    #FIXME need to investigate bibtex' source
    s = i.pop()
    i.push(len(s))

@builtin
def write(i):
    #FIXME encodings
    s = i.pop()
    i.output(s.encode('UTF-8'))

builtins = {
        '>': operator_more,
        '<': operator_less,
        '=': operator_equals,
        '+': operator_plus,
        '-': operator_minus,
        '*': operator_asterisk,
        ':=': operator_assign,
        'add.period$': add_period,
        'call.type$': call_type,
        'change.case$': change_case,
        'cite$': cite,
        'duplicate$': duplicate,
        'empty$': empty,
        'format.name$': format_name,
        'if$': if_,
        'int.to.str$': int_to_str,
        'missing$': missing,
        'newline$': newline,
        'num.names$': num_names,
        'pop$': pop,
        'preamble$': preamble,
        'skip$': skip,
        'substring$': substring,
        'swap$': swap,
        'text.length$': text_length,
        'warning$': warning,
        'while$': while_,
        'width$': width,
        'write$': write,
}
