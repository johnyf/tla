"""LR machine that creates RVERTICAL, END_LET as needed."""
import argparse as _arg
import collections as _cl
import collections.abc as _abc
from dataclasses import dataclass
import functools as _ft
import os
import typing as _ty

import parstools._introspection as _intro
import parstools._lex as _prs_lex
import parstools._lr.parser as _p
from parstools._lr.parser import (
    CachedIterable,
    _ROOT,
    _END,
    _TreeMap)

import tla._ast as _tla_ast
import tla._grammar as _tla_grm
import tla._langdef as _opdef
import tla._lex as _lex
import tla._preparser as _prp
import tla._utils as _utils


# auto-generated tokens by the parser,
# with effect similar to the LR end-marker
_AUTO_VIRTUAL_TOKENS: _ty.Final = {
    'RVERTICAL',
    # 'END_VERTICAL',
    # 'DEF_SIG',
    # 'END_DEFINE',
    'END_BSLASH_A',
    'END_BSLASH_E',
    'END_BSLASH_AA',
    'END_BSLASH_EE',
    'END_CHOOSE',
    'END_LAMBDA',
    'END_IF',
    'END_CASE',
    'END_LET',
    'END_PICK',
    }
_TOKEN_PAIRS: _ty.Final = {
    '/\\': 'RVERTICAL',
    '\\/': 'RVERTICAL',
    'LET': 'END_LET',
    'BSLASH_A': 'END_BSLASH_A',
    'BSLASH_E': 'END_BSLASH_E',
    'BSLASH_AA': 'END_BSLASH_AA',
    'BSLASH_EE': 'END_BSLASH_EE',
    'CHOOSE': 'END_CHOOSE',
    'LAMBDA': 'END_LAMBDA',
    'IF': 'END_IF',
    'CASE': 'END_CASE',
    'PICK': 'END_PICK'}
_UNDELIMITED_TOKENS = set(_TOKEN_PAIRS)
_UNDELIMITED_TOKENS.difference_update({'/\\', '\\/'})
_LEXEME_PRECEDENCE = _opdef.LEXEME_PRECEDENCE
_TLA_OPERATOR_FIXITY = _opdef.TLA_OPERATOR_FIXITY
_EXCEPT_TOKEN_TYPES = _tla_grm.EXCEPT_TOKEN_TYPES
_VERTICAL_LEXEMES = _opdef.VERTICAL_LEXEMES


class Grammar(
        _tla_grm.OperatorPrecedenceGrammar):
    """Stacks for undelimited constructs."""

    def __init__(
            self
            ) -> None:
        """Initialize state."""
        super().__init__()
        self.scopes_stack: list = list()
            # LET, vertical lexemes, quantification,
            # and other undelimited constructs
        self.columns_stack: list = list()
            # opening columns of
            # vertical operators

    def p_vertical_operator(
            self, p):
        """vertical_op:
            | AND
            | OR
        """
        op = p[1]
        p[0] = op
        self.scopes_stack.append(op)
        trees = p[-1]
        if len(trees) != 1:
            raise AssertionError(trees)
        vertical_op, = trees
        self.columns_stack.append(
            vertical_op.column)
        # The LR parser via this method
        # changes the stacks only when
        # an operator occurs that
        # starts a vertical item.


@dataclass
class Result:
    """Parsing result, including tokens.

    The attribute `equation` is
    the grammar equation that produced
    this result during parsing.

    Similar to the class
    `parstools._lr.parser.Result`.
    """

    symbol: str
    value: _ty.Any=None
    # equation: str | None=None
    # start position
    line: int | None=None  # start
    column: int | None=None  # start
    # positional information
    start: _tla_ast.Position | None=None
    end: _tla_ast.Position | None=None


_State = _ty.TypeVar('_State')


@dataclass
class Action(
        _ty.Generic[_State]):
    """Shift-reduce action."""

    state: _State | None=None
    equation: _ty.Any=None
    eq_str: str | None=None  # cached


_Actions = _abc.Mapping[
    _State,
    _abc.MutableMapping[str, Action[_State]]]


