from __future__ import absolute_import, division, print_function, unicode_literals
import re
import sys
import json
try:
    from urllib2 import urlopen, Request, HTTPError
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError


class DOIArticle(object):
    DOI_SERVER = 'https://dx.doi.org'
    ARXIV_SERVER = 'https://arxiv.org'
    INSPIRE_API = 'https://inspirehep.net/search'
    DATA_KEY = "primary_report_number,system_control_number,authors,title,abstract,publication_info"

    @classmethod
    def get_info(cls, doi):
        # use inspireHEP to get information

        query_url = '{}?p={}&of=recjson&ot={}'.format(cls.INSPIRE_API, doi, cls.DATA_KEY)
        try:
            f = urlopen(query_url)  # "with" does not work on python2
            s = f.read()
            f.close()
        except HTTPError as e:
            raise Exception("Failed to fetch inspireHEP information: " + e.__str__())
        try:
            results = json.loads(s.decode("utf-8"))
        except Exception as e:
            raise Exception('parse failed; maybe doi {} not found in inspireHEP: '.format(doi) + e.__str__())
        if (not isinstance(results, list)) or len(results) == 0:
            raise Exception('doi {} not found in inspireHEP: '.format(doi))
        if len(results) > 1:
            print('Warning: more than one entries are found')
        result = results[0]

        return result

    @classmethod
    def shorten_author(cls, author):
        family_name = author['last_name']
        return family_name.replace('-', '')

    @classmethod
    def try_to_construct(cls, key):
        try:
            obj = cls(key)
        except ValueError:
            return False
        return obj

    def __init__(self, doi):
        self._doi = None
        self.doi = doi
        self._info = None

    @property
    def doi(self):
        return self._doi

    @doi.setter
    def doi(self, i):
        doi_style = re.match(r'^(doi:)?(10\.\d{4,}/.*)$', i)
        if doi_style:
            self._doi = doi_style.group(2)
        else:
            raise ValueError('incorrect doi')

    @property
    def info(self):
        if not self._info:
            self._info = self.get_info(self.doi)

            self._info['arXiv'] = None
            for i in self._info["primary_report_number"]:
                arxiv_pattern = re.match(r'^arXiv:(.*)$', i)
                if arxiv_pattern:
                    self._info['arXiv'] = arxiv_pattern.group(1)

            self._info['inspire_key'] = None
            for i in self._info['system_control_number']:
                if i['institute'] == 'INSPIRETeX':
                    self._info['inspire_key'] = i['value']

            self._info['authors_plain'] = ['{first_name} {last_name}'.format(**a) for a in self._info['authors']]
            # print(self._info['title'])
            # print(self._info['publication_info'])
            # print(self._info['abstract'])
            # print(self._info['authors'])
            # print(self._info['arXiv'])
            # print(self._info['inspire_key'])
        return self._info

    def abs_url(self):
        return '{}/{}'.format(self.DOI_SERVER, self.doi)

    def pdf_url(self):
        # use arXiv-PDF url
        if self.info['arXiv']:
            return '{}/pdf/{}'.format(self.ARXIV_SERVER, self.info['arXiv'])
        else:
            return None

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

    def arxiv_id(self):
        return self.info['arXiv']

    def inspire_key(self):
        return self.info['inspire_key']

    def publication_info(self):
        if self.info['publication_info']:
            return '{title} {volume} ({year}) {pagination}'.format(**(self.info['publication_info']))
        return None

    def download_parameters(self):
        if self.arxiv_id() and self.pdf_url():
            filename = '{id}-{authors}.pdf'.format(id=self.arxiv_id(), authors=self.authors_short())
            return self.pdf_url(), filename
