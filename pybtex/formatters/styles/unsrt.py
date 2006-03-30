from pybtex import utils
from pybtex.utils import Phrase, Word, try_format
from pybtex.richtext import Tag
from pybtex.formatters.styles import FormatterBase

class Formatter(FormatterBase):
    def format_authors(self, authors):
        p = Phrase()
        for author in authors:
            p.append(author.format([['f'], ['ll']]))
        return p

    def format_article(self, e):
        p = self.default_phrase(self.format_authors(e.authors), e['title'])
        pages = utils.dashify(e['pages'])
        if e.has_key('volume'):
            vp = Word(e['volume'], try_format(pages, ':%s'))
        else:
            vp = try_format(pages, 'pages %s')
        p.append(Phrase(Tag('emph', e['journal']), vp, e['year']))
        return p
        
    def format_book(self, e):
        p = self.default_phrase()
        if e.authors:
            p.append(self.format_authors(e.authors))
        else:
            editors = self.format_authors(e.editors)
            if e.editors.count > 1:
                editors.append('editors')
            else:
                editors.append('editor')
            p.append(editors)
        p.append(Tag('emph', e['title']))
        p.append(Phrase(e['publisher'], e['year'], add_period=True))
        return p
