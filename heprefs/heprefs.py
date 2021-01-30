#!/usr/bin/env python

from __future__ import absolute_import, division, print_function
import click
import os
import sys
import re
import tarfile
from logging import basicConfig, getLogger, DEBUG
from collections import OrderedDict
from .arxiv_article import ArxivArticle
from .cds_article import CDSArticle
from .inspire_article import InspireArticle

__author__ = 'Sho Iwamoto / Misho'
__version__ = '0.1.5'
__license__ = 'MIT'

basicConfig(level=DEBUG)
logger = getLogger(__name__)

types = OrderedDict([
    ('arxiv', ArxivArticle),
    ('cds', CDSArticle),
    ('ins', InspireArticle),
])


def retrieve_hook(bar):
    return lambda b, c, t: bar.update(min(int(b * c / t * 100), 100))


def construct_article(key, type=None):
    if type in types.keys():
        classes = [types[type]]
        force = True
    elif type is None:
        classes = list(types.values())
        force = False
    else:
        raise Exception('invalid type specified')

    for c in classes:
        obj = c.try_to_construct(key, force=force)  # type: ignore
        if obj:
            return obj

    click.echo('Reference for {} not found.'.format(key), err=True)
    sys.exit(1)


@click.group(help='Handle the references for high-energy physics',
             context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(__version__, '-V', '--version')
# @click.option('-v', '--verbose', is_flag=True, default=False, help="Show verbose output")
def heprefs_main(**args):
    pass


def heprefs_subcommand(help_msg):
    d1 = heprefs_main.command(short_help=help_msg, help=help_msg)
    d2 = click.option('-t', '--type',
                      type=click.Choice(types.keys()),
                      help='Specify article type (guessed if unspecified)')
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
    click.echo('Opening {} ...'.format(url), err=True)
    click.launch(url)


@heprefs_subcommand(help_msg='Open PDF with Browser')
@with_article
def pdf(article):
    url = article.pdf_url()
    click.echo('Opening {} ...'.format(url), err=True)
    click.launch(url)


@heprefs_subcommand(help_msg='display short information of the article')
@click.option('-s', '--shortauthors', is_flag=True, default=False, help='Shorten authors')
@with_article
def short_info(article, shortauthors):
    authors = article.authors_short() if shortauthors else article.authors()
    click.echo(u"{authors}\n{title}\n{abs_url}".format(
        authors=authors,
        title=article.title(),
        abs_url=article.abs_url(),
    ))


@heprefs_subcommand(help_msg='Download PDF file and display the filename')
@click.option('-o', '--open', is_flag=True, default=False, help='Open PDF file by viewer')
@with_article
def get(article, open):
    (pdf_url, filename) = article.download_parameters()
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    click.echo('Downloading {} ...'.format(pdf_url), err=True)

    with click.progressbar(length=100, label=filename, file=sys.stderr) as bar:
        try:
            import urllib
            urllib.urlretrieve(pdf_url, filename, reporthook=retrieve_hook(bar))  # type: ignore
        except AttributeError:
            from urllib import request
            request.urlretrieve(pdf_url, filename, reporthook=retrieve_hook(bar))
    # display the name so that piped to other scripts
    click.echo(filename)
    if open:
        click.launch(filename)


@heprefs_subcommand(help_msg='Download arXiv source file and display the filename')
@click.option('-u', '--untar', is_flag=True, default=False, help='Untar downloaded file')
@with_article
def source(article, untar):
    if isinstance(article, ArxivArticle):
        url = article.source_url()
        filename = '{}.tar.gz'.format(article.arxiv_id)
        dirname = '{}.source'.format(article.arxiv_id)
    else:
        click.echo('`source` is available only for arXiv articles.', err=True)
        sys.exit(1)

    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    click.echo('Downloading {} ...'.format(url), err=True)

    with click.progressbar(length=100, label=filename, file=sys.stderr) as bar:
        try:
            import urllib
            urllib.urlretrieve(url, filename, reporthook=retrieve_hook(bar))  # type: ignore
        except AttributeError:
            from urllib import request
            request.urlretrieve(url, filename, reporthook=retrieve_hook(bar))

    if not os.path.isfile(filename):
        click.echo('Download failed and file {} is not created.'.format(filename), err=True)
        sys.exit(1)

    if untar:
        if tarfile.is_tarfile(filename):
            with tarfile.open(filename) as f:
                f.list()
                f.extractall(path=dirname)

            click.echo('\n{filename} successfully extracted to {dirname}.'.format(
                filename=filename, dirname=dirname), err=True)
        else:
            click.echo("""
{filename} has been downloaded but seems not a TAR file.
Execute `gunzip {filename}` and inspect the file.""".format(filename=filename), err=True)
    # display the name so that piped to other scripts
    click.echo(filename)


@heprefs_subcommand(help_msg='display information')
@with_article
def debug(article):
    article.debug()
