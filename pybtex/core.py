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

"""pybtex' core datatypes
"""

import re

class FormattedEntry:
    """Formatted bibliography entry. Consists of
    - key (which is used for sorting);
    - label (which appears in the resulting bibliography)
    - text (usually RichText)
    """
    def __init__(self, key, text, label=None):
        self.key = key
        self.text = text
        self.label = label

class Entry(object):
    """Bibliography entry. Important members are:
    - persons (a dict of Person objects)
    - fields (all dict of string)
    """

    class FieldDict(dict):
        def __init__(self, parent, *args, **kwargw):
            self.parent = parent
            dict.__init__(self, *args, **kwargw)
        def __missing__(self, key):
            persons = self.parent.persons[key]
            return ' and '.join(unicode(person) for person in persons)

    def __init__(self, type_, fields = None, persons = None):
        if fields is None:
            fields = {}
        if persons is None:
            persons = {}
        self.type = type_
        self.fields = self.FieldDict(self, fields)
        self.persons = dict(persons)

        # for BibTeX interpreter
        self.vars = {}

    def add_person(self, person, role):
        self.persons.setdefault(role, []).append(person)

class Person:
    """Represents a person (usually human).
    """
    valid_roles = ['author', 'editor'] 
    style1_re = re.compile('^(.+),\s*(.+)$')
    style2_re = re.compile('^(.+),\s*(.+),\s*(.+)$')
    def __init__(self, string="", first="", middle="", prelast="", last="", lineage=""):
        self._first = []
        self._middle = []
        self._prelast = []
        self._last = []
        self._lineage = []
        string = string.strip()
        if string:
            self.parse_string(string)
        self._first.extend(first.split())
        self._middle.extend(middle.split())
        self._prelast.extend(prelast.split())
        self._last.extend(last.split())
        self._lineage.extend(lineage.split())

    def parse_string(self, s):
        """Extract various parts of the name from a string.
        Supported formats are:
         - von Last, First
         - von Last, Jr, First
         - First von Last
        (see BibTeX manual for explanation)
        """
        def process_first_middle(s):
            try:
                self._first.append(s[0])
                self._middle.extend(s[1:])
            except IndexError:
                pass
        def process_von_last(s):
            for part in s.split():
                if part.islower():
                    self._prelast.append(part)
                else:
                    self._last.append(part)
        match1 = self.style1_re.match(s)
        match2 = self.style2_re.match(s)
        if match2: # von Last, Jr, First
            parts = match2.groups()
            process_von_last(parts[0])
            self._lineage.extend(parts[1].split())
            process_first_middle(parts[2].split())
        elif match1: # von Last, First
            parts = match1.groups()
            process_von_last(parts[0])
            process_first_middle(parts[1].split())
        else: # First von Last
            first_middle = []
            first = True

            for part in s.split():
                if part.islower():
                    self._prelast.append(part)
                    first = False
                elif first:
                    first_middle.append(part)
                else:
                    self._last.append(part)
            process_first_middle(first_middle)

    def __unicode__(self):
        return ('%s %s, %s, %s %s' %
                (self.get_part_as_text('prelast'),
                self.get_part_as_text('last'),
                self.get_part_as_text('lineage'),
                self.get_part_as_text('first'),
                self.get_part_as_text('middle')))

    def get_part_as_text(self, type):
        names = getattr(self, '_' + type)
        return ' '.join(names)

    def get_part(self, type, abbr=False):
        names = getattr(self, '_' + type)
        if abbr:
            from pybtex.textutils import abbreviate
            names = [abbreviate(name) for name in names]
        return names

    #FIXME needs some thinking and cleanup
    def bibtex_first(self):
        """Return first and middle names together.
        (BibTeX treats all middle names as first)
        """
        return self._first + self._middle

    def first(self, abbr=False):
        return self.get_part('first', abbr)
    def middle(self, abbr=False):
        return self.get_part('middle', abbr)
    def prelast(self, abbr=False):
        return self.get_part('prelast', abbr)
    def last(self, abbr=False):
        return self.get_part('last', abbr)
    def lineage(self, abbr=False):
        return self.get_part('lineage', abbr)
