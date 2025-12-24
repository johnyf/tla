"""Miscellanea."""
import collections.abc as _abc
from dataclasses import dataclass
import functools as _ft
import inspect
import itertools as _itr
import logging as _log
import os
import pprint as _pp
import re
import typing as _ty


import parstools as _prs


logger = _log.getLogger(__name__)
Token = _prs.Token


def make_operator_precedence_grammar(
        precedence_associativity:
            tuple[str, ...],
        tokens_of_symbols:
            dict[str, str],
        instance:
            _ty.Any
        ) -> None:
    """Add grammar equalities to `instance`.

    The new parser methods construct
    syntax-tree nodes by instantiating
    as follows:

    ```python
    instance._nodes.OperatorApplication(
        operator=...,
        arguments=...)
    ```

    @param precedence_associativity:
        names, used for:
        - lowercased as grammar symbols
        - uppercased as token names,
          unless lowercased they are
          keys of `tokens_of_symbols`

        The last item is not mapped to
        a new grammar equality.
    @param tokens_of_symbols:
        maps grammar symbols to token names
    @param tokens_of_symbols:
        with lowercase keys
        and uppercase values
    @param instance:
        parser to which to attach the
        new grammar equalities
    """
    pairs = _itr.pairwise(
        precedence_associativity)
    for operator, operand in pairs:
        operator = operator.lower()
        operand = operand.lower()
        _make_grammar_equality_for_op(
            operator, operand,
            tokens_of_symbols, instance)


def _make_grammar_equality_for_op(
        operator:
            str,
        operand:
            str,
        tokens_of_symbols:
            dict[str, str],
        instance:
            _ty.Any
        ) -> None:
    """Attach new grammar methods for operator.

    The newly created methods describe
    the grammar of `operator`, and are
    attached as bound methods to `instance`.

    @param operator:
        name of operator (lowercase)
    @param operand:
        name of operand (lowercase)

    Read the docstring of the function
    `make_operator_precedence_grammar`.
    """
    operator_token = _make_op_token(
        operator, tokens_of_symbols)
    _make_op = _pick_make_func(operator)
    functions = _make_op(
        operator, operand,
        operator_token)
    for function in functions:
        name = function.__name__
        if not _is_grammar_method_name(name):
            raise ValueError(
                name, function)
        # line numbers remain unchanged here
        _attach_as_method(function, instance)


def _pick_make_func(
        operator:
            str
        ) -> _abc.Callable:
    """Map `operator` to function."""
    *_, fixity = operator.rpartition('_')
    if fixity not in _FIXITY_TO_MK:
        raise ValueError(operator)
    return _FIXITY_TO_MK[fixity]


def _attach_as_method(
        function:
            _abc.Callable,
        instance:
            _ty.Any,
        attribute_name:
            str |
            None=None
        ) -> None:
    """Add `function` as method to `instance`.

    The new method is created by
    binding `function` to `instance`.

    @param attribute_name:
        name of the attribute of
        `instance` that will be assigned
        the new method
    """
    if attribute_name is None:
        attribute_name = function.__name__
    bound_func = function.__get__(instance)
    setattr(
        instance, attribute_name,
        bound_func)


def _make_prefix_op(
        operator_name:
            str,
        operand:
            str,
        operator_token:
            str
        ) -> list[
            _abc.Callable]:
    """Production for prefix operator.

    This operator does not nest.

    ```
    G.operator_name =
        | L.OPERATOR_TOKEN & G.operand
            (* apply *)
        | G.operand
            (* skip *)
    ```

    @param operator_name:
        (lowercase) name of
        the grammar symbol of
        this production
    @param operand:
        (lowercase) name of
        the grammar symbol that
        is the production with
        precedence higher than
        this production
    @param operator_token:
        token of operator
    @return:
        unbound functions named as
        the intended parser methods
    """
    skip_method = _make_skip_method(
        operator_name, operand)
    prefix_method = _make_fixity_method(
        operator_name, 'prefix')
    prefix_method.__doc__ = f'''
        {operator_name}:
            {operator_token}
            {operand}
        '''
    return [prefix_method, skip_method]


