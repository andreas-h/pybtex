#!/usr/bin/env python

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

from optparse import make_option

from pybtex.cmdline import CommandLine

class PybtexConvertCommandLine(CommandLine):
    prog = 'pybtex-convert'
    args = '[options] in_filename out_filename' 
    num_args = 2

    options = (
        (None, (
            make_option('-f', '--from', action='store', type='string', dest='from_format'),
            make_option('-t', '--to', action='store', type='string', dest='to_format'),
            make_option('--allow-keyless-bibtex-entries', action='store_true', dest='allow_keyless_entries'),
        )),
        ('encoding options', (
            make_option('--input-encoding', action='store', type='string', dest='input_encoding'),
            make_option('--output-encoding', action='store', type='string', dest='output_encoding'),
        )),
    )
    option_defaults = {
        'allow_keyless_entries': False,
    }

    def run(self, options, args):
        from pybtex.database.convert import convert, ConvertError

        try:
            convert(args[0], args[1],
                    options.from_format,
                    options.to_format,
                    input_encoding=options.input_encoding,
                    output_encoding=options.output_encoding,
                    parser_options = {'allow_keyless_entries': options.allow_keyless_entries})
        except ConvertError, s:
            opt_parser.error(s)

main = PybtexConvertCommandLine()

if __name__ == '__main__':
    main()
