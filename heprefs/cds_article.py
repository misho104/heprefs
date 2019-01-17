from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
import os
import re
from logging import getLogger
from typing import Tuple  # noqa: F401

import heprefs.invenio as invenio
try:
    from urllib import quote_plus           # type: ignore   # noqa
    from urllib2 import urlopen, HTTPError  # type: ignore   # noqa
except ImportError:
    from urllib.parse import quote_plus
    from urllib.request import urlopen

logger = getLogger(__name__)


class CDSArticle(object):
    API = 'https://cds.cern.ch/search'
    RECORD_PATH = 'http://cds.cern.ch/record/'
    ARXIV_SERVER = 'https://arxiv.org'
    DOI_SERVER = 'https://dx.doi.org'
    DATA_KEY = 'primary_report_number,recid,system_control_number,' + \
               'authors,corporate_name,title,abstract,publication_info,files'

    LIKELY_PATTERNS = [
        r'^[A-Za-z-]+-\d+-\d+$',   # "ATLAS-CONF-2018-001" "CMS PAS EXO-16-009"
    ]

    @classmethod
    def get_info(cls, query):
        query_url = '{}?p={}&of=recjson&ot={}&rg=3'.format(cls.API, quote_plus(query), cls.DATA_KEY)
        try:
            f = urlopen(query_url)  # "with" does not work on python2
            s = f.read()
            f.close()
        except HTTPError as e:
            raise Exception('Failed to fetch CDS information: ' + e.__str__())
        try:
            results = json.loads(s.decode('utf-8'))
        except Exception as e:
            raise Exception('parse failed; query {} to CDS, but seems no result.: '.format(query) + e.__str__())
        if (not isinstance(results, list)) or len(results) == 0:
            raise Exception('query {} to CDS gives no result: '.format(query))
        if len(results) > 1:
            warning_text = 'more than one entries are found, whose titles are' + os.linesep
            for i in results:
                title = i.get('title', dict()).get('title') or 'unknown ' + i.get('primary_report_number')
                warning_text += '    ' + title + os.linesep
            logger.warning(warning_text)

        result = results[0]

        return result

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
        return self._info

    def abs_url(self):
        # type: () -> str
        if 'doi' in self.info:
            return '{}/{}'.format(self.DOI_SERVER, self.info['doi'])

        arxiv_id = invenio.arxiv_id(self.info)
        if arxiv_id:
            return '{}/abs/{}'.format(self.ARXIV_SERVER, arxiv_id)

        if 'recid' in self.info:
            return self.RECORD_PATH + str(self.info['recid'])

        return ''

    def pdf_url(self):
        # type: () -> str
        arxiv_id = invenio.arxiv_id(self.info)
        if arxiv_id:
            return '{}/pdf/{}'.format(self.ARXIV_SERVER, arxiv_id)

        pdf_files = [i for i in self.info.get('files', []) if i['superformat'] == '.pdf']
        if pdf_files:
            if len(pdf_files) > 1:
                print('Note: Fulltext PDF file is guessed by its size.')
            pdf_files.sort(key=lambda i: int(i.get('size', 0)), reverse=True)
            return pdf_files[0].get('url', '')

        return ''

    def title(self):
        # type: () -> str
        return re.sub(r'\s+', ' ', invenio.title(self.info))

    def authors(self):
        # type: () -> str
        collaborations_list = invenio.collaborations(self.info)
        if collaborations_list:
            return ', '.join([c + ' (collaboration)' for c in collaborations_list])
        else:
            return ', '.join(invenio.flatten_authors(self.info))

    def authors_short(self):
        # type: () -> str
        return invenio.shorten_authors_text(self.info)

    def first_author(self):
        # type: () -> str
        a = self.authors()
        return a[0] if len(a) > 0 else ''

    def publication_info(self):
        # type: () -> str
        return invenio.publication_info_text(self.info)

    def download_parameters(self):
        # type: () -> Tuple[str, str]
        url = self.pdf_url()
        if not url:
            return '', ''

        arxiv_id = invenio.arxiv_id(self.info)
        primary_report_number = invenio.primary_report_number(self.info)
        file_title = \
            arxiv_id if arxiv_id else \
            primary_report_number if primary_report_number else \
            self.info['doi'] if 'doi' in self.info else \
            'unknown'

        names = invenio.shorten_authors_text(self.info).replace(', ', '-').replace('et al.', 'etal')
        filename = '{title}-{names}.pdf'.format(title=file_title, names=names)
        return url, filename

    def debug(self):
        data = {
            'abs_url': self.abs_url(),
            'pdf_url': self.pdf_url(),
            'title': self.title(),
            'authors': self.authors(),
            'first_author': self.first_author(),
            'publication_info': self.publication_info(),
            '(download_filename)': self.download_parameters()[1],
            '(collaborations)': invenio.collaborations(self.info)
        }
        for k, v in data.items():
            print('{}: {}'.format(k, v))
