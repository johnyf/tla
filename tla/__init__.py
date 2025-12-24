"""TLA+ parser and syntax tree."""
import tla._ast as _ast
import tla._lex as _lex
import tla._lre as _lr
import tla._pprint as _pp


def _load_version() -> str | None:
    """Return package version."""
    try:
        import tla._version as _version
        return _version.version
    except ImportError:
        return None


__version__: str | None = _load_version()


Lexer = _lex.Lexer
Parser = _lr.Parser
ExprParser = _lr.ExprParser
parse = _lr.parse
parse_expr = _lr.parse_expr
pformat_ast = _pp.pformat_ast
pformat_tla = _pp.pformat_tla
make_nodes = _ast.make_nodes
