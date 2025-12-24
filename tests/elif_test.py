"""Test Boolean conditional."""
import tla._lre as _lr


def test_elif_conditional():
    module = '''
    ---- MODULE elif_test ----
    A == IF TRUE THEN
            1
        ELIF TRUE THEN
            2
        ELIF FALSE THEN
            3
        ELSE
            4
    ==========================
    '''
    parser = _lr.Parser()
    tree = parser.parse(module)
    print(tree)


if __name__ == '__main__':
    test_elif_conditional()