def _make_before_op(
        operator_name:
            str,
        operand:
            str,
        operator_token:
            str
        ) -> list[
            _abc.Callable]:
    """Production for nestable prefix operator.

    This operator can nest.

    ```
    G.operator_name =
        | L.OPERATOR_TOKEN & G.operator_name
            (* apply; maybe nested *)
        | G.operand
            (* skip or start applying *)
    ```
    """
    skip_method = _make_skip_method(
        operator_name, operand)
    prefix_method = _make_fixity_method(
        operator_name, 'prefix')
    prefix_method.__doc__ = f'''
        {operator_name}:
            {operator_token}
            {operator_name}
        '''
    return [prefix_method, skip_method]


def _make_left_assoc_op(
        operator_name:
            str,
        operand:
            str,
        operator_token:
            str
        ) -> list[
            _abc.Callable]:
    """Production for left associative operator.

    This operator can nest.

    ```
    G.operator_name =
        | G.operator_name &
            L.OPERATOR_TOKEN &
            G.operand
                (* apply; maybe nested *)
        | G.operand
            (* skip or start applying *)
    ```
    """
    skip_method = _make_skip_method(
        operator_name, operand)
    infix_method = _make_fixity_method(
        operator_name, 'infix')
    infix_method.__doc__ = f'''
        {operator_name}:
            {operator_name}
            {operator_token}
            {operand}
        '''
    return [infix_method, skip_method]


def _make_right_assoc_op(
        operator_name:
            str,
        operand:
            str,
        operator_token:
            str
        ) -> list[
            _abc.Callable]:
    """Production for right associative operator.

    This operator can nest.

    ```
    G.operator_name =
        | G.operand &
            L.OPERATOR_TOKEN &
            G.operator_name
                (* apply; maybe nested *)
        | G.operand
            (* skip or start applying *)
    ```
    """
    # NOTE: for an LR(1) parser a more
    # efficient approach is to use left recursion,
    # and an intermediary production that
    # applies `reversed()` on the accumulated `list`,
    # and then folds the list into a tree.
    skip_method = _make_skip_method(
        operator_name, operand)
    infix_method = _make_fixity_method(
        operator_name, 'infix')
    infix_method.__doc__ = f'''
        {operator_name}:
            {operand}
            {operator_token}
            {operator_name}
        '''
    return [infix_method, skip_method]


def _make_nonassoc_op(
        operator_name:
            str,
        operand:
            str,
        operator_token:
            str
        ) -> list[
            _abc.Callable]:
    """Production for nonassociative operator.

    This operator does not nest.

    ```
    G.operator_name =
        | G.operand &
            L.OPERATOR_TOKEN &
            G.operand
                (* apply *)
        | G.operand
            (* skip *)
    ```
    """
    skip_method = _make_skip_method(
        operator_name, operand)
    infix_method = _make_fixity_method(
        operator_name, 'infix')
    infix_method.__doc__ = f'''
        {operator_name}:
            {operand}
            {operator_token}
            {operand}
        '''
    return [infix_method, skip_method]


def _make_postfix_op(
        operator_name:
            str,
        operand:
            str,
        operator_token:
            str
        ) -> list[
            _abc.Callable]:
    """Production for postfix operator.

    This operator does not nest.

    ```
    G.operator_name =
        | G.operand & L.OPERATOR_TOKEN
            (* apply *)
        | G.operand
            (* skip *)
    ```
    """
    skip_method = _make_skip_method(
        operator_name, operand)
    postfix_method = _make_fixity_method(
        operator_name, 'postfix')
    postfix_method.__doc__ = f'''
        {operator_name}:
            {operand}
            {operator_token}
        '''
    return [postfix_method, skip_method]


def _make_after_op(
        operator_name:
            str,
        operand:
            str,
        operator_token:
            str
        ) -> list[
            _abc.Callable]:
    """Production for nestable postfix operator.

    This operator can nest.

    ```
    G.operator_name =
        | G.operator_name & L.OPERATOR_TOKEN
            (* apply; maybe nested *)
        | G.operand
            (* skip or start applying *)
    ```
    """
    skip_method = _make_skip_method(
        operator_name, operand)
    postfix_method = _make_fixity_method(
        operator_name, 'postfix')
    postfix_method.__doc__ = f'''
        {operator_name}:
            {operator_name}
            {operator_token}
        '''
    return [postfix_method, skip_method]


