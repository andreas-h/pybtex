# Copyright 2006 Andrey Golovizin
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

try:
    import cElementTree as ET
except ImportError:
    try:
        from elementtree import ElementTree as ET
    except ImportError:
        from xml.etree import ElementTree as ET
from pybtex.core import Entry, Person
from pybtex.database.input import ParserBase

bibtexns = '{http://bibtexml.sf.net/}'
file_extension = 'bibtexml'

def remove_ns(s):
    if s.startswith(bibtexns):
        return s[len(bibtexns):]

class Parser(ParserBase):
    def parse_file(self, file):
        self.entries = {}
        t = ET.parse(file)
        for entry in t.findall(bibtexns + 'entry'):
            self.process_entry(entry)
        return self.entries

    def process_entry(self, entry):
        def process_person(person_entry, role):
            persons = person_entry.findall(bibtexns + 'person')
            if persons:
                for person in persons:
                    process_person(person, role)
            else:
                text = person_entry.text.strip()
                if text:
                    e.add_person(Person(text), role)
                else:
                    names = {}
                    for name in person_entry.getchildren():
                        names[remove_ns(name.tag)] = name.text
                    e.add_person(Person(**names), role)
                        

        id_ = entry.get('id')
        item = entry.getchildren()[0]
        type = remove_ns(item.tag)
        e = Entry(type)
        for field in item.getchildren():
            field_name = remove_ns(field.tag)
            if field_name in Person.valid_roles:
                process_person(field, field_name)
            else:
                e.fields[field_name] = field.text.strip()
        self.entries[id_] = e
