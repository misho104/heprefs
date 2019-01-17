from __future__ import absolute_import, division, print_function, unicode_literals
import re
import os
import arxiv
import feedparser
from logging import getLogger

logger = getLogger(__name__)


class ArxivArticle(object):
    SERVER = 'https://arxiv.org'
    API = 'http://export.arxiv.org/api/query'

    OLD_FORMAT_DEFAULT = 'hep-ph'

    @classmethod
    def get_info(cls, arxiv_id):
        # Code from arxiv.py https://github.com/lukasschwab/arxiv.py
        query_url = '{}?id_list={}'.format(cls.API, arxiv_id)
        results = feedparser.parse(query_url)
        if results.get('status') != 200:
            raise Exception('Failed to fetch arXiv article information: HTTP Error ' +
                            str(results.get('status', 'no status')))

        if len(results['entries']) == 0 \
           or 'id' not in results['entries'][0]:  # because arXiv api returns one blank entry even if nothing found
            raise Exception('arXiv:{} not found'.format(arxiv_id))
        elif len(results['entries']) > 1:
            warning_text = 'more than one entries are found, whose titles are' + os.linesep
            for i in results:
                title = i.get('title', dict()).get('title') or 'unknown ' + i.get('primary_report_number')
                warning_text += '    ' + title + os.linesep
            logger.warning(warning_text)

        result = results['entries'][0]
        arxiv.mod_query_result(result)
        return result

    @classmethod
    def shorten_author(cls, author):
        author = re.sub('collaboration', '', author, flags=re.IGNORECASE).strip()
        family_name = re.split(r'[ .]', author)[-1]
        return family_name.replace('-', '')

    @classmethod
    def try_to_construct(cls, key, force=False):
        try:
            obj = cls(key)
        except ValueError as e:
            if force:
                raise e
            return False
        return obj

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
        old_style = re.match(r'^([a-zA-Z.-]+/)?\d{7}$', i)
        if new_style:
            (first, second) = (new_style.group(1), new_style.group(2))
            if int(first) >= 1500:
                self._arxiv_id = i if (len(second) == 5) else '{}.0{}'.format(first, second)
            elif len(second) == 4:
                self._arxiv_id = i
            else:
                raise ValueError('incorrect arXiv id')
        elif old_style:
            self._arxiv_id = i if old_style.group(1) else self.OLD_FORMAT_DEFAULT + '/' + i
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

    def source_url(self):
        return '{}/e-print/{}'.format(self.SERVER, self.arxiv_id)

    def title(self):
        return re.sub(r'\s+', ' ', self.info['title'])

    def authors(self):
        return ', '.join(self.info['authors'])

    def first_author(self):
        return self.info['authors'][0]

    def authors_short(self):
        authors = [self.shorten_author(a) for a in self.info['authors']]
        if len(authors) > 5:
            authors = authors[0:4] + ['et al.']
        return ', '.join(authors)

    def download_parameters(self):
        authors = self.authors_short().replace(', ', '-').replace('et al.', 'etal')
        filename = '{id}-{authors}.pdf'.format(id=self.arxiv_id, authors=authors)
        return self.info['pdf_url'], filename

    def debug(self):
        data = {
            'abs_url': self.abs_url(),
            'pdf_url': self.pdf_url(),
            'title': self.title(),
            'authors': self.authors(),
            'first_author': self.first_author(),
            '(download_filename)': self.download_parameters()[1],
        }
        for k, v in data.items():
            print('{}: {}'.format(k, v))
