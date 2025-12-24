"""Parse the files in the TLAPS library."""
import os

import tla._lre as _parser
import tla._pprint as _pp_tla


# change this variable to a path where
# the TLAPS library is present
TLAPS_LIB_PATH = '$HOME/git/tlapm/library'


def parse_tlaps_modules():
    module_paths = _collect_tlaps_module_files()
    parser = _parser.Parser()
    for module_path in module_paths:
        print(f'parsing module `{module_path}`')
        text = _read_file(module_path)
        _parse_and_format(text, parser)


def _collect_tlaps_module_files(
        ) -> list[
            str]:
    path = TLAPS_LIB_PATH
    path = os.path.expandvars(path)
    tla_files = list()
    with os.scandir(path) as it:
        for entry in it:
            is_tla_file = (
                entry.is_file() and
                entry.name.endswith('.tla'))
            if is_tla_file:
                tla_files.append(entry)
    return [
        entry.path
        for entry in tla_files]


def _read_file(
        path:
            str
        ) -> str:
    with open(path,
                mode='r',
                encoding='utf-8') as fd:
        return fd.read()


def _parse_and_format(
        text:
            str,
        parser):
    """Return syntax-tree from `text`."""
    tree = parser.parse(text)
    if tree is None:
        raise AssertionError(tree)
    # text = _pp_tla.pformat_ast(tree)
    text = _pp_tla.pformat_tla(text)
    print(text)
    # _pp_tla._print_overwide_lines(
    #     text, _pp_tla.LINE_WIDTH)
    return tree


if __name__ == '__main__':
    parse_tlaps_modules()
