heprefs: CLI for high-energy physics references
===============================================

![screen shot](https://user-images.githubusercontent.com/776101/36547606-8aa5d438-17ee-11e8-9ddb-64a5a4e7d2f5.gif)

Do you think the commands are too long? Simply configure your shell by editing  `.zshrc`; for example,

```:.zshrc
function xa()      { if [ $# != 0 ]; then for i in $*; do heprefs abs $i; done; fi }
function xx()      { if [ $# != 0 ]; then for i in $*; do heprefs pdf $i; done; fi }
function xget()    { if [ $# != 0 ]; then for i in $*; do heprefs get -o $i; done; fi }
function xsource() { if [ $# != 0 ]; then for i in $*; do heprefs source -u $i; done; fi }
```

(or see below) and you will just type `xget 1802.07720 1708.00283` etc. to download multiple PDFs!

### Set up

For Python 2 or 3.

#### Install

```console
$ pip install git+https://github.com/misho104/heprefs.git

Collecting git+https://github.com/misho104/heprefs.git
  Cloning https://github.com/misho104/heprefs.git to /private/tmp/pip-wjd8srsu-build
...
Successfully installed arxiv-0.1.1 click-6.7 feedparser-5.2.1 heprefs-0.1.0 requests-2.13.0
```

or you can install specific version by, e.g.,

```console
$ pip install git+https://github.com/misho104/heprefs.git@v0.1.0       # for v0.1.0
$ pip install git+https://github.com/misho104/heprefs.git@development  # for development version
```

#### Upgrade

```console
$ pip install git+https://github.com/misho104/heprefs.git --upgrade
```

#### Uninstall

```console
$ pip uninstall heprefs
```


### Usage

#### Open abstract pages by a browser

```console
$ heprefs abs 1505.02996               # arXiv
$ heprefs abs hep-th/9711200           # arXiv (old style)
$ heprefs abs ATLAS-CONF-2017-018      # CERN Document Server
$ heprefs abs 10.1038/nphys3005        # DOI (inspireHEP)
$ heprefs abs "fin a Ellis"            # inspireHEP (first result is only shown)

$ heprefs abs 9709356                  # equivalent to 'hep-ph/9709356'
```

#### Open PDF by browser, or Download PDF file

PDF may not be found for CDS or inspireHEP queries.

```console
$ heprefs pdf 1505.02996               # arXiv
$ heprefs pdf ATLAS-CONF-2017-018      # CERN Document Server

$ heprefs get 10.1038/nphys3005        # DOI (inspireHEP)
$ heprefs get "fin a Ellis"            # inspireHEP (first result)

$ heprefs get -o "fin a Giudice"       # open the PDF file
```

#### Show information

```console
$ heprefs authors 1505.02996
$ heprefs first_author hep-th/9711200
$ heprefs title 10.1038/nphys3005
$ heprefs short_info ATLAS-CONF-2017-018
```


### Advanced usage

#### Specify search engine

There are three **types**: arXiv, inspireHEP, and CDS. They are automatically guessed, but you can specify a type:

```console
$ heprefs abs -t arxiv 1505.02996           # arXiv
$ heprefs abs -t cds   "top asymmetry"      # CDS
$ heprefs abs -t ins   "top asymmetry"      # inspireHEP

$ heprefs abs        ATLAS-CONF-2017-018    # guessed as CDS search
$ heprefs abs -t ins ATLAS-CONF-2017-018    # forced to use inspireHEP
```

#### Commands are too long?

In your `.zshrc`, `.bashrc`, etc...

```:.zshrc
alias xa='heprefs abs'
alias xx='heprefs pdf'
alias xget='heprefs get'
```

or if you want to handle multiple arguments,

```:.zshrc
function xa()      { if [ $# != 0 ]; then for i in $*; do heprefs abs $i; done; fi }
function xx()      { if [ $# != 0 ]; then for i in $*; do heprefs pdf $i; done; fi }
function xget()    { if [ $# != 0 ]; then for i in $*; do heprefs get -o $i; done; fi }
function xsource() { if [ $# != 0 ]; then for i in $*; do heprefs source -u $i; done; fi }
```



(You may want to use inspire search as well, though this is not a feature of this software.)

```:.zshrc
function browser() {
  google-chrome $* &             # on Linux
  # open $* -a Google\ Chrome    # on macOS
}

function fin() {
  local query; if [ $# != 0 ]; then; for i in $*; do; query="$query+$i"; done; fi
  query=`echo $query | sed 's/^\+//'`
  browser http://inspirehep.net/search\?p=fin+$query &
}

function insp() {
  local query; if [ $# != 0 ]; then; for i in $*; do; query="$query+$i"; done; fi
  query=`echo $query | sed 's/^\+//'`
  browser http://inspirehep.net/search\?p=$query &
}
```

and now you can invoke

```console
$ xa 1505.02996
$ xget 9709356
$ fin a Giudice and Masiero
$ fin bb hep-th/9711200
$ insp relaxion
```


#### Debug command for developers

```console
$ heprefs debug 1505.02996
```