def _make_infix_items_op(
        operator_name:
            str,
        operand:
            str,
        operator_token:
            str
        ) -> list[
            _abc.Callable]:
    r"""Production for infix itemized operator.

    This operator can repeat,
    similarly lexically to nestable operators.

    ```
    /\ G.operator_name =
        | G.items
            (* apply listy operator *)
        | G.operand
            (* skip *)
    /\ G.items =
        | G.items & L.OPERATOR_TOKEN & G.operand
            (* continue applying *)
        | G.operand & L.OPERATOR_TOKEN & G.operand
            (* start applying *)
    ```
    """
    skip_method = _make_skip_method(
        operator_name, operand)
    itemize, repeat, start = (
        _make_infix_items_method(
            operator_name))
    items = f'{operator_name}_items'
    itemize.__doc__ = f'''
        {operator_name}:
            {items}
        '''
    repeat.__doc__ = f'''
        {items}:
            {items}
            {operator_token}
            {operand}
        '''
    start.__doc__ = f'''
        {items}:
            {operand}
            {operator_token}
            {operand}
        '''
    return [
        itemize, repeat, start,
        skip_method]


_FIXITY_TO_MK: _ty.Final = dict(
    prefix=_make_prefix_op,
    before=_make_before_op,
    infix=_make_nonassoc_op,
    left=_make_left_assoc_op,
    between=_make_infix_items_op,
    right=_make_right_assoc_op,
    postfix=_make_postfix_op,
    after=_make_after_op,
    )


def _make_op_token(
        operator_name:
            str,
        tokens_of_symbols:
            dict[str, str]
        ) -> str:
    """Return name of token of `operator_name`.

    ```
    ASSUME
        operator_name.islower()
    ```
    """
    return tokens_of_symbols.get(
        operator_name, operator_name).upper()


def _make_fixity_method(
        operator_name:
            str,
        fixity:
            str
        ) -> _abc.Callable:
    r"""Return function for parser equation.

    ```
    ASSUME
        /\ operator_name.islower()
        /\ fixity.islower()
    ```

    @return:
        unbound function named as
        the intended parser method
    """
    match fixity:
        case 'prefix':
            _method = _prefix_method
        case 'infix':
            _method = _infix_method
        case 'postfix':
            _method = _postfix_method
        case _:
            raise ValueError(fixity)
    def method(self, p):
        _method(self, p)
    method.__name__ = f'p_{operator_name}'
    return method


def _make_infix_items_method(
        operator_name:
            str
        ) -> list:
    """Return functions for parser equation.

    ```
    ASSUME
        operator_name.islower()
    ```

    @return:
        `list` of unbound functions,
        named as the intended parser methods
    """
    def itemize(self, p):
        # docstring dynamically assigned to wrapper
        # grammar equality of the form
        # nonleaf: nonleaf_repetition
        op_lexeme, *args = p[1]
        p[0] = self._nodes.OperatorApplication(
            operator=op_lexeme,
            arguments=args)
    def append(self, p):
        _repetition_append_method(self, p)
    def start(self, p):
        _repetition_start_method(self, p)
    itemize.__name__ = f'p_{operator_name}'
    append.__name__ = f'p_{operator_name}_append'
    start.__name__ = f'p_{operator_name}_start'
    return [itemize, append, start]


def _prefix_method(
        self, p
        ) -> None:
    # docstring dynamically assigned to wrapper
    # grammar equality of the form
    # nonleaf: OPERATOR operand
    p[0] = self._nodes.OperatorApplication(
        operator=p[1],
        arguments=[p[2]])


def _infix_method(
        self, p
        ) -> None:
    # docstring dynamically assigned to wrapper
    # grammar equality of the form
    # nonleaf: operand OPERATOR operand
    p[0] = self._nodes.OperatorApplication(
        operator=p[2],
        arguments=[p[1], p[3]])


def _postfix_method(
        self, p
        ) -> None:
    # docstring dynamically assigned to wrapper
    # grammar equality of the form
    # nonleaf: operand OPERATOR
    p[0] = self._nodes.OperatorApplication(
        operator=p[2],
        arguments=[p[1]])


