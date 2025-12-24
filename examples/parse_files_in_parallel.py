"""Parsing files in parallel using multiple processes."""
import argparse as _arg
import multiprocessing as _mlp
import os
import time

import tla


def main():
    """Entry point."""
    args = _parse_args()
    path = args.path
    if os.path.isdir(path):
        trees = parse_in_parallel(path)
    elif os.path.isfile(path):
        tree = parse_file(path)
        trees = [tree]
    else:
        raise ValueError(
            f'{filename} is not a directory or file.')
    for tree in trees:
        # text = tla.pformat_ast(tree)
        # print(text)
        print(tree)


def parse_in_parallel(
        root:
            str
        ) -> list[tuple]:
    """Parse files using multiple processes.

    Parses files in the directory tree
    rooted at `root`.
    """
    n_cpus = os.cpu_count()
    filepaths = _enum_tla_files(root)
    with _mlp.Pool(n_cpus) as pool:
        trees = pool.imap(parse_file, filepaths)
        t1 = time.perf_counter()
        trees = list(trees)
        t2 = time.perf_counter()
    input(f'parsing time: {t2-t1:1.2}')
    return trees


def parse_file(
        path:
            str
        ) -> tuple:
    """Return syntax tree from file."""
    with open(path,
                mode='r',
                encoding='utf-8') as fd:
        file_text = fd.read()
    file_text = _replace_tabs(path, file_text)
    print(f'Parsing file: `{path}`')
    tree = tla.parse(file_text)
    print(f'Completed parsing file: `{path}`')
    return tree


def _replace_tabs(
        filepath:
            str,
        text:
            str
        ) -> str:
    """Optionally replace tabs in `text`."""
    if '\t' not in text:
        return text
    print(
        f'File contains TAB: `{filepath}`\n'
        'Will replace each tab with 4 spaces.')
    return text.replace('\t', 4*'\x20')


def _enum_tla_files(
        root:
            str):
    """Yield paths of TLA+ files."""
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext != '.tla':
                continue
            yield os.path.join(dirpath, filename)


def _parse_args(
        ) -> _arg.Namespace:
    """Return program arguments."""
    parser = _arg.ArgumentParser()
    parser.add_argument(
        'path',
        help='path to directory that contains '
            'TLA+ files to parse, or to a file')
    return parser.parse_args()


if __name__ == '__main__':
    main()
