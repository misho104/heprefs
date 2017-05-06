"""
    Utilities to handle JSON output from INVENIO system (inspireHEP/CDS).
"""

import re


def flatten_author(a):
    # type: (dict) -> str
    if a.get('first_name') and a.get('last_name'):
        return '{first_name} {last_name}'.format(**a)
    elif a.get('full_name'):
        return a['full_name'] or ''
    else:
        print('Note: how to handle the author name?: {}'.format(a.__str__()))
        return ''


def flatten_authors(json):
    # type: (dict) -> list
    authors = json.get('authors') or list()
    return [flatten_author(a) for a in authors]


def shorten_author(a):
    # type: (dict) -> str
    if a.get('last_name'):
        return a['last_name'].replace('-', '')
    elif a.get('full_name'):
        return re.split(r', ', a['full_name'])[0].replace('-', '')
    else:
        print('Note: how to handle the author name?: {}'.format(a.__str__()))
        return ''


def shorten_authors(json):
    # type: (dict) -> list
    authors = json.get('authors') or list()
    return [shorten_author(a) for a in authors]


def collaborations(json):
    # type: (dict) -> list
    corporate_name = json.get('corporate_name')
    if not corporate_name:
        return list()

    collaborations_list = list()
    for i in corporate_name:
        for k, v in i.items():
            if k == 'collaboration':
                collaborations_list.append(v)
            elif k == 'name':
                v = re.sub(r'the', '', v, flags=re.IGNORECASE)
                v = re.sub(r'collaboration', '', v, flags=re.IGNORECASE)
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
        return '-'.join(collaborations_list)

    authors_short = shorten_authors(json)
    if len(authors_short) > 4:
        authors_short.append('etal')
    return '-'.join(authors_short)


def publication_info_text(json):
    # type: (dict) -> str
    if json.get('publication_info'):
        items = [json['publication_info'].get(key, '') for key in ['title', 'volume', 'year', 'pagination']]
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
    report_numbers = json['primary_report_number']
    if isinstance(report_numbers, str):
        report_numbers = list(report_numbers)

    arxiv_ids = list()
    for i in report_numbers:
        arxiv_pattern = re.match(r'^arXiv:(.*)$', i)
        if arxiv_pattern:
            arxiv_ids.append(arxiv_pattern.group(1))
    if len(arxiv_ids) > 1:
        print('Note: multiple arxiv IDs are found? : ' + ' & '.join(arxiv_ids))
    return arxiv_ids[0] if arxiv_ids else ''


def primary_report_number(json):
    # type: (dict) -> str
    if 'primary_report_number' not in json:
        return ''
    elif isinstance(json['primary_report_number'], str):
        return json['primary_report_number']
    elif isinstance(json['primary_report_number'], list):
        if arxiv_id(json):
            return arxiv_id(json)
        else:
            return json['primary_report_number'][0]
    else:
        raise ValueError('primary_report_number is in unknown format: ' + json['primary_report_number'].__str__())