def _repetition_append_method(
        self, p
        ) -> None:
    # docstring dynamically assigned to wrapper
    # grammar equality of the form
    # nonleaf_repetition:
    #     nonleaf_repetition OPERATOR operand
    p[1].append(p[3])
    p[0] = p[1]


def _repetition_start_method(
        self, p
        ) -> None:
    # docstring dynamically assigned to wrapper
    # grammar equality of the form
    # nonleaf_repetition: operand
    p[0] = [p[2], p[1], p[3]]


def _make_skip_method(
        operator_name:
            str,
        operand:
            str
        ) -> _abc.Callable:
    r"""Production that skips to `operand`.

    ```
    ASSUME
        /\ operator_name.islower()
        /\ operand.islower()
    ```

    @return:
        unbound function
    """
    def skip_method(self, p):
        p[0] = p[1]
    method_name = f'p_{operator_name}_skip'
    method_docstring = f'''
        {operator_name}: {operand}
        '''
    skip_method.__name__ = method_name
    skip_method.__doc__ = method_docstring
    return skip_method


def format_bnf_docstrings(
        grammar
        ) -> None:
    """Infix pipe, splice lines, space around `:`.

    @param grammar:
        instance, to format the docstrings of
        `p_*` methods
    """
    for name, method in _methods_of(grammar):
        if not _is_grammar_method_name(name):
            continue
        doc = method.__doc__
        if doc is None:
            continue
        doc = _transform_bnf(doc)
        method.__func__.__doc__ = doc


def _transform_bnf(
        doc:
            str
        ) -> str:
    """Infix pipe, splice lines, space ` : `."""
    doc = re.sub(
        r' ([^\s]) : ',
        r'\1 :',
        doc,
        flags=re.VERBOSE)
    doc = re.sub(
        r' : \s* \| ',
        ': ',
        doc,
        flags=re.VERBOSE)
    return re.sub(
        r' \n \s* ([^|\s]) ',
        r' \1',
        doc,
        flags=re.VERBOSE)


def check_bnf_grammar(
        grammar
        ) -> None:
    """Assert no `grammar._p_*` methods.

    Raises `AssertionError` if any methods
    are found whose names start with `_p_`.
    """
    for name, method in _methods_of(grammar):
        if not name.startswith('_p_'):
            continue
        raise AssertionError(name, method)


def make_token_grammar(
        lexemes_to_tokens:
            dict,
        tokens_to_regexes:
            dict,
        instance
        ) -> None:
    """Add tokenization methods for literals.

    @param instance:
        grammar class
    """
    lextok = lexemes_to_tokens
    regexes = tokens_to_regexes
    for token_type, regex in regexes.items():
        if regex is None:
            continue
        def method(self, token):
            return token
        name = _name_token_var(token_type)
        method.__name__ = name
        method.__doc__ = regex
        bound_func = method.__get__(instance)
        setattr(instance, name, bound_func)
    lexemes = sort_lexemes(lextok)
    for lexeme in lexemes:
        token_type = lextok[lexeme]
        name = _name_token_var(token_type)
        regex = re.escape(lexeme)
        # NOTE: `instance.__dict__` records
        # insertion order by `setattr()`
        if hasattr(instance, name):
            raise ValueError(name, regex)
        setattr(instance, name, regex)


def _name_token_var(
        token_type
        ) -> str:
    """Return lexer method name."""
    return f't_{token_type}'


def sort_lexemes(
        lexemes:
            _abc.Iterable
        ) -> list:
    """Sort `lexemes` in descending length."""
    return sorted(
        lexemes,
        key=len,
        reverse=True)


def _format_docstring(
        *,
        _=None,
        **kw
        ) -> _abc.Callable:
    """Format doctsring using `**kw`.

    Formats the docstring of function
    `func`, using the key-value pairs
    in the dictionary `kw` as keyword
    parameter-argument pairs passed
    to the method `func.__doc__.format`.

    This decorator is needed because
    formatted string literals cannot
    be docstrings.
    """
    if _ is not None:
        raise TypeError(
            'only keyword arguments '
            'other than `_`')
    def _decorator(func):
        if func.__doc__ is not None:
            func.__doc__ = (
                func.__doc__.format(**kw))
            return func
        raise ValueError(
            f'`{func}` appears to '
            'not have a docstring')
    return _decorator


