#!/usr/bin/env python

from __future__ import absolute_import, division, print_function
import click
from collections import OrderedDict
from heprefs.arxiv_article import ArxivArticle
from heprefs.cds_article import CDSArticle
from heprefs.doi_article import DOIArticle


__version__ = "0.1.0"
types = OrderedDict([
    ('arxiv', ArxivArticle),
    ('cds', CDSArticle),
    ('doi', DOIArticle),
])

def construct_article(key, type=None):
    if type in types.keys():
        classes = [types[type]]
    elif type is None:
        classes = types.values()
    else:
        raise Exception('invalid type specified')

    for c in classes:
        obj = c.try_to_construct(key)
        if obj:
            return obj

    click.echo('Reference for {} not found.'.format(key))


@click.group(help='Handle the references for high-energy physics')
@click.version_option(__version__, '-V', '--version')
# @click.option('-v', '--verbose', is_flag=True, default=False, help="Show verbose output")
def heprefs_main(**args):
    pass


def heprefs_subcommand(help):
    d1 = heprefs_main.command(help=help)
    d2 = click.option('-t', '--type',
                      type=click.Choice(['arxiv', 'cds', 'doi']),
                      help="Specify article type (guessed if unspecified)")
    d3 = click.argument('key', required=True)
    def decorator(func):
        d1(d2(d3(func)))
    return decorator


@heprefs_subcommand(help='Open abstract page with Browser')
def abs(key, type):
    article = construct_article(key, type)
    click.launch(article.abs_url())


@heprefs_subcommand(help='Open PDF with Browser')
def pdf(key, type):
    article = construct_article(key, type)
    click.launch(article.pdf_url())


@heprefs_subcommand(help='Download PDF file')
def get(key, type):
    article = construct_article(key, type)
    (pdf_url, filename) = article.download_parameters()

    with click.progressbar(length=1, label=filename) as bar:
        try:
            import urllib
            urllib.urlretrieve(pdf_url, filename, reporthook=lambda b, c, t: bar.update(c/t))
        except AttributeError:
            from urllib import request
            request.urlretrieve(pdf_url, filename, reporthook=lambda b, c, t: bar.update(c/t))


@heprefs_subcommand(help='display title of the article')
def title(key, type):
    article = construct_article(key, type)
    click.echo(article.title())


@heprefs_subcommand(help='display authors of the article')
def authors(key, type):
    article = construct_article(key, type)
    click.echo(article.authors())


@heprefs_subcommand(help='display first author of the article')
def first_author(key, type):
    article = construct_article(key, type)
    click.echo(article.first_author())

