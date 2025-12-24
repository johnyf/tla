"""Operator fixity and associativity.

These definitions can then be shared between LR parsers.
"""
import itertools as _itr
import typing as _ty

import tla._utils as _utils


PrecRange = tuple[int, int]


KEYWORDS = {
    'ACTION',
    'ASSUME',
    'ASSUMPTION',
    'AXIOM',
    'BOOLEAN',
    'BY',
    'CASE',
    'CHOOSE',
    'CONSTANT',
    'CONSTANTS',
    'COROLLARY',
    'DEF',
    'DEFINE',
    'DEFS',
    'DOMAIN',
    'ELSE',
    'ELIF',
        # added to TLA
    'ENABLED',
    'EXCEPT',
    'EXTENDS',
    'FALSE',
    'HAVE',
    'HIDE',
    'IF',
    'IN',
    'INSTANCE',
    'LAMBDA',
    'LEMMA',
    'LET',
    'LOCAL',
    'MODULE',
    'NEW',
    'OBVIOUS',
    'OMITTED',
    'ONLY',
    'OTHER',
    'PICK',
    'PROOF',
    'PROPOSITION',
    'PROVE',
    'QED',
    'RECURSIVE',
    # 'SF_',
        # regex used
    'STATE',
    'STRING',
    'SUBSET',
    'SUFFICES',
    'TAKE',
    'TEMPORAL',
    'THEN',
    'THEOREM',
    'TRUE',
    'UNCHANGED',
    'UNION',
    'USE',
    'VARIABLE',
    'VARIABLES',
    # 'WF_',
        # regex used
    'WITH',
    'WITNESS',
    }
_utils.assert_len(KEYWORDS, 58)


def _bslash(
        suffix:
            str
        ) -> str:
    r"""Prefix with `\`."""
    return f'\\{suffix}'


_FIXITIES: _ty.Final[set[str]] = {
    'prefix', 'before',
    'infix', 'left', 'between', 'right',
    'postfix', 'after',
    }
_utils.assert_len(_FIXITIES, 8)
# Table 6 on page 271 of
# the book "Specifying Systems"
LEXEME_PRECEDENCE: _ty.Final[
    dict[str, tuple[int, int]]] = {
    # symbol: (start, end)
    # where:
    # - `start..end`: is the set of precedence
    #   levels of the operator
    #
    #   (nonfix operators are user-defined
    #    and represented by alphanumeric
    #    identifiers, so not in this `dict`)
    #
    # logic
    '=>':
        (1, 1),
    '<=>':
        (2, 2),
    '/\\':
        (3, 3),
    r'\/':
        (3, 3),
    '~':
        (4, 4),
    '=':
        (5, 5),
    '#':
        (5, 5),
    '/=':
        (5, 5),
    # set theory
    'SUBSET':
        (8, 8),
    'UNION':
        (8, 8),
    'DOMAIN':
        (9, 9),
    r'\subseteq':
        (5, 5),
    r'\in':
        (5, 5),
    r'\notin':
        (5, 5),
    '\\':
        (8, 8),
    r'\cap':
        (8, 8),
    r'\cup':
        (8, 8),
    r'\X':
        (10, 13),
    # action operators
    "'":
        (15, 15),
    'UNCHANGED':
        (4, 15),
    r'\cdot':
        (5, 14),
    'ENABLED':
        (4, 15),
    # modal operators
    '[]':
        (4, 15),
    '<>':
        (4, 15),
    '~>':
        (2, 2),
    '-+->':
        (2, 2),
    # user-defined operators
    '^':
        (14, 14),
    '/':
        (13, 13),
    '*':
        (13, 13),
    '-.':
        (12, 12),
        # within operator signatures
    # '-':
    #    (11, 11),
        # `op_11_dash_left` in
        # `positioning`, within
        #  the class `Grammar`
    # '-':
    #    (12, 12),
        # `op_12_dash_before` in
        # `positioning`, within
        # the class `Grammar`
    '+':
        (10, 10),
    '^+':
        (15, 15),
    '^*':
        (15, 15),
    '^#':
        (15, 15),
    '<':
        (5, 5),
    '=<':
        (5, 5),
    '<=':
        (5, 5),
    '>':
        (5, 5),
    '>=':
        (5, 5),
    '..':
        (9, 9),
    '...':
        (9, 9),
    '|':
        (10, 11),
    '||':
        (10, 11),
    '&':
        (13, 13),
    '&&':
        (13, 13),
    '$':
        (9, 13),
    '$$':
        (9, 13),
    '??':
        (9, 13),
    '%':
        (10, 11),
    '%%':
        (10, 11),
    '##':
        (9, 13),
    '++':
        (10, 10),
    '--':
        (11, 11),
    '**':
        (13, 13),
    '//':
        (13, 13),
    '^^':
        (14, 14),
    '@@':
        (6, 6),
    '!!':
        (9, 13),
    '|-':
        (5, 5),
    '|=':
        (5, 5),
    '-|':
        (5, 5),
    '=|':
        (5, 5),
    '<:':
        (7, 7),
    ':>':
        (7, 7),
    ':=':
        (5, 5),
    '::=':
        (5, 5),
    '(+)':
        (10, 10),
    '(-)':
        (11, 11),
    '(.)':
        (13, 13),
    '(/)':
        (13, 13),
    r'(\X)':
        (13, 13),
    } | _utils.map_keys(_bslash, {
        'uplus':
            (9, 13),
        'sqcap':
            (9, 13),
        'sqcup':
            (9, 13),
        'div':
            (13, 13),
        'wr':
            (9, 14),
        'star':
            (13, 13),
        'circ':
            (13, 13),
        # 'o':  # synonym of `\circ`
        #     (13, 13),
        'bigcirc':
            (13, 13),
        'bullet':
            (13, 13),
        'prec':
            (5, 5),
        'succ':
            (5, 5),
        'preceq':
            (5, 5),
        'succeq':
            (5, 5),
        'sim':
            (5, 5),
        'simeq':
            (5, 5),
        'll':
            (5, 5),
        'gg':
            (5, 5),
        'asymp':
            (5, 5),
        'subset':
            (5, 5),
        'supset':
            (5, 5),
        'supseteq':
            (5, 5),
        'approx':
            (5, 5),
        'cong':
            (5, 5),
        'sqsubset':
            (5, 5),
        'sqsubseteq':
            (5, 5),
        'sqsupset':
            (5, 5),
        'sqsupseteq':
            (5, 5),
        'doteq':
            (5, 5),
        'propto':
            (5, 5),
        })
