#!/usr/bin/env python

from __future__ import absolute_import, division, print_function
import click
import sys, re
from collections import OrderedDict
from heprefs.arxiv_article import ArxivArticle
from heprefs.cds_article import CDSArticle
from heprefs.inspire_article import InspireArticle


__version__ = '0.1.2'
types = OrderedDict([
    ('arxiv', ArxivArticle),
    ('cds', CDSArticle),
    ('ins', InspireArticle),
])


def construct_article(key, type=None):
    if type in types.keys():
        classes = [types[type]]
        force = True
    elif type is None:
        classes = types.values()
        force = False
    else:
        raise Exception('invalid type specified')

    for c in classes:
        obj = c.try_to_construct(key, force=force)
        if obj:
            return obj

    click.echo('Reference for {} not found.'.format(key))
    sys.exit(1)


@click.group(help='Handle the references for high-energy physics',
             context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(__version__, '-V', '--version')
# @click.option('-v', '--verbose', is_flag=True, default=False, help="Show verbose output")
def heprefs_main(**args):
    pass


def heprefs_subcommand(help_msg):
    d1 = heprefs_main.command(help=help_msg)
    d2 = click.option('-t', '--type',
                      type=click.Choice(types.keys()),
                      help="Specify article type (guessed if unspecified)")
    d3 = click.argument('key', required=True)

    def decorator(func):
        d1(d2(d3(func)))
    return decorator


def with_article(func):
    def decorator(key, type, **kwargs):
        article = construct_article(key, type)
        func(article, **kwargs)
    decorator.__name__ = func.__name__
    return decorator


@heprefs_subcommand(help_msg='display title of the article')
@with_article
def title(article):
    click.echo(article.title())


@heprefs_subcommand(help_msg='display authors of the article')
@with_article
def authors(article):
    click.echo(article.authors())


@heprefs_subcommand(help_msg='display first author of the article')
@with_article
def first_author(article):
    click.echo(article.first_author())


@heprefs_subcommand(help_msg='Open abstract page with Browser')
@with_article
def abs(article):
    url = article.abs_url()
    click.echo("Opening {} ...".format(url))
    click.launch(url)


@heprefs_subcommand(help_msg='Open PDF with Browser')
@with_article
def pdf(article):
    url = article.pdf_url()
    click.echo("Opening {} ...".format(url))
    click.launch(url)


@heprefs_subcommand(help_msg='display short information of the article')
@with_article
def short_info(article):
    click.echo(u"{authors}\n{title}\n{abs_url}".format(
        authors=article.authors(),
        title=article.title(),
        abs_url=article.abs_url(),
    ))


@heprefs_subcommand(help_msg='Download PDF file')
@click.option('-o', '--open', is_flag=True, default=False, help="Open PDF file by viewer")
@with_article
def get(article, open):
    (pdf_url, filename) = article.download_parameters()
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    click.echo("Downloading {} ...".format(pdf_url))

    with click.progressbar(length=1, label=filename) as bar:
        try:
            import urllib
            urllib.urlretrieve(pdf_url, filename, reporthook=lambda b, c, t: bar.update(c/t))
        except AttributeError:
            from urllib import request
            request.urlretrieve(pdf_url, filename, reporthook=lambda b, c, t: bar.update(c/t))
    if open:
        click.launch(filename)


@heprefs_subcommand(help_msg='display information')
@with_article
def debug(article):
    article.debug()