def dumps_grammar(
        grammar,
        add_braces:
            bool=False
        ) -> str:
    """Return equalities of `grammar`.

    @param grammar:
        instance with `p_*` methods
    """
    (tokens,
        start_symbol,
        nonleaf_symbols,
        grammar_text,
        ) = collect_grammar_info(
            grammar, add_braces)
    return grammar_text


def collect_grammar_info(
        grammar:
            _ty.Any,
        add_braces:
            bool
        ) -> tuple[
            set[str],
            str,
            set[str],
            str]:
    """Return grammar symbols and equalities.

    @param grammar:
        the information is collected from
        the `p_*` methods of this object
    @param add_braces:
        if `True`,
        then append `{ }` to each production
        (for semantic actions)
    @return:
        ```py
        (leaf_symbols,
         root_symbol,
         nonleaf_symbols,
         grammar_text)
        ```
    """
    root_symbol = grammar.start
    methods = list(_methods_of(grammar))
    # print(f'{len(methods)} grammar rules')
    def sieve(x):
        name, _ = x
        return _is_grammar_method_name(name)
    methods = filter(sieve, methods)
    def symbol_of(x):
        _, method = x
        docstring = method.__doc__
        if docstring.count(':') != 1:
            raise ValueError(docstring)
        symbol, _ = docstring.split(':')
        return symbol.strip()
    def line_number(x):
        _, method = x
        _, start_line = inspect.getsourcelines(
            method)
        return start_line
    methods = sorted(
        methods,
        key=line_number)
    # methods = list(methods)
    # for name, _ in methods:
    #     print(name)
    INDENT = ' ' * 4
    def format_line(line):
        line = line.strip()
        if '=' in line:
            line = f'/\\ {line}'
        if line.startswith('|'):
            line = f'{INDENT}{line}'
        return line
    grammar_symbols = set()
    def format_expansion(
            expansion:
                str
            ) -> str:
        symbols = expansion.split()
        grammar_symbols.update(symbols)
        return ' & '.join(symbols)
    nonleaf_symbols = set()
    out_lines = list()
    last_symbol = None
    for _, method in methods:
        docstring = method.__doc__
        if docstring.count(':') != 1:
            raise ValueError(docstring)
        symbol, expansion = docstring.split(':')
        symbol = symbol.strip()
        expansions = expansion.split('|')
        expansions = map(
            format_expansion,
            expansions)
        expansion = '\n| '.join(expansions)
        if symbol == last_symbol:
            docstring = f'| {expansion}'
        else:
            docstring = f'{symbol} = {expansion}'
        lines = docstring.splitlines()
        lines = map(format_line, lines)
        lines = filter(
            lambda x: x,
            lines)
        if add_braces:
            lines = map(
                lambda x: x + ' { }',
                lines)
        out_lines.extend(lines)
        nonleaf_symbols.add(symbol)
        last_symbol = symbol
    leaf_symbols = grammar_symbols - nonleaf_symbols
    grammar_text = '\n'.join(out_lines)
    return (
        leaf_symbols,
        root_symbol,
        nonleaf_symbols,
        grammar_text)


def _is_grammar_method_name(
        name:
            str
        ) -> bool:
    """Return `True` if a grammar method name."""
    return (
        name.startswith('p_') and
        name != 'p_error')


def _methods_of(
        instance
        ) -> _abc.Iterable:
    """Return iterator over methods."""
    yield from inspect.getmembers(
        instance,
        predicate=inspect.ismethod)


