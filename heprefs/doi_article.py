from __future__ import absolute_import, division, print_function, unicode_literals
import re
import arxiv

class DOIArticle:
    @classmethod
    def try_to_construct(cls, key):
        return False
