# Copyright (C) 2006, 2007, 2008  Andrey Golovizin
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

"""name formatting styles
"""
from pybtex.richtext import Symbol, Text, nbsp
from pybtex.style.template import join, together, node, _format_list
from pybtex.bibtex.name import tie_or_space

@node
def name_part(children, data, before='', tie=False):
    parts = together [children].format_data(data)
    if not parts:
        return Text()
    if tie:
        return Text(before, parts, tie_or_space(parts, nbsp, ' '))
    else:
        return Text(before, parts)


def plain(person, abbr=False):
    r"""
    >>> from pybtex.core import Person
    >>> name = Person(string=r"Charles Louis Xavier Joseph de la Vall{\'e}e Poussin")
    >>> print plain(name).format().plaintext()
    de<nbsp>la Vall{\'e}e<nbsp>Poussin, Charles Louis Xavier<nbsp>Joseph
    >>> print plain(name, abbr=True).format().plaintext()
    de<nbsp>la Vall{\'e}e<nbsp>Poussin, C.<nbsp>L. X.<nbsp>J.
    >>> name = Person(first='First', last='Last', middle='Middle')
    >>> print plain(name).format().plaintext()
    Last, First<nbsp>Middle
    >>> print plain(name, abbr=True).format().plaintext()
    Last, F.<nbsp>M.

    """
    return join [
        name_part(tie=True) [person.prelast()],
        name_part [person.last()],
        name_part(before=', ') [person.lineage()],
        name_part(before=', ') [person.first(abbr) + person.middle(abbr)],
    ]