class Traversal:
    """Tree traversal.

    Similar mechanism to how
    parser grammars are defined.

    Methods that match nodes are
    named with the prefix `p_`.

    The docstring of each method
    contains the symbol name for
    the type of node that it matches,
    i.e., the value of `tree.symbol`.

    To match any namedtuple subtree,
    use the underscore as docstring.
    For example:

    ```python
    class TreeCheck(Traversal):
        def p_op_def(
                self,
                tree,
                **kw):
            \"\"\"operator_definition\"\"\"
            ...

        def p_default_case(
                self,
                tree,
                **kw):
            \"\"\"_\"\"\"
            ...
    ```
    """

    def __init__(
            self):
        methods = list(_methods_of(self))
        def sieve(x):
            name, _ = x
            return _is_grammar_method_name(name)
        methods = filter(sieve, methods)
        symbol_to_method = dict()
        for name, method in methods:
            symbol = method.__doc__
            symbol_to_method[symbol] = method
        self._symbol_to_method = symbol_to_method

    def traverse(
            self,
            tree,
            **kw):
        """Visit each node of `tree`.

        In `p_` methods, to recurse call this method.
        """
        rec = _ft.partial(self.traverse, **kw)
        match tree:
            case str() | bool() | int() | None:
                return tree
            case tuple() if not hasattr(tree, 'symbol'):
                trees = tuple(map(rec, tree))
                # namedtuple ?
                if hasattr(tree, '_make'):
                    return tree._make(trees)
                return trees
            case list():
                return list(map(rec, tree))
        if not hasattr(tree, 'symbol'):
            raise ValueError(
                'Expected `str` or `bool` or '
                '`int` or `None` or `tuple` or '
                'namedtuple or `list`. '
                f'Got instead: {tree}')
        symbol = tree.symbol
        method = self._symbol_to_method.get(symbol)
        if method is not None:
            return method(tree, **kw)
        # default defined ?
        method = self._symbol_to_method.get('_')
        if method is not None:
            return method(tree, **kw)
        # default recursion
        symbol, *attrs = tree
        attrs = map(rec, attrs)
        cls = type(tree)
        return cls(symbol, *attrs)


def rewrite_tables(
        parser_class,
        ) -> None:
    """Write parser table to file.

    Overwrite pre-existing file.
    """
    parser = parser_class()
    filepath = parser.cache_filepath
    if os.path.isfile(filepath):
        logger.info(
            f'found file `{filepath}`')
        os.remove(filepath)
        logger.info(
            f'removed file `{filepath}`')
    parser.build()
    if not os.path.isfile(filepath):
        raise AssertionError(
            'rebuilt parser cache not '
            f'found at: {filepath}')


def configure_logging(
        logger_name:
            str
        ) -> None:
    """Setup logging for `logger_name`."""
    logger = _log.getLogger(logger_name)
    logger.setLevel(_log.INFO)
    handler = _log.StreamHandler()
    fmt = '[%(levelname)s]: %(message)s'
    formatter = _log.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def add_column_to_tokens(
        tokens:
            _abc.Iterable[
                Token],
        text:
            str
        ) -> _abc.Iterable:
    """Generate tokens annotated with columns.

    Returns an iterator of new token objects
    that have also an attribute `token.column`.
    """
    text_length = len(text)
    row = 0
    line_start = 0
    newline_indices = _index_newlines(text)
    for token in tokens:
        # for type checking
        if token.line is None:
            raise AssertionError(token)
        if row > token.line:
            raise ValueError(
                token.line, row)
        while row < token.line:
            row += 1
            index = next(newline_indices)
            line_start = index + 1
        # for type checking
        if token.start is None:
            raise AssertionError(token)
        column = (token.start - line_start) + 1
        if column < 0 or column >= text_length:
            raise AssertionError(
                'expected '
                rf'column \in 1..{text_length} '
                f'(computed `{column = }`)')
        yield copy_lex_token(
            token,
            column=column)


def _index_newlines(
        text:
            str
        ) -> _abc.Iterator[int]:
    r"""Generate indices of newlines in `text`.

    Returns an iterator of indices of the
    newline characters `\n` that are in `text`.
    """
    for m in re.finditer('\n', text):
        yield m.start()


def find_token_column(
        string:
            str,
        token:
            Token
        ) -> int:
    r"""Return start column of `token`.

    @param string:
        input to lexer
    @return:
        number of column where
        `token` starts, with
        `column \in 1..len(string)`
    """
    index = string.rfind('\n', 0, token.start)
    line_start = index + 1
    # for type checking
    if token.start is None:
        raise AssertionError(token)
    column = (token.start - line_start) + 1
    string_length = len(string)
    if column < 1 or column > string_length:
        raise AssertionError(
            'expected'
            rf'`column \in 1..{string_length}` '
            f'(computed `{column = }`)')
    return column


