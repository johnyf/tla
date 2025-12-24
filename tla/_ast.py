"""Syntax tree that represents TLA+."""
import argparse as _arg
import collections as _cl
import collections.abc as _abc
import enum
import functools as _ft
import itertools as _itr
import pprint as _pp
import shlex as _sh
import subprocess as _sbp
import time
import typing as _ty

import tla._lex as _lex
import tla._langdef as _opdef


_MIN_LINE_LEN = 4
_DASH_LINE = 'DASH_LINE'
_EQ_LINE = 'EQ_LINE'
_LPAREN = 'LPAREN'
_RPAREN = 'RPAREN'
_LBRACE = 'LBRACE'
_RBRACE = 'RBRACE'
_LBRACKET = 'LBRACKET'
_RBRACKET = 'RBRACKET'
_TLA_OPERATOR_FIXITY = _opdef.TLA_OPERATOR_FIXITY
_lexemes_to_tokens = _lex.map_lexemes_to_tokens()


NODE_SPECS = dict(
    AXIOM=
        'name, expression, axiom_keyword',
        # `axiom_keyword` is one of
        # `'AXIOM'`, `'ASSUMPTION'`, `'ASSUME'`
    BOOLEAN_LITERAL=
        'value',
    BY=
        'only, facts, names, keyword',
        # `keyword` is `'DEF'` or `'DEFS'`
        # or `None`
    CASES=
        'cases, other',
        # Represents both `CASE` and `ELIF`
        # constructs. The specific form is
        # considered concrete information
        # (tokeny).
    CASE_ITEM=
        'predicate, expression',
    CHOOSE=
        'declaration, predicate',
        # "predicate" here is for readability:
        # this expression may take values outside
        # of the set `BOOLEAN`
    CONSTANTS=
        'names, keyword',
        # `keyword` is `'CONSTANT'` or `'CONSTANTS'`
    DEFINE=
        'definitions, keyword',
        # `keyword` is `'DEFINE'` or `None`
    EXCEPT=
        'function, changes',
    FAIRNESS=
        'operator, subscript, action',
    FIELD=
        'expression, name',
    FLOAT_NUMERAL=
        'value',
    FUNCTION=
        'declaration, value',
    FUNCTION_APPLICATION=
        'function, arguments',
    FUNCTION_CHANGE=
        'item, expression',
    HAVE=
        'expression',
    HIDE=
        'facts, names, keyword',
        # `keyword` is `'DEF'` or `'DEFS'`
        # or `None`
    IF=
        'predicate, then, else_',
    IFS=
        'cases, other',
    IF_ITEM=
        'predicate, expression',
    INSTANCE=
        'name, with_substitution, local',
    INTEGRAL_NUMERAL=
        'value',
    KEY_BOUND=
        'name, bound',
    LAMBDA=
        'parameters, expression',
    LET=
        'definitions, expression',
    MODULE=
        'name, extendees, units',
    MODULE_NAME=
        'name',
    OBVIOUS=
        '',
    OMITTED=
        '',
    OPERATOR_APPLICATION=
        'operator, arguments, nonfix',
        # `nonfix` is `True` or `None`
        #
        # `nonfix=True` means that a prefix,
        # infix, or postfix operator is
        # applied as nonfix, for example
        # `+(1, 2)`
        #
        # The default formatting for fixal
        # operators is based on their fixity.
        # `nonfix` changes it to nonfix
        # formatting.
    OPERATOR_DECLARATION=
        'name, level, new_keyword',
        # `new_keyword` is `True` or `None`
    OPERATOR_DEFINITION=
        'name, arity, '
        'definiens, local, function',
            # `function` means
            # the form:
            # `f[...] == ...`
    PARAMETER_DECLARATION=
        'name, arity',
    PARENTHESES=
        'expression',
    PICK=
        'declarations, predicate',
    PROOF=
        'steps, proof_keyword',
        # `proof_keyword` is `True` or `None`
    PROOF_CASE=
        'expression',
    PROOF_STEP=
        'name, main, proof, proof_keyword',
        # "proof step" distinguishes
        # from a pair of states in
        # the semantics
    QUANTIFICATION=
        'quantifier, declarations, predicate',
        # "predicate" here is for readability:
        # this expression may take values outside
        # of the set `BOOLEAN`
    QUANTIFIER_WITNESS=
        'expressions',
    RECORD=
        'key_values',
    RECURSIVE_OPERATORS=
        'names',
    SEQUENT=
        'assume, prove',
    SET_COMPREHENSION=
        'item, declarations',
        # expression ?
    SET_ENUMERATION=
        'items',
        # expressions ?
    SET_OF_BOOLEANS=
        '',
    SET_OF_FUNCTIONS=
        'domain, codomain',
    SET_OF_RECORDS=
        'key_bounds',
    SET_OF_STRINGS=
        '',
    SET_SLICE=
        'declaration, predicate',
    STRING_LITERAL=
        'value',
    SUBEXPRESSION_REFERENCE=
        'items',
    SUBSCRIPTED_ACTION=
        'operator, action, subscript',
    SUFFICES=
        'predicate',
    TAKE=
        'declarations',
    TEMPORAL_QUANTIFICATION=
        'quantifier, declarations, predicate',
        # "predicate" here is for readability:
        # this expression may take values outside
        # of the set `BOOLEAN`
    THEOREM=
        'name, goal, proof, theorem_keyword',
        # `theorem_keyword` is one of `'THEOREM'`,
        # `'LEMMA'`, `'PROPOSITION'`, `'COROLLARY'`
    TUPLE=
        'items',
    USE=
        'facts, names, only, keyword',
        # `keyword` is `'DEF'` or `'DEFS'`
        # or `None`
    VARIABLES=
        'names, keyword',
        # `keyword` is `'VARIABLE'` or `'VARIABLES'`
    VERTICAL_LIST=
        'operator, arguments',
    VERTICAL_ITEM=
        'operator, expression',
    WITH_INSTANTIATION=
        'name, expression'
    )


