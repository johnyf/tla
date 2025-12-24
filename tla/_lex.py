"""Lexer for TLA+."""
import argparse as _arg
import collections.abc as _abc
import logging
import re
import time

import parstools._lex as _lex
import tla._langdef as _langdef
import tla._utils as _utils


logger = logging.getLogger(__name__)


COMMENT_TOKENS = [
    'UNILINE_COMMENT',
        # `\* ...\n`
    'MULTILINE_COMMENT']
        # `(* ... *)`
_utils.assert_len(COMMENT_TOKENS, 2)
_LITERAL_LEXEMES = {
    'DASH_LINE':
        r' \-\-\-\-(\-)* ',
    'EQ_LINE':
        r' ====(=)* ',
    'STEP_NUMBER':
        r'''
        <[0-9]+>
        [a-zA-Z0-9_]*
        \.*
        ''',
    'STEP_NUMBER_ASTERISK':
        r'''
        <\*>
        \.*
        ''',
    'STEP_NUMBER_PLUS':
        r'''
        <\+>
        \.*
        ''',
    }
_utils.assert_len(_LITERAL_LEXEMES, 5)
_OTHER_TOKENS = {
    'FLOAT',
    'DECIMAL_INTEGER',
    'NAME',
    'MULTILINE_STRING_LITERAL',
    'SF_',
    'STRING_LITERAL',
    'WF_',
    }
_BSLASH_SUFFIXES = {
    'A',
    'AA',
    'approx',
    'asymp',
    'bigcirc',
    'bullet',
    'cap',
    'cdot',
    'circ',
        # synonym to `\o`
    'cong',
    'cup',
    'div',
    'doteq',
    'E',
    'EE',
    'equiv',
        # synonym to `<=>`
    'geq',
        # synonym to `>=`
    'gg',
    'in',
    'intersect',
        # synonym to `\cap`
    'land',
        # synonym to `/\`
    'leadsto',
        # synonym to `~>`
    'leq',
        # synonym to `<=`
    'll',
    'lnot',
        # synonym to `~`
    'lor',
        # synonym to `\/`
    'mod',
        # synonym to `%`
    'neg',
        # synonym to `~`
    'notin',
    'o',
    'odot',
        # synonym to `(.)`
    'ominus',
        # synonym to `(-)`
    'oplus',
        # synonym to `(+)`
    'oslash',
        # synonym to `(\)`
    'otimes',
        # synonym to `(\X)`
    'prec',
    'preceq',
    'propto',
    'setminus',
        # synonym to `\`
    'sim',
    'simeq',
    'sqcap',
    'sqcup',
    'sqsubset',
    'sqsubseteq',
    'sqsupset',
    'sqsupseteq',
    'star',
    'subset',
    'subseteq',
    'succ',
    'succeq',
    'supset',
    'supseteq',
    'times',
        # synonym to `\X`
    'union',
        # synonym to `\cup`
    'uplus',
    'wr',
    'X',
        # CARTESIAN
    }
