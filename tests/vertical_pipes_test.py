"""Tests for vertical expressions with `|`.

To parse pipes as vertical, add `'|'` to
`tla._langdef.VERTICAL_LEXEMES` and where
vertical conjunction and disjunction is
specified.
"""
import tla._ast as _ast
import tla._lre as _lr


source = r'''
---- MODULE example ----

A == | B
     | C

========================
'''


def vertical_pipes():
    parser = _lr.Parser()
    tree = parser.parse(source)
    _ast.pprint_tree(tree)


if __name__ == '__main__':
    vertical_pipes()
