# `tla` package documentation


## Parsing overview

Modules and expressions have different syntax, so different
parsers exist for each:
- `tla.parse()` and
- `tla.parse_expr()`

Examples:

```py
import tla

tla.parse('---- MODULE name ---- A == 1 ====')

tla.parse_expr('x + 1')
```

Module and expressions can be parsed also using classes:
- `tla.Parser`
- `tla.ExprParser`

```py
import tla

parser = tla.Parser()
parser.parse('---- MODULE name ---- A == x ====')
```


## Parsing modules

This section describes the trees returned by `tla.parse()`,
and the next section `tla.parse_expr()`.
The function can be invoked as follows:

```py
import tla

module_text = r'''
--------------- MODULE Cycle -------------
(* Alternation between two values. *)
VARIABLE x

Init == x = 1
Next == x' = IF x = 1 THEN 2 ELSE 1
Spec == Init /\ [][Next]_x /\ WF_x(Next)
==========================================
'''

tree = tla.parse(module_text)
```

The function `parse()` takes one positional argument, the
string to be parsed. This string includes an entire module,
otherwise a `ValueError` is raised.

The returned `tree` is a `typing.NamedTuple`:

```py
print(type(tree))
    # <class 'tla._ast.Module'>
```

The syntax tree definition is in `tla._ast.NODE_SPECS`.

Formatting of the syntax tree is implemented by the
function `tla.pformat_ast()`:

```python
import tla

text = tla.pformat_ast(
    tree,
    width=50)
print(text)
```

The result is:

```tla
------------------ MODULE Cycle ------------------
VARIABLE x
Init == x = 1
Next == x' = IF x = 1 THEN 2 ELSE 1
Spec == Init /\ [] [Next]_x /\ WF_x(Next)
==================================================
```

Note that the formatting has changed, because `pformat_ast()`
applies a formatting definition. Also, the comment is not
present, because the tree does not store comments.

(Comments can be inserted by tokenizing the formatted text
and copying comments from the input token sequence,
maintaining relative positioning of comments.)


## Syntax trees

`tla._ast.NODE_SPECS` defines the attributes of AST nodes.
Reading this definition provides information for writing
traversals of the syntax tree.

For example, module namedtuples are defined in `tla._ast` as:

```py
NODE_SPECS = dict(
...
    MODULE=
        'name, extendees, units',
... )
```

```py
print(tree.name)
    # 'Cycle'

print(tree.units)
    # [Variables(symbol=<NodeTypes.VARIABLES: 'variables'>,
    # ...
```

Other syntax tree nodes have different attributes.
All tree nodes have an attribute `symbol` that names the
type of node. This attribute is for convenience in tree
traversals, for example:

```py
def traverse(
        tree):
    """Recursively traverse syntax tree."""
    match tree:
        case str() | bool() | int() | None:
            return tree
        case tuple() if not hasattr(tree, 'symbol'):
            trees = tuple(map(
                traverse, tree))
            # namedtuple ?
            if hasattr(tree, '_make'):
                return tree._make(trees)
            return trees
        case list():
            return list(map(
                traverse, tree))
    match tree.symbol:
        case 'theorem':
            ...
        case _:
            symbol, *attrs = tree
            attrs = map(traverse, attrs)
            cls = type(tree)
            return cls(symbol, *attrs)
```

Class names can be used in the `case` patterns, instead of
lowercase. Function `tla._ast.enum_to_class()` converts from
lowercase with underscores to class names.

Trees can be printed as branching diagrams using the
function `tla._ast.pprint_tree()`.


## Parsing expressions

An example of parsing expressions using `tla.ExprParser`:

```py
import tla


expr = r'[n \in Nat |-> n + 1]'
expr_parser = tla.ExprParser()
tree = expr_parser.parse(expr)
text = tla.pformat_ast(tree)
print(text)
    # [n \in Nat |-> n + 1]
```

The keyword argument `width` defines the column width within
which the formatter fits the TLA+ elements that are
converted to string representation. For example:

```py
text = tla.pformat_ast(tree, width=10)
print(text)
```

prints:

```tla
[n \in
    Nat |->
    n + 1]
```


## Traversing the syntax tree

Suppose we want to replace names of operators by their
definienda, i.e., expand the operators. We can use a
dictionary for this purpose:

```python
import tla


expr_1 = tla.parse_expr(r'x /\ y')
expr_2 = tla.parse_expr(r'[n \in Nat |-> n + 2]')
definitions = dict(
    Op=expr_1,
    Other=expr_2)
```

In this example we construct the dictionary directly.
In a TLA+ translator, such a dictionary of definitions
would result from analysis of the parsed module up to
the point of interest.

We now define a traversal function to check if a name is in
the dictionary of defined operators, and if so then replace
the node with the syntax tree for that defined operator.

```python
import functools as _ft


def replace(
        tree,
        definitions):
    """Recursively traverse syntax tree."""
    rec = _ft.partial(
        replace,
        definitions=definitions)
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
            return list(map(
                rec, tree))
    match tree.symbol:
        case 'operator_application' if (
                tree.arguments is None):
            # Occurrences of nullary operators are
            # represented as operator application
            # with `arguments=None`.
            name = tree.operator
            if name in definitions:
                return definitions[name]
            return tree
        case _:
            symbol, *attrs = tree
            attrs = map(rec, attrs)
            cls = type(tree)
            return cls(symbol, *attrs)
```

Next we parse the expression where the substitutions will
be done, and perform the substitutions of the operators
`Op` and `Other` with the expressions that have been parsed
above.

```python
import tla


tree = tla.parse_expr(r'Op /\ (Other = f)')
new_tree = replace(
    tree,
    definitions=definitions)
text = tla.pformat_ast(new_tree)
print(text)
```

The printed output is:

```tla
x /\ y /\ ([n \in Nat |-> n + 2] = f)
```

Traversals can be written without repeating the code
for handling default cases by using the
class `tla._utils.Traversal`.

The [visitor pattern](
    https://en.wikipedia.org/wiki/Visitor_pattern)
can be implemented by passing the function to call
recursively:

```py
def traverse(
        tree,
        recurse=None):
    """Recursively traverse syntax tree."""
    if recurse is None:
        recurse = traverse
    ...
    match tree.symbol:
        ...
        case _:
            symbol, *attrs = tree
            attrs = map(recurse, attrs)
            cls = type(tree)
            return cls(symbol, *attrs)
```


## Structure of the package

- `tla._ast`: abstract syntax tree and its tokenization
- `tla._grammar`: grammar equations and quotienting methods
- `tla._langdef`: keywords, operator precedence and fixity
- `tla._lex`: lexing from strings to tokens
- `tla._lre`: LR(1) parser that generates virtual tokens
- `tla._pprint`: syntax-tree formatter as string
- `tla._preparser`: inserts and changes tokens
- `tla._utils`: grammar auto-generation and other functions


## Copying

This document has been placed in the public domain.
