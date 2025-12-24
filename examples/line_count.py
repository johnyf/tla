"""Count nonempty, comment, blank lines in a TLA+ file."""
import argparse as _arg

import tla


_COMMENT_TOKENS = {
    'UNILINE_COMMENT',
    'MULTILINE_COMMENT'}


def count_lines(
        text:
            str
        ) -> dict[str, int]:
    """Return count of nonempty, comment, blank lines."""
    lexer = tla.Lexer()
    tokens = list(lexer.parse(text))
    comment_lines = set()
    nonempty_lines = set()
    other_lines = set()
    for token in tokens:
        start_line = token.line
        nonempty_lines.add(start_line)
        if token.symbol not in _COMMENT_TOKENS:
            other_lines.add(start_line)
            continue
        if token.symbol == 'UNILINE_COMMENT':
            comment_lines.add(start_line)
        if token.symbol != 'MULTILINE_COMMENT':
            raise AssertionError(token)
        n_newlines = token.value.count('\n')
        for diff in range(n_newlines + 1):
            line = start_line + diff
            comment_lines.add(line)
            nonempty_lines.add(line)
    n_nonempty = len(nonempty_lines)
    only_comment = comment_lines - other_lines
    n_comments = len(only_comment)
    n_lines = text.count('\n')
    if not text.endswith('\n'):
        n_lines += 1
    n_blank = n_lines - n_nonempty
    n_other = n_nonempty - len(only_comment)
    return dict(
        n_lines=n_lines,
        n_comments=n_comments,
        n_blank=n_blank,
        n_other=n_other)


def _main():
    """Entry point."""
    args = _parse_args()
    filename = args.filename
    with open(filename,
                mode='r',
                encoding='utf-8') as fd:
        text = fd.read()
    line_stats = count_lines(text)
    lines = '\n'.join(
        f'{k} = {v}'
        for k, v in line_stats.items())
    print(lines)


def _parse_args(
        ) -> _arg.Namespace:
    """Return program arguments."""
    parser = _arg.ArgumentParser(
        description='Line statistics for TLA+ files.')
    parser.add_argument(
        'filename',
        type=str,
        help='A TLA+ file.')
    return parser.parse_args()


if __name__ == '__main__':
    _main()
