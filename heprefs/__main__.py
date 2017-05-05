import os
import sys

"""
Entry point if executed as 'python heprefs
"""


if __name__ == '__main__':
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir)
    sys.path.insert(0, path)
    from heprefs.heprefs import heprefs_main
    sys.exit(heprefs_main())
