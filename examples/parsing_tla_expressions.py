"""How to parse a TLA+ expression."""
import tla


expr = r'''
    \/ /\ x = 1
       /\ x' = 2

    \/ /\ x = 2
       /\ x' = 1
    '''


def parse_expr():
    """Parse a TLA+ expression."""
    tree = tla.parse_expr(expr)
    print(tree)


def parse_expr_and_format():
    """Parse, format, print a TLA+ expression."""
    tree = tla.parse_expr(expr)
    text = tla.pformat_ast(tree)
    print(text)


if __name__ == '__main__':
    parse_expr()
    parse_expr_and_format()
