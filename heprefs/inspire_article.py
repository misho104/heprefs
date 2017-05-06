from __future__ import absolute_import, division, print_function, unicode_literals
import re
import sys
import json
import heprefs.invenio as invenio
try:
    from urllib import quote_plus
    from urllib2 import urlopen, Request, HTTPError
except ImportError:
    from urllib.parse import quote_plus
    from urllib.request import urlopen, Request


class InspireArticle(object):
    API = 'https://inspirehep.net/search'
    RECORD_PATH = 'http://inspirehep.net/record/'
    ARXIV_SERVER = 'https://arxiv.org'
    DOI_SERVER = 'https://dx.doi.org'
    DATA_KEY = "primary_report_number,recid,system_control_number," + \
               "authors,corporate_name,title,abstract,publication_info,files"

    LIKELY_PATTERNS = [
        r'^(doi:)?10\.\d{4,}/.*$',  # doi
        r'^find? .+',               # old spires style
    ]

    @classmethod
    def get_info(cls, query):
        query_url = '{}?p={}&of=recjson&ot={}&rg=3'.format(cls.API, quote_plus(query), cls.DATA_KEY)
        try:
            f = urlopen(query_url)  # "with" does not work on python2
            s = f.read()
            f.close()
        except HTTPError as e:
            raise Exception("Failed to fetch inspireHEP information: " + e.__str__())
        try:
            results = json.loads(s.decode("utf-8"))
        except Exception as e:
            raise Exception('parse failed; query {} to inspireHEP gives no result?: '.format(query) + e.__str__())
        if (not isinstance(results, list)) or len(results) == 0:
            raise Exception('query {} to inspireHEP gives no result: '.format(query))
        if len(results) > 1:
            print('Warning: more than one entries are found, whose titles are')
            for i in results:
                title = i.get('title', dict()).get('title') or 'unknown ' + i.get('primary_report_number')
                print('    ' + title)
            print()

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
        scoap3_url = [i['url'] for i in self.info.get('files', []) if i['full_name'] == 'scoap3-fulltext.pdf']
        if scoap3_url:
            return scoap3_url[0]

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
        return invenio.title(self.info)

    def authors(self):
        # type: () -> str
        collaborations_list = invenio.collaborations(self.info)
        if collaborations_list:
            return ', '.join([c + ' (collaboration)' for c in collaborations_list])
        else:
            return ', '.join(invenio.flatten_authors(self.info))

    def first_author(self):
        # type: () -> str
        a = self.authors()
        return a[0] if len(a) > 0 else ''

    def texkey(self):
        # type: () -> str
        scn = self.info.get('system_control_number')
        if scn:
            if isinstance(scn, dict):
                scn = [scn]
            texkeys = [i['value'] for i in scn if i['institute'] == 'INSPIRETeX']
            if len(texkeys) > 1:
                print('Note: multiple TeXkeys are found? : ' + ' & '.join(texkeys))
            return texkeys[0] if texkeys else ''
        return ''

    def publication_info(self):
        # type: () -> str
        return invenio.publication_info_text(self.info)

    def download_parameters(self):
        # type: () -> (str, str)
        url = self.pdf_url()
        if not url:
            return ''

        arxiv_id = invenio.arxiv_id(self.info)
        primary_report_number = invenio.primary_report_number(self.info)
        file_title = \
            arxiv_id if arxiv_id else \
            primary_report_number if primary_report_number else \
            self.info['doi'] if 'doi' in self.info else \
            'unknown'

        filename = '{title}-{names}.pdf'.format(title=file_title, names=invenio.shorten_authors_text(self.info))
        return url, filename

    def debug(self):
        data = {
            'abs_url': self.abs_url(),
            'pdf_url': self.pdf_url(),
            'title': self.title(),
            'authors': self.authors(),
            'first_author': self.first_author(),
            'texkey': self.texkey(),
            'publication_info': self.publication_info(),
            '(download_filename)': self.download_parameters()[1],
            '(collaborations)': invenio.collaborations(self.info)
        }
        for k, v in data.items():
            print('{}: {}'.format(k, v))