_utils.assert_len(
    LEXEME_PRECEDENCE, 100)
# fixity and associativity:
# - prefix (not directly nestable)
# - before (nestable prefix)
# - infix (not directly nestable)
# - left (nestable, left-associative)
# - right (nestable, right-associative)
# - between (listy, parsed as separator)
# - postfix (not directly nestable)
# - after (nestable postfix)
TLA_OPERATOR_FIXITY: _ty.Final = dict(
    prefix={
        'UNCHANGED',
        '-.',  # in operator signatures
        },
    before={
        '~', '[]', '<>',
        # the dash `-` appears
        # within the class `Grammar`
        'DOMAIN',
        'ENABLED',
        'SUBSET',
        'UNION',
        },
    infix={
        '=>', '<=>', '~>', '-+->',
        '=', '#', '/=',
        '^', '/',
        '<', '<=', '=<', '>=', '>',
        '..', '...', '%',
        '\\', '//', '^^', '!!',
        '|-', '-|',
        '|=', '=|',
        '<:', ':>',
        ':=', '::=',
        '(/)',
        }.union(map(_bslash, [
            'approx',
            'asymp',
            'cong',
            'div',
            'doteq',
            'gg',
            'll',
            'notin',
            'prec',
            'preceq',
            'propto',
            'sim',
            'simeq',
            'sqsubset',
            'sqsubseteq',
            'sqsupset',
            'sqsupseteq',
            'subset',
            'subseteq',
            'succ',
            'succeq',
            'supset',
            'supseteq',
            'wr',
            ])),
    left={
        '/\\', r'\/',
        r'\cap', r'\cup',
        '*', '+',
        # the dash `-` appears
        # within the class `Grammar`
        '|', '||',
        '&', '&&',
        '$', '$$',
        '??',
        '%%', '##',
        '++', '--', '**',
        '@@',
        r'\cdot',
        '(+)', '(-)', '(.)', r'(\X)',
        }.union(map(_bslash, [
            'bigcirc',
            'bullet',
            'circ',
            # 'o',  # synonym of `\circ`
            'sqcap',
            'sqcup',
            'star',
            'uplus',
            ])),
        # the dot `.` appears
        # directly in the grammar
    between=set(map(_bslash, [
        'in',
            # The operator `\in`
            # cannot be nested inside
            # expressions. It is here
            # to represent declarations.
        'X',
            # The operator `\X`
            # is described in
            # Section 15.2.1 on
            # page 284 of the book
            # "Specifying Systems".
        ])),
    postfix={
        "'",
        },
    after={
        '^+', '^*', '^#',
        },
    )