NodeTypes = enum.StrEnum(
    'NodeTypes',
    sorted(NODE_SPECS))


def make_nodes(
        ) -> _arg.Namespace:
    """Return syntax tree classes.

    The classes are returned in a namespace.
    For example:

    ```python
    import tla

    tree_types = tla.make_nodes()
    thm = tree_types.Theorem(
        name='PrimesInf',
        goal=...,
        proof=...,
        theorem_keyword='THEOREM')
    ```

    The same classes are returned by each call.
    This enables pickling and thus using
    the `multiprocessing` and `pickle` modules.
    """
    glob = globals()
    node_types = dict()
    items = NODE_SPECS.items()
    for node_name, attr_names in items:
        class_name = enum_to_class(node_name)
        # already generated ?
        if class_name in glob:
            node_types[class_name] = glob[class_name]
            continue
        # generate class
        node_enum = NodeTypes[node_name]
        # attribute names
        attr_names = [
            attr
            for attr in
                attr_names.split(',')
            if attr]
        attr_names = (
            'symbol',
            *attr_names,
            'start',  # Position(line, column)
            'end')  # Position(line, column)
        # default values of attributes
        n_attrs = len(attr_names)
        defaults = (
            (node_enum,) +
            (None,) * (n_attrs - 1))
        attrs = ', '.join(attr_names)
        node_types[class_name] = _cl.namedtuple(
            class_name, attrs,
            defaults=defaults)
        glob[class_name] = node_types[class_name]
            # this enables pickling syntax trees
    return _arg.Namespace(
        **node_types)


def enum_to_class(
        enum_name:
            str
        ) -> str:
    """Return class name."""
    return enum_name.title().replace('_', '')


def class_to_enum(
        class_name:
            str
        ) -> str:
    """Return enumeration name."""
    def prepend(
            char:
                str
            ) -> str:
        if char.isupper():
            return f'_{char}'
        return char
    enum_name = ''.join(map(
        prepend, class_name))
    return enum_name[1:].upper()


_nodes = make_nodes()


class Position(_ty.NamedTuple):
    """Text location."""

    line: int | None=None
    column: int | None=None


_LEAF_PROOFS = {
    'by',
    'obvious',
    'omitted'}


def map_steps_to_proofs(
        tree):
    """Map to nested proofs.

    Based on step numbers, lists of steps
    are mapped to hierarchical trees of
    proofs.
    """
    rec = map_steps_to_proofs
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
    enum_name = enum_to_class(
        tree.symbol)
    match enum_name:
        case 'Theorem':
            has_leaf_proof = (
                tree.proof is not None and
                tree.proof.steps is not None and
                len(tree.proof.steps) == 1 and
                tree.proof.steps[0].symbol in
                    _LEAF_PROOFS)
            if has_leaf_proof:
                proof = tree.proof
            else:
                proof = rec(tree.proof)
            return _nodes.Theorem(
                name=tree.name,
                goal=tree.goal,
                proof=proof,
                theorem_keyword=
                    tree.theorem_keyword,
                start=tree.start,
                end=tree.end)
        case 'ProofStep':
            proof = rec(tree.proof)
            return _nodes.ProofStep(
                name=tree.name,
                main=tree.main,
                proof=proof,
                proof_keyword=
                    tree.proof_keyword)
        case 'Proof':
            return make_steps_tree(tree)
        case _:
            symbol, *attrs = tree
            attrs = map(rec, attrs)
            cls = type(tree)
            return cls(symbol, *attrs)


