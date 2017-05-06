from __future__ import absolute_import, division, print_function, unicode_literals
import re
import sys
import json
try:
    from urllib2 import urlopen, Request, HTTPError
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError


class CDSArticle(object):
    API = 'https://cds.cern.ch/search'
    ARXIV_SERVER = 'https://arxiv.org'
    DOI_SERVER = 'https://dx.doi.org'
    DATA_KEY = "primary_report_number,system_control_number,authors,title,abstract,publication_info,files"

    LIKELY_PATTERNS = [
        r'^[A-Za-z-]+-\d{4}-\d{3}$',
    ]

    @classmethod
    def get_info(cls, query):
        query_url = '{}?p={}&of=recjson&ot={}'.format(cls.API, query, cls.DATA_KEY)
        try:
            f = urlopen(query_url)  # "with" does not work on python2
            s = f.read()
            f.close()
        except HTTPError as e:
            raise Exception("Failed to fetch CDS information: " + e.__str__())
        try:
            results = json.loads(s.decode("utf-8"))
        except Exception as e:
            raise Exception('parse failed; query {} to CDS gives no result?: '.format(query) + e.__str__())
        if (not isinstance(results, list)) or len(results) == 0:
            raise Exception('query {} to CDS gives no result: '.format(query))
        if len(results) > 1:
            print('Warning: more than one entries are found')
        result = results[0]

        return result

    @classmethod
    def shorten_author(cls, author):
        family_name = author['last_name']
        return family_name.replace('-', '')

    @classmethod
    def try_to_construct(cls, query, force=False):
        if not force:
            if not any(re.match(r, query) for r in cls.LIKELY_PATTERNS):
                return False
        return cls(query)

    def __init__(self, query):
        self.query = query
        self._info = None

    @property
    def info(self):
        if not self._info:
            self._info = self.get_info(self.query)
            self._info['authors_plain'] = ['{first_name} {last_name}'.format(**a) for a in self._info['authors']]
        return self._info

    def report_number(self):
        return self.info['primary_report_number']

    def inspire_abs_url(self):
        return

    def abs_url(self):
        pass # return '{}/{}'.format(self.DOI_SERVER, self.doi)

    def pdf_url(self):
        pass #

    def title(self):
        return self.info['title']['title']

    def authors(self):
        return ', '.join(self.info['authors_plain'])

    def first_author(self):
        return self.info['authors_plain'][0]

    def authors_short(self):
        authors = [self.shorten_author(a) for a in self.info['authors']]
        if len(authors) > 4:
            authors = authors[0:4] + ['etal']
        return '-'.join(authors)

    def download_parameters(self):
        pass
        #if self.arxiv_id() and self.pdf_url():
        #    filename = '{id}-{authors}.pdf'.format(id=self.arxiv_id(), authors=self.authors_short())
        #    return self.pdf_url(), filename