_utils.assert_len(
    TLA_OPERATOR_FIXITY, 7)
# Lexemes of vertical operators.
VERTICAL_LEXEMES: _ty.Final = {
    '/\\', r'\/',
    # '&', '&&',
    # '*', '**',
    # '%', '%%',
    # '|', '||',
    # '+', '++',
    # '@@',
    # '^^',
    # '--',
    # '!!',
    # '##',
    # '??'
    }
_utils.assert_len(
    VERTICAL_LEXEMES, 2)
SYNONYMS = {
    '<=>':
        r'\equiv',
    '/\\':
        r'\land',
    r'\/':
        r'\lor',
    # '#':
    #     '/=',
    '\\':
        r'\setminus',
    r'\cap':
        r'\intersect',
    r'\cup':
        r'\union',
    r'\X':
        r'\times',
    '~>':
        r'\leadsto',
    '>=':
        r'\geq',
    '%':
        r'\mod',
    '(+)':
        r'\oplus',
    '(-)':
        r'\ominus',
    '(.)':
        r'\odot',
    '(/)':
        r'\oslash',
    r'(\X)':
        r'\otimes',
    r'\circ':
        r'\o',
    '~':
        (r'\neg', r'\lnot'),
    '=<':
        (r'\leq',),  # '<='
    }
_utils.assert_len(SYNONYMS, 18)


def make_op_to_fixity(
        ) -> dict[str, str]:
    """Map operator lexemes to fixity."""
    op_to_fixity = dict()
    items = TLA_OPERATOR_FIXITY.items()
    for fixity, operators in items:
        for op in operators:
            op_to_fixity[op] = fixity
    op_synonyms = make_synonymous_lexemes()
    for op, synonyms in op_synonyms.items():
        fixity = op_to_fixity[op]
        for other in synonyms:
            if other in op_to_fixity:
                raise AssertionError(
                    op, other, op_to_fixity)
            op_to_fixity[other] = fixity
    return op_to_fixity


def make_synonymous_lexemes(
        ) -> dict[
            str,
            tuple[str]]:
    """Return `dict` of synonyms."""
    def mapper(x):
        if isinstance(x, str):
            return (x,)
        return x
    return _utils.map_values(
        mapper, SYNONYMS)


def _collect_fixal(
        fixities:
            set[str]
        ) -> set[str]:
    """Return operator lexemes."""
    return {
        lexeme
        for lexeme, fixity in
            OP_TO_FIXITY.items()
        if fixity in fixities}


OP_TO_FIXITY: dict[str, str] = make_op_to_fixity()
INFIXAL: _ty.Final[set[str]] = _collect_fixal(
    {'infix', 'left', 'right', 'between'})
    # NOTE: does not contain DASH `-`
    # because the grammar mentions DASH directly
POSTFIXAL: _ty.Final[set[str]] = _collect_fixal(
    {'postfix', 'after'})
PREFIXAL: _ty.Final[set[str]] = _collect_fixal(
    {'prefix', 'before'})
    # NOTE: does not contain DASH `-`
    # because the grammar mentions DASH directly


def check_lexprec(
        ) -> None:
    """Assert properties of operator tables."""
    for prec in LEXEME_PRECEDENCE.values():
        _check_precedence(prec)
    # assert pairwise disjoint sets
    accum: set[str] = set()
    items = TLA_OPERATOR_FIXITY.items()
    for fixity, operators in items:
        if accum & operators:
            raise ValueError(
                fixity, operators)
        accum.update(operators)


def _check_precedence(
        prec:
            PrecRange
        ) -> None:
    """Assert precedence is correct."""
    if len(prec) != 2:
        raise ValueError(prec)
    start, end = prec
    if 1 > start:
        raise ValueError(start)
    if start > end:
        raise ValueError(start, end)
