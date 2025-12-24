"""Generation and coalescing of tokens.

This is a layer between lexer and parser.
"""
import collections.abc as _abc
import functools as _ft
import re

import tla._langdef as _opdef
import tla._lex as _lex
import tla._utils as _utils


_PREFIXAL = _opdef.PREFIXAL
_PREFIXAL_OR_DASH = _PREFIXAL | {'-'}
_INFIXAL = _opdef.INFIXAL - _opdef.VERTICAL_LEXEMES
_INFIXAL_OR_BOTH = _INFIXAL | {'-'}
_POSTFIXAL = _opdef.POSTFIXAL
# Tokens that are step numbers.
STEP_NUMBER_TOKENS = {
    'STEP_NUMBER',
    'STEP_NUMBER_PLUS',
    'STEP_NUMBER_ASTERISK',
    }
_utils.assert_len(
    STEP_NUMBER_TOKENS, 3)
# A step number that follows any
# of these tokens is the start
# of a step. Otherwise, step numbers
# are identifiers (converted to
# token `NAME`).
_TOKENS_BEFORE_STEP_START = {
    # operators: POSTFIX
    'BOOLEAN',
    'COLON',
    'DOUBLE_LANGLE',
        # `COLON` and `DOUBLE_LANGLE`
        # can appear at the end of
        # a subexpression reference
    'FALSE',
    'OBVIOUS',
    'OMITTED',
    'PROOF',
    'QED',
    'STRING',
    'TRUE',
    'BINARY_INTEGER',
    'DECIMAL_INTEGER',
    'FLOAT',
    'HEXADECIMAL_INTEGER',
    'MULTILINE_STRING_LITERAL',
    'NAME',
    'OCTAL_INTEGER',
    # 'STEP_NUMBER',
    # 'STEP_NUMBER_ASTERISK',
    # 'STEP_NUMBER_PLUS',
    'STRING_LITERAL',
    'RPAREN',
    'RBRACE',
    'RBRACKET',
    'DOUBLE_RANGLE',
    # coalesced tokens created by
    # `join_as_one_token()`
    # which are part of
    # subexpression references
    'EXCLAMATION_AT',
    'EXCLAMATION_COLON',
    'EXCLAMATION_DOUBLE_LANGLE',
    'EXCLAMATION_DOUBLE_RANGLE',
    'EXCLAMATION_NAME',
    }
_utils.assert_len(
    _TOKENS_BEFORE_STEP_START, 27)
MODULE_SCOPE_TOKENS = STEP_NUMBER_TOKENS | {
    'DEF_SIG',
    'EQ_LINE',
    'DASH_LINE',
    'VARIABLE',
    'VARIABLES',
    'CONSTANT',
    'CONSTANTS',
    'RECURSIVE',
    'ASSUMPTION',
    'ASSUME',
    'AXIOM',
    'THEOREM',
    'PROPOSITION',
    'PROOF',
    'PROVE',
    'LEMMA',
    'COROLLARY',
    'BY',
    'DEF',
    'DEFS',
    'OBVIOUS',
    'OMITTED',
    'USE',
    'HIDE',
    'INSTANCE',
        # `INSTANCE` occurs either:
        # - in module scope
        # - after `==`
        # - after `STEP_NUMBER`
    }
_utils.assert_len(
    MODULE_SCOPE_TOKENS,
    25 + len(STEP_NUMBER_TOKENS))
# Tokens that close a `DEFINE` section.
_DEFINE_CLOSING_TOKENS = (
    MODULE_SCOPE_TOKENS - {
        'DEF_SIG', 'INSTANCE'})
_utils.assert_len(
    _DEFINE_CLOSING_TOKENS,
    -2 + len(MODULE_SCOPE_TOKENS))
_BEFORE_POSTFIXAL = {
    'ASSUMPTION',
    'ASSUME',
    'AXIOM',
    'THEOREM',
    'PROPOSITION',
    'PROVE',
    'LEMMA',
    'COROLLARY',
        # for example `ASSUME +(1, 2) = 3`
    'DEF',
    'DEFS',
    'COMMA',
    'LPAREN',
    'WITH',
    'LARROW',
    'EXCLAMATION',
    'MAPSTO',
    }
_utils.assert_len(
    _BEFORE_POSTFIXAL, 16)
_AFTER_PREFIXAL = (MODULE_SCOPE_TOKENS | {
    'COMMA',
    'RPAREN',
    'LARROW',
    'EXCLAMATION',
    })
_utils.assert_len(
    _AFTER_PREFIXAL,
    4 + len(MODULE_SCOPE_TOKENS))