class OperatorLexer:
    """Adapts token sequence for parser."""

    def __init__(
            self
            ) -> None:
        """Initialization."""
        self._lexer = _lex.Lexer()
        self._token_grouping = self._make_token_types()

    def _make_token_types(
            self
            ) -> dict:
        """Make grouping of tokens."""
        keywords = {
            v: v for v in _opdef.KEYWORDS}
        lexemes_to_tokens = (
            keywords |
            _lex.map_lexemes_to_tokens())
        groups = dict()
        items = _LEXEME_PRECEDENCE.items()
        for lexeme, prec in items:
            old_type = lexemes_to_tokens[lexeme]
            if old_type in _EXCEPT_TOKEN_TYPES:
                continue
            new_type = self._type_of_prec(
                lexeme, prec)
            groups[old_type] = new_type
                # Synonym lexemes have the same
                # token type, so this mapping
                # applies to them too.
                # This is about `_langdef._SYNONYMS`.
        return groups

    def _type_of_prec(
            self,
            lexeme:
                str,
            prec:
                _opdef.PrecRange
            ) -> str:
        """Return token type for precedence."""
        start, _ = prec
        items = _TLA_OPERATOR_FIXITY.items()
        for fixity, operators in items:
            if lexeme not in operators:
                continue
            return f'OP_{start}_{fixity}'.upper()
        raise AssertionError(lexeme)

    def _group_tokens(
            self,
            tokens
            ) -> _abc.Iterable[
                _prs_lex.Token]:
        """Adapt token symbols."""
        group = self._token_grouping.get
        modified_tokens = list()
        for token in tokens:
            ts = token.symbol
            new_type = group(ts, ts)
            token.symbol = new_type
            modified_tokens.append(token)
        return modified_tokens

    def _make_result(
            self,
            token:
                _prs_lex.Token
            ) -> Result:
        """Return a result with start position."""
        line = token.line
        column = token.column
        if line is None:
            raise AssertionError(token)
        if column is None:
            raise AssertionError(token)
        start = _tla_ast.Position(
            line=line,
            column=column)
        if token.symbol == 'MULTILINE_STRING_LITERAL':
            string = token.value
            line += string.count('\n')
            *_, last_line = string.rsplit('\n', 1)
            column = len(last_line)
        elif token.symbol in ('DEF_SIG', 'END_DEFINE'):
            pass  # same column
        else:
            column += len(token.value)
        end = _tla_ast.Position(
            line=line,
            column=column)
        return Result(
            symbol=token.symbol,
            value=token.value,
            line=start.line,
            column=start.column,
            start=start,
            end=end)

    def parse(
            self,
            text:
                str
            ) -> _abc.Iterable[Result]:
        """Return tokenized `text`."""
        text = _prp.filter_preamble(text)
        tokens = self._lexer.parse(text)
        tokens = _prp.filter_postamble(tokens)
            # NOTE: interacts with lexer,
            # by detecting end of main module
            # and thus not lexing beyond that
        tokens = _prp.filter_comments(tokens)
        tokens = self._group_tokens(tokens)
        tokens = _prp.preparse(tokens)
        return list(map(self._make_result, tokens))


