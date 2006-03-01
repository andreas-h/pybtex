#!/usr/bin/env python
import sys, aux
import filters
from formatters import label

def import_style(name):
    m = __import__('formatters.latex', globals(), locals(), [name])
    return getattr(m, name)

def prepare_entries(bib_data, aux_data):
    n = 1
    entries = []
    for key in aux_data.citations:
        print key
        entry = bib_data[key]
        entry.number = n
        entry.key = key
        entry.label = label.number(entry)
        entries.append(entry)
        n += 1
    def l(e):
        return e.label
    entries.sort(key=l)
    return entries

def parse_filename(filename):
    dot = filename.rfind('.')
    if dot == -1:
        return filename, None
    else:
        return (filename[:dot], filename[dot + 1:])

def main():
    filename, ext = parse_filename(sys.argv[1])

    bib_parser = filters.find_filter('input', ext)
    aux_data = aux.parse_file(filename + ".aux")
    bib_data = bib_parser.parse_file('%s.%s' % (aux_data.data, ext))
    
    entries = prepare_entries(bib_data, aux_data)
    del bib_data
    #from formatters.latex import unsorted
    style = import_style(aux_data.style)
    style.Formatter(entries).output_bibliography(filename + ".bbl")


if __name__ == '__main__':
    main()