_AFTER_PREFIXAL_EXCEPT_STEPS = (
    _AFTER_PREFIXAL -
    STEP_NUMBER_TOKENS)
    # All prefix operators except `-` are builtin,
    # thus they do not appear in `DEF`.
    # Only `-.` can appear in `DEF`, and
    # it cannot be applied to an expression.
    # Therefore, `-.` before step identifier
    # is only possible at end of `DEF` list.
    #
    # Infix conjunction and disjunction cannot
    # appear in `DEF`, therefore when followed
    # by step identifier, they are an operator.
    #
    # For all other infix operators,
    # when they appear in `DEF`, they are
    # preceded by either `DEF`, `DEFS`, or `COMMA`.
    # This case is handled using `_BEFORE_POSTFIXAL`.
    #
    # So no need to check whether step number
    # follows infix in other cases.
    # In those cases, the infix is applied to
    # the step identifier, which becomes `NAME`.
_KEYWORDS_FOR_DOT = {'SF_', 'WF_', *_opdef.KEYWORDS}
Token = _utils.Token


def preparse(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    """Prepare tokens for parser."""
    tokens = insert_def_starts_tokens(tokens)
    tokens = swap_local_keyword(tokens)
    tokens = switch_keywords_after_dot(tokens)
        # `L.WITH &` needs switching `WITH` to
        # `NAME` token before checking the
        # fixal operator `&`
    tokens = switch_fixal_operators(tokens)
    tokens = switch_step_identifiers(tokens)
        # `BY DEF + <1>2` needs switching fixal
        # operators to `NAME`, before switching
        # step identifiers
    tokens = end_define_proof_steps(tokens)
    return tokens


def insert_def_starts_tokens(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    """Delimit start of definitions."""
    return _utils.pipe(
        tokens,
        _utils.reverse,
        _insert_def_sig_tokens_nonfix,
        _insert_def_sig_tokens_fixal,
        _utils.reverse)


def _insert_def_sig_tokens_fixal(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    r"""Insert `DEF_SIG` tokens.

    - `name infixal name ==`
    - `name ==`
    - `-. name ==`
    - `name postfixal ==`
    """
    last_tokens: list = list()
    for token in tokens:
        # prefix-operator definition
        is_prefix_def = (
            len(last_tokens) >= 2 and
            last_tokens[-2].symbol == 'DOUBLE_EQ' and
            last_tokens[-1].symbol == 'NAME' and
            token.value in _PREFIXAL)
                # Not `-` (`DASH`) here,
                # because `-.` used in this case.
        if is_prefix_def:
            yield token
            yield _make_def_sig(token)
        # infix-operator definition
        is_infix_def = (
            len(last_tokens) >= 3 and
            last_tokens[-3].symbol == 'DOUBLE_EQ' and
            last_tokens[-2].symbol == 'NAME' and
            last_tokens[-1].value in _INFIXAL_OR_BOTH and
            token.symbol == 'NAME')
        if is_infix_def:
            yield token
            yield _make_def_sig(token)
        # postfix-operator definition
        is_postfix_def = (
            len(last_tokens) >= 2 and
            last_tokens[-2].symbol == 'DOUBLE_EQ' and
            last_tokens[-1].value in _POSTFIXAL and
            token.symbol == 'NAME')
        if is_postfix_def:
            yield token
            yield _make_def_sig(token)
        # nullary-operator definition
        is_nullary_def = (
            len(last_tokens) >= 2 and
            last_tokens[-2].symbol == 'DOUBLE_EQ' and
            last_tokens[-1].symbol == 'NAME' and
            not is_prefix_def and
            token.value not in _INFIXAL_OR_BOTH)
        if is_nullary_def:
            yield _make_def_sig(last_tokens[-1])
            yield token
        is_def = (
            is_prefix_def or
            is_infix_def or
            is_postfix_def or
            is_nullary_def)
        if not is_def:
            yield token
        last_tokens.append(token)


def _insert_def_sig_tokens_nonfix(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    r"""Insert `DEF_SIG` tokens.

    Cases:
    - `name(...) ==`
    - `name[...] ==` (nesting of definition
        signatures can occur here, e.g.,
        `f[x \in LET -. r == r IN {-1}] == x`)

    `LOCAL` can precede any of these cases.

    @param tokens:
        iterable of tokens reversed from
        how they appear in the TLA+ source,
        i.e., in the lexer's output
    @return:
        iterable of tokens,
        in the same direction as the input
        (i.e., reversed from their order
         in the TLA+ source)
    """
    stack = list()
    last_token = _utils.make_lex_token(None)
    for token in tokens:
        ts = token.symbol
        if (ts in ('RPAREN', 'RBRACKET') and
                last_token.symbol == 'DOUBLE_EQ'):
            stack.append(2)
            yield token
        elif not stack:
            yield token
        elif (ts in ('LPAREN', 'LBRACKET') and
                stack[-1] > 0):
            stack[-1] -= 1
            yield token
        elif (ts in ('RPAREN', 'RBRACKET') and
                stack[-1] > 0):
            stack[-1] += 1
            yield token
        elif ts == 'NAME' and stack[-1] == 1:
            stack.pop()
            yield token
            yield _make_def_sig(token)
        elif stack[-1] != 0:
            yield token
        else:
            yield token
        last_token = token
    if not stack:
        return
    raise ValueError(stack)


def _make_def_sig(
        token:
            Token
        ) -> Token:
    return _utils.make_lex_token(
        'DEF_SIG',
        line=token.line,
        column=token.column,
        start=token.start)


def swap_local_keyword(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    """Swap `LOCAL DEF_SIG` to `DEF_SIG LOCAL`."""
    previous = None
    for token in tokens:
        ts = token.symbol
        if ts == 'LOCAL':
            previous = token
            continue
        swap = (
            previous is not None and
            token.symbol == 'DEF_SIG')
        if swap:
            yield token
            yield previous
        elif previous is not None:
            yield previous
            yield token
        else:
            yield token
        if previous is not None:
            previous = None
    if previous is not None:
        yield previous


def end_define_proof_steps(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    """Add `END_DEFINE` at end of `DEFINE`."""
    define_start_tokens = {'DEF_SIG', 'DEFINE'}
    inside_define_step = False
    previous = _utils.make_lex_token(None)
    for token in tokens:
        ts = token.symbol
        pt = previous.symbol
        module_scope_instance = (
            ts == 'INSTANCE' and
            pt != 'DOUBLE_EQ')
        is_closing = (
            ts in _DEFINE_CLOSING_TOKENS or
            module_scope_instance)
        add_token = (
            inside_define_step and
            is_closing)
        if add_token:
            inside_define_step = False
            # column information is not needed,
            # because `END_DEFINE` ends also
            # vertical items, as a
            # non-blankspace token
            yield _utils.make_lex_token(
                'END_DEFINE',
                line=token.line,
                column=token.column)
        inside_define_step |= (
            pt in STEP_NUMBER_TOKENS and
            ts in define_start_tokens)
        previous = token
        yield token


def switch_step_identifiers(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    """Convert step identifiers to `NAME`.

    For occurrences of step identifiers
    within leaf proofs (`BY` proofs).
    """
    last_token = _utils.make_lex_token(None)
    for token in tokens:
        switch = (
            token.symbol in
                STEP_NUMBER_TOKENS and
            last_token.symbol not in
                _TOKENS_BEFORE_STEP_START and
            last_token.value not in
                _POSTFIXAL)
        if switch:
            token.symbol = 'NAME'
        last_token = token
        yield token


def switch_fixal_operators(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    """Convert fixal to `NAME`.

    For operators as arguments, for example:
    `Op(+, 1, 2)`

    The `+` is converted from an operator
    to `NAME`.

    Also for subexpression references:
    `Op!+(1, 2)`
    """
    forward_scan = _ft.partial(
        _switch_scan,
        current=_INFIXAL | _POSTFIXAL,
        previous=_BEFORE_POSTFIXAL)
        # Not DASH `-` here, because `f(-5)`
        # contains an expression between
        # the parentheses. Suffices for DASH
        # to be checked as prefixal (below).
    binary_dash_scan = _ft.partial(
        _switch_scan,
        current={'-', '-.'},
        previous={'WITH', 'EXCLAMATION'})
        # handles `M!-(1, 2)`
    reverse_dash_scan = _ft.partial(
        _switch_scan,
        current={'-.'},
        previous=_AFTER_PREFIXAL)
    reverse_scan = _ft.partial(
        _switch_scan,
        current=_PREFIXAL_OR_DASH | _INFIXAL |
            _opdef.VERTICAL_LEXEMES,
        previous=_AFTER_PREFIXAL_EXCEPT_STEPS)
    return _utils.pipe(
        tokens,
        forward_scan,
        binary_dash_scan,
        _utils.reverse,
        reverse_dash_scan,
        reverse_scan,
        _switch_fixal_exclamation,
        _utils.reverse)


def switch_keywords_after_dot(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    """Map `DOT KEYWORD` to `DOT NAME`.

    For example, `f.LET` means `f["LET"]`
    when this transformation is applied.
    """
    return _switch_scan(
        tokens,
        current=_KEYWORDS_FOR_DOT,
        previous={'DOT'})


def _switch_scan(
        tokens:
            _abc.Iterable[Token],
        current:
            set[str],
        previous:
            set[str]
        ) -> _abc.Iterable[Token]:
    previous_token = _utils.make_lex_token(None)
    for token in tokens:
        switch = (
            token.value in current and
            previous_token.symbol in previous)
        if switch:
            token.symbol = 'NAME'
        previous_token = token
        yield token


def _switch_fixal_exclamation(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    """Map fixal before `(...)!`, to `NAME`.

    This can occur in subexpression references.
    For example `+(1, 2)!b`
    """
    stack: list[int] = list()
    last_token = None
    for token in tokens:
        ts = token.symbol
        if (ts == 'RPAREN' and
                last_token is not None and
                last_token.symbol.startswith(
                    'EXCLAMATION')):
            stack.append(1)
            yield token
        elif not stack:
            yield token
        elif ts == 'RPAREN':
            stack[-1] += 1
            yield token
        elif ts == 'LPAREN':
            stack[-1] -= 1
            yield token
        elif stack[-1] > 0:
            yield token
        elif ((ts.startswith('OP_') or
                ts == 'DASH') and
                # NOTE: The other operators in
                # `_grammar.EXCEPT_TOKEN_TYPES`
                # are builtin
                stack[-1] == 0):
            stack.pop()
            yield _utils.copy_lex_token(
                token,
                symbol='NAME')
        elif stack[-1] == 0:
            # A(...)!
            # already `NAME`, not fixal
            stack.pop()
            yield token
        else:
            yield token
        last_token = token
    if not stack:
        return
    raise ValueError(stack)


def filter_comments(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterator[Token]:
    """Omit tokens that are comments."""
    comments = _lex.COMMENT_TOKENS
    for token in tokens:
        if token.symbol in comments:
            continue
        yield token


def filter_preamble(
        text:
            str
        ) -> str:
    """Omit text before start of module.

    Keeps newlines, for line counting.
    Convert to spaces the prefix of the
    MODULE line, for column counting.

    For example, the following module has
    a preamble:

    ```tla
    This is text in the preamble.
    ---- MODULE main ----
    A == 1
    ====
    ```
    """
    start = find_module_start(text)
    # keep preamble newlines,
    # for counting lines later
    # and also columns of MODULE line
    preamble = text[:start]
    n_newlines = preamble.count('\n')
    *_, prefix = preamble.rsplit('\n', 1)
    newlines = '\n' * n_newlines
    spaces = '\x20' * len(prefix)
    new_preamble = f'{newlines}{spaces}'
    rest = text[start:]
    new_text = f'{new_preamble}{rest}'
    return new_text


def find_module_start(
        text:
            str
        ) -> int:
    """Returns index where main module starts."""
    # find start of outermost module
    pattern = r' \-\-\-\-(\-)* \s* MODULE '
    matches = re.finditer(
        pattern, text,
        flags=re.VERBOSE)
    module_start = next(matches, None)
    if module_start is None:
        raise ValueError(
            'No module start found.')
    return module_start.start()


def filter_postamble(
        tokens:
            _abc.Iterable[Token]
        ) -> _abc.Iterable[Token]:
    """Yield tokens up to end of main module.

    For example, the following module has
    a postamble:

    ```tla
    ---- MODULE main ----
    A == 1
    ====
    This is text in the postamble.
    ```
    """
    tokens = iter(tokens)
    # first token
    token = next(tokens, None)
    if token is None:
        raise ValueError(
            'No module start found.')
    if token.symbol != 'DASH_LINE':
        raise ValueError(
            f'Unexpected first token: {token}')
    last_symbol = token.symbol
    yield token
    # other tokens
    found_modules = False
    module_count = 0
    for token in tokens:
        module_starts = (
            last_symbol == 'DASH_LINE' and
            token.symbol == 'MODULE')
        last_symbol = token.symbol
        if module_starts:
            module_count += 1
            found_modules = True
        module_ends = (
            token.symbol == 'EQ_LINE')
        if module_ends and module_count > 1:
            module_count -= 1
        elif module_ends and module_count == 1:
            yield token
            break
        if module_count > 0:
            yield token
    if not found_modules:
        raise ValueError(
            'No module start found.')
