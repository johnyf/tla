"""Test multiline string literals."""
import tla._ast
import tla._lre as _lr


text = r'''
---- MODULE example ----
A == """
    This is a multiline string
    in TLA+
    """
========================
'''


def test_multiline_strings():
    parser = _lr.Parser()
    tree = parser.parse(text)
    print(tree)
    out = tla._ast.pprint_tree(tree)
    print(out)


def test_multiline_string_position():
    lexer = _lr.OperatorLexer()
    tokens = lexer.parse(text)
    Result = _lr.Result
    Position = tla._ast.Position
    tokens_ = [
        Result(
            symbol='DASH_LINE',
            value='----',
            line=1,
            column=0,
            start=Position(
                line=1,
                column=0),
            end=Position(
                line=1,
                column=4)),
        Result(
            symbol='MODULE',
            value='MODULE',
            line=1,
            column=5,
            start=Position(
                line=1,
                column=5),
            end=Position(
                line=1,
                column=11)),
        Result(
            symbol='NAME',
            value='example',
            line=1,
            column=12,
            start=Position(
                line=1,
                column=12),
            end=Position(
                line=1,
                column=19)),
        Result(
            symbol='DASH_LINE',
            value='----',
            line=1,
            column=20,
            start=Position(
                line=1,
                column=20),
            end=Position(
                line=1,
                column=24)),
        Result(
            symbol='DEF_SIG',
            value='DEF_SIG',
            line=2,
            column=0,
            start=Position(
                line=2,
                column=0),
            end=Position(
                line=2,
                column=0)),
        Result(
            symbol='NAME',
            value='A',
            line=2,
            column=0,
            start=Position(
                line=2,
                column=0),
            end=Position(
                line=2,
                column=1)),
        Result(
            symbol='DOUBLE_EQ',
            value='==',
            line=2,
            column=2,
            start=Position(
                line=2,
                column=2),
            end=Position(
                line=2,
                column=4)),
        Result(
            symbol='MULTILINE_STRING_LITERAL',
            value=(
                '"""\n'
                '    This is a multiline string\n'
                '    in TLA+\n'
                '    """'),
            line=2,
            column=5,
            start=Position(
                line=2,
                column=5),
            end=Position(
                line=5,
                column=7)),
        Result(
            symbol='EQ_LINE',
            value='========================',
            line=6,
            column=0,
            start=Position(
                line=6,
                column=0),
            end=Position(
                line=6,
                column=24)),
        ]
    assert tokens == tokens_, tokens


if __name__ == '__main__':
    test_multiline_strings()
