from setuptools import setup
import re
import ast

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('heprefs/heprefs.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(f.read().decode('utf-8')).group(1)))

setup(
    name='heprefs',
    version=version,
    packages=['heprefs'],
    install_requires=['click', 'arxiv'],
    entry_points={
        'console_scripts': 'heprefs = heprefs.heprefs:heprefs_main'
    },
    zip_safe=False,  
    classifiers=[  
        'Environment :: Console',
        'Programming Language :: Python',
    ],
)  