def make_steps_tree(
        tree):
    """Return proof tree, from steps sequence."""
    # no steps ?
    if not tree.steps:
        return tree
    # get level of first step
    #
    # This handles the case of outer proof level
    # not 1, for example:
    # THEOREM TRUE
    # <8>1. TRUE
    if len(tree.steps) < 1:
        raise AssertionError(tree)
    step = tree.steps[0]
    start_level = _step_level(step)
    # initialize
    steps_stack = [list()]
    current_level = start_level
    steps = tree.steps
    end_step = _nodes.ProofStep(
        name=f'<{current_level}>')
        # used to cause the final popping
        # of levels in `steps_stack` into
        # the first level
    steps.append(end_step)
    for step in steps:
        proof = step.proof
        has_proof = (
            proof is not None and
            proof.symbol not in
                _LEAF_PROOFS)
        if has_proof:
            raise ValueError(
                'proof step already has '
                'nonleaf proof')
        level = _step_level(step)
        # print(f'{level = }')
        if level > current_level:
            # print('adding proof level')
            steps_stack.append(list())
            current_level = level
        elif level < current_level:
            while level < current_level:
                # print('popping proof level')
                proof_steps = steps_stack.pop()
                # get step of smaller level
                prev_level = steps_stack[-1]
                last_step = prev_level.pop()
                if last_step.proof is not None:
                    step_num = last_step.name
                    raise AssertionError(
                        f'`{step_num}` already has '
                        'a proof, that would be '
                        'overwritten by this '
                        'sequence of proof-steps.')
                current_level = _step_level(last_step)
                proof = _nodes.Proof(
                    steps=proof_steps,
                    start=proof_steps[0].start,
                    end=proof_steps[-1].end)
                last_step = _nodes.ProofStep(
                    name=last_step.name,
                    main=last_step.main,
                    proof=proof,
                    proof_keyword=
                        last_step.proof_keyword,
                    start=last_step.start,
                    end=proof.end)
                steps_stack[-1].append(
                    last_step)
        if level != current_level:
            raise AssertionError(
                level, current_level)
        steps_stack[-1].append(step)
    if len(steps_stack) > 1:
        raise AssertionError(
            len(steps_stack))
    proof_steps, = steps_stack
    proof_steps.pop()  # end-step
    start = proof_steps[0].start
    end = proof_steps[-1].end
    return _nodes.Proof(
        steps=proof_steps,
        proof_keyword=tree.proof_keyword,
        start=start,
        end=end)


def _step_level(
        step
        ) -> int:
    """Return level of `step`."""
    label = step.name
    prefix, _ = label.split('>')
    middle = prefix.lstrip('<')
    if middle in ('+', '*'):
        raise NotImplementedError(
            f'Unsupported proof step type: {label}')
    level = int(middle)
    return level


def op_decl_name_bound_arity(
        tree
        ) -> tuple:
    """Return details of `OperatorDeclaration`."""
    if tree.operator == '\\in':
        name, bound = tree.arguments
        arity = None
    else:
        name = tree.operator
        bound = None
        arity = tree.arguments
    if name.arguments is not None:
        raise AssertionError(name)
    name = name.operator
    return (
        name,
        bound,
        arity)


def declarations_as_name_bounds(
        expressions:
            list[tuple]
        ) -> list[tuple]:
    r"""Return names and bounds of declared variables.

    Also duplicates bounds, for example
    `x, y \in S` becomes
    `[(x, S), `(y, S)]`.
    """
    name_bounds = list()
    for expr in expressions:
        if expr.operator == '\\in':
            name, bound = expr.arguments
            name_bounds.append(
                (name, bound))
                # `name` can be a `Tuple`
        elif expr.arguments is None:
            name = expr
            bound = None
            name_bounds.append(
                (name, bound))
        else:
            raise ValueError(expr)
    # ditto bounds
    ditto_bounds = list()
    last_bound = None
    for name, bound in reversed(name_bounds):
        if bound is None:
            bound = last_bound
        last_bound = bound
        ditto_bounds.append(
            (name, bound))
    return list(reversed(ditto_bounds))


