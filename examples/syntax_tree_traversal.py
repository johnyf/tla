"""How to traverse syntax trees."""
import functools as _ft

import tla


_nodes = tla.make_nodes()
    # namespace of tree classes (namedtuples)


def traverse_tla_tree():
    """Traverse syntax tree to rename operators."""
    expr = r'x = 1 /\ y = 2'
    tree = tla.parse_expr(expr)
    renaming = dict(x='p', y='q')
    renamed_tree = traverse(tree, renaming)
    text = tla.pformat_ast(renamed_tree)
    print(text)


def traverse(
        tree,
        renaming:
            dict[str, str]):
    """Recursively traverse syntax tree."""
    rec = _ft.partial(
        traverse,
        renaming=renaming)
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
    match tree.symbol:
        case 'operator_application':
            op = rec(tree.operator)
            args = rec(tree.arguments)
            # operator name ?
            if tree.arguments is None:
                name = tree.operator
                op = renaming.get(name, name)
            return _nodes.OperatorApplication(
                operator=op,
                arguments=args)
        case _:
            symbol, *attrs = tree
            attrs = map(rec, attrs)
            cls = type(tree)
            return cls(symbol, *attrs)


if __name__ == '__main__':
    traverse_tla_tree()
