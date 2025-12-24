"""Tests for the package `tla`."""
import pytest
import tla._langdef as _opdef
import tla._lex as _lex
import tla._lre as _lr


def test_check_lexprec():
    _opdef.check_lexprec()


expr_tests = [
    " FALSE ",
    " TRUE ",
    " ~ FALSE ",
    " ~ TRUE ",
    " ~ x ",
    " ~ y ",
    " ~ 1 ",
    " ~ 2 ",
    " FALSE /\\ TRUE ",
    " x /\\ y ",
    " FALSE \\/ TRUE ",
    " x \\/ y ",
    " FALSE => TRUE ",
    " x => y ",
    " FALSE <=> TRUE ",
    " x <=> y ",
    " IF FALSE THEN FALSE ELSE FALSE ",
    " IF x = 1 THEN 2 ELSE 3 ",
    " x = 5 ",
    " y = 2 ",
    " x # 5 ",
    " y # 2 ",
    " Nat ",
    " 15 ",
    ' "15" ',
    " @ ",
    " x @@ y ",
    " (x @@ y) ",
    " x :> y ",
    " (x :> y) ",
    " x <: y ",
    " (x <: y) ",
    " x + y ",
    " (x + y) ",
    " x - y ",
    " (x - y) ",
    " - x ",
    " (- x) ",
    " -x ",
    " (-x) ",
    " - 1 ",
    " (- 1) ",
    " -1 ",
    " (-1) ",
    " x / y ",
    " (x / y) ",
    " x % y ",
    " (x % y) ",
    " (x + 1) ",
    # quantification
    " \\A y \\in R:  \\A <<u, v>> \\in S:  G(y, u, v) ",
    " \\E x, y:  x + y < 0 ",
    " \\AA x: TRUE ",
    " \\EE x, y: TRUE ",
    # `CHOOSE`
    " CHOOSE foo: FALSE ",
    r" CHOOSE <<u, v>> \in S:  A(u, v) ",
    " CHOOSE <<x, y>>: x = y ",
    # set theory
    " {1, 2, 3, 4 / 5} ",
    " {Foo \\in FALSE: FALSE} ",
    " {FALSE: x \\in {1, 2}} ",
    " {FALSE, FALSE} ",
    " SUBSET A.r ",
    " UNION {S \\in A:  S \\cap Q # {}} ",
    " {x \\in Int:  x < 0} ",
    " x \\subseteq y ",
    " x \\in S ",
    " x \\notin S ",
    " x \\in 1 ",
    " x \\in {1, 2} ",
    " x \\notin 2 ",
    " x \\notin {3, 4} ",
    " S \\ Q ",
    " S \\cap Q ",
    " S \\cup Q ",
    " A \\X B \\X C ",
    " "
    # functions
    " [foo |-> FALSE] ",
    " [foo |-> FALSE, bar |-> FALSE] ",
    " [FALSE -> FALSE] ",
    " [x, y \\in S, uv \\in T |-> G(x, y, uv[1], uv[2])] ",
    " DOMAIN f ",
    r" [x, y \in S, <<u, v>> \in T |-> G(x, y, u, v)] ",
    " f[x]' ",
    " f[k + 1, r] ",
    " [(A \\cup B) -> C] ",
    " [a |-> u + v, b |-> w] ",
    " [a: Int, b: A \\cup B] ",
    # EXCEPT
    " [f EXCEPT !.foo = FALSE] ",
    " [f EXCEPT ![FALSE] = FALSE] ",
    " [f EXCEPT ![FALSE] = FALSE, !.foo = FALSE] ",
    "[f EXCEPT ![1, x] = e] ",
    " [f EXCEPT ![1].g = 2, ![<<t, 3>>] = u] ",
    # tuples
    " <<TRUE>> ",
    " <<TRUE, TRUE>> ",
    " <<1, 2, 3 + 5 >> ",
    " Int \\X (1..2) \\X Real ",
    # actions
    " (TRUE + 1)' ",
    " (1 + 2)' /\\ 3 ",
    " [x \\in {1, 2} |-> x' + 1] ",
    " [FALSE]_TRUE ",
    " <<TRUE>>_TRUE ",
    " [x' = x + 1]_<<x, y>> ",
    " <<x' = x + 1>>_<<x, y>> ",
    " [M \\/ N]_<<u, v>> ",
    " <<x' = x + 1>>_(x * y) ",
    " ENABLED (x' = x + 1) ",
    " (x = 0 /\\ x' = 1) \\cdot "
        "(x = 1 /\\ x' = 2) ",
    " UNCHANGED x ",
    " UNCHANGED FALSE ",
    " UNCHANGED TRUE ",
    " UNCHANGED 1 ",
    " UNCHANGED <<x>> ",
    " UNCHANGED <<x, y>> ",
    " UNCHANGED <<x, y, z>> ",
    # temporal formulas
    " []A ",
    " <>A ",
    " [][A]_v ",
    " [][x' = x + 1]_<<x, y>> ",
    " <><<A>>_v ",
    " <><<x' = x + y>>_<<x, y, z>> ",
    " A -+-> B ",
    " ([]p) -+-> ([]q) ",
    # liveness formulas
    " A ~> B ",
    " WF_TRUE (TRUE) ",
    " WF_<<x, y>>(N /\\ M)",
    " WF_x(N) ",
    " SF_TRUE(TRUE) ",
    # `LAMBDA`
    " LAMBDA Foo:  TRUE ",
    # `LET ... IN`
    " LET a == 1 IN a ",
    " LET x == 1  y == 2 IN x + y ",
    " A(y - 1)!B!C ",
    " A!Op(y - 1, B) ",
    # user-defined operators
    " (x ^ y) ",
    " (x / y) ",
    " (x * y) ",
    " (-x) ",
    " (x + y) ",
    " (x^+) ",
    " (x^*) ",
    " (x^#) ",
    " (x < y) ",
    " (x =< y) ",
    " (x <= y) ",
    " (x > y) ",
    " (x >= y) ",
    " (x ... y) ",
    " (x .. y) ",
    " (x | y) ",
    " (x || y) ",
    " (x && y) ",
    " (x & y) ",
    " (x $$ y) ",
    " (x $ y) ",
    " (x ?? y) ",
    " (x %% y) ",
    " (x % y) ",
    " (x ## y) ",
    " (x ++ y) ",
    " (x -- y) ",
    " (x ** y) ",
    " (x // y) ",
    " (x ^^ y) ",
    " (x @@ y) ",
    " (x !! y) ",
    " (x |- y) ",
    " (x |= y) ",
    " (x -| y) ",
    " (x =| y) ",
    " (x <: y) ",
    " (x :> y) ",
    " (x := y) ",
    " (x ::= y) ",
    " (x (+) y) ",
    " (x (-) y) ",
    " (x (.) y) ",
    " (x (/) y) ",
    " (x (\\X) y) ",
    " (x \\uplus y) ",
    " (x \\sqcap y) ",
    " (x \\sqcup y) ",
    " (x \\div y) ",
    " (x \\wr y) ",
    " (x \\star y) ",
    " (x \\o y) ",
    " (x \\bigcirc y) ",
    " (x \\bullet y) ",
    " (x \\prec y) ",
    " (x \\succ y) ",
    " (x \\preceq y) ",
    " (x \\succeq y) ",
    " (x \\sim y) ",
    " (x \\simeq y) ",
    " (x \\ll y) ",
    " (x \\gg y) ",
    " (x \\asymp y) ",
    " (x \\subset y) ",
    " (x \\supseteq y) ",
    " (x \\approx y) ",
    " (x \\cong y) ",
    " (x \\sqsubset y) ",
    " (x \\sqsubseteq y) ",
    " (x \\sqsupset y) ",
    " (x \\sqsupseteq y) ",
    " (x \\doteq y) ",
    " (x \\propto y) ",
    ]