class GeneratingParser(
        _ty.Generic[_State]):
    """Shift-reduce parser.

    For a set of "virtual tokens",
    the parser generates them when
    they are missing from the input.

    This approach is correct for
    handling syntactic features of
    a number of languages.

    Actions are structured as:
    `dict[node, dict[lookahead, ...]]`
    """

    def __init__(
            self
            ) -> None:
        """Initialize."""
        # cache filename
        filename = 'tla_parser.json'
        path, _ = os.path.split(__file__)
        cache_filepath = os.path.join(
            path, filename)
        # LR tables
        self.grammar = Grammar()
        op_prec = self.grammar.precedence
        parser: _p.Parser[_State] = _intro.make_parser(
            self.grammar,
            precedence=op_prec,
            cache_filepath=cache_filepath)
        self._initial: _State = parser._initial
            # NOTE: When running the parser
            # after returned by the generator,
            # each state is a set of LR items.
            #
            # When the parser is loaded from
            # the JSON file where it is memoized,
            # the states are integers.
        actions = self._restructure_actions(
            parser._actions)
        self._actions: _Actions = actions
        if parser._tree_map is None:
            raise AssertionError(parser)
        self._tree_map: _TreeMap = parser._tree_map
        # stacks
        lexer = OperatorLexer()

    def _restructure_actions(
            self,
            actions:
                _abc.Mapping
            ) -> _Actions:
        """Return nested dictionary."""
        actions_ns: _Actions = _cl.defaultdict(dict)
        kvs = actions.items()
        for (node, symbol), action in kvs:
            if action.equation is None:
                eq_str = None
            else:
                eq_str = str(action.equation)
            actions_ns[node][symbol
                ] = Action(
                    state=action.state,
                    equation=action.equation,
                    eq_str=eq_str)
                    # instead of `str()`
                    # while parsing
        return dict(actions_ns)

    def _clear_state(
            self
            ) -> None:
        """Initialize parser variables."""
        self.grammar.scopes_stack.clear()
        self.grammar.columns_stack.clear()

    def parse(
            self,
            items:
                _abc.Iterable[Result]
            ) -> tuple | None:
        """Reduce items to a tree."""
        self._clear_state()
        sequence = list(items)
        end = Result(
            symbol=_END,
            value=_END)
        sequence.append(end)
        symbols: CachedIterable[Result]
        symbols = CachedIterable(sequence)
            # input stack
        results: list[Result] = list()
            # output stack
        path: list[_State] = [self._initial]
        shift_or_reduce = _ft.partial(
            self._shift_or_reduce,
            symbols=symbols,
            results=results,
            path=path)
        while symbols.peek() and path:
            self._generate_dedents(symbols)
            shift_or_reduce()
        if symbols.peek() or path:
            return None
        if len(results) != 1:
            raise AssertionError(results)
        if self.grammar.scopes_stack:
            raise AssertionError(
                self.grammar.scopes_stack)
        if self.grammar.columns_stack:
            raise AssertionError(
                self.grammar.columns_stack)
        return results[0].value

    def _shift_or_reduce(
            self,
            symbols:
                CachedIterable[Result],
            results:
                list[Result],
            path:
                list[_State]
            ) -> None:
        """Step of shift-reduce parser."""
        if not path:
            raise AssertionError(path)
        peek = symbols.peek()
        if peek is None:
            raise AssertionError(symbols)
        lookahead = peek.symbol
        # if isinstance(peek.value, str):
        #     print(peek)
        if lookahead == _ROOT:
            results.append(symbols.pop())
            treelet = symbols.pop()
            if treelet.symbol != _END:
                raise AssertionError(_END)
            path.pop()
            return
        node = path[-1]
        action = self._actions[node].get(lookahead)
        # generate virtual token ?
        generate = (
            action is None and
            self.grammar.scopes_stack)
        if generate:
            self._generate_virtual_tokens(
                node, symbols, results)
            return
        # parsing error ?
        if action is None:
            self._print_info(symbols, results)
            path.clear()
            return
        if action.equation is not None:
            eq = action.equation
            symbol, expansion = eq
            n_items = len(expansion)
            _p.popk(path, n_items)
            # equation = str(eq)
            equation = action.eq_str
            trees = _p.popk(results, n_items)
            reduce = self._tree_map[equation]
            p = [None, *(
                u.value
                for u in trees),
                trees]
            reduce(p)
            result = trees[0]
                # fewer instantiations
                # results in speedup
            # add positional information
            end = self._get_end_position(trees)
            tree = self._add_position(
                p[0], result.start, end)
            result.symbol = symbol
            result.value = tree
            result.end = end
            result.line = None
            result.column = None
            symbols.append(result)
        elif action.state is not None:
            path.append(action.state)
            treelet = symbols.pop()
            results.append(treelet)
            self._scopes_stack_append(
                treelet.symbol)
        else:
            raise AssertionError(
                node, lookahead, action)

    def _add_position(
            self,
            tree,
            start,
            end):
        """Annotate with start and end."""
        # not a tree node ?
        # e.g., a `list`
        if not hasattr(tree, 'symbol'):
            return tree
        # call namedtuple `_replace()`
        return tree._replace(
            start=start,
            end=end)

    def _get_end_position(
            self,
            trees):
        """Return end position from `trees`."""
        # virtual tokens at end ?
        for i in range(1, 1+len(trees)):
            st = trees[-i]
            if not hasattr(st, 'end'):
                raise AssertionError(trees)
            end = st.end
            if end is not None:
                return end
        if len(trees) == 1:
            return None
        raise AssertionError(trees)

    def _scopes_stack_append(
            self,
            symbol:
                str
            ) -> None:
        """Append if start of undelimited."""
        if symbol not in _UNDELIMITED_TOKENS:
            return
        self.grammar.scopes_stack.append(symbol)

    def _generate_virtual_tokens(
            self,
            node:
                _State,
            symbols:
                CachedIterable[Result],
            results:
                list[Result]
            ) -> None:
        """Insert a suitable virtual token.

        Virtual tokens are listed in
        `_AUTO_VIRTUAL_TOKENS`.

        `results` is used only for printing
        information if an error occurs.
        """
        scopes_stack = self.grammar.scopes_stack
        columns_stack = self.grammar.columns_stack
        node_actions = self._actions[node]
        vtokens = _AUTO_VIRTUAL_TOKENS.intersection(
            node_actions)
        stack_token = scopes_stack[-1]
        token_value = _TOKEN_PAIRS[stack_token]
        if token_value not in vtokens:
            print(
                'Expected to insert token:\n'
                f'{token_value}\n'
                'Possible next tokens based on '
                f'parser state machine:\n{vtokens}')
            self._print_info(symbols, results)
            raise ValueError('Error while parsing.')
        if stack_token in _VERTICAL_LEXEMES:
            if token_value != 'RVERTICAL':
                raise AssertionError(token_value)
            end_vertical = Result(
                symbol='END_VERTICAL',
                value='END_VERTICAL',
                column=None)
                # This RVERTICAL is not due to dedent,
                # thus the vertical expression closes
                # at this point.
            symbols.append(end_vertical)
            if not columns_stack:
                raise AssertionError(
                    scopes_stack)
            column = columns_stack[-1]
            rvertical = Result(
                symbol='RVERTICAL',
                value=stack_token,
                column=column)
            symbols.append(rvertical)
        else:
            token = Result(
                symbol=token_value,
                value=token_value,
                column=None)
            symbols.append(token)
        self._pop_scope_assert(stack_token)
        # print(f'auto-generated: {token_value}')

    def _pop_scope_assert(
            self,
            symbol:
                str
            ) -> None:
        """Pop expected symbol."""
        scopes_stack = self.grammar.scopes_stack
        token_symbol = scopes_stack[-1]
        if token_symbol != symbol:
            raise AssertionError(
                token_symbol)
        scopes_stack.pop()
        columns_stack = self.grammar.columns_stack
        if symbol in _VERTICAL_LEXEMES:
            columns_stack.pop()
        inv = (
            len(scopes_stack) >=
            len(columns_stack))
        if inv:
            return
        raise AssertionError(
            scopes_stack,
            columns_stack)

    def _generate_dedents(
            self,
            symbols
            ) -> None:
        """Insert dedents.

        Inserts `RVERTICAL` due to dedent.
        """
        scopes_stack = self.grammar.scopes_stack
        columns_stack = self.grammar.columns_stack
        if not columns_stack:
            return
        if not scopes_stack:
            raise AssertionError(columns_stack)
        # get box column
        box_column = columns_stack[-1]
        if box_column < 0:
            raise AssertionError(box_column)
        # get next-token column
        next_token = symbols.peek()
        not_generate = (
            next_token.symbol == 'RVERTICAL' or
                # CASE: nested vertical expressions,
                # avoid circular recursion
            next_token.column is None or
                # nonleaf next
            next_token.column > box_column)
                # no dedent
        if not_generate:
            # print('not generating', next_token, box_column)
            return
        # print('generating dedent', next_token, box_column)
        # dedent
        # pop stacks
        index = _utils.rindex(
            _VERTICAL_LEXEMES, scopes_stack)
        vertical_lexeme = scopes_stack.pop(index)
        columns_stack.pop()
        # generate `END_VERTICAL` only if
        # next token does not start vertical item
        next_is_vitem = (
            next_token.value == vertical_lexeme and
            next_token.column == box_column)
        if not next_is_vitem:
            # print('generating END_VERTICAL', next_token,
            #     vertical_lexeme, box_column)
            # generate `END_VERTICAL`
            end_vertical = Result(
                symbol='END_VERTICAL',
                value='END_VERTICAL',
                column=None)
                # This RVERTICAL is not followed
                # by a vertical item, thus the
                # vertical expression closes.
            symbols.append(end_vertical)
        # generate `RVERTICAL`
        dedent = Result(
            symbol='RVERTICAL',
            value=vertical_lexeme,
            column=box_column,
            line=next_token.line)
        symbols.append(dedent)
        # print('RVERTICAL by dedent')
        # check stacks
        if len(scopes_stack) < len(columns_stack):
            raise AssertionError(
                len(scopes_stack),
                len(columns_stack))

    def _print_info(
            self,
            symbols,
            results
            ) -> None:
        """Print information."""
        if results:
            result = results[-1]
            if result.start is not None:
                print(
                    'Top of stack `results` has '
                    'start line: '
                    f'{result.start.line}, '
                    'and column: '
                    f'{result.start.column}')
            if result.end is not None:
                print(
                    'Top of stack `results` has '
                    'end line: '
                    f'{result.end.line}, '
                    'and column: '
                    f'{result.end.column}')
            print(
                f'Top of stack `results`:\n{result}')
        else:
            print('Empty stack `results`')
        next_symbol = symbols.peek()
        if next_symbol is None:
            print('\nNo symbols remain in the input.')
        else:
            print(
                '\nNext symbol in input:\n'
                f'{next_symbol}')
        print(
            '`scopes_stack`:\n'
            f'{self.grammar.scopes_stack}')
        print(
            '`columns_stack`:\n'
            f'{self.grammar.columns_stack}')


