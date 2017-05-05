from __future__ import absolute_import, division, print_function, unicode_literals
import re
import arxiv

class ArxivArticle:
    SERVER = 'https://arxiv.org'

    @classmethod
    def get_info(cls, arxiv_id):
        # Code from arxiv.py https://github.com/lukasschwab/arxiv.py
        results = arxiv.feedparser.parse(arxiv.root_url + 'query?id_list=' + arxiv_id)
        if results.get('status') != 200:
            raise Exception("Failed to fetch arXiv article information: HTTP Error " + str(results.get('status', 'no status')))

        if len(results['entries']) == 0 \
           or 'id' not in results['entries'][0]:  # because arXiv api returns one blank entry even if nothing found
            raise Exception('arXiv:{} not found'.format(arxiv_id))
        elif len(results['entries']) > 1:
            print('Warning: more than one entries are found')

        result = results['entries'][0]
        arxiv.mod_query_result(result)
        return result

    @classmethod
    def shorten_author(cls, author):
        author = re.sub(r'collaboration', '', author, flags=re.IGNORECASE).strip()
        family_name = re.split(r'[ .]', author)[-1]
        return family_name.replace('-', '')

    @classmethod
    def try_to_construct(cls, key):
        try:
            object = cls(key)
        except ValueError:
            return False
        return object

    def __init__(self, arxiv_id):
        self._arxiv_id = None
        self.arxiv_id = arxiv_id
        self._info = None

    @property
    def arxiv_id(self):
        return self._arxiv_id

    @arxiv_id.setter
    def arxiv_id(self, i):
        new_style = re.match(r'^(\d{4})\.(\d{4,5})$', i)
        if new_style:
            (first, second) = (new_style.group(1), new_style.group(2))
            if int(first) >= 1500:
                self._arxiv_id = i if (len(second) == 5) else '{}.0{}'.format(first, second)
            elif len(second) == 4:
                self._arxiv_id = i
            else:
                raise ValueError('incorrect arXiv id')
        elif re.match('^[a-zA-Z.-]+/\d{7}$', i):
            self._arxiv_id = i
        else:
            raise ValueError('incorrect arXiv id')

    @property
    def info(self):
        if not self._info:
            self._info = self.get_info(self.arxiv_id)
        return self._info

    def abs_url(self):
        return '{}/abs/{}'.format(self.SERVER, self.arxiv_id)

    def pdf_url(self):
        return '{}/pdf/{}'.format(self.SERVER, self.arxiv_id)

    def title(self):
        return self.info['title']

    def authors(self):
        return ', '.join(self.info['authors'])

    def first_author(self):
        return self.info['authors'][0]

    def authors_short(self):
        authors = [self.shorten_author(a) for a in self.info['authors']]
        if len(authors) > 4:
            authors = authors[0:4] + ['etal']
        return '-'.join(authors)

    def download_parameters(self):
        filename = '{id}-{authors}.pdf'.format(id=self.arxiv_id, authors=self.authors_short())
        return (self.info['pdf_url'], filename)