expr_tests.append(r'''
    /\ \/ FALSE
       \/ FALSE
    /\ FALSE
    ''')
expr_tests.append(r'''
    /\ (f = [x \in {1, 2} |-> x' + 1])
    /\ a = b
    ''')
expr_tests.append(r'''
    CASE   A -> u
        [] B -> v
        [] OTHER -> w
    ''')
expr_tests.append(r'''
    LET
        x == y - 1
        f[u \in Int] == u^2
    IN
        x + f[v]
    ''')

# tests for module parser
module_tests = list()
module_tests.append(r'''
    ---- MODULE definitions ----
    a == 1
    a == INSTANCE M WITH x <- 1
    Foo(x, y) == x + y
    Foo(x, Bar(_)) == x + y

    a == /\ f = [x \in {1, 2} |-> x]
         /\ g = b
    ====
    ''')
module_tests.append(r'''
    ---- MODULE sequents ----
    THEOREM
        ASSUME TRUE
        PROVE TRUE

    THEOREM
        ASSUME NEW x \in {1, 2}
        PROVE x \in {1, 2, 3}
    ====
    ''')
module_tests.append(r'''
    ---- MODULE Foo ----
    x == 1
    ====================
    ''')
module_tests.append(r'''
    ---- MODULE Bar ----
    b == /\ a = 1
         /\ c = d
    ====================
    ''')