_utils.assert_len(_BSLASH_SUFFIXES, 59)
_PICTORIAL_LEXEMES = {
    '=>':
        'EQ_RANGLE',
    '<=>':
        'LANGLE_EQ_RANGLE',
    '~':
        'TILDE',
    "'":
        'PRIME',
    '^+':
        'CIRCUMFLEX_PLUS',
    '^*':
        'CIRCUMFLEX_ASTERISK',
    '^#':
        'CIRCUMFLEX_HASHMARK',
    '(+)':
        'OPLUS',
    '(-)':
        'ODASH',
    '(/)':
        'OSLASH',
    '(.)':
        'ODOT',
    r'(\X)':
        'OCARTESIAN',
    '/':
        'SLASH',
    '//':
        'DOUBLE_SLASH',
    '\\':
        'BSLASH',
    '/\\':
        'AND',
    r'\/':
        'OR',
    '??':
        'DOUBLE_QUESTION',
    '.':
        'DOT',
    '..':
        'DOUBLE_DOT',
    '...':
        'TRIPLE_DOT',
    '=':
        'EQ',
    '==':
        'DOUBLE_EQ',
    '|':
        'PIPE',
    '||':
        'DOUBLE_PIPE',
    '&':
        'ET',
    '&&':
        'DOUBLE_ET',
    '$':
        'DOLLAR',
    '$$':
        'DOUBLE_DOLLAR',
    '@':
        'AT',
    '@@':
        'DOUBLE_AT',
    '+':
        'PLUS',
    '++':
        'DOUBLE_PLUS',
    '-.':
        'DASH_DOT',
    '-':
        'DASH',
    '--':
        'DOUBLE_DASH',
    '*':
        'ASTERISK',
    '**':
        'DOUBLE_ASTERISK',
    '^':
        'CIRCUMFLEX',
    '^^':
        'DOUBLE_CIRCUMFLEX',
    '!':
        'EXCLAMATION',
    '!!':
        'DOUBLE_EXCLAMATION',
    '%':
        'PERCENT',
    '%%':
        'DOUBLE_PERCENT',
    '/=':
        'NEQ',
    '#':
        'HASHMARK',
    '##':
        'DOUBLE_HASHMARK',
    '|-':
        'PIPE_DASH',
    '|=':
        'PIPE_EQ',
    '-|':
        'DASH_PIPE',
    '=|':
        'EQ_PIPE',
    ':':
        'COLON',
    '::':
        'DOUBLE_COLON',
    ':=':
        'COLON_EQ',
    '::=':
        'DOUBLE_COLON_EQ',
    '<:':
        'LANGLE_COLON',
    ':>':
        'COLON_RANGLE',
    ',':
        'COMMA',
    '<-':
        'LARROW',
    '->':
        'RARROW',
    '|->':
        'MAPSTO',
    '-+->':
        'ARROW_PLUS',
    '~>':
        'LEADSTO',
    '(':
        'LPAREN',
    ')':
        'RPAREN',
    '{':
        'LBRACE',
    '}':
        'RBRACE',
    '[':
        'LBRACKET',
    ']':
        'RBRACKET',
    ']_':
        'RBRACKET_UNDERSCORE',
    '[]':
        'LBRACKET_RBRACKET',
    '<':
        'LANGLE',
    '>':
        'RANGLE',
    '<>':
        'LANGLE_RANGLE',
    '<<':
        'DOUBLE_LANGLE',
    '>>':
        'DOUBLE_RANGLE',
    '>>_':
        'DOUBLE_RANGLE_UNDERSCORE',
    '=<':
        'EQ_LANGLE',
    '<=':
        'LANGLE_EQ',
    '>=':
        'RANGLE_EQ',
    '_':
        'UNDERSCORE',
    }
_utils.assert_len(_PICTORIAL_LEXEMES, 81)
_TOKEN_RENAMING = {
    'BSLASH_CAP':
        'CAP',
    'BSLASH_CIRC':
        'CIRC',
    'BSLASH_CUP':
        'CUP',
    'BSLASH_TIMES':
        'CARTESIAN',
    'BSLASH_X':
        'CARTESIAN',
    # 'HASHMARK':
    #     'NEQ',
    }
_utils.assert_len(_TOKEN_RENAMING, 5)


def map_lexemes_to_tokens(
        ) -> dict[str, str]:
    """Return mapping lexemes to token names."""
    lextok = {
        rf'\{s}':
            f'BSLASH_{s.upper()}'
        for s in _BSLASH_SUFFIXES}
    lextok |= _PICTORIAL_LEXEMES
    op_synonyms = _langdef.make_synonymous_lexemes()
    for op, synonyms in op_synonyms.items():
        for other in synonyms:
            token_name = lextok[op]
            _add_to_dict(other, token_name, lextok)
    def mapper(value):
        return _TOKEN_RENAMING.get(value, value)
    lextok = _utils.map_values(mapper, lextok)
    return lextok


def _add_to_dict(
        key:
            str,
        value:
            str,
        mapping:
            dict
        ) -> None:
    """Set `mapping[key] = value`.

    Raise `AssertionError` if `key`
    is already in `mapping`.
    """
    add = (
        key not in mapping or
        _is_bslash_operator(key))
    if add:
        mapping[key] = value
        return
    raise AssertionError(
        f'{key = }, '
        f'{mapping = }')