def copy_lex_token(
        token:
            Token,
        **kw
        ) -> Token:
    """Return a copy of `token`.

    The new token has a `column` attribute.
    Keyword arguments in `kw` change the
    values of attributes of `token`.
    """
    column = getattr(token, 'column', None)
    attrs = dict(
        symbol=token.symbol,
        value=token.value,
        line=token.line,
        column=column,
        start=token.start)
    attrs.update(kw)
    new_token = Token(**attrs)
    return new_token


def make_lex_token(
        token_type:
            str,
        token_value:
            str |
            None=None,
        line:
            int |
            None=-1,
        column:
            int |
            None=None,
        start:
            int |
            None=-1
        ) -> Token:
    """Return a modified token.

    If `token_value is None`, then the
    returned token has `token_type` as
    valued.
    """
    if token_value is None:
        token_value = token_type
    return Token(
        symbol=token_type,
        value=token_value,
        line=line,
        column=column,
        start=start)


def pipe(
        x,
        *pipeline:
            _abc.Callable):
    """Apply each item of `pipeline` to `x`.

    Example:

    ```python
    import operator

    x = 1
    pipeline = [operator.neg, hex]
    y = pipe(x, *pipeline)
    assert y == '-0x1', y
    ```

    @param x:
        value for input to `pipeline[0]`
    """
    return _ft.reduce(
        _postfix_apply, pipeline, x)


def _postfix_apply(
        x,
        f:
            _abc.Callable):
    """Return `f(x)`."""
    return f(x)


def reverse(
        iterable:
            _abc.Iterable
        ) -> _abc.Iterable:
    """Return `reversed(list(iterable))`."""
    return reversed(list(iterable))


def printer(
        items:
            _abc.Iterable
        ) -> list:
    """Print and return `list(items)`."""
    items = list(items)
    start_line = 10 * '-'
    print(start_line)
    for item in items:
        print(item)
    end_line = 10 * '='
    print(end_line)
    return items


def map_dict(
        key_mapper:
            _abc.Callable,
        value_mapper:
            _abc.Callable,
        kv:
            dict
        ) -> dict:
    """Map keys and values of `kv`."""
    return {
        key_mapper(k): value_mapper(v)
        for k, v in kv.items()}


def map_keys(
        key_mapper:
            _abc.Callable,
        kv:
            dict
        ) -> dict:
    """Map keys of `kv` (same values)."""
    return {
        key_mapper(k): v
        for k, v in kv.items()}


def map_values(
        value_mapper:
            _abc.Callable,
        kv:
            dict
        ) -> dict:
    """Map values of `kv` (same keys)."""
    return {
        k: value_mapper(v)
        for k, v in kv.items()}


def assert_len(
        container:
            _abc.Sized,
        expected_length:
            int
        ) -> None:
    """Assert `container` has `expected_length`.

    Raises `AssertionError` if
    `len(container) != expected_length`.

    Example:

    ```python
    import tla._utils as _utils


    _MODULE_CONSTANT = {
        'item_1',
        'item_2',
        'iten_3',  # typo
        }
    _utils.assert_len(_MODULE_CONSTANT, 3)
    _MORE = _MODULE_CONSTANT | {
        'item_4',
        'item_5',
        }
    _utils.assert_len(
        _MORE,
        2 + len(_MODULE_CONSTANT))
    ```

    ```
    ASSUME
        expected_length >= 0
    ```
    """
    length = len(container)
    if length == expected_length:
        return
    formatted = _pp.pformat(container)
    message = (
        'container has unexpected length:\n'
        f'expected length:  {expected_length}\n'
        f'actual length:  {length}\n'
        f'Typo ?\n'
        f'The container is:\n{formatted}')
    raise AssertionError(message)


def rindex(
        values,
        sequence
        ) -> int:
    """Return first index, searching from end."""
    n = len(sequence)
    for index in range(n - 1, -1, -1):
        if sequence[index] in values:
            return index
    raise ValueError(
        'sequence does not contain '
        f'elements in: {values}')