module_tests.append(r'''
---- MODULE Foo_Bar ----
EXTENDS Foo

VARIABLE x

Foo == TRUE  (*{ by (prover:"smt3") }*)
Bar == f[<<a, b>>]
OpLabel == label(b):: 1


THEOREM
    \E r, q:  TRUE
PROOF
<1>1. TRUE
    OBVIOUS
<1>2. TRUE
    OMITTED
<1> USE ONLY TRUE, TRUE DEF Foo
<1> USE TRUE
<1> HIDE <1>2
<1> DEFINE r == 1
<1>3. ASSUME TRUE
      PROVE TRUE
<1> QED

------------------------

THEOREM
    ASSUME TRUE, 1, NEW r \in S,
        ASSUME TRUE
        PROVE TRUE
    PROVE TRUE
PROOF
<1>1. TRUE
    OBVIOUS
<1> SUFFICES TRUE
<1> TAKE r \in S, q \in S
<1> QED


(* A multi-line comment.

*)

(*
(* A nested multi-line comment.
*)
*)
========================
''')


def test_expr_parser():
    """Testing of expression parser."""
    lexer = _lex.Lexer()
    parser = _lr.ExprParser()
    for expr in expr_tests:
        tokens = list(lexer.parse(expr))
        print(tokens)
        print(' ')
        print(expr)
        r = parser.parse(expr)
        assert r is not None
        print(r)


def test_module_parser():
    """Testing of module parser."""
    parser = _lr.Parser()
    for module in module_tests:
        print(module)
        r = parser.parse(module)
        assert r is not None


def test_parser_stacks_cleared():
    """Ensure parser initializes its state."""
    parser = _lr.Parser()
    # input without errors
    text = '---- MODULE name ---- A == 1 ===='
    module = parser.parse(text)
    assert module is not None, module
    assert module.symbol == 'module', module
    assert not parser._parser.grammar.scopes_stack, (
        parser._parser.grammar.scopes_stack)
    assert not parser._parser.grammar.columns_stack, (
        parser._parser.grammar.columns_stack)
    # syntax error in input
    text = '---- MODULE name ---- A == LET x == 1 IN ===='
    with pytest.raises(ValueError):
        parser.parse(text)
        # the stacks are nonempty due to the error,
        # but will be cleared when `parse()` is
        # called again
    # again input without errors
    text = '''---- MODULE name ---- A ==
        LET x == 1 IN x ===='''
    module = parser.parse(text)
    assert module is not None, module
    assert module.symbol == 'module', module
    assert not parser._parser.grammar.scopes_stack, (
        parser._parser.grammar.scopes_stack)
    assert not parser._parser.grammar.columns_stack, (
        parser._parser.grammar.columns_stack)


def test_parser_tokens_end():
    # Ensure parser raises `ValueError` when
    # it reaches the end of input before done.
    text = '---- MODULE test ----'
    with pytest.raises(ValueError):
        _lr.parse(text)
    # input without errors
    module = _lr.parse('---- MODULE other ---- ====')
    assert module is not None, module
    assert module.symbol == 'module', module
    assert module.name == 'other', module


if __name__ == '__main__':
    test_check_lexprec()
    test_expr_parser()
    test_module_parser()
