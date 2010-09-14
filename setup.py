from distutils.core import setup
from textwrap import dedent, fill

def format_desc(desc):
    return fill(dedent(desc), 200)

def format_classifiers(classifiers):
    return dedent(classifiers).strip().split('\n')

setup(
    name = "CloseableQueue",
    version = "0.9",
    author = "Ted Tibbetts",
    author_email = "intuited@gmail.com",
    url = "http://github.com/intuited/CloseableQueue",
    description = format_desc("""
        These classes and functions provide the facility to close a queue
        and to use it as an iterator.
        """),
    classifiers = format_classifiers("""
        Development Status :: 4 - Beta
        Intended Audience :: Developers
        License :: OSI Approved :: BSD License
        Operating System :: OS Independent
        Programming Language :: Python
        Programming Language :: Python :: 2
        Topic :: Software Development :: Libraries :: Python Modules
        Topic :: Utilities
        """),
    keywords = 'queue threading iterator iterable'.split(' '),
    packages = ['CloseableQueue'],
    package_dir = {'CloseableQueue': ''},
    )
