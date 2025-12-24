"""Installation script."""
import logging
import os
import sys

import setuptools


PACKAGE_NAME = 'tla'
DESCRIPTION = (
    'Parser and syntax tree for TLA+, '
    'the temporal logic of actions.')
README = 'README.md'
URL = 'https://github.com/johnyf/tla'
VERSION_FILE = f'{PACKAGE_NAME}/_version.py'
VERSION = '0.0.4'
VERSION_FILE_TEXT = (
    '# This file was generated from `setup.py`\n'
    f"version = '{VERSION}'\n")
PYTHON_REQUIRES = '>=3.11'
INSTALL_REQUIRES = [
    'parstools >= 0.0.5',
    ]
TESTS_REQUIRE = [
    'pytest >= 7.4.4',
    ]
CLASSIFIERS = [
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3 :: Only',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development :: Compilers',
    ]
KEYWORDS = [
    'TLA+', 'TLA', 'temporal logic of actions',
    'formal', 'specification',
    'expression', 'formula', 'module',
    'mathematics', 'theorem', 'proof',
    'parser', 'lexer', 'parsing',
    'ast', 'abstract syntax tree', 'syntax tree',
    ]


def run_setup():
    """Write version file and install package."""
    with open(README,
                mode='r',
                encoding='utf-8') as f:
        long_description = f.read()
    with open(VERSION_FILE,
                mode='w',
                encoding='utf-8') as f:
        f.write(VERSION_FILE_TEXT)
    _build_lr_parser()
    setuptools.setup(
        name='tla',
        version=VERSION,
        description=DESCRIPTION,
        long_description=long_description,
        long_description_content_type='text/markdown',
        author='Ioannis Filippidis',
        author_email='jfilippidis@gmail.com',
        url=URL,
        license='BSD-3-Clause',
        python_requires=PYTHON_REQUIRES,
        install_requires=INSTALL_REQUIRES,
        packages=['tla'],
        package_dir={'tla': 'tla'},
        package_data={
            'tla': ['tla_parser.json']},
        classifiers=CLASSIFIERS,
        keywords=KEYWORDS)


def _build_lr_parser():
    """Build the LR(1) parser state-machine."""
    if 'egg_info' in sys.argv:
        print(
            'found parameter '
            '`egg_info`, skipping '
            'building the parser')
        return
    if not _parstools_is_installed():
        return
    dirpath = os.path.dirname(__file__)
    sys.path.insert(0, dirpath)
        # to import `tla._lre` from here
    import tla._lre as _lr
    # logging.basicConfig(level=logging.DEBUG)
    parser = _lr.ExprParser()
    parser.parse('1')


def _parstools_is_installed(
        ) -> bool:
    """Return `True` if `parstools` is installed."""
    try:
        import parstools
    except ImportError:
        print(
            'WARNING: package `tla` could not '
            'cache the LR(1) parser tables, '
            'during installation.')
        return False
    return True


if __name__ == '__main__':
    run_setup()
