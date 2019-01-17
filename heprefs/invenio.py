from logging import getLogger
from typing import List, Mapping      # noqa: F401
import re
import sys

"""
    Utilities to handle JSON output from INVENIO system (inspireHEP/CDS).
"""


if sys.version_info[0] < 3:
    str = basestring            # noqa: F821
logger = getLogger(__name__)


def normalize_authors(json):
    # type: (dict) -> list
    authors = json.get('authors') or list()
    if not isinstance(authors, list):
        authors = [authors]

    authors_normal = list()      # type: List[Mapping[str, str]]
    collaborations_mode = False
    for i in authors:
        if i is None or not i.get('full_name'):  # 'full_name' might be None.
            continue

        if re.search('on behalf', i['full_name'], flags=re.IGNORECASE):
            break  # anything after 'on behalf of' is ignored.

        if re.search('collaborations ', i['full_name'], flags=re.IGNORECASE):
            # if no personal name is given, list collaboration names only
            if len(authors_normal) == 0:
                collaborations_mode = True
            if collaborations_mode:
                authors_normal.append(i)
        else:
            if not collaborations_mode:
                authors_normal.append(i)

    return authors_normal


def flatten_author(a):
    # type: (dict) -> str
    if a.get('first_name') and a.get('last_name'):
        return u'{first_name} {last_name}'.format(**a)
    elif a.get('full_name'):
        return a['full_name'] or ''
    else:
        logger.warning(u'how to handle the author name?: {}'.format(a.__str__()))
        return ''


def flatten_authors(json):
    # type: (dict) -> list
    return [flatten_author(a) for a in normalize_authors(json)]


def shorten_author(a):
    # type: (dict) -> str
    if a.get('last_name'):
        return a['last_name'].replace('-', '').replace(' ', '')
    elif a.get('full_name'):
        tmp = re.sub('on behalf of.*', '', a['full_name'], flags=re.IGNORECASE)
        return re.split(r', ', tmp)[0].replace('-', '')
    else:
        logger.warning(u'how to handle the author name?: {}'.format(a.__str__()))
        return ''


def shorten_authors(json):
    # type: (dict) -> list
    return [shorten_author(a) for a in normalize_authors(json)]


def collaborations(json):
    # type: (dict) -> list
    corporate_name = json.get('corporate_name')
    if not corporate_name:
        return list()

    collaborations_list = list()
    for i in corporate_name:
        for k, v in i.items():
            if k == 'collaboration' or k == 'name':
                v = re.sub('the', '', v, flags=re.IGNORECASE)
                v = re.sub('collaboration', '', v, flags=re.IGNORECASE)
                collaborations_list.append(v.strip())

    # remove duplicated entries (case insensitive)
    c_dict = dict()
    for c in collaborations_list:
        c_dict[c.lower()] = c
    return list(c_dict.values())


def shorten_authors_text(json):
    # type: (dict) -> str
    collaborations_list = collaborations(json)
    if collaborations_list:
        return ', '.join(collaborations_list)

    authors_short = shorten_authors(json)
    if len(authors_short) > 5:
        authors_short.append('et al.')
    return ', '.join(authors_short)


def publication_info_text(json):
    # type: (dict) -> str
    publication_info = json.get('publication_info')
    if publication_info:
        if isinstance(publication_info, list):
            publication_info = publication_info[0]
            logger.warning(u'More than one publication_info is found; first one is used.')
        if not isinstance(publication_info, dict):
            raise ValueError('publication_list is not a JSON hash.')
        items = [publication_info.get(key, '') for key in ['title', 'volume', 'year', 'pagination']]
        if items[2]:
            items[2] = '(' + items[2] + ')'
            items = [i for i in items if i]
        return ' '.join(items)
    return ''


def title(json):
    # type: (dict) -> str
    if 'title' in json and 'title' in json['title']:
        return json['title']['title']
    else:
        return ''


def arxiv_id(json):
    # type: (dict) -> str
    if 'primary_report_number' not in json:
        return ''
    report_numbers = json['primary_report_number'] or []
    if isinstance(report_numbers, str):
        report_numbers = list(report_numbers)

    arxiv_ids = list()
    for i in report_numbers:
        arxiv_pattern = re.match(r'^arXiv:(.*)$', i or '')
        if arxiv_pattern:
            arxiv_ids.append(arxiv_pattern.group(1))
    if len(arxiv_ids) > 1:
        logger.warning('multiple arxiv IDs are found? : ' + ' & '.join(arxiv_ids))
    return arxiv_ids[0] if arxiv_ids else ''


def primary_report_number(json):
    # type: (dict) -> str
    content = ''
    if json.get('primary_report_number') is None:
        pass
    elif isinstance(json['primary_report_number'], str):
        content = json['primary_report_number']
    elif isinstance(json['primary_report_number'], list):
        if arxiv_id(json):
            content = arxiv_id(json)
        else:
            content = json['primary_report_number'][0]
    else:
        raise ValueError('primary_report_number is in unknown format: ' + json['primary_report_number'].__str__())
    content = re.sub(r'^arXiv:', '', content, re.IGNORECASE)
    return content