class Parser:
    """Parser of TLA+ modules."""

    def __init__(
            self
            ) -> None:
        self._lexer: OperatorLexer | None
        self._lexer = None
        self._parser: GeneratingParser | None
        self._parser = None

    def parse(
            self,
            module_text:
                str
            ) -> tuple:
        """Return syntax tree from `module_text`."""
        if self._parser is None:
            self._lexer = OperatorLexer()
            self._parser = GeneratingParser()
        tokens = self._lexer.parse(module_text)
        tree = self._parser.parse(tokens)
        if tree is None:
            raise ValueError('Error while parsing.')
        tree = _tla_ast.map_steps_to_proofs(tree)
        return tree


def lex(
        text:
            str
        ) -> list[Result]:
    """Parse lexemes."""
    lexer = OperatorLexer()
    tokens = lexer.parse(text)
    tokens = list(tokens)
    # for token in tokens:
    #     print(token)
    return tokens


class ExprParser(
        Parser):
    """Parser of TLA+ expressions."""

    def parse(
            self,
            tla_expr:
                str
            ) -> _ty.Any:
        """Parse a TLA+ expression."""
        tla_module_text = f'''
            ---- MODULE name ----
            AXIOM name == \n{tla_expr}
            ====
            '''
        module_tree = super().parse(
            tla_module_text)
        expr_tree = module_tree.units[0].expression
        return expr_tree


def parse(
        module_text:
            str
        ) -> tuple:
    """Return syntax tree for `module_text`."""
    if not hasattr(parse, 'parser'):
        parse.parser = Parser()
    return parse.parser.parse(module_text)


def parse_expr(
        expr_text:
            str
        ) -> tuple:
    """Return syntax tree for `expr_text`."""
    if not hasattr(parse_expr, 'parser'):
        parse_expr.parser = ExprParser()
    return parse_expr.parser.parse(expr_text)


def _parse_file(
        filename:
            str
        ) -> None:
    """Parsing file `filename`."""
    with open(filename,
                mode='r',
                encoding='utf-8') as fd:
        file_text = fd.read()
    tree = parse(file_text)
    print(tree)
    _tla_ast.pprint_tree(tree)


def _main():
    """Entry point."""
    args = _parse_args()
    filename = args.filename
    _parse_file(filename)


def _parse_args(
        ) -> _arg.Namespace:
    """Return arguments."""
    parser = _arg.ArgumentParser()
    parser.add_argument(
        'filename',
        help='TLA+ file to parse')
    return parser.parse_args()


if __name__ == '__main__':
    _main()