def _pformat_nt_tree(
        tree:
            tuple |
            list |
            str
        ) -> str:
    """Format `tree`."""
    d = _pformat_nt_tree_recurse(tree)
    return _pp.pformat(d, width=70)


def _pformat_nt_tree_recurse(
        tree):
    if (isinstance(tree, tuple) and
            hasattr(tree, '_fields')):
        return _pformat_namedtuple(tree)
    elif isinstance(tree, (tuple, list)):
        return _pformat_list(tree)
    else:
        return tree


def _pformat_namedtuple(
        nt):
    d = dict()
    for key in nt._fields:
        value = getattr(nt, key)
        d[key] = _pformat_nt_tree_recurse(value)
    return d


def _pformat_list(
        x):
    return [
        _pformat_nt_tree_recurse(v)
        for v in x]


def dump_tree_as_graph(
        tree:
            tuple,
        filename:
            str
        ) -> None:
    """Layout syntax tree as PDF."""
    graph = _tree_to_graph(tree)
    dot_lines = list()
    for node, label in graph.nodes.items():
        node_dot = f'{node} [label="{label}"];'
        dot_lines.append(node_dot)
    for node, other in graph.edges:
        edge_dot = f'{node} -> {other};'
        dot_lines.append(edge_dot)
    dot_text = '\n'.join(dot_lines)
    dot_text = f'digraph {{ {dot_text} }}'
    # write PDF file
    pdf_filename = f'{filename}.pdf'
    dot_filename = f'{filename}.dot'
    with open(dot_filename,
                mode='w',
                encoding='utf-8') as fd:
        fd.write(dot_text)
    prog = _sh.split(f'''
        dot -Tpdf
            -o {pdf_filename}
            {dot_filename}
        ''')
    _sbp.call(prog)


class DiGraph:
    """Graph with directed edges."""

    def __init__(
            self
            ) -> None:
        self.nodes: dict = dict()
        self.edges: set = set()


def _tree_to_graph(
        tree):
    """Convert tree to graph."""
    graph = DiGraph()
    _tree_to_graph_recurse(tree, graph)
    return graph


def _tree_to_graph_recurse(
        tree:
            tuple |
            list |
            str,
        graph:
            DiGraph
        ) -> int:
    """Create graph node for `tree`."""
    u = len(graph.nodes)
    if isinstance(tree, tuple):
        label = f'{tree.symbol}'
        label = label.replace(
            '.', r'_').replace(
            '"', '').replace(
            '\\', '\\\\')
        graph.nodes[u] = label
    elif isinstance(tree, str):
        label = tree
        label = label.replace(
            '.', r'_').replace(
            '"', '').replace(
            '\\', '\\\\')
        graph.nodes[u] = label
    if isinstance(tree, (tuple, list)):
        for succ in tree:
            if succ is None:
                continue
            v = _tree_to_graph_recurse(
                succ, graph)
            graph.edges.add((u, v))
    return u


LINE = '\u2500' * 2
BOTTOM_LEFT_CORNER = '\u2514'
BRANCH = '\u251c'
VERTICAL_LINE = '\u2502'
END = f'{BOTTOM_LEFT_CORNER}{LINE}'
SPACE = '\x20'


def pprint_tree(
        tree
        ) -> None:
    """Print formatted syntax `tree`."""
    text = pformat_tree(tree)
    print(text)


def pformat_tree(
        tree
        ) -> str:
    """Return formatted text for `tree`."""
    lines = _pformat_tree(tree)
    return '\n'.join(lines)


def _pformat_tree(
        tree):
    """Yield lines showing `tree`."""
    if (isinstance(tree, tuple) and
            hasattr(tree, '_fields')):
        treed = tree._asdict()
    elif isinstance(tree, (list, tuple)):
        treed = {i: v for i, v in enumerate(tree)}
    else:
        yield f'{END} {tree}'
        return
    for i, u in enumerate(treed):
        prefix = (
            f'{BRANCH}{LINE}' if
                i < len(treed) - 1 else END)
        yield f'{prefix} {u}'
        if treed[u] is None:
            continue
        prefix = (VERTICAL_LINE if
            i < len(treed) - 1 else SPACE)
        for line in _pformat_tree(treed[u]):
            yield f'{prefix}   {line}'