# lexer states
_INITIAL_LEXER_STATE = 'initial'
_COMMENT_LEXER_STATE = 'multilinecomment'
_STRING_LEXER_STATE = 'string'
_MULTILINE_STRING_LEXER_STATE = 'multilinestring'


class Lexer(
        _lex.StatefulLexer):
    """Lexer for TLA+.

    Use the `Lexer.parse()` method to obtain
    tokens from text. For example:

    ```python
    import tla

    text = '''
        ---- MODULE example ----
        A == 1
        ====
        '''
    lexer = tla.Lexer()
    tokens = lexer.parse(text)
    for token in tokens:
        print(token)
    ```

    This class describes the grammar to
    build the TLA+ lexer, as methods and
    attributes that start with `t_`.

    Relevant functions:

    - `tla._preparser.filter_preamble()`
    - `tla._preparser.filter_postamble()`

    If these functions are used, combine them
    with the lexer as follows:

    ```python
    import tla
    import tla._preparser as _prp

    text = '''
        ---- MODULE example ----
        A == 1
        ====
        '''
    lexer = tla.Lexer()
    text = _prp.filter_preamble(text)
    tokens = lexer.parse(text)
    tokens = _prp.filter_postamble(tokens)
        # interacts with the lexer,
        # by yielding tokens up to the
        # end of the main module
    ```
    """

    lexing_states = (
        _INITIAL_LEXER_STATE,
        _COMMENT_LEXER_STATE,
        _STRING_LEXER_STATE,
        _MULTILINE_STRING_LEXER_STATE)

    def __init__(
            self
            ) -> None:
        self._lextok = map_lexemes_to_tokens()
        self.tokens = sorted(set().union(
            _langdef.KEYWORDS,
            COMMENT_TOKENS,
            _LITERAL_LEXEMES,
            _OTHER_TOKENS,
            self._lextok.values(),
            ))
        self.token_types = self.tokens
        self.states = (
            (_COMMENT_LEXER_STATE,
                'exclusive'),
            (_STRING_LEXER_STATE,
                'exclusive'),
            (_MULTILINE_STRING_LEXER_STATE,
                'exclusive'))
        self._keywords = set(_langdef.KEYWORDS)
        self._check_bslash_token_regex()
        self._make_token_vars()
        # state
        self._comment_level: int = 0
        self._comment_start: int | None = None
        self._string_start: int | None = None
        super().__init__()

    def _make_token_vars(
            self
            ) -> None:
        regexes = dict(_LITERAL_LEXEMES)
        lextok = {
            k: v
            for k, v in self._lextok.items()
            if not _is_bslash_operator(k)}
        _utils.make_token_grammar(
            lextok, regexes, self)

    def parse(
            self,
            text:
                str
            ) -> _abc.Iterable[_lex.Token]:
        """Yield tokens for `text`.

        To tokenize the lexeme `ELIF` as
        an identifier:

        ```python
        self._keywords.remove('ELIF')
        ```
        """
        # reset the lexer's state
        self._comment_level = 0
        self._comment_start = None
        self._string_start = None
        tokens = super().parse(text)
        yield from _lex.add_line_column(
            text, tokens)
        self._check_lexing_state(text)

    def _check_lexing_state(
            self,
            text:
                str
            ) -> None:
        """Raise error if not at initial state.

        Checks for unclosed comments or strings.
        """
        if self.lexing_state == _INITIAL_LEXER_STATE:
            if self._comment_level != 0:
                raise AssertionError(
                    self._comment_level)
            return
        elif self.lexing_state == _COMMENT_LEXER_STATE:
            prefix = text[:self._comment_start]
            line = prefix.count('\n')
            raise ValueError(
                'Unclosed multi-line comment, '
                f'starting at line: {line}')
        elif (self.lexing_state ==
                _MULTILINE_STRING_LEXER_STATE):
            prefix = text[:self._string_start]
            line = prefix.count('\n')
            raise ValueError(
                'Unclosed multi-line string literal, '
                f'starting at position: {line}')
        elif (self.lexing_state ==
                _STRING_LEXER_STATE):
            prefix = text[:self._string_start]
            line = prefix.count('\n')
            raise ValueError(
                'Unclosed string literal, '
                'starting at position: '
                f'{self._string_start}')
        else:
            raise AssertionError(
                'Unknown lexing state after lexing: '
                f'{self.lexing_state = }')

    # integer literal methods need to be
    # defined before method `t_BSLASH_TOKEN`
    def t_BINARY_INTEGER(
            self,
            token):
        r'''
        (
              \\b
            | \\B
        )
        [0-1]+
        '''
        return token

    def t_HEXADECIMAL_INTEGER(
            self,
            token):
        r'''
        (
              \\h
            | \\H
        )
        (
              [0-9]
            | [A-F]
            | [a-f]
        )+
        '''
        return token

    def t_OCTAL_INTEGER(
            self,
            token):
        r'''
        (
              \\o
            | \\O
        )
        [0-7]+
        '''
        return token

    def t_UNILINE_COMMENT(
            self,
            token):
        r' \\ \* [^\n]* \n '
        return token

    # This matches if the previous method does not
    # and `\*` occurs in the text.
    # If there is space between `\` and `*`,
    # then this will not match, and
    # lexing will be as `BSLASH` `ASTERISK`.
    def t_UNCLOSED_UNILINE_COMMENT(
            self,
            token):
        r' \\ \* [^\n]* '
        start = token.start
        prefix = self.input_text[:start]
        line = prefix.count('\n')
        raise ValueError(
            'Unclosed single-line comment, '
            f'starting on line: {line}\n'
            f'and containing:\n{token.value}')

    def t_COMMENT(
            self,
            token):
        r' \( \* '
        self._comment_level = 1
        self.lexing_state = _COMMENT_LEXER_STATE
        self._comment_start = token.start

    def t_multilinecomment_left_paren(
            self,
            token):
        r' \( \* '
        self._comment_level += 1

    def t_multilinecomment_right_paren(
            self,
            token):
        r' \* \) '
        self._comment_level -= 1
        if self._comment_level < 0:
            raise AssertionError(
                self._comment_level)
        if self._comment_level > 0:
            return
        self.lexing_state = _INITIAL_LEXER_STATE
        # make token
        start = self._comment_start
        end = token.start + len(token.value)
        value = self.input_text[start:end]
        return _lex.Token(
            symbol='MULTILINE_COMMENT',
            value=value,
            start=start)

    def t_multilinecomment_newline(
            self,
            token):
        r' \n '
        # self._line_number += 1

    def t_multilinecomment_other(
            self,
            token):
        r' [^\n(\*]+ '
        return None

    def t_multilinecomment_lparen(
            self,
            token):
        r' \( '
        return None

    def t_multilinecomment_asterisk(
            self,
            token):
        r' \* '
        return None

    def t_MULTILINE_STRING_LITERAL(
            self,
            token):
        r' """ '
        self._string_start = token.start
        self.lexing_state = _MULTILINE_STRING_LEXER_STATE

    def t_multilinestring_escaped_quotes(
            self,
            token):
        r"""
          \\ t
        | \\ n
        | \\ f
        | \\ r
        | \\ \\
        """

    def t_multilinestring_newline(
            self,
            token):
        r' \n '

    def t_multilinestring_other_characters(
            self,
            token):
        r' [^"\\]+ '

    def t_multilinestring_closing(
            self,
            token):
        r' """ '
        return self._collect_string(
            token, 'MULTILINE_STRING_LITERAL')

    def t_multilinestring_quotes(
            self,
            token):
        r"""
          ""
        | "
        """

    def t_STRING_LITERAL(
            self,
            token):
        r' " '
        self._string_start = token.start
        self.lexing_state = _STRING_LEXER_STATE

    def t_string_escaped_quotes(
            self,
            token):
        r"""
          \\ "
        | \\ t
        | \\ n
        | \\ f
        | \\ r
        | \\ \\
        """

    def t_string_newline(
            self,
            token):
        r' \n '
        raise ValueError(
            f'Newline within string {t}.')

    def t_string_other_characters(
            self,
            token):
        r' [^"\\]+ '

    def t_string_closing(
            self,
            token):
        r' " '
        return self._collect_string(
            token, 'STRING_LITERAL')

    def _collect_string(
            self,
            token,
            token_type):
        self.lexing_state = _INITIAL_LEXER_STATE
        # form token
        start = self._string_start
        end = token.start + len(token.value)
        value = self.input_text[start:end]
        return _lex.Token(
            symbol=token_type,
            value=value,
            start=start)

    def t_SF_WF(
            self,
            token):
        r"""
          SF_
        | WF_
        """
        token.symbol = token.value
        return token

    def t_NAME(
            self,
            token):
        r"""
        [a-zA-Z_0-9]*
        [a-zA-Z]
        [a-zA-Z_0-9]*
        """
        if token.value in self._keywords:
            token.symbol = token.value
        return token

    def t_BSLASH_TOKEN(
            self,
            token):
        r""" \\ (
            wr | uplus | union | times | supseteq |
            supset | succeq | succ | subseteq |
            subset | star | sqsupseteq | sqsupset |
            sqsubseteq | sqsubset | sqcup | sqcap |
            simeq | sim | setminus | propto |
            preceq | prec | otimes | oslash |
            oplus | ominus | odot | o | notin |
            neg | mod | lor | lnot | ll | leq |
            leadsto | land | intersect | in |
            gg | geq | equiv | doteq | div | cup |
            cong | circ | cdot | cap | bullet |
            bigcirc | asymp | approx | X | EE | E |
            AA | A
            )
        """
        # docstring checked by method
        # `_check_bslash_token_regex()`
        if token.value not in self._lextok:
            prefix = self.input_text[:token.start]
            line = prefix.count('\n')
            raise ValueError(
                f'`{token.value}` is not '
                f'a known lexeme (line {line}). '
                'Known lexemes of '
                'this form are in: '
                f'{self._lextok}')
        symbol = self._lextok[token.value]
        token.symbol = symbol
        return token

    def _check_bslash_token_regex(
            self):
        """Assert docstring of `t_BSLASH_TOKEN`

        matches the lexemes in `_BSLASH_SUFFIXES`.
        """
        suffixes = ' | '.join(sorted(
            _BSLASH_SUFFIXES,
            reverse=True))
        pattern = rf' \\ ({suffixes}) '
        method = self.t_BSLASH_TOKEN
        def rm_blanks(s):
            return re.sub(r'\s*', '', s)
        regex = rm_blanks(method.__doc__)
        regex_ = rm_blanks(pattern)
        if regex == regex_:
            return
        raise AssertionError(
            'Unexpected regex in docstring:\n'
            f'{method.__doc__}\n'
            f'Expected:\n{pattern}')

    def t_FLOAT(
            self,
            token):
        r"""
        [0-9]+
        \.
        [0-9]+
        """
        return token

    def t_DECIMAL_INTEGER(
            self,
            token):
        ' [0-9]+ '
        return token

    t_omit = r' \x20* '

    def t_NEWLINE(
            self,
            token):
        r' \n+ '
        # self._line_number += token.value.count('\n')

    def t_tab(
            self,
            token):
        r' \t '
        raise ValueError(
            r'TAB characters (`\t`) '
            'are unsupported.')


def _is_bslash_operator(
        lexeme:
            str
        ) -> bool:
    r"""True if `lexeme` matches `\[a-zA-Z]`."""
    return (
        lexeme.startswith('\\') and
        lexeme[1:].isalpha())


def _main():
    # read file
    args = _parse_args()
    filename = args.filename
    with open(filename,
                mode='r',
                encoding='utf-8') as fd:
        file_text = fd.read()
    # lex
    lexer = Lexer()
    t1 = time.perf_counter()
    tokens = lexer.parse(file_text)
    tokens = list(tokens)
    t2 = time.perf_counter()
    dt = t2 - t1
    for token in tokens:
        print(token)
    print(
        f'Success lexing file: {filename} '
        f'in {dt:2f} seconds')


def _parse_args(
        ) -> _arg.Namespace:
    """Return arguments."""
    parser = _arg.ArgumentParser()
    parser.add_argument(
        'filename',
        help='TLA+ file name to lex')
    return parser.parse_args()


if __name__ == '__main__':
    _main()
