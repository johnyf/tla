"""Parser testing."""
import pytest
import tla._ast as _ast
import tla._langdef
import tla._lre as _lr
import tla._pprint as _pp
import tla._utils


def test_set_of_tuples():
    text = r'''
        A \X B \X C
        '''
    expr = _lr.parse_expr(text)
    assert expr.symbol.name == 'OPERATOR_APPLICATION', (
        expr.symbol)
    assert expr.operator == '\\X', expr.operator
    assert len(expr.arguments) == 3, expr.arguments
    arg_a, arg_b, arg_c = expr.arguments
    assert_operator_name(arg_a, 'A')
    assert_operator_name(arg_b, 'B')
    assert_operator_name(arg_c, 'C')
    # print
    text = _pp.pformat_ast(expr)
    print(text)


def test_set_theory_operators():
    text = r'''
        A \cap B \cup C
        '''
    expr = _lr.parse_expr(text)
    assert expr.symbol.name == 'OPERATOR_APPLICATION', (
        expr.symbol)
    assert expr.operator == '\\cup', expr.operator
    assert len(expr.arguments) == 2, len(expr.arguments)
    ab, arg_c = expr.arguments
    # expression `C`
    assert_operator_name(arg_c, 'C')
    # expression `A \cap B`
    assert ab.symbol.name == 'OPERATOR_APPLICATION', (
        ab.symbol)
    assert ab.operator == '\\cap', ab.operator
    assert len(ab.arguments) == 2, len(ab.arguments)
    arg_a, arg_b = ab.arguments
    assert_operator_name(arg_a, 'A')
    assert_operator_name(arg_b, 'B')
    # print
    text = _pp.pformat_ast(expr)
    print(text)


def test_keyword_unary_operators():
    text = r'''
        ---- MODULE unary_operators ----
        domain == DOMAIN f
        enabled == ENABLED action
        subsets == SUBSET S
        unchanged == UNCHANGED vars
        set_union == UNION R
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'unary_operators', module.name
    assert len(module.units) == 5, module.units
    # DOMAIN
    domain_def = module.units[0]
    assert_op_def(domain_def, 'domain')
    expr = domain_def.definiens
    assert_unary_op_app(expr, 'DOMAIN')
    arg, = expr.arguments
    assert_operator_name(arg, 'f')
    # ENABLED
    enabled_def = module.units[1]
    assert_op_def(enabled_def, 'enabled')
    expr = enabled_def.definiens
    assert_unary_op_app(expr, 'ENABLED')
    arg, = expr.arguments
    assert_operator_name(arg, 'action')
    # SUBSET
    subset_def = module.units[2]
    assert_op_def(subset_def, 'subsets')
    expr = subset_def.definiens
    assert_unary_op_app(expr, 'SUBSET')
    arg, = expr.arguments
    assert_operator_name(arg, 'S')
    # UNCHANGED
    unchanged_def = module.units[3]
    assert_op_def(unchanged_def, 'unchanged')
    expr = unchanged_def.definiens
    assert_unary_op_app(expr, 'UNCHANGED')
    arg, = expr.arguments
    assert_operator_name(arg, 'vars')
    # UNION
    set_union_def = module.units[4]
    assert_op_def(set_union_def, 'set_union')
    expr = set_union_def.definiens
    assert_unary_op_app(expr, 'UNION')
    arg, = expr.arguments
    assert_operator_name(arg, 'R')
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_unary_minus_as_argument():
    text = r'''
        op(-.)
        '''
    expr = _lr.parse_expr(text)
    assert_unary_op_app(expr, 'op')
    arg, = expr.arguments
    assert arg.symbol.name == 'OPERATOR_APPLICATION', (
        arg.symbol)
    assert arg.operator == '-.', arg.operator
    assert arg.arguments is None, arg.arguments
    # print
    text = _pp.pformat_ast(expr)
    print(text)


def test_unary_minus_as_operator():
    text = r'''
        - 1
        '''
    expr = _lr.parse_expr(text)
    assert expr.symbol.name == 'OPERATOR_APPLICATION', (
        expr.symbol)
    assert expr.operator == '-', expr.operator
    assert len(expr.arguments) == 1, len(expr.arguments)
    arg, = expr.arguments
    assert arg.symbol.name == 'INTEGRAL_NUMERAL', (
        arg.symbol)
    assert arg.value == '1', arg.value
    # print
    text = _pp.pformat_ast(expr)
    print(text)


def test_set_slice_operator():
    text = r'''
        {x \in S: y \in R}
        '''
    expr = _lr.parse_expr(text)
    assert expr.symbol == 'set_slice', expr.symbol
    x_in_s = expr.declaration
    y_in_r = expr.predicate
    # declarations
    assert_binary_op_app(x_in_s, r'\in')
    args = x_in_s.arguments
    x, s = args
    assert_operator_name(x, 'x')
    assert_operator_name(s, 'S')
    # predicate
    assert_binary_op_app(y_in_r, r'\in')
    args = y_in_r.arguments
    y, r = args
    assert_operator_name(y, 'y')
    assert_operator_name(r, 'R')


def test_set_comprehension_operator():
    parser = _lr.ExprParser()
    text = r'''
        {x: x \in R}
        '''
    expr = parser.parse(text)
    assert expr.symbol.name == 'SET_COMPREHENSION', (
        expr.symbol)
    assert_operator_name(expr.item, 'x')
    assert len(expr.declarations)
    x_in_r = expr.declarations[0]
    # declarations
    assert_binary_op_app(x_in_r, r'\in')
    args = x_in_r.arguments
    x, r = args
    assert_operator_name(x, 'x')
    assert_operator_name(r, 'R')


def test_always_eventually():
    text = r'''
        []<> P
        '''
    expr = _lr.parse_expr(text)
    assert expr.symbol.name == 'OPERATOR_APPLICATION', (
        expr.symbol)
    assert expr.operator == '[]', expr.operator
    assert len(expr.arguments) == 1, len(expr.arguments)
    arg, = expr.arguments
    assert arg.symbol.name == 'OPERATOR_APPLICATION', (
        arg.symbol)
    assert arg.operator == '<>', expr.operator
    assert len(arg.arguments) == 1, len(expr.arguments)
    p_op, = arg.arguments
    assert p_op.symbol.name == 'OPERATOR_APPLICATION', (
        p_op.symbol)
    assert p_op.operator == 'P', p_op.operator
    assert p_op.arguments is None, p_op.arguments
    # print
    text = _pp.pformat_ast(expr)
    print(text)


def test_eventually_always():
    text = r'''
        <>[] P
        '''
    expr = _lr.parse_expr(text)
    assert expr.symbol.name == 'OPERATOR_APPLICATION', (
        expr.symbol)
    assert expr.operator == '<>', expr.operator
    assert len(expr.arguments) == 1, len(expr.arguments)
    arg, = expr.arguments
    assert arg.symbol.name == 'OPERATOR_APPLICATION', (
        arg.symbol)
    assert arg.operator == '[]', expr.operator
    assert len(arg.arguments) == 1, len(expr.arguments)
    p_op, = arg.arguments
    assert p_op.symbol.name == 'OPERATOR_APPLICATION', (
        p_op.symbol)
    assert p_op.operator == 'P', p_op.operator
    assert p_op.arguments is None, p_op.arguments
    # print
    text = _pp.pformat_ast(expr)
    print(text)


def test_unbounded_declarations():
    #
    # constant quantification `\A` and `\E`
    text = r'''
        ---- MODULE test ----
        A == \E x, y:  x = y
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    expr = op_def.definiens
    assert_quantification(expr, r'\E', 2)
    # x, y
    x, y = expr.declarations
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # `x = y`
    pred = expr.predicate
    assert_binary_op_app(pred, '=')
    x, y = pred.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    text = r'''
        ---- MODULE test ----
        A == \A x, y, z:  x = y
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    expr = op_def.definiens
    assert_quantification(expr, r'\A', 3)
    # x, y, z
    x, y, z = expr.declarations
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert_operator_name(z, 'z')
    # `x = y`
    pred = expr.predicate
    assert_binary_op_app(pred, '=')
    x, y = pred.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    text = r'''
        ---- MODULE test ----
        A == \A <<x, y, z>>:  x = y
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    #
    # temporal quantification
    text = r'''
        ---- MODULE test ----
        P == \EE x, y:  [](x = y)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'P')
    expr = op_def.definiens
    assert expr.symbol == 'temporal_quantification', expr
    assert expr.quantifier == r'\EE', expr.quantifier
    assert expr.declarations is not None, expr
    assert len(expr.declarations) == 2, expr.declarations
    assert expr.predicate is not None, expr
    # x, y
    x, y = expr.declarations
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # `[](x = y)`
    pred = expr.predicate
    assert_unary_op_app(pred, '[]')
    ps, = pred.arguments
    assert ps.symbol == 'parentheses', ps
    assert ps.expression is not None, ps
    eq = ps.expression
    assert_binary_op_app(eq, '=')
    x, y = eq.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    #
    # `CHOOSE`
    text = '''
        ---- MODULE test ----
        A == CHOOSE x:  x # 0
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    expr = op_def.definiens
    assert expr.symbol == 'choose', expr
    assert expr.declaration is not None, expr
    assert expr.predicate is not None, expr
    decl = expr.declaration
    assert_operator_name(decl, 'x')
    pred = expr.predicate
    assert_binary_op_app(pred, '#')
    x, zero = pred.arguments
    assert_operator_name(x, 'x')
    assert_integer_numeral(zero, '0')
    # error: too many declarations
    text = '''
        ---- MODULE test ----
        A == CHOOSE x, y:  x # y
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    # tuple declaration in `CHOOSE`
    text = '''
        ---- MODULE test ----
        A == CHOOSE <<x, y>>:  x > y
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    expr = op_def.definiens
    assert expr.symbol == 'choose', expr
    assert expr.predicate is not None, expr
    decl = expr.declaration
    assert_tuple(decl, 2)
    x, y = decl.items
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    pred = expr.predicate
    assert_binary_op_app(pred, '>')
    x, y = pred.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    #
    # `PICK`
    text = r'''
        ---- MODULE test ----
        THEOREM TRUE
        <1>1. PICK x, y, z:  x = y /\ y = z
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    assert_proof_step(step1, '<1>1.')
    pick = step1.main
    assert pick.symbol == 'pick', pick
    assert pick.declarations is not None, pick
    assert len(pick.declarations) == 3, pick.declarations
    assert pick.predicate is not None, pick
    x, y, z = pick.declarations
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert_operator_name(z, 'z')
    pred = pick.predicate
    assert_binary_op_app(pred, '/\\')
    xy, yz = pred.arguments
    assert_binary_op_app(xy, '=')
    assert_binary_op_app(yz, '=')
    x, y = xy.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    y, z = yz.arguments
    assert_operator_name(y, 'y')
    assert_operator_name(z, 'z')
    #
    # `TAKE`
    text = '''
        ---- MODULE test ----
        THEOREM TRUE
        <1>2. TAKE x, y, z
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is not None, thm
    assert_boolean_literal(thm.goal, 'TRUE')
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    assert_proof_step(step1, '<1>2.')
    take = step1.main
    assert take.symbol == 'take', take
    assert take.declarations is not None, take
    assert len(take.declarations) == 3, take.declarations
    x, y, z = take.declarations
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert_operator_name(z, 'z')
    #
    # record with one field (not a function)
    text = '''
        ---- MODULE test ----
        f == [x |-> x]
        ====
        '''
        # NOTE: `[x, y |-> x]` does get parsed.
        # It requires a separate check after
        # parsing, to ensure bounds are present.
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    f_def, = module.units
    assert_op_def(f_def, 'f')
    record = f_def.definiens
    assert record.symbol == 'record', record
    assert record.key_values is not None, record.key_values
    kv = record.key_values
    assert len(kv) == 1, kv
    pair, = kv
    assert len(pair) == 2, pair
    field_name, field_value = pair
    assert field_name == 'x', field_name
    assert_operator_name(field_value, 'x')
    #
    # function (error)
    text = '''
        ---- MODULE test ----
        f == [<<x, y>> |-> x]
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    #
    # set slice (error)
    text = '''
        ---- MODULE test ----
        f == {x:  x > 1}
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    #
    # set comprehension (error)
    text = '''
        ---- MODULE test ----
        f == {<<x, y>>:  x}
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)


def test_bounded_declarations():
    #
    # constant quantification
    text = r'''
        ---- MODULE test ----
        A == \E x, y \in S, z \in R:
                x + y = z
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    expr = op_def.definiens
    assert_quantification(expr, r'\E', 3)
    # `x, y \in S, z \in R`
    x, y_in_s, z_in_r = expr.declarations
    assert_operator_name(x, 'x')
    assert_binary_op_app(y_in_s, r'\in')
    y, s = y_in_s.arguments
    assert_operator_name(y, 'y')
    assert_operator_name(s, 'S')
    assert_binary_op_app(z_in_r, r'\in')
    z, r = z_in_r.arguments
    assert_operator_name(z, 'z')
    assert_operator_name(r, 'R')
    # `x + y = z`
    pred = expr.predicate
    assert_binary_op_app(pred, '=')
    x_plus_y, z = pred.arguments
    assert_operator_name(z, 'z')
    assert_binary_op_app(x_plus_y, '+')
    x, y = x_plus_y.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    text = r'''
        ---- MODULE test ----
        A == \A x \in S, <<z, y>> \in R:
                x + y = z
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    expr = op_def.definiens
    assert_quantification(expr, r'\A', 2)
    x_in_s, zy_in_r = expr.declarations
    # `x \in S`
    assert_binary_op_app(x_in_s, r'\in')
    x, s = x_in_s.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(s, 'S')
    # `<<z, y>> \in R`
    assert_binary_op_app(zy_in_r, r'\in')
    zy, r = zy_in_r.arguments
    assert_operator_name(r, 'R')
    assert_tuple(zy, 2)
    z, y = zy.items
    assert_operator_name(z, 'z')
    assert_operator_name(y, 'y')
    #
    # `CHOOSE`
    text = r'''
        ---- MODULE test ----
        A == CHOOSE <<x, y>> \in S:
                x = y
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    choose = op_def.definiens
    assert_choose(choose)
    # `<<x, y>> \in S`
    xy_in_s = choose.declaration
    assert_binary_op_app(xy_in_s, r'\in')
    xy, s = xy_in_s.arguments
    assert_operator_name(s, 'S')
    assert_tuple(xy, 2)
    x, y = xy.items
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # `x = y`
    pred = choose.predicate
    assert_binary_op_app(pred, '=')
    x, y = pred.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    #
    # `PICK`
    text = r'''
        ---- MODULE test ----
        LEMMA x = y
        <1>1. PICK z \in S, q \in T:
                    q => (z = c)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'LEMMA', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    # `x = y`
    goal = thm.goal
    assert_binary_op_app(goal, '=')
    x, y = goal.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    assert step1.symbol == 'proof_step', step1
    assert step1.name == '<1>1.', step1.name
    assert step1.proof_keyword is None, step1.proof_keyword
    assert step1.proof is None, step1.proof
    assert step1.main is not None, step1
    pick = step1.main
    assert pick.symbol == 'pick', pick
    assert pick.declarations is not None, pick
    assert len(pick.declarations) == 2, pick.declarations
    assert pick.predicate is not None, pick
    # `z \in S, q \in T`
    z_in_s, q_in_t = pick.declarations
    assert_binary_op_app(z_in_s, r'\in')
    assert_binary_op_app(q_in_t, r'\in')
    z, s = z_in_s.arguments
    assert_operator_name(z, 'z')
    assert_operator_name(s, 'S')
    q, t = q_in_t.arguments
    assert_operator_name(q, 'q')
    assert_operator_name(t, 'T')
    # `q => (z = c)`
    pred = pick.predicate
    assert_binary_op_app(pred, '=>')
    q, ps = pred.arguments
    assert_operator_name(q, 'q')
    assert ps.symbol == 'parentheses', ps
    z_eq_c = ps.expression
    assert_binary_op_app(z_eq_c, '=')
    z, c = z_eq_c.arguments
    assert_operator_name(z, 'z')
    assert_operator_name(c, 'c')
    text = r'''
        ---- MODULE test ----
        THEOREM x = y
        <1>1. PICK <<x, y>> \in A \X B:
                    x \in P /\ y > 2
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    # `x = y`
    x_eq_y = thm.goal
    assert_binary_op_app(x_eq_y, '=')
    x, y = x_eq_y.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # proof
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    assert_proof_step(step1, '<1>1.')
    pick = step1.main
    assert pick.symbol == 'pick', pick
    assert pick.declarations is not None, pick
    assert len(pick.declarations) == 1, pick.declarations
    assert pick.predicate is not None, pick
    # `<<x, y>> \in A \X B`
    xy_in_ab, = pick.declarations
    assert_binary_op_app(xy_in_ab, r'\in')
    xy, ab = xy_in_ab.arguments
    # `<<x, y>>`
    assert_tuple(xy, 2)
    x, y = xy.items
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # `A \X B`
    assert ab.symbol == 'operator_application', ab
    assert ab.operator == r'\X', ab.operator
    assert ab.arguments is not None, ab
    assert len(ab.arguments) == 2, ab.arguments
    a, b = ab.arguments
    assert_operator_name(a, 'A')
    assert_operator_name(b, 'B')
    # `x \in P /\ y > 2`
    pred = pick.predicate
    assert_binary_op_app(pred, '/\\')
    x_in_p, y_gt_2 = pred.arguments
    assert_binary_op_app(x_in_p, r'\in')
    x, p = x_in_p.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(p, 'P')
    assert_binary_op_app(y_gt_2, '>')
    y, two = y_gt_2.arguments
    assert_operator_name(y, 'y')
    assert_integer_numeral(two, '2')
    #
    # `TAKE`
    text = r'''
        ---- MODULE test ----
        THEOREM x \sim y
        <1>step. TAKE z \in S
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    # `x ~ y`
    goal = thm.goal
    assert_binary_op_app(goal, r'\sim')
    x, y = goal.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # proof
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    assert_proof_step(step1, '<1>step.')
    take = step1.main
    assert take.symbol == 'take', take
    assert take.declarations is not None, take
    assert len(take.declarations) == 1, take.declarations
    z_in_s, = take.declarations
    assert_binary_op_app(z_in_s, r'\in')
    assert_operator_name(z, 'z')
    assert_operator_name(s, 'S')
    #
    # function constructor
    text = r'''
        ---- MODULE test ----
        A == [x, y \in S |-> x + y]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    expr = op_def.definiens
    assert expr.symbol == 'function', expr
    assert expr.declaration is not None, expr
    assert expr.value is not None, expr
    # `x, y \in S`
    decls = expr.declaration
    assert len(decls) == 2, decls
    x, y_in_s = decls
    assert_operator_name(x, 'x')
    assert_binary_op_app(y_in_s, r'\in')
    y, s = y_in_s.arguments
    assert_operator_name(y, 'y')
    assert_operator_name(s, 'S')
    # `x + y`
    x_plus_y = expr.value
    assert_binary_op_app(x_plus_y, '+')
    x, y = x_plus_y.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    #
    # set slice
    text = r'''
        ---- MODULE test ----
        A == {x \in S:  x @@ 5}
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    expr = op_def.definiens
    assert expr.symbol == 'set_slice', expr
    assert expr.declaration is not None, expr
    assert expr.predicate is not None, expr
    # `x \in S`
    decl = expr.declaration
    assert_binary_op_app(decl, r'\in')
    x, s = decl.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(s, 'S')
    # `x @@ 5`
    pred = expr.predicate
    assert_binary_op_app(pred, '@@')
    x, five = pred.arguments
    assert_operator_name(x, 'x')
    assert_integer_numeral(five, '5')
    #
    # set comprehension
    text = r'''
        ---- MODULE test ----
        A == {<<x, y>>: x \in R, y \in S}
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    expr = op_def.definiens
    assert expr.symbol == 'set_comprehension', expr
    assert expr.item is not None, expr
    assert expr.declarations is not None, expr
    assert len(expr.declarations) == 2, expr.declarations
    # `<<x, y>>`
    xy_tuple = expr.item
    assert_tuple(xy_tuple, 2)
    x, y = xy_tuple.items
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # `x \in R, y \in S`
    x_in_r, y_in_s = expr.declarations
    # `x \in R`
    assert_binary_op_app(x_in_r, r'\in')
    x, r = x_in_r.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(r, 'R')
    # `y \in S`
    assert_binary_op_app(y_in_s, r'\in')
    y, s = y_in_s.arguments
    assert_operator_name(y, 'y')
    assert_operator_name(s, 'S')


def test_switching_infix_after_mapsto():
    text = r'''
        ---- MODULE mapsto_in_record ----
        A == [r |-> +(1, 2)]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'mapsto_in_record')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    record = op_def.definiens
    assert record.symbol == 'record', record
    assert record.key_values is not None, record
    assert len(record.key_values) == 1, record.key_values
    pair, = record.key_values
    assert len(pair) == 2, pair
    r, plus = pair
    assert r == 'r', r
    assert_binary_op_app(plus, '+')
    one, two = plus.arguments
    assert_integer_numeral(one, '1')
    assert_integer_numeral(two, '2')
    text = r'''
        ---- MODULE mapsto_in_function ----
        A == [x \in S |-> >=(x, y)]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'mapsto_in_function')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    func = op_def.definiens
    assert func.symbol == 'function', func
    assert func.declaration is not None, func
    assert len(func.declaration) == 1, func.declaration
    assert func.value is not None, func
    # declaration
    decl, = func.declaration
    assert_binary_op_app(decl, r'\in')
    x, s = decl.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(s, 'S')
    # expression `>=(x, y)`
    expr = func.value
    assert_binary_op_app(expr, '>=')
    assert expr.nonfix is True, expr.nonfix
    x, y = expr.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')


def test_switching_infix_ops_and_steps():
    text = r'''
        ---- MODULE test ----
        THEOREM TRUE
        <1>1. TRUE
            BY DEF -.
        <1>2. -<1>1
            BY DEF +
        <1>3. 1 + <1>2
        <1>4. x = <1>3
        <1>5. QED
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert module.units is not None, module.units
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', thm
    assert thm.name is None, thm.name
    assert thm.proof is not None, thm
    assert thm.goal is not None, thm
    assert_boolean_literal(thm.goal, 'TRUE')
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 5, proof.steps
    step_1, step_2, step_3, step_4, qed = proof.steps
    #
    # step `<1>1`
    assert step_1.symbol == 'proof_step', step_1.symbol
    assert step_1.proof_keyword is None, (
        step_11.proof_keyword)
    assert step_1.name == '<1>1.', step_1.name
    main = step_1.main
    assert_boolean_literal(main, 'TRUE')
    assert step_1.proof is not None, step_1.proof
    proof = step_1.proof
    # proof of step `<1>1`
    assert proof.symbol == 'by', proof
    assert proof.only is False, proof.only
    assert proof.facts is None, proof.facts
    assert len(proof.names) == 1, proof.names
    opname, = proof.names
    assert_operator_name(opname, '-.')
    #
    # step `<1>2`
    assert step_2.symbol == 'proof_step', step_2.symbol
    assert step_2.proof_keyword is None, (
        step_11.proof_keyword)
    assert step_2.name == '<1>2.', step_2.name
    main = step_2.main
    assert_unary_op_app(main, '-')
    arg, = main.arguments
    assert_operator_name(arg, '<1>1')
    assert step_2.proof is not None, step_2.proof
    proof = step_2.proof
    # proof of step `<1>2`
    assert proof.symbol == 'by', proof
    assert proof.only is False, proof.only
    assert proof.facts is None, proof.facts
    assert len(proof.names) == 1, proof.names
    opname, = proof.names
    assert_operator_name(opname, '+')
    #
    # step `<1>3`
    assert step_3.symbol == 'proof_step', step_3.symbol
    assert step_3.proof_keyword is None, (
        step_3.proof_keyword)
    assert step_3.name == '<1>3.', step_3.name
    main = step_3.main
    assert_binary_op_app(main, '+')
    one, step_number = main.arguments
    assert_integer_numeral(one, '1')
    assert_operator_name(step_number, '<1>2')
    assert step_3.proof is None, step_3.proof
    #
    # step `<1>4`
    assert step_4.symbol == 'proof_step', step_4.symbol
    assert step_4.proof_keyword is None, (
        step_4.proof_keyword)
    assert step_4.name == '<1>4.', step_4.name
    main = step_4.main
    assert_binary_op_app(main, '=')
    x, step_number = main.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(step_number, '<1>3')
    assert step_4.proof is None, step_4.proof


def test_infix_in_def_of_leaf_proof():
    text = r'''
        ---- MODULE infix_then_step ----
        THEOREM TRUE
        PROOF
        <1>1. TRUE
            BY DEF ++
        <1>2. TRUE
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol == 'module', module
    assert module.name == 'infix_then_step', module.name
    assert len(module.units) == 1, module.units
    theorem, = module.units
    assert theorem.symbol == 'theorem', theorem
    assert theorem.name is None, theorem.name
    assert theorem.theorem_keyword == 'THEOREM', (
        theorem.theorem_keyword)
    goal = theorem.goal
    proof = theorem.proof
    # theorem goal `TRUE`
    assert_boolean_literal(goal, 'TRUE')
    # proof of theorem
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is True, proof.proof_keyword
    assert len(proof.steps) == 2, len(proof.steps)
    step_11, step_12 = proof.steps
    # step `<1>1`
    assert step_11.symbol == 'proof_step', step_11.symbol
    assert step_11.proof_keyword is None, (
        step_11.proof_keyword)
    assert step_11.name == '<1>1.', step_11.name
    main = step_11.main
    assert_boolean_literal(main, 'TRUE')
    assert step_11.proof is not None, step_11.proof
    proof = step_11.proof
    # proof of step `<1>1`
    assert proof.symbol == 'by', proof
    assert proof.only is False, proof.only
    assert proof.facts is None, proof.facts
    assert len(proof.names) == 1, proof.names
    # identifier of operator `+`
    plus, = proof.names
    assert plus.symbol == 'operator_application', plus
    assert plus.operator == '++', plus.operator
    assert plus.arguments is None, plus.arguments
    # step `<1>2`
    assert step_12.symbol == 'proof_step', step_12.symbol
    assert step_12.proof_keyword is None, (
        step_12.proof_keyword)
    assert step_12.name == '<1>2.', step_12.name
    main = step_12.main
    assert_boolean_literal(main, 'TRUE')
    assert step_12.proof is None, step_12.proof
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_identifiers_in_leaf_proofs():
    text = r'''
        ---- MODULE leaf_proof ----
        COROLLARY ASSUME TRUE PROVE TRUE
        <1>2. M!Op
            BY ONLY <1>1 DEF M!Op
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'leaf_proof', module.name
    assert len(module.units) == 1, module.units
    theorem, = module.units
    assert theorem.symbol.name == 'THEOREM', (
        theorem.symbol)
    assert theorem.name is None, theorem.name
    assert theorem.theorem_keyword == 'COROLLARY', (
        theorem.theorem_keyword)
    goal = theorem.goal
    proof = theorem.proof
    # theorem goal `TRUE`
    assert goal.symbol.name == 'SEQUENT', goal.symbol
    asms = goal.assume
    assert len(asms) == 1, len(asms)
    assume, = asms
    assert_boolean_literal(assume, 'TRUE')
    assert_boolean_literal(goal.prove, 'TRUE')
    # proof
    assert proof.symbol.name == 'PROOF', proof.symbol
    assert proof.proof_keyword is None, proof.proof_keyword
    assert len(proof.steps) == 1, len(proof.steps)
    step_12, = proof.steps
    # step `<1>2`
    assert step_12.symbol.name == 'PROOF_STEP', (
        step_12.symbol)
    assert step_12.proof_keyword is None, (
        step_12.proof_keyword)
    assert step_12.name == '<1>2.', step_12.name
    main = step_12.main
    proof = step_12.proof
    # `M!Op`
    assert (main.symbol.name ==
        'SUBEXPRESSION_REFERENCE'), main.symbol
    assert len(main.items) == 2, len(main.items)
    assert_operator_name(main.items[0], 'M')
    assert main.items[1] == 'Op', main.items
    # `BY <1>1 DEF M!Op`
    assert proof.symbol.name == 'BY', proof.symbol
    assert proof.only is True, proof.only
    facts = proof.facts
    names = proof.names
    assert len(facts) == 1, facts
    assert len(names) == 1, names
    # `<1>1`
    step_11, = facts
    assert (step_11.symbol.name ==
        'OPERATOR_APPLICATION'), step_11.symbol
    assert step_11.operator == '<1>1', step_11.operator
    assert step_11.arguments is None, step_11.arguments
    # `DEF M!Op`
    name, = names
    assert (name.symbol.name ==
        'SUBEXPRESSION_REFERENCE'), name.symbol
    assert len(name.items) == 2, len(name.items)
    assert_operator_name(name.items[0], 'M')
    assert name.items[1] == 'Op', name.items
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_theorem_with_proof_keyword_only():
    text = '''
        ---- MODULE test ----
        THEOREM TRUE
        PROOF
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem.keyword)
    assert thm.name is None, thm.name
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is True, proof.proof_keyword
    assert proof.steps is None, proof.steps


def test_proof_with_outer_level_not_1():
    text = '''
        ---- MODULE test ----
        THEOREM TRUE
        <8>1. TRUE
        <8> QED
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem.keyword)
    assert thm.name is None, thm.name
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 2, proof.steps
    step, qed = proof.steps
    # step `<8>1`
    assert step.symbol == 'proof_step', step
    assert step.name == '<8>1.', step.name
    assert_boolean_literal(step.main, 'TRUE')
    assert step.proof is None, step.proof
    assert step.proof_keyword is None, step.proof_keyword
    # step `<8> QED`
    assert qed.symbol == 'proof_step', step
    assert qed.name == '<8>', qed.name
    assert qed.main == 'QED', qed.main
    assert qed.proof is None, qed.proof
    assert qed.proof_keyword is None, qed.proof_keyword
    text = '''
        ---- MODULE test ----
        THEOREM TRUE
        <0>1. TRUE
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem.keyword)
    assert thm.name is None, thm.name
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step, = proof.steps
    assert step.symbol == 'proof_step', step
    assert step.name == '<0>1.', step.name
    assert_boolean_literal(step.main, 'TRUE')
    assert step.proof is None, step.proof
    assert step.proof_keyword is None, step.proof_keyword
    text = '''
        ---- MODULE test ----
        THEOREM TRUE
        <-5> TRUE
        ====
        '''
        # the `<-5>` is lexed as `LARROW` etc
    with pytest.raises(ValueError):
        _lr.parse(text)


def test_suffices_proof_step():
    text = r'''
        ---- MODULE suffices_pf_step ----
        THEOREM TRUE
        <1>1. SUFFICES \A n \in Nat:  n < n + 1
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'suffices_pf_step', module.name
    assert len(module.units) == 1, module.units
    theorem, = module.units
    assert theorem.symbol.name == 'THEOREM', (
        theorem.symbol)
    assert theorem.name is None, theorem.name
    assert theorem.theorem_keyword == 'THEOREM', (
        theorem.theorem_keyword)
    expr = theorem.goal
    proof = theorem.proof
    # `TRUE`
    assert_boolean_literal(expr, 'TRUE')
    # proof
    assert proof.symbol.name == 'PROOF', proof.symbol
    assert proof.proof_keyword is None, proof.proof_keyword
    assert len(proof.steps) == 1, proof.steps
    step_11, = proof.steps
    # step `<1>1`
    assert step_11.symbol.name == 'PROOF_STEP', (
        step_11.symbol)
    assert step_11.name == '<1>1.', step_11.name
    assert step_11.proof is None, step_11.proof
    assert step_11.proof_keyword is None, (
        step_11.proof_keyword)
    main = step_11.main
    # `SUFFICES \A n \in Nat:  n < n + 1`
    assert main.symbol.name == 'SUFFICES', main.symbol
    expr = main.predicate
    # `\A n \in Nat:  n < n + 1`
    assert expr.symbol.name == 'QUANTIFICATION', (
        expr.symbol)
    assert expr.quantifier == '\\A', expr.quantifier
    assert len(expr.declarations) == 1, expr.declarations
    decl, = expr.declarations
    pred = expr.predicate
    # `n \in Nat`
    assert_binary_op_app(decl, '\\in')
    n, nat = decl.arguments
    assert_operator_name(n, 'n')
    assert_operator_name(nat, 'Nat')
    # `n < n + 1`
    assert_binary_op_app(pred, '<')
    n, n1 = pred.arguments
    assert_operator_name(n, 'n')
    assert_binary_op_app(n1, '+')
    n, one = n1.arguments
    assert_operator_name(n, 'n')
    assert one.symbol.name == 'INTEGRAL_NUMERAL', one
    assert one.value == '1', one.value
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_assume_prove_proof_step():
    text = r'''
        ---- MODULE test ----
        THEOREM x @@ y
        <1>1. ASSUME NEW z \in S
              PROVE z > x
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    # `x @@ y`
    goal = thm.goal
    assert_binary_op_app(goal, '@@')
    x, y = goal.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    assert_proof_step(step1, '<1>1.')
    main = step1.main
    assert main.symbol == 'sequent', main
    assert main.assume is not None, main
    assert main.prove is not None, main
    assert len(main.assume) == 1
    asm, = main.assume
    assert asm.symbol == 'operator_declaration', asm
    assert asm.name is not None, asm
    assert asm.level is None, asm.level
    assert asm.new_keyword is True, asm.new_keyword
    z_in_s = asm.name
    assert_binary_op_app(z_in_s, r'\in')
    z, s = z_in_s.arguments
    assert_operator_name(z, 'z')
    assert_operator_name(s, 'S')
    prove = main.prove
    assert_binary_op_app(prove, '>')
    z, x = prove.arguments
    assert_operator_name(z, 'z')
    assert_operator_name(x, 'x')


def test_have_proof_step():
    text = r'''
        ---- MODULE test ----
        THEOREM x > 1
        <1>1. HAVE z > x
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    # `x > 1`
    goal = thm.goal
    assert_binary_op_app(goal, '>')
    x, one = goal.arguments
    assert_operator_name(x, 'x')
    assert_integer_numeral(one, '1')
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    assert_proof_step(step1, '<1>1.')
    main = step1.main
    assert main.symbol == 'have', main
    z_gt_x = main.expression
    assert_binary_op_app(z_gt_x, '>')
    z, x = z_gt_x.arguments
    assert_operator_name(z, 'z')
    assert_operator_name(x, 'x')


def test_witness_proof_step():
    text = r'''
        ---- MODULE test ----
        THEOREM x ## y
        <1>1. WITNESS x \in S
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    # `x ## y`
    goal = thm.goal
    assert_binary_op_app(goal, '##')
    x, y = goal.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    assert_proof_step(step1, '<1>1.')
    main = step1.main
    assert main.symbol == 'quantifier_witness', main
    assert main.expressions is not None, main
    assert len(main.expressions) == 1, main.expressions
    x_in_s, = main.expressions
    assert_binary_op_app(x_in_s, r'\in')
    x, s = x_in_s.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(s, 'S')


def test_use_proof_step():
    text = r'''
        ---- MODULE test ----
        THEOREM x @@ y
        <1>1. USE x > 1, y = x DEF Op
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    # `x @@ y`
    goal = thm.goal
    assert_binary_op_app(goal, '@@')
    x, y = goal.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    assert_proof_step(step1, '<1>1.')
    main = step1.main
    assert main.symbol == 'use', main
    assert main.facts is not None, main
    assert len(main.facts) == 2, main.facts
    assert main.names is not None, main
    assert len(main.names) == 1, main.names
    assert main.only is False, main.only
    assert main.keyword == 'DEF', main.keyword
    x_gt_one, y_eq_x = main.facts
    # `x > 1`
    assert_binary_op_app(x_gt_one, '>')
    x, one = x_gt_one.arguments
    assert_operator_name(x, 'x')
    assert_integer_numeral(one, '1')
    # `y = x`
    assert_binary_op_app(y_eq_x, '=')
    y, x = y_eq_x.arguments
    assert_operator_name(y, 'y')
    assert_operator_name(x, 'x')
    # `Op`
    op_name, = main.names
    assert_operator_name(op_name, 'Op')


def test_hide_proof_step():
    text = r'''
        ---- MODULE test ----
        THEOREM x @@ y
        <1>1. HIDE DEFS a, b, c
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    # `x @@ y`
    goal = thm.goal
    assert_binary_op_app(goal, '@@')
    x, y = goal.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert thm.proof is not None, thm
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    assert_proof_step(step1, '<1>1.')
    main = step1.main
    assert main.symbol == 'hide', main
    assert main.keyword == 'DEFS', main.keyword
    assert main.facts is None, main.facts
    assert main.names is not None, main
    assert len(main.names) == 3, main.names
    a, b, c = main.names
    assert_operator_name(a, 'a')
    assert_operator_name(b, 'b')
    assert_operator_name(c, 'c')


def test_quantifier_vertical_expression():
    text = r'''
        ---- MODULE quantifier_vexpr ----
        THEOREM \E n \in Nat:  /\ P(n)
                               /\ \A m \in S:  ~ P(m)
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'quantifier_vexpr', module.name
    assert len(module.units) == 1, module.units
    theorem, = module.units
    assert theorem.symbol.name == 'THEOREM', theorem.symbol
    assert theorem.theorem_keyword == 'THEOREM', (
        theorem.theorem_keyword)
    assert theorem.name is None, theorem.name
    assert theorem.proof is None, theorem.proof
    qexpr = theorem.goal
    # `\E n \in Nat: ...`
    assert qexpr.symbol.name == 'QUANTIFICATION', (
        qexpr.symbol)
    assert qexpr.quantifier == '\\E', qexpr.quantifier
    assert len(qexpr.declarations) == 1, qexpr.declarations
    decl, = qexpr.declarations
    vexpr = qexpr.predicate
    # `n \in Nat`
    assert_binary_op_app(decl, '\\in')
    n, nat = decl.arguments
    assert_operator_name(n, 'n')
    assert_operator_name(nat, 'Nat')
    # vertical conjunction
    assert vexpr.symbol.name == 'VERTICAL_LIST', (
        vexpr.symbol)
    assert vexpr.operator == '/\\', vexpr.operator
    assert len(vexpr.arguments) == 2, vexpr.arguments
    item_1, item_2 = vexpr.arguments
    # `/\ P(n)`
    assert item_1.symbol.name == 'VERTICAL_ITEM', (
        item_1.symbol)
    expr = item_1.expression
    assert_unary_op_app(expr, 'P')
    n, = expr.arguments
    assert_operator_name(n, 'n')
    # `/\ \A m \in S:  ~ P(m)`
    assert item_2.symbol.name == 'VERTICAL_ITEM', (
        item_2.symbol)
    qexpr = item_2.expression
    assert qexpr.symbol.name == 'QUANTIFICATION', (
        qexpr.symbol)
    assert qexpr.quantifier == '\\A', qexpr.quantifier
    assert len(qexpr.declarations) == 1, qexpr.declarations
    decl, = qexpr.declarations
    pred = qexpr.predicate
    # `m \in S`
    assert_binary_op_app(decl, '\\in')
    m, nat = decl.arguments
    assert_operator_name(m, 'm')
    assert_operator_name(nat, 'S')
    # `~ P(m)`
    assert_unary_op_app(pred, '~')
    pexpr, = pred.arguments
    assert_unary_op_app(pexpr, 'P')
    m, = pexpr.arguments
    assert_operator_name(m, 'm')
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_pick_proof_step():
    text = r'''
        ---- MODULE test ----
        THEOREM
            TRUE
        <1>1. PICK <<p, q>> \in S:  p = q
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.name is None, thm.name
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.goal is not None, thm
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is not None, thm
    # `PROOF`
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    # `<1>1.`
    assert step1.symbol == 'proof_step', step1
    assert step1.name == '<1>1.', step1.name
    assert step1.proof_keyword is None, step1.proof_keyword
    assert step1.proof is None, step1.proof
    # `PICK`
    pick = step1.main
    assert pick.symbol == 'pick', pick
    assert pick.declarations is not None, pick
    assert pick.predicate is not None, pick
    decls = pick.declarations
    assert len(decls) == 1, decls
    decl, = decls
    assert_binary_op_app(decl, r'\in')
    pq, s_bound = decl.arguments
    # `<<p, q>>`
    assert pq.symbol == 'tuple', pq
    assert pq.items is not None, pq
    assert len(pq.items) == 2
    p, q = pq.items
    assert_operator_name(p, 'p')
    assert_operator_name(q, 'q')
    # `S`
    assert_operator_name(s_bound, 'S')


def test_take_proof_step_bounded_tuples():
    text = r'''
        ---- MODULE test ----
        THEOREM
            TRUE
        <1>2. TAKE
                <<p, q>> \in S,
                <<u, v>> \in Q \X R \X S
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.name is None, thm.name
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.goal is not None, thm
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is not None, thm
    # `PROOF`
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    # `<1>2.`
    assert step1.symbol == 'proof_step', step1
    assert step1.name == '<1>2.', step1.name
    assert step1.proof_keyword is None, step1.proof_keyword
    assert step1.proof is None, step1.proof
    # `TAKE`
    take = step1.main
    assert take.symbol == 'take', take
    assert take.declarations is not None, take.declarations
    decls = take.declarations
    assert len(decls) == 2, decls
    pq_s, uv_qrs = decls
    # `<<p, q>> \in S`
    assert_binary_op_app(pq_s, r'\in')
    pq, s_bound = pq_s.arguments
    assert pq.symbol == 'tuple', pq
    assert pq.items is not None, pq.items
    assert len(pq.items) == 2, pq.items
    p, q = pq.items
    assert_operator_name(p, 'p')
    assert_operator_name(q, 'q')
    assert_operator_name(s_bound, 'S')
    # `<<u, v>> \in R \X S`
    assert_binary_op_app(uv_qrs, r'\in')
    uv, qrs_bound = uv_qrs.arguments
    assert uv.symbol == 'tuple', uv
    assert uv.items is not None, uv.items
    assert len(uv.items) == 2, uv.items
    u, v = uv.items
    assert_operator_name(u, 'u')
    assert_operator_name(v, 'v')
    assert qrs_bound.symbol == 'operator_application', (
        qrs_bound)
    assert qrs_bound.operator == r'\X', qrs_bound.operator
    args = qrs_bound.arguments
    assert args is not None, qrs_bound
    assert len(args) == 3, args
    q, r, s = args
    assert_operator_name(q, 'Q')
    assert_operator_name(r, 'R')
    assert_operator_name(s, 'S')


def test_decl_bslash_in_bound_errors():
    # These errors are for cases where the
    # elements of the bound-expression would
    # anyway be unspecified. These cases are:
    #
    # `y \in z`
    # `y /\ z`
    # `y \/ z`
    # `y = z`
    # `y ~> z`
    # `y -+-> z`
    # `y <=> z`
    # `y => z`
    #
    # These all are builtin operators,
    # so their meaning is known and such
    # that the elements of these sets are
    # not specified by the semantics.
    #
    # So using them as bounds is not expected.
    text = r'''
        ---- MODULE test ----
        A == \E x \in y \in z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    text = r'''
        ---- MODULE test ----
        A == \A x \in y /\ z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    text = r'''
        ---- MODULE test ----
        A == \E x \in y \/ z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    text = r'''
        ---- MODULE test ----
        A == \A x \in y = z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    text = r'''
        ---- MODULE test ----
        A == \E x \in y ~> z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    text = r'''
        ---- MODULE test ----
        A == \A x \in y \leadsto z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    text = r'''
        ---- MODULE test ----
        A == \E x \in y -+-> z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    text = r'''
        ---- MODULE test ----
        A == \A x \in y <=> z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    text = r'''
        ---- MODULE test ----
        A == \E x \in y \equiv z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    text = r'''
        ---- MODULE test ----
        A == \A x \in y => z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)
    # This is a different error:
    # the bounded thing is `x + y`,
    # so neither operator name nor tuple.
    text = r'''
        ---- MODULE test ----
        A == \A x + y \in z:  x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)


def test_decl_bslash_in_other_operators():
    # Parsed correctly because
    # `BSLASH_IN` has smaller precedence
    # than all other operators that have
    # precedence 5.
    infix_ops = _make_infix_ops() - {
        '=>', r'\equiv', r'\/', r'\land',
        '<=>', r'\in', '~>', '=', r'\leadsto',
        '/\\', r'\lor', '-+->'}
    for op in infix_ops:
        _make_decl_bound_using_infix_op(op)
    postfix_ops = {'^+', '^*', '^#', "'"}
    for op in postfix_ops:
        _make_decl_bound_using_postfix_op(op)


def _make_decl_bound_using_infix_op(
        op:
            str):
    """Check operator as bound expression."""
    text = rf'''
        ---- MODULE test ----
        A == \A x \in y {op} z:  x
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    qexpr = a_def.definiens
    assert qexpr.symbol == 'quantification', qexpr
    assert qexpr.quantifier == r'\A', qexpr
    assert qexpr.predicate is not None, qexpr
    assert_operator_name(qexpr.predicate, 'x')
    decls = qexpr.declarations
    assert decls is not None, qexpr
    assert len(decls) == 1, decls
    decl, = decls
    # `x \in y op z`
    assert_binary_op_app(decl, r'\in')
    x, bound_expr = decl.arguments
    # `x`
    assert_operator_name(x, 'x')
    # `y op z`
    assert_binary_op_app(bound_expr, op)
    y, z = bound_expr.arguments
    assert_operator_name(y, 'y')
    assert_operator_name(z, 'z')


def _make_decl_bound_using_postfix_op(
        op:
            str):
    """Check operator as bound expression."""
    text = rf'''
        ---- MODULE test ----
        A == \A x \in y {op}:  x
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    qexpr = a_def.definiens
    assert qexpr.symbol == 'quantification', qexpr
    assert qexpr.quantifier == r'\A', qexpr
    assert qexpr.predicate is not None, qexpr
    assert_operator_name(qexpr.predicate, 'x')
    decls = qexpr.declarations
    assert decls is not None, qexpr
    assert len(decls) == 1, decls
    decl, = decls
    # `x \in y op`
    assert_binary_op_app(decl, r'\in')
    x, bound_expr = decl.arguments
    # `x`
    assert_operator_name(x, 'x')
    # `y op`
    assert_unary_op_app(bound_expr, op)
    y, = bound_expr.arguments
    assert_operator_name(y, 'y')


def test_vertical_expr_proof_step():
    text = r'''
        ---- MODULE vexpr_pf_step ----
        PROPOSITION TRUE
        <1>1.
              /\ <<e>> # << >>
            OBVIOUS
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'vexpr_pf_step', module.name
    assert len(module.units) == 1, module.units
    theorem, = module.units
    assert theorem.symbol.name == 'THEOREM', theorem.symbol
    assert theorem.name is None, theorem.name
    assert theorem.goal is not None
    assert theorem.proof is not None
    assert theorem.theorem_keyword == 'PROPOSITION', (
        theorem.theorem_keyword)
    goal = theorem.goal
    proof = theorem.proof
    # goal `TRUE`
    assert goal.symbol.name == 'BOOLEAN_LITERAL', (
        goal.symbol)
    assert goal.value == 'TRUE', goal.value
    # proof
    assert proof.symbol.name == 'PROOF', proof.symbol
    assert proof.proof_keyword is None, (
        proof.proof_keyword)
    assert len(proof.steps) == 1, len(proof.steps)
    step_11, = proof.steps
    assert step_11.symbol.name == 'PROOF_STEP', (
        step_11.symbol)
    assert step_11.proof_keyword is None, (
        step_11.proof_keyword)
    assert step_11.name == '<1>1.', step_11.name
    main = step_11.main
    proof = step_11.proof
    # step number
    # `/\ <<e>> # << >>`
    assert main.symbol.name == 'VERTICAL_LIST', main.symbol
    assert main.operator == '/\\', main.operator
    assert len(main.arguments) == 1, main.arguments
    vitem, = main.arguments
    assert vitem.symbol.name == 'VERTICAL_ITEM', (
        vitem.symbol)
    assert vitem.operator == '/\\', vitem.operator
    expr = vitem.expression
    # `<<e>> # << >>`
    assert expr.symbol.name == 'OPERATOR_APPLICATION', (
        expr.symbol)
    assert expr.operator == '#', expr.operator
    assert len(expr.arguments) == 2, expr.arguments
    e_tuple, empty_tuple = expr.arguments
    # `<<e>>`
    assert e_tuple.symbol.name == 'TUPLE', (
        e_tuple.symbol)
    assert len(e_tuple.items) == 1, e_tuple.items
    e, = e_tuple.items
    # `e`
    assert e.symbol.name == 'OPERATOR_APPLICATION', (
        e.symbol)
    assert e.operator == 'e', e.operator
    assert e.arguments is None, e.arguments
    # `<< >>`
    assert empty_tuple.symbol.name == 'TUPLE', (
        empty_tuple.symbol)
    assert len(empty_tuple.items) == 0, empty_tuple.items
    # `OBVIOUS`
    assert proof.symbol.name == 'OBVIOUS', proof.symbol
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_named_theorem():
    text = r'''
        ---- MODULE named_theorem ----
        LEMMA named ==
            TRUE
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'named_theorem', module.name
    assert len(module.units) == 1, module.units
    theorem, = module.units
    assert theorem.symbol.name == 'THEOREM', theorem.symbol
    assert theorem.name == 'named', theorem.name
    assert theorem.proof is None, theorem.proof
    assert theorem.theorem_keyword == 'LEMMA', (
        theorem.theorem_keyword)
    goal = theorem.goal
    # `TRUE`
    assert goal.symbol.name == 'BOOLEAN_LITERAL', (
        goal.symbol)
    assert goal.value == 'TRUE', goal.value
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_quantifier_temporal_predicate():
    text = r'''
        ---- MODULE temporal_formula ----
        LOCAL L == \A r \in S:  SF_x(expr)
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'temporal_formula', module.name
    assert len(module.units) == 1, module.units
    defn, = module.units
    assert defn.symbol.name == 'OPERATOR_DEFINITION', (
        defn.symbol)
    assert defn.name == 'L', defn.name
    assert defn.arity is None, defn.arity
    assert defn.local is True, defn.local
    assert defn.function is None, defn.function
    qexpr = defn.definiens
    # `\A r \in S:  SF_x(expr)`
    assert qexpr.symbol.name == 'QUANTIFICATION', (
        qexpr.symbol)
    assert qexpr.quantifier == '\\A', qexpr.quantifier
    assert len(qexpr.declarations) == 1, qexpr.declarations
    decl, = qexpr.declarations
    pred = qexpr.predicate
    # `r \in S`
    assert decl.symbol.name == 'OPERATOR_APPLICATION', (
        decl.symbol)
    assert decl.operator == '\\in', decl.operator
    assert len(decl.arguments) == 2, len(decl.arguments)
    arg_r, arg_s = decl.arguments
    assert arg_r.symbol.name == 'OPERATOR_APPLICATION', (
        arg_r.symbol)
    assert arg_r.operator == 'r', arg_r.operator
    assert arg_r.arguments is None, arg_r.arguments
    assert arg_s.symbol.name == 'OPERATOR_APPLICATION', (
        arg_s.symbol)
    assert arg_s.operator == 'S', arg_s.operator
    assert arg_s.arguments is None, arg_s.arguments
    # `SF_x(expr)`
    assert pred.symbol.name == 'FAIRNESS', pred.symbol
    assert pred.operator == 'SF_', pred.operator
    x = pred.subscript
    expr = pred.action
    # subscript `x`
    assert x.symbol.name == 'OPERATOR_APPLICATION', (
        x.symbol)
    assert x.operator == 'x', x.operator
    assert x.arguments is None, x.arguments
    # action `expr`
    assert expr.symbol.name == 'OPERATOR_APPLICATION', (
        expr.symbol)
    assert expr.operator == 'expr', expr.operator
    assert expr.arguments is None, expr.arguments
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_unary_minus_operator_definition():
    text = r'''
        ---- MODULE binary_operator_def ----
        -. A == 0 - A
        ----
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'binary_operator_def', module.name
    assert len(module.units) == 2, len(module.units)
    # definition
    uminus_def, dash_line = module.units
    assert dash_line == '----', dash_line
    assert uminus_def.symbol.name == 'OPERATOR_DEFINITION', (
        uminus_def.symbol)
    assert uminus_def.name == '-.', oplus_def.name
    assert uminus_def.local is None, oplus_def.local
    assert uminus_def.function is None, oplus_def.function
    arity = uminus_def.arity
    definiens = uminus_def.definiens
    # arity
    assert len(arity) == 1, arity
    param_a, = arity
    # parameter `A`
    assert param_a.symbol.name == 'OPERATOR_APPLICATION', (
        param_a.symbol)
    assert param_a.operator == 'A', param_a.operator
    assert param_a.arguments is None, param_a.arguments
    # definiens `0 - A`
    assert (definiens.symbol.name ==
        'OPERATOR_APPLICATION'), definiens.symbol
    assert definiens.operator == '-', definiens
    assert len(definiens.arguments) == 2, len(
        definiens.arguments)
    zero, arg_a = definiens.arguments
    # argument `0`
    assert zero.symbol.name == 'INTEGRAL_NUMERAL', (
        zero.symbol)
    assert zero.value == '0', zero.value
    # argument `A`
    assert arg_a.symbol.name == 'OPERATOR_APPLICATION', (
        arg_a.symbol)
    assert arg_a.operator == 'A', arg_a.operator
    assert arg_a.arguments is None, arg_a.arguments
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_synonym_operators():
    text = r'''
        ---- MODULE synonyms ----
        x \equiv y == 1
        x \land y == 2
        x \lor y == 3
        x \geq y == 4
        x \mod y == 5
        x \oplus y == 6
        x \ominus y == 7
        x \odot y == 8
        x \oslash y == 9
        x \otimes y == 10
        x \o y == 11
        x \leq y == 12

        (* tested, though builtin *)
        x \setminus y == 13
        x \intersect y == 14
        x \union y == 15
        x \times y == 16
        x \leadsto y == 17
        \neg x == 18
        \lnot x == 19
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'synonyms', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 19, module.units
    operators = [
        r'\equiv', r'\land', r'\lor', r'\geq', r'\mod',
        r'\oplus', r'\ominus', r'\odot', r'\oslash',
        r'\otimes', r'\o', r'\leq',
        r'\setminus', r'\intersect', r'\union', r'\times',
        r'\leadsto', r'\neg', r'\lnot']
    unary = {r'\neg', r'\lnot'}
    pairs = zip(module.units, operators)
    for i, pair in enumerate(pairs):
        modunit, operator = pair
        assert modunit.symbol == 'operator_definition', (
            modunit)
        assert modunit.name == operator, (
            modunit.operator, operator)
        assert modunit.arity is not None, modunit.arity
        assert modunit.local is None, modunit.local
        assert modunit.function is None, modunit.function
        # operator arity
        arity = modunit.arity
        if operator in unary:
            assert len(arity) == 1, arity
            assert_operator_name(x, 'x')
        else:
            assert len(arity) == 2, arity
            x, y = arity
            assert_operator_name(x, 'x')
            assert_operator_name(y, 'y')
        # expression
        expr = modunit.definiens
        assert_integer_numeral(expr, str(1+i))


def test_by_def_operator_synonym():
    text = r'''
        ---- MODULE by_def_operator ----
        LEMMA TRUE
        BY DEF \equiv, \land, \lor, \geq, \mod,
                \oplus, \ominus, \odot, \oslash,
                \otimes, \o, \leq
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'by_def_operator', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    theorem, = module.units
    # theorem
    assert theorem.theorem_keyword == 'LEMMA', (
        theorem.theorem_keyword)
    assert theorem.name is None, theorem.name
    assert_boolean_literal(theorem.goal, 'TRUE')
    assert theorem.proof is not None
    # proof
    proof = theorem.proof
    assert proof.symbol == 'proof', proof.symbol
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None
    assert len(proof.steps) == 1, proof.steps
    # steps
    step, = proof.steps
    assert step.symbol == 'by', step
    assert step.only is False, step.only
    assert step.facts is None, step.facts
    names = [
        r'\equiv', r'\land', r'\lor', r'\geq', r'\mod',
        r'\oplus', r'\ominus', r'\odot', r'\oslash',
        r'\otimes', r'\o', r'\leq']
    assert len(step.names) == len(names), step.names
    for tree, name in zip(step.names, names):
        assert_operator_name(tree, name)


def test_operator_parsing():
    prefix_ops = _make_prefix_ops()
    infix_ops = _make_infix_ops()
    postfix_ops = _make_postfix_ops()
    for op in prefix_ops:
        _make_op_app(op, 'prefix')
        if op == '-':
            op_name = '-.'
        else:
            op_name = op
        _make_op_definition(op_name, 'prefix')
    for op in infix_ops:
        _make_op_app(op, 'infix')
        # vertical operator ?
        if op in {'/\\', '\\/'}:
            continue
        _make_op_definition(op, 'infix')
    for op in postfix_ops:
        _make_op_app(op, 'postfix')
        _make_op_definition(op, 'postfix')
    operators = prefix_ops | infix_ops | postfix_ops
    operators -= tla._langdef.VERTICAL_LEXEMES
        # vertical operators cannot appear as arguments
        # of second-order operators
    for op in operators:
        _make_op_as_arg(op)
        _make_op_instantiation(op)
    # DOT
    text = '---- MODULE test ---- A == f.x ===='
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    a_def, = module.units
    # definition
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.definiens is not None, a_def
    # expression
    expr = a_def.definiens
    assert expr.symbol == 'field', expr
    assert_operator_name(expr.expression, 'f')
    assert expr.name == 'x', expr.name


def _make_op_definition(
        op:
            str,
        fixity:
            str):
    """Make, parse and check operator definition."""
    op_sig = _op_app_expr(op, fixity)
    text = f'---- MODULE opdefs ---- {op_sig} == 1 ===='
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'opdefs', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    op_def, = module.units
    # definition
    assert op_def.symbol == 'operator_definition', op_def
    assert op_def.name == op, op_def.name
    assert op_def.arity is not None, op_def.arity
    assert op_def.local is None, op_def.local
    assert op_def.definiens is not None, op_def
    # arity
    arity = op_def.arity
    match fixity:
        case 'prefix' | 'postfix':
            x, = arity
            assert_operator_name(x, 'x')
        case 'infix':
            x, y = arity
            assert_operator_name(x, 'x')
            assert_operator_name(y, 'y')
        case _:
            raise ValueError(fixity, op, arity)
    # expression
    assert_integer_numeral(op_def.definiens, '1')


def _make_op_app(
        op:
            str,
        fixity:
            str):
    """Make, parse and check operator application."""
    expr = _op_app_expr(op, fixity)
    text = f'---- MODULE test ---- A == {expr} ===='
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    a_def, = module.units
    # definition
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.definiens is not None, a_def
    # expression
    expr = a_def.definiens
    match fixity:
        case 'prefix' | 'postfix':
            assert_unary_op_app(expr, op)
            x, = expr.arguments
            assert_operator_name(x, 'x')
        case 'infix':
            assert_binary_op_app(expr, op)
            x, y = expr.arguments
            assert_operator_name(x, 'x')
            assert_operator_name(y, 'y')
        case _:
            raise ValueError(fixity, op)


def _make_op_as_arg(
        op:
            str):
    """Test operator as itself an argument.

    An operator can be an argument of a second-order
    operator.
    """
    #
    # operator between parentheses
    text = f'---- MODULE test ---- A == f( {op} ) ===='
        # spaces around `op` to avoid `f(-)`
        # being lexed as `f` followed by
        # the lexeme `(-)`
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    a_def, = module.units
    # definition
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.definiens is not None, a_def
    # expression
    expr = a_def.definiens
    assert expr.symbol == 'operator_application', expr
    assert expr.operator == 'f', expr.operator
    assert expr.arguments is not None, expr.arguments
    assert len(expr.arguments) == 1, expr.arguments
    arg, = expr.arguments
    assert_operator_name(arg, op)
    #
    # operator between commas
    text = f'---- MODULE test ---- A == f(x, {op}, 1) ===='
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    a_def, = module.units
    # definition
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.definiens is not None, a_def
    # expression
    expr = a_def.definiens
    assert expr.symbol == 'operator_application', expr
    assert expr.operator == 'f', expr.operator
    assert expr.arguments is not None, expr.arguments
    assert len(expr.arguments) == 3, expr.arguments
    x, arg, one = expr.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(arg, op)
    assert_integer_numeral(one, '1')


def _make_op_instantiation(
        op:
            str):
    text = f'''
        ---- MODULE inst ----
        INSTANCE ModuleName WITH {op} <- {op}
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'inst')
    assert len(module.units) == 1, module.units
    instance, = module.units
    assert instance.symbol == 'instance', (
        instance.symbol)
    assert instance.name == 'ModuleName', instance.name
    assert instance.local is None, instance.local
    with_ = instance.with_substitution
    assert len(with_) == 1, len(with_)
    sub, = with_
    # op <- op
    assert sub.symbol == 'with_instantiation', sub
    assert sub.name == op, sub.name
    assert_operator_name(sub.expression, op)


def _op_app_expr(
        op:
            str,
        fixity:
            str):
    """Return expression of operator application."""
    match fixity:
        case 'prefix':
            return f'{op} x'
        case 'infix':
            return f'x {op} y'
        case 'postfix':
            return f'x {op}'
        case _:
            raise ValueError(fixity, op)


def _make_prefix_ops() -> set[str]:
    """Return prefix operators."""
    return {
        '-', '~', r'\lnot', r'\neg', '[]', '<>',
        'DOMAIN', 'ENABLED', 'SUBSET', 'UNCHANGED',
        'UNION'}


def _make_infix_ops() -> set[str]:
    """Return infix operators."""
    return {
        '!!', '#', '##', '$', '$$', '%', '%%',
        '&', '&&', '(+)', '(-)', '(.)', '(/)', r'(\X)',
        '*', '**', '+', '++', '-', '--', '-+->',
        '-|', '..', '...', '/', '//', '/=', '/\\',
        '::=', ':=', ':>', '<', '<:', '<=>', '=',
        '=<', '=>', '=|', '>', '>=', '??', '@@', '\\',
        '\\/', '^', '^^', '|', '|-', '|=', '||', '~>',
        '<=',
        r'\approx', r'\asymp', r'\bigcirc', r'\bullet',
        r'\cap', r'\cdot', r'\circ', r'\cong', r'\cup',
        r'\div', r'\doteq', r'\equiv', r'\geq', r'\gg',
        r'\in', r'\intersect', r'\land', r'\leadsto',
        r'\leq', r'\ll',
        r'\lor', r'\o', r'\odot', r'\ominus', r'\oplus',
        r'\oslash', r'\otimes', r'\prec', r'\preceq',
        r'\propto', r'\sim', r'\simeq', r'\sqcap',
        r'\sqcup', r'\sqsubset', r'\sqsubseteq',
        r'\sqsupset', r'\sqsupseteq', r'\star', r'\subset',
        r'\subseteq', r'\succ', r'\succeq', r'\supset',
        r'\supseteq', r'\union', r'\uplus', r'\wr',
        r'\notin'}


def _make_postfix_ops() -> set[str]:
    """Return postfix operators."""
    return {'^+', '^*', '^#', "'"}


def test_second_order_op_def_prefix_param():
    text = '''
        ---- MODULE second_order_op ----
        F(-. _) == - 1
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'second_order_op')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert op_def.symbol == 'operator_definition', (
        op_def.symbol)
    assert op_def.name == 'F', op_def.name
    assert op_def.arity is not None, op_def
    assert op_def.local is None, op_def.local
    assert op_def.function is None, op_def.function
    # arity
    assert len(op_def.arity) == 1, op_def.arity
    param, = op_def.arity
    assert_unary_op_app(param, '-.')
    arg, = param.arguments
    assert arg == '_', arg
    # definiens
    expr = op_def.definiens
    assert_unary_op_app(expr, '-')
    arg, = expr.arguments
    assert_integer_numeral(arg, '1')


def test_second_order_op_def_infix_param():
    text = '''
        ---- MODULE second_order_op ----
        F(_ + _) == 1 + 2
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'second_order_op')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert op_def.symbol == 'operator_definition', (
        op_def.symbol)
    assert op_def.name == 'F', op_def.name
    assert op_def.arity is not None, op_def
    assert op_def.local is None, op_def.local
    assert op_def.function is None, op_def.function
    # arity
    assert len(op_def.arity) == 1, op_def.arity
    param, = op_def.arity
    assert_binary_op_app(param, '+')
    arg1, arg2 = param.arguments
    assert arg1 == '_', arg1
    assert arg2 == '_', arg2
    # definiens
    expr = op_def.definiens
    assert_binary_op_app(expr, '+')
    one, two = expr.arguments
    assert_integer_numeral(one, '1')
    assert_integer_numeral(two, '2')


def test_second_order_op_def_postfix_param():
    text = '''
        ---- MODULE second_order_op ----
        F(x, _ ^*) == x^*
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'second_order_op')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert op_def.symbol == 'operator_definition', (
        op_def.symbol)
    assert op_def.name == 'F', op_def.name
    assert op_def.arity is not None, op_def
    assert op_def.local is None, op_def.local
    assert op_def.function is None, op_def.function
    # arity
    assert len(op_def.arity) == 2, op_def.arity
    x, param = op_def.arity
    assert_operator_name(x, 'x')
    assert_unary_op_app(param, '^*')
    arg, = param.arguments
    assert arg == '_', arg
    # definiens
    expr = op_def.definiens
    assert_unary_op_app(expr, '^*')
    arg, = expr.arguments
    assert_operator_name(arg, 'x')


def test_dash_operator():
    #
    # dash as only argument of second-order operator
    text = '---- MODULE test ---- y == f( - ) ===='
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    y_def, = module.units
    assert y_def.symbol == 'operator_definition', a_def
    assert y_def.name == 'y', a_def.name
    assert y_def.arity is None, a_def.arity
    assert y_def.local is None, a_def.local
    assert y_def.definiens is not None, a_def
    expr = y_def.definiens
    assert_unary_op_app(expr, 'f')
    arg, = expr.arguments
    assert_operator_name(arg, '-')
    #
    # error: dash between parentheses without spaces
    text = '---- MODULE test ---- y == f(-) ===='
    with pytest.raises(ValueError):
        _lr.parse(text)
    #
    # dash among arguments of second-order operator
    text = '---- MODULE test ---- y == f(-, 3) ===='
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    y_def, = module.units
    assert y_def.symbol == 'operator_definition', a_def
    assert y_def.name == 'y', a_def.name
    assert y_def.arity is None, a_def.arity
    assert y_def.local is None, a_def.local
    assert y_def.definiens is not None, a_def
    expr = y_def.definiens
    assert_binary_op_app(expr, 'f')
    arg, three = expr.arguments
    assert_operator_name(arg, '-')
    assert_integer_numeral(three, '3')
    #
    # dash as binary operator being defined
    text = '---- MODULE test ---- x - y == 2 ===='
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert op_def.symbol == 'operator_definition', op_def
    assert op_def.name == '-', op_def.name
    assert op_def.arity is not None, op_def.arity
    assert op_def.local is None, op_def.local
    assert op_def.definiens is not None, op_def
    arity = op_def.arity
    assert len(arity) == 2, arity
    x, y = arity
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    expr = op_def.definiens
    assert_integer_numeral(expr, '2')
    #
    # error: dash as unary operator being defined
    text = '---- MODULE test ---- - y == 4 ===='
    with pytest.raises(ValueError):
        _lr.parse(text)
    #
    # unary dash definition
    text = '---- MODULE test ---- -. y == 5 ===='
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert op_def.symbol == 'operator_definition', op_def
    assert op_def.name == '-.', op_def.name
    assert op_def.arity is not None, op_def.arity
    assert op_def.local is None, op_def.local
    assert op_def.definiens is not None, op_def
    arity = op_def.arity
    assert len(arity) == 1, arity
    y, = arity
    assert_operator_name(y, 'y')
    expr = op_def.definiens
    assert_integer_numeral(expr, '5')
    #
    # dash as instantiated operator
    text = '---- MODULE test ---- A == M!-(x, y) ===='
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'A')
    expr = op_def.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr
    assert len(expr.items) == 2, expr.items
    m, xy = expr.items
    assert_operator_name(m, 'M')
    assert_binary_op_app(xy, '-')
    x, y = xy.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')


def test_binary_operator_definition():
    text = r'''
        ---- MODULE binary_operator_def ----
        LOCAL A (+) B == TRUE
        ----
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'binary_operator_def', module.name
    assert len(module.units) == 2, len(module.units)
    # definition
    oplus_def, dash_line = module.units
    assert dash_line == '----', dash_line
    assert oplus_def.symbol.name == 'OPERATOR_DEFINITION', (
        oplus_def.symbol)
    assert oplus_def.name == '(+)', oplus_def.name
    assert oplus_def.local is True, oplus_def.local
    assert oplus_def.function is None, oplus_def.function
    arity = oplus_def.arity
    definiens = oplus_def.definiens
    # arity
    assert len(arity) == 2, arity
    param_a, param_b = arity
    # parameter `A`
    assert param_a.symbol.name == 'OPERATOR_APPLICATION', (
        param_a.symbol)
    assert param_a.operator == 'A', param_a.operator
    assert param_a.arguments is None, param_a.arguments
    # parameter `B`
    assert param_b.symbol.name == 'OPERATOR_APPLICATION', (
        param_b.symbol)
    assert param_b.operator == 'B', param_b.operator
    assert param_b.arguments is None, param_b.arguments
    # definiens `TRUE`
    assert definiens.symbol.name == 'BOOLEAN_LITERAL', (
        definiens.symbol)
    assert definiens.value == 'TRUE', definiens
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_labeled_vertical_expression():
    text = r'''
        ----MODULE labeled ----
        y == label(1, 2) :: /\ x
                            /\ y
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module.symbol
    assert module.name == 'labeled', module.name
    assert module.extendees is None, module.extendees
    assert module.units is not None, module
    assert len(module.units) == 1, module.units
    y_def, = module.units
    assert_op_def(y_def, 'y')
    expr = y_def.definiens
    assert_binary_op_app(expr, '::')
    label, vexpr = expr.arguments
    # `label(1, 2)`
    assert_binary_op_app(label, 'label')
    one, two = label.arguments
    assert_integer_numeral(one, '1')
    assert_integer_numeral(two, '2')
    # `/\ x`
    assert vexpr.symbol == 'vertical_list', vexpr
    assert vexpr.operator == '/\\', vexpr.operators
    assert vexpr.arguments is not None, vexpr
    assert len(vexpr.arguments) == 2, vexpr.arguments
    x, y = vexpr.arguments
    assert x.symbol == 'vertical_item', x
    assert x.operator == '/\\', x.operator
    assert_operator_name(x.expression, 'x')
    assert y.symbol == 'vertical_item', y
    assert y.operator == '/\\', y.operator
    assert_operator_name(y.expression , 'y')


def test_infix_conj_after_subexpression_reference():
    # infix conjunction `/\` after a subexpression
    # that ends in a colon `:`
    text = r'''
        ---- MODULE test ----
        y == a!: /\ x
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module.symbol
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert module.units is not None, module
    assert len(module.units) == 1, module.units
    y_def, = module.units
    assert_op_def(y_def, 'y')
    expr = y_def.definiens
    assert_binary_op_app(expr, '/\\')
    subexpr, x = expr.arguments
    assert_operator_name(x, 'x')
    assert subexpr.symbol == 'subexpression_reference', (
        subexpr)
    assert subexpr.items is not None, subexpr
    assert len(subexpr.items) == 2, subexpr.items
    a, colon = subexpr.items
    assert_operator_name(a, 'a')
    assert colon == ':', colon


def test_conj_as_operator_argument():
    text = r'''
        ---- MODULE test ----
        y == f(/\)
        z == g(1, \/)
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module.symbol
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert module.units is not None, module
    assert len(module.units) == 2, module.units
    y_def, z_def = module.units
    assert_op_def(y_def, 'y')
    assert_op_def(z_def, 'z')
    expr = y_def.definiens
    assert_unary_op_app(expr, 'f')
    arg, = expr.arguments
    assert_operator_name(arg, '/\\')
    expr = z_def.definiens
    assert_binary_op_app(expr, 'g')
    one, lor = expr.arguments
    assert_integer_numeral(one, '1')
    assert_operator_name(lor, '\\/')


def test_subexpression_references():
    text = r'''
        ---- MODULE subexpr ----
        A == @@(x, y)!>>!(u, v, w)!b
        numeral == a!1!b
        rangle == a!>>!b
        langle == a!<<!b
        colon == a!:!b
        op_args == a!(x, y)!b
        prefix == -(1)!b
        infix == -(3, z)!b
        postfix == ^+(x)!b
        op_start == f(x, y, z)!b!c
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module.symbol
    assert module.name == 'subexpr', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 10, module.units
    #
    # A == @@(x, y)!>>!(u, v, w)!b
    opdef = module.units[0]
    assert_op_def(opdef, 'A')
    expr = opdef.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr.items
    assert len(expr.items) == 4, expr.items
    xy, rangle, uvw, b = expr.items
    # @@(x, y)
    assert_binary_op_app(xy, '@@')
    x, y = xy.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # >>
    assert rangle == '>>', rangle
    # (u, v, w)
    assert uvw.symbol == 'operator_application', uvw
    assert uvw.operator is None, uvw.operator
    assert uvw.arguments is not None
    assert len(uvw.arguments) == 3, uvw.arguments
    u, v, w = uvw.arguments
    assert_operator_name(u, 'u')
    assert_operator_name(v, 'v')
    assert_operator_name(w, 'w')
    # b
    assert b == 'b', b
    #
    # numeral == a!1!b
    opdef = module.units[1]
    assert_op_def(opdef, 'numeral')
    expr = opdef.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr.items
    assert len(expr.items) == 3, expr.items
    a, one, b = expr.items
    assert_operator_name(a, 'a')
    assert one == '1', one
    assert b == 'b', b
    #
    # rangle == a!>>!b
    opdef = module.units[2]
    assert_op_def(opdef, 'rangle')
    expr = opdef.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr.items
    assert len(expr.items) == 3, expr.items
    a, rangle, b = expr.items
    assert_operator_name(a, 'a')
    assert rangle == '>>', rangle
    assert b == 'b', b
    #
    # langle == a!<<!b
    opdef = module.units[3]
    assert_op_def(opdef, 'langle')
    expr = opdef.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr.items
    assert len(expr.items) == 3, expr.items
    a, langle, b = expr.items
    assert_operator_name(a, 'a')
    assert langle == '<<', langle
    assert b == 'b', b
    #
    # colon == a!:!b
    opdef = module.units[4]
    assert_op_def(opdef, 'colon')
    expr = opdef.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr.items
    assert len(expr.items) == 3, expr.items
    a, colon, b = expr.items
    assert_operator_name(a, 'a')
    assert colon == ':', colon
    assert b == 'b', b
    #
    # op_args == a!(x, y)!b
    opdef = module.units[5]
    assert_op_def(opdef, 'op_args')
    expr = opdef.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr.items
    assert len(expr.items) == 3, expr.items
    a, xy, b = expr.items
    assert_operator_name(a, 'a')
    # (x, y)
    assert xy.symbol == 'operator_application', xy
    assert xy.operator is None, xy.operator
    assert xy.arguments is not None, xy
    assert len(xy.arguments) == 2, xy.arguments
    x, y = xy.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # b
    assert b == 'b', b
    #
    # prefix == -(1)!b
    opdef = module.units[6]
    assert_op_def(opdef, 'prefix')
    expr = opdef.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr.items
    assert len(expr.items) == 2, expr.items
    dash, b = expr.items
    assert_unary_op_app(dash, '-')
    one, = dash.arguments
    assert_integer_numeral(one, '1')
    assert b == 'b', b
    #
    # infix == -(3, z)!b
    opdef = module.units[7]
    assert_op_def(opdef, 'infix')
    expr = opdef.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr.items
    assert len(expr.items) == 2, expr.items
    dash, b = expr.items
    assert_binary_op_app(dash, '-')
    three, z = dash.arguments
    assert_integer_numeral(three, '3')
    assert_operator_name(z, 'z')
    assert b == 'b', b
    #
    # postfix == ^+(x)!b
    opdef = module.units[8]
    assert_op_def(opdef, 'postfix')
    expr = opdef.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr.items
    assert len(expr.items) == 2, expr.items
    op_app, b = expr.items
    assert_unary_op_app(op_app, '^+')
    x, = op_app.arguments
    assert_operator_name(x, 'x')
    assert b == 'b', b
    #
    # op_start == f(x, y, z)!b!c
    opdef = module.units[9]
    assert_op_def(opdef, 'op_start')
    expr = opdef.definiens
    assert expr.symbol == 'subexpression_reference', expr
    assert expr.items is not None, expr.items
    assert len(expr.items) == 3, expr.items
    fxyz, b, c = expr.items
    assert fxyz.symbol == 'operator_application', fxyz
    assert fxyz.operator == 'f', fxy.operator
    assert fxyz.arguments is not None, fxyz.arguments
    assert len(fxyz.arguments) == 3, fxyz.arguments
    x, y, z = fxyz.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert_operator_name(z, 'z')
    assert b == 'b', b
    assert c == 'c', c


def test_subexpression_reference_to_operator_name():
    text = r'''
        ---- MODULE op_name_subexpr ----
        x + y == 1 /\
            LET
                a * b == 2
            IN
                3 * 4

        A == +(1, 2)!>>!*(3, 4)

        THEOREM
            TRUE
        BY DEF +!>>!*
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'op_name_subexpr')
    assert len(module.units) == 3, module.units
    op_def, a_def, thm = module.units
    # `x + y == ...`
    assert (op_def.symbol ==
        'operator_definition'), op_def
    assert op_def.name == '+', op_def.name
    assert op_def.local is None, op_def.local
    assert op_def.function is None, op_def.function
    assert op_def.arity is not None, op_def
    arity = op_def.arity
    assert len(arity) == 2, arity
    x, y = arity
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # definiens
    conj = op_def.definiens
    assert_binary_op_app(conj, '/\\')
    one, let_expr = conj.arguments
    assert_integer_numeral(one, '1')
    assert let_expr.symbol == 'let', let_expr
    # `LET` definitions
    defs = let_expr.definitions
    assert defs is not None, let_expr
    assert len(defs) == 1, defs
    ab_def, = defs
    assert (ab_def.symbol ==
        'operator_definition'), ab_def
    assert ab_def.name == '*', ab_def.name
    assert ab_def.local is None, ab_def.local
    assert ab_def.function is None, ab_def.function
    assert ab_def.arity is not None, ab_def
    arity = ab_def.arity
    assert len(arity) == 2, arity
    a, b = arity
    assert_operator_name(a, 'a')
    assert_operator_name(b, 'b')
    assert_integer_numeral(ab_def.definiens, '2')
    # `LET` expression
    expr = let_expr.expression
    assert_binary_op_app(expr, '*')
    three, four = expr.arguments
    assert_integer_numeral(three, '3')
    assert_integer_numeral(four, '4')
    # `A == ...`
    assert_op_def(a_def, 'A')
    sub = a_def.definiens
    assert sub.symbol == 'subexpression_reference', sub
    # `+(1, 2)!>>!*(3, 4)`
    assert sub.items is not None, sub.items
    assert len(sub.items) == 3, sub.items
    plus, angle, asterisk = sub.items
    assert_binary_op_app(plus, '+')
    assert plus.nonfix is True, plus
    one, two = plus.arguments
    assert_integer_numeral(one, '1')
    assert_integer_numeral(two, '2')
    assert angle == '>>', angle
    assert_binary_op_app(asterisk, '*')
    assert asterisk.nonfix is True, asterisk
    three, four = asterisk.arguments
    assert_integer_numeral(three, '3')
    assert_integer_numeral(four, '4')
    # `THEOREM`
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    assert thm.proof is not None, thm
    assert_boolean_literal(thm.goal, 'TRUE')
    # `BY DEF +!>>!*`
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof.steps
    assert len(proof.steps) == 1, proof.steps
    by, = proof.steps
    assert by.symbol == 'by', by
    assert by.only is False, by.only
    assert by.keyword == 'DEF', by.keyword
    assert by.facts is None, by.facts
    assert by.names is not None, by
    assert len(by.names) == 1, by.names
    # `+!>>!*`
    sub, = by.names
    assert sub.symbol == 'subexpression_reference', sub
    assert sub.items is not None, sub.items
    assert len(sub.items) == 3, sub.items
    plus, angle, asterisk = sub.items
    assert_operator_name(plus, '+')
    assert angle == '>>', angle
    assert asterisk == '*', asterisk


def test_subexpression_reference_as_function():
    text = r'''
        ---- MODULE subexpr ----
        A == g!:[x, y]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'subexpr')
    assert len(module.units) == 1, module.units
    opdef = module.units[0]
    assert_op_def(opdef, 'A')
    expr = opdef.definiens
    assert expr.symbol == 'function_application', expr
    assert expr.function is not None, expr
    # `[x, y]`
    assert expr.arguments is not None, expr
    assert len(expr.arguments) == 2, expr.arguments
    x, y = expr.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # `g!:`
    sub = expr.function
    assert sub.symbol == 'subexpression_reference', sub
    assert sub.items is not None, sub.items
    assert len(sub.items) == 2, sub.items
    g, colon = sub.items
    assert_operator_name(g, 'g')
    assert colon == ':', colon


def test_subexpression_reference_as_operator_error():
    # subexpression references are values,
    # not operators
    text = r'''
        ---- MODULE subexpr ----
        A == g!:(x, y)
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)


def test_pipe_instantiation():
    text = r'''
        ---- MODULE pipe_inst ----
        INSTANCE M WITH | <- |, x <- a | b
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module.symbol
    assert module.name == 'pipe_inst', module.name
    assert len(module.units) == 1, len(module.units)
    # instance
    instance, = module.units
    assert instance.symbol == 'instance', (
        instance.symbol)
    assert instance.name == 'M', instance.name
    assert instance.local is None, instance.local
    with_ = instance.with_substitution
    assert len(with_) == 2, len(with_)
    pipe_sub, x_sub = with_
    # `| <- |`
    assert pipe_sub.symbol == 'with_instantiation', (
        pipe_sub.symbol)
    assert pipe_sub.name == '|', pipe_sub.name
    assert_operator_name(pipe_sub.expression, '|')
    # `x <- x`
    assert x_sub.symbol == 'with_instantiation', (
        x_sub.symbol)
    assert x_sub.name == 'x', x_sub.name
    op_app = x_sub.expression
    assert_binary_op_app(op_app, '|')
    a, b = op_app.arguments
    assert_operator_name(a, 'a')
    assert_operator_name(b, 'b')
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_at_at_instantiation():
    text = '''
        ---- MODULE at_at_inst ----
        INSTANCE Q WITH @@ <- +
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'at_at_inst')
    assert len(module.units) == 1, module.units
    instance, = module.units
    assert instance.symbol == 'instance', (
        instance.symbol)
    assert instance.name == 'Q', instance.name
    assert instance.local is None, instance.local
    with_ = instance.with_substitution
    assert len(with_) == 1, len(with_)
    sub, = with_
    # `@@ <- +`
    assert sub.symbol == 'with_instantiation', sub
    assert sub.name == '@@', sub.name
    assert_operator_name(sub.expression, '+')


def test_nested_proofs():
    module_name = 'case_proof_step'
    source = r'''
        ---- MODULE case_proof_step ----
        THEOREM TRUE
        PROOF
        <1>1. CASE x
            PROOF
            <2>1. x = 1
            <2> QED
                BY <2>1
        <1>2. CASE ~ x
            OBVIOUS
        <1> QED
        ====
        '''
    module = _lr.parse(source)
    assert module is not None
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'case_proof_step', module.name
    assert len(module.units) == 1, len(module.units)
    # theorem
    theorem, = module.units
    assert theorem.name is None, theorem.name
    assert theorem.theorem_keyword == 'THEOREM', (
        theorem.theorem_keyword)
    goal = theorem.goal
    proof = theorem.proof
    # theorem goal TRUE
    assert goal.symbol.name == 'BOOLEAN_LITERAL', (
        goal.symbol)
    assert goal.value == 'TRUE', goal.value
    # proof
    assert proof.symbol.name == 'PROOF'
    assert proof.proof_keyword is True, proof.proof_keyword
    assert len(proof.steps) == 3, len(proof.steps)
    step_11, step_12, step_1qed = proof.steps
    # step <1>1
    assert step_11.symbol.name == 'PROOF_STEP', (
        step_11.symbol.name)
    assert step_11.proof_keyword is True, (
        step_11.proof_keyword)
    assert step_11.name == '<1>1.', step_11.name
    main = step_11.main
    proof = step_11.proof
    # goal `CASE x`
    assert main.symbol.name == 'PROOF_CASE', main.symbol
    expr = main.expression
    # expression `x`
    assert expr.symbol.name == 'OPERATOR_APPLICATION', (
        expr.symbol)
    assert expr.operator == 'x', expr.operator
    assert expr.arguments is None, expr.arguments
    # nested proof of <1>1
    assert proof.symbol.name == 'PROOF', proof.symbol
    assert proof.proof_keyword is None, proof.proof_keyword
    assert len(proof.steps) == 2, len(proof.steps)
    step_21, step_2qed = proof.steps
    # step <2>1
    assert step_21.symbol.name == 'PROOF_STEP', (
        step_21.symbol)
    assert step_21.proof is None, step_21.proof
    assert step_21.proof_keyword is None, (
        step_21.proof_keyword)
    assert step_21.name == '<2>1.', step_21.name
    main = step_21.main
    # goal `x = 1`
    assert main.symbol.name == 'OPERATOR_APPLICATION', (
        main.symbol)
    assert main.operator == '=', main.operator
    assert len(main.arguments) == 2, len(main.arguments)
    x, one = main.arguments
    assert x.symbol.name == 'OPERATOR_APPLICATION', (
        x.symbol)
    assert x.operator == 'x', x.operator
    assert x.arguments is None, x.arguments
    assert one.symbol.name == 'INTEGRAL_NUMERAL', (
        one.symbol)
    assert one.value == '1', one.value
    # step <2> QED
    assert step_2qed.symbol.name == 'PROOF_STEP', (
        step_2qed.symbol)
    assert step_2qed.name == '<2>', step_2qed.name
    assert step_2qed.main == 'QED', step_2qed.main
    assert step_2qed.proof is not None, step_2qed.proof
    assert step_2qed.proof_keyword is None, (
        step_1qed.proof_keyword)
    # proof `BY <2>1`
    proof = step_2qed.proof
    assert proof.symbol.name == 'BY', proof.symbol
    assert proof.only is False, proof.only
    assert proof.names is None, proof.names
    assert len(proof.facts) == 1, proof.facts
    step_name, = proof.facts
    assert (step_name.symbol.name ==
        'OPERATOR_APPLICATION'), step_name.symbol
    assert step_name.operator == '<2>1', step_name.operator
    assert step_name.arguments is None, step_name.arguments
    # step <1>2
    assert step_12.symbol.name == 'PROOF_STEP', (
        step_12.symbol.name)
    assert step_12.name == '<1>2.', step_12.name
    assert step_12.proof_keyword is None, (
        step_12.proof_keyword)
    main = step_12.main
    proof = step_12.proof
    # goal `CASE ~ x`
    assert main.symbol.name == 'PROOF_CASE', main.symbol
    expr = main.expression
    # expression `~ x`
    assert expr.symbol.name == 'OPERATOR_APPLICATION', (
        expr.symbol)
    assert expr.operator == '~', expr.operator
    assert len(expr.arguments) == 1, len(expr.arguments)
    arg, = expr.arguments
    assert arg.symbol.name == 'OPERATOR_APPLICATION', (
        arg.symbol)
    assert arg.operator == 'x', arg.operator
    assert arg.arguments is None, arg.arguments
    # proof OBVIOUS
    assert proof.symbol.name == 'OBVIOUS', proof.symbol
    # step <1> QED
    assert step_1qed.symbol.name == 'PROOF_STEP', (
        step_1qed.symbol)
    assert step_1qed.name == '<1>', step_1qed
    assert step_1qed.main == 'QED', step_1qed.main
    assert step_1qed.proof is None, step_1qed.proof
    assert step_1qed.proof_keyword is None, (
        step_1qed.proof_keyword)
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_function_definition_one_declaration():
    source = r'''
        ---- MODULE function_definition ----
        f[n \in Nat] == n + 1
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol.name == 'MODULE', module
    assert module.name == 'function_definition', module
    assert len(module.units) == 1, module
    f_def, = module.units
    # `f` definition
    assert (f_def.symbol.name ==
        'OPERATOR_DEFINITION'), f_def
    assert f_def.name == 'f', f_def
    assert f_def.arity is None, f_def
    assert f_def.local is None, f_def
    assert f_def.function is True, f_def
    # `f` definiens
    f_definiens = f_def.definiens
    assert (f_definiens.symbol.name ==
        'FUNCTION'), f_definiens
    # function constructor
    assert isinstance(
        f_definiens.declaration, list), f_definiens
    decl, = f_definiens.declaration
    expr = f_definiens.value
    # function declaration
    assert (decl.symbol.name ==
        'OPERATOR_APPLICATION'), decl
    assert decl.operator == '\\in', decl
    assert len(decl.arguments) == 2, decl
    n, nat = decl.arguments
    assert (n.symbol.name ==
        'OPERATOR_APPLICATION'), n
    assert n.arguments is None, n
    assert n.operator == 'n', n
    assert (nat.symbol.name ==
        'OPERATOR_APPLICATION'), nat
    assert nat.arguments is None, nat
    assert nat.operator == 'Nat', nat
    # function value
    assert (expr.symbol.name ==
        'OPERATOR_APPLICATION'), expr
    assert expr.operator == '+', expr
    assert len(expr.arguments) == 2, expr
    n, one = expr.arguments
    assert (n.symbol.name ==
        'OPERATOR_APPLICATION'), n
    assert n.arguments is None, n
    assert n.operator == 'n', n
    assert (one.symbol.name ==
        'INTEGRAL_NUMERAL'), one
    assert one.value == '1', one


def test_function_definition_multiple_declarations():
    text = r'''
        ---- MODULE test ----
        f[x \in S, y \in Q] == - x ^^ y
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    f_def, = module.units
    assert f_def.symbol == 'operator_definition', f_def
    assert f_def.name == 'f', f_def.name
    assert f_def.arity is None, f_def.arity
    assert f_def.local is None, f_def.local
    assert f_def.function == True, f_def.function
    # definiens
    func = f_def.definiens
    assert func.symbol == 'function', func
    assert func.declaration is not None, func
    assert func.value is not None, func
    # declarations
    decls = func.declaration
    assert len(decls) == 2, decls
    x_in_s, y_in_q = decls
    assert_binary_op_app(x_in_s, r'\in')
    x, s = x_in_s.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(s, 'S')
    assert_binary_op_app(y_in_q, r'\in')
    y, q = y_in_q.arguments
    assert_operator_name(y, 'y')
    assert_operator_name(q, 'Q')
    # `- x ^^ y` expression
    expr = func.value
    assert_unary_op_app(expr, '-')
    xy, = expr.arguments
    assert_binary_op_app(xy, '^^')
    x, y = xy.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')


def test_function_definition_declaration_error():
    text = r'''
        ---- MODULE error ----
        f[x] == x
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)


def test_vertical_operator_end_by_infix_dedent():
    source = r'''
        ---- MODULE name ----
        A == \/ a
             \/ b
            \/ c
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol.name == 'MODULE', module
    assert module.name == 'name', module.name
    assert len(module.units) == 1, len(module.units)
    a_def, = module.units
    # `A` definition
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    # `A` definiens
    a_definiens = a_def.definiens
    assert (a_definiens.symbol.name ==
        'OPERATOR_APPLICATION'), a_definiens
    assert a_definiens.operator == r'\/', a_definiens
    assert len(a_definiens.arguments) == 2, a_definiens
    vexpr, disj = a_definiens.arguments
    # vertical expression
    assert (vexpr.symbol.name ==
        'VERTICAL_LIST'), vexpr
    assert vexpr.operator == r'\/', vexpr
    assert len(vexpr.arguments) == 2, vexpr
    a_vitem, b_vitem = vexpr.arguments
    # `\/ a`
    assert (a_vitem.symbol.name ==
        'VERTICAL_ITEM'), a_vitem
    assert a_vitem.operator == r'\/', a_vitem
    a_expr = a_vitem.expression
    assert_operator_name(a_expr, 'a')
    # `\/ b`
    assert (b_vitem.symbol.name ==
        'VERTICAL_ITEM'), b_vitem
    assert b_vitem.operator == r'\/', b_vitem
    b_expr = b_vitem.expression
    assert_operator_name(b_expr, 'b')
    # disjunct `c`
    assert_operator_name(disj, 'c')


def test_vertical_operator_contains_infix():
    source = r'''
        ---- MODULE name ----
        A == \/ a
             \/ b
              \/ c
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol.name == 'MODULE', module
    assert module.name == 'name', module.name
    assert len(module.units) == 1, len(module.units)
    a_def, = module.units
    # `A` definition
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    # `A` definiens
    vexpr = a_def.definiens
    # vertical expression
    assert (vexpr.symbol.name ==
        'VERTICAL_LIST'), vexpr
    assert vexpr.operator == r'\/', vexpr
    assert len(vexpr.arguments) == 2, vexpr
    a_vitem, b_vitem = vexpr.arguments
    # `\/ a`
    assert (a_vitem.symbol.name ==
        'VERTICAL_ITEM'), a_vitem
    assert a_vitem.operator == r'\/', a_vitem
    a_expr = a_vitem.expression
    assert (a_expr.symbol.name ==
        'OPERATOR_APPLICATION'), a_expr
    assert a_expr.operator == 'a', a_expr
    assert a_expr.arguments is None, a_expr
    # `\/ b \/ c`
    assert (b_vitem.symbol.name ==
        'VERTICAL_ITEM'), b_vitem
    assert b_vitem.operator == r'\/', b_vitem
    disj = b_vitem.expression
    assert (disj.symbol.name ==
        'OPERATOR_APPLICATION'), disj
    assert disj.operator == r'\/', disj
    assert len(disj.arguments) == 2, disj
    b_expr, c_expr = disj.arguments
    assert_operator_name(b_expr, 'b')
    assert_operator_name(c_expr, 'c')


def test_vertical_operator_end_by_infix_aligned():
    source = r'''
        ---- MODULE name ----
        A == \/ a
             \/ b
             /\ c
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol.name == 'MODULE', module
    assert module.name == 'name', module.name
    assert len(module.units) == 1, len(module.units)
    a_def, = module.units
    # `A` definition
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    # `A` definiens
    a_definiens = a_def.definiens
    assert (a_definiens.symbol.name ==
        'OPERATOR_APPLICATION'), a_definiens
    assert a_definiens.operator == '/\\', a_definiens
    assert len(a_definiens.arguments) == 2, a_definiens
    vexpr, disj = a_definiens.arguments
    # vertical expression
    assert (vexpr.symbol.name ==
        'VERTICAL_LIST'), vexpr
    assert vexpr.operator == r'\/', vexpr
    assert len(vexpr.arguments) == 2, vexpr
    a_vitem, b_vitem = vexpr.arguments
    # `\/ a`
    assert (a_vitem.symbol.name ==
        'VERTICAL_ITEM'), a_vitem
    assert a_vitem.operator == r'\/', a_vitem
    a_expr = a_vitem.expression
    assert_operator_name(a_expr, 'a')
    # `\/ b`
    assert (b_vitem.symbol.name ==
        'VERTICAL_ITEM'), b_vitem
    assert b_vitem.operator == r'\/', b_vitem
    b_expr = b_vitem.expression
    assert_operator_name(b_expr, 'b')
    # disjunct `c`
    assert_operator_name(disj, 'c')


def test_vertical_operator_after_prove():
    text = r'''
        ---- MODULE vertical ----
        THEOREM
            ASSUME TRUE
            PROVE /\ x
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol == 'module', module
    assert module.name == 'vertical', module.name
    assert module.extendees is None, module.extendees
    assert module.units is not None, module
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    assert thm.proof is None, thm.proof
    assert thm.goal is not None, thm
    goal = thm.goal
    assert goal.symbol == 'sequent', goal
    assert goal.assume is not None, goal
    assert len(goal.assume) == 1, goal.assume
    assert goal.prove is not None, goal
    asm, = goal.assume
    assert_boolean_literal(asm, 'TRUE')
    prove = goal.prove
    assert prove.symbol == 'vertical_list', prove
    assert prove.operator == '/\\', prove.operator
    assert prove.arguments is not None, prove.arguments
    assert len(prove.arguments) == 1, prove.arguments
    vitem, = prove.arguments
    assert vitem.symbol == 'vertical_item', vitem
    assert vitem.operator == '/\\', vitem.operator
    assert vitem.expression is not None, vitem
    assert_operator_name(vitem.expression, 'x')


def test_vertical_operators():
    module_name = 'vertical_after_infix'
    source = r'''
        ---- MODULE vertical_after_infix ----
        A == \/ b / /\ c
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol.name == 'MODULE', module
    assert module.name == module_name, module
    assert len(module.units) == 1, module
    a_def, = module.units
    # `A` definition
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def
    assert a_def.arity is None, a_def
    assert a_def.local is None, a_def
    # `A` definiens
    a_definiens = a_def.definiens
    assert (a_definiens.symbol.name ==
        'VERTICAL_LIST'), a_definiens
    assert a_definiens.operator == r'\/', a_definiens
    assert len(a_definiens.arguments) == 1, a_definiens
    # disjunct `\/ b / /\ c`
    disjunct, = a_definiens.arguments
    assert (disjunct.symbol.name ==
        'VERTICAL_ITEM'), item
    assert disjunct.operator == r'\/', disjunct
    # expression `b / /\ c`
    expr = disjunct.expression
    assert (expr.symbol.name ==
        'OPERATOR_APPLICATION'), expr
    assert expr.operator == '/', expr
    assert len(expr.arguments) == 2, expr
    b_expr, conj = expr.arguments
    # expression `b`
    assert (b_expr.symbol.name ==
        'OPERATOR_APPLICATION'), b_expr
    assert b_expr.operator == 'b', b_expr
    assert b_expr.arguments is None, b_expr
    # expression `/\ c`
    assert (conj.symbol.name ==
        'VERTICAL_LIST'), conj
    assert conj.operator == '/\\', conj
    assert len(conj.arguments) == 1, conj
    # conjunct `/\ c`
    conjunct, = conj.arguments
    assert (conjunct.symbol.name ==
        'VERTICAL_ITEM'), conjunct
    # expression `c`
    c_expr = conjunct.expression
    assert (c_expr.symbol.name ==
        'OPERATOR_APPLICATION'), c_expr
    assert c_expr.operator == 'c', c_expr
    assert c_expr.arguments is None, c_expr


def test_module_start_error():
    text = '----MODULEname----A==-5===='
    with pytest.raises(ValueError):
        _lr.parse(text)


def test_module_line_no_spaces():
    text = '----MODULE name----A==-5===='
    module = _lr.parse(text)
    assert module.symbol == 'module', module
    assert module.name == 'name', module
    assert module.extendees is None, module
    assert len(module.units) == 1, module
    a_def, = module.units
    # definition: operator name
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'A', a_def
    assert a_def.arity is None, a_def
    assert a_def.local is None, a_def
    # definition: expression
    a_expr = a_def.definiens
    assert_unary_op_app(a_expr, '-')
    assert len(a_expr.arguments) == 1, a_expr
    five, = a_expr.arguments
    assert_integer_numeral(five, '5')


def test_any_chars_in_module_error():
    text = '---- MODULE test ---- A == `1 ===='
    with pytest.raises(ValueError):
        _lr.parse(text)


def test_preamble_with_any_chars():
    module_text = '''
        ````` (*
        ---- MODULE test ----
        A == 2
        ====
        '''
    module = _lr.parse(module_text)
    assert module.symbol == 'module', module
    assert module.name == 'test', module
    assert module.extendees is None, module
    assert len(module.units) == 1, module
    a_def, = module.units
    # definition: operator name
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'A', a_def
    assert a_def.arity is None, a_def
    assert a_def.local is None, a_def
    # definition: expression
    a_expr = a_def.definiens
    assert_integer_numeral(a_expr, '2')


def test_preamble_resembles_module_start():
    module_text = '''
        ---- MODUL
        ---- MODULE test ----
        Q == 1 ++ 2
        ====
        '''
    module = _lr.parse(module_text)
    assert module.symbol == 'module', module
    assert module.name == 'test', module
    assert module.extendees is None, module
    assert len(module.units) == 1, module
    q_def, = module.units
    # definition: operator name
    assert q_def.symbol == 'operator_definition', q_def
    assert q_def.name == 'Q', q_def
    assert q_def.arity is None, q_def
    assert q_def.local is None, q_def
    # definition: expression
    q_expr = q_def.definiens
    assert q_expr.symbol == 'operator_application', q_expr
    assert q_expr.operator == '++', q_expr
    assert q_expr.arguments is not None, q_expr
    assert len(q_expr.arguments) == 2, q_expr
    one, two = q_expr.arguments
    assert_integer_numeral(one, '1')
    assert_integer_numeral(two, '2')


def test_text_after_main_module():
    module_text = '''
        ---- MODULE test ----
        INSTANCE M
        ====
        *) more text, including characters
        that would cause lexing errors: ```
        '''
    module = _lr.parse(module_text)
    assert module.symbol == 'module', module
    assert module.name == 'test', module
    assert module.extendees is None, module
    assert len(module.units) == 1, module
    mod_inst, = module.units
    assert mod_inst.symbol == 'instance', mod_inst
    assert mod_inst.name == 'M', mod_inst
    assert mod_inst.local is None, mod_inst
    assert mod_inst.with_substitution is None, mod_inst


def test_module_after_main_module():
    module_text = '''
        ---- MODULE test ----
        A(x) == 1
        ====

        ---- MODULE other ----
        ====
        '''
    module = _lr.parse(module_text)
    assert module.symbol == 'module', module
    assert module.name == 'test', module
    assert module.extendees is None, module
    assert len(module.units) == 1, module


def test_definitions_outside_main_module():
    module_name = 'preamble_comments'
    module_text = r'''
        A == 1
        ---- MODULE preamble_comments ----
        LOCAL B == 1
        ====
        A == 1
        '''
    module = _lr.parse(module_text)
    assert module.symbol == 'module', module
    assert module.name == module_name, module
    assert module.extendees is None, module
    assert len(module.units) == 1, module
    b_def, = module.units
    # `B` definition
    assert (b_def.symbol ==
        'operator_definition'), b_def
    assert b_def.name == 'B', b_def
    assert b_def.arity is None, b_def
    assert b_def.local is True, b_def
    # `B` definiens
    b_definiens = b_def.definiens
    assert_integer_numeral(b_definiens, '1')


def test_empty_module():
    module_text = '''
        ---- MODULE empty ----
        ====
        '''
    module = _lr.parse(module_text)
    assert module.symbol == 'module', module
    assert module.name == 'empty', module
    assert module.extendees is None, module
    assert module.units is None, module


def test_module_with_only_extends():
    source = '''
        ---- MODULE only_extends ----
        EXTENDS Sequences
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol == 'module', module
    assert module.name == 'only_extends', module.name
    assert len(module.extendees) == 1, module.extendees
    sequences, = module.extendees
    assert_operator_name(sequences, 'Sequences')
    assert module.units is None, module.units


def test_let_expression():
    text = '''
        ---- MODULE test ----
        A == LET
                x == 1
                y == a + b
             IN
                x !! y
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    let_expr = a_def.definiens
    assert let_expr.symbol == 'let', let_expr
    assert let_expr.definitions is not None, let_expr
    assert let_expr.expression is not None, let_expr
    defs = let_expr.definitions
    expr = let_expr.expression
    # definitions
    assert len(defs) == 2, defs
    x_def, y_def = defs
    assert_op_def(x_def, 'x')
    assert_integer_numeral(x_def.definiens, '1')
    assert_op_def(y_def, 'y')
    ab = y_def.definiens
    assert_binary_op_app(ab, '+')
    a, b = ab.arguments
    assert_operator_name(a, 'a')
    assert_operator_name(b, 'b')
    # `x !! y` expression
    assert_binary_op_app(expr, '!!')
    x, y = expr.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')


def test_constant_quantification():
    text = r'''
        ---- MODULE test ----
        A == \A x, y, z:  f(x, y) <= z
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert_quantification(expr, r'\A', 3)
    # `x, y, z`
    x, y, z = expr.declarations
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert_operator_name(z, 'z')
    # `f(x, y) <= z`
    pred = expr.predicate
    assert_binary_op_app(pred, '<=')
    fxy, z = pred.arguments
    assert_operator_name(z, 'z')
    assert_binary_op_app(fxy, 'f')
    x, y = fxy.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    text = r'''
        ---- MODULE test ----
        A == \E x, y \in S, z \in R:  g!:[x, y]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert_quantification(expr, r'\E', 3)
    # `x, y \in S, z \in R`
    x, y_in_s, z_in_r = expr.declarations
    assert_operator_name(x, 'x')
    assert_binary_op_app(y_in_s, r'\in')
    y, s = y_in_s.arguments
    assert_operator_name(y, 'y')
    assert_operator_name(s, 'S')
    assert_binary_op_app(z_in_r, r'\in')
    z, r = z_in_r.arguments
    assert_operator_name(z, 'z')
    assert_operator_name(r, 'R')
    # `g!:[x, y]`
    pred = expr.predicate
    assert pred.symbol == 'function_application', pred
    assert pred.function is not None, pred
    assert pred.arguments is not None, pred
    assert len(pred.arguments) == 2, pred.arguments
    x, y = pred.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # `g!:`
    sub = pred.function
    assert sub.symbol == 'subexpression_reference', sub
    assert sub.items is not None, sub
    assert len(sub.items) == 2, sub.items
    g, colon = sub.items
    assert_operator_name(g, 'g')
    assert colon == ':', colon


def test_temporal_quantification():
    text = r'''
        ---- MODULE test ----
        A == \AA x, y:  [](x = y) => <>(y = x)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert_temporal_quantification(expr, r'\AA', 2)
    # declarations
    x, y = expr.declarations
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # predicate
    pred = expr.predicate
    assert_binary_op_app(pred, '=>')
    always, eventually = pred.arguments
    assert_unary_op_app(always, '[]')
    assert_unary_op_app(eventually, '<>')
    ps, = always.arguments
    assert ps.symbol == 'parentheses', ps
    xy = ps.expression
    assert_binary_op_app(xy, '=')
    x, y = xy.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    ps, = eventually.arguments
    assert ps.symbol == 'parentheses', ps
    yx = ps.expression
    assert_binary_op_app(yx, '=')
    y, x = yx.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    text = r'''
        ---- MODULE test ----
        A == \EE x, y:  x = 1 /\ <>(x = y)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert_temporal_quantification(expr, r'\EE', 2)
    # declarations
    x, y = expr.declarations
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # predicate
    pred = expr.predicate
    assert_binary_op_app(pred, '/\\')
    x_eq_1, eventually = pred.arguments
    assert_binary_op_app(x_eq_1, '=')
    x, one = x_eq_1.arguments
    assert_operator_name(x, 'x')
    assert_integer_numeral(one, '1')
    assert_unary_op_app(eventually, '<>')
    ps, = eventually.arguments
    assert ps.symbol == 'parentheses', ps
    xy = ps.expression
    assert_binary_op_app(xy, '=')
    x, y = xy.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')


def test_choose_expression():
    text = '''
        ---- MODULE test ----
        A == CHOOSE x:  P(x)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    choose = a_def.definiens
    assert_choose(choose)
    assert_operator_name(choose.declaration, 'x')
    px = choose.predicate
    assert_unary_op_app(px, 'P')
    x, = px.arguments
    assert_operator_name(x, 'x')
    text = '''
        ---- MODULE test ----
        A == CHOOSE <<x>>:  P(x)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    choose = a_def.definiens
    assert_choose(choose)
    decl = choose.declaration
    assert_tuple(decl, 1)
    x, = decl.items
    assert_operator_name(x, 'x')
    px = choose.predicate
    assert_unary_op_app(px, 'P')
    x, = px.arguments
    assert_operator_name(x, 'x')
    text = '''
        ---- MODULE test ----
        A == CHOOSE <<x, y>>:  y + 2 * P(x) <= 1
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    choose = a_def.definiens
    assert_choose(choose)
    # `<<x, y>>`
    decl = choose.declaration
    assert_tuple(decl, 2)
    x, y = decl.items
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # `y + 2 * P(x)`
    pred = choose.predicate
    assert_binary_op_app(pred, '<=')
    expr, one = pred.arguments
    assert_integer_numeral(one, '1')
    assert_binary_op_app(expr, '+')
    y, expr = expr.arguments
    assert_operator_name(y, 'y')
    assert_binary_op_app(expr, '*')
    two, px = expr.arguments
    assert_integer_numeral(two, '2')
    assert_unary_op_app(px, 'P')
    x, = px.arguments
    assert_operator_name(x, 'x')
    text = r'''
        ---- MODULE test ----
        A == CHOOSE x \in S:  P(x)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    choose = a_def.definiens
    assert_choose(choose)
    # `x \in S`
    decl = choose.declaration
    assert_binary_op_app(decl, r'\in')
    x, s = decl.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(s, 'S')
    # `P(x)`
    pred = choose.predicate
    assert_unary_op_app(pred, 'P')
    x, = pred.arguments
    assert_operator_name(x, 'x')
    text = r'''
        ---- MODULE test ----
        A == CHOOSE <<x, y, z>> \in A \X B \X C:
                P(x, y, z)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    choose = a_def.definiens
    assert_choose(choose)
    # `<<x, y, z>> \in A \X B \X C`
    decl = choose.declaration
    assert_binary_op_app(decl, r'\in')
    xyz, abc = decl.arguments
    # `<<x, y, z>>`
    assert_tuple(xyz, 3)
    x, y, z = xyz.items
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert_operator_name(z, 'z')
    # `A \X B \X C`
    assert abc.symbol == 'operator_application', abc
    assert abc.operator == r'\X', abc.operator
    assert abc.arguments is not None, abc
    assert len(abc.arguments) == 3, abc.arguments
    a, b, c = abc.arguments
    assert_operator_name(a, 'A')
    assert_operator_name(b, 'B')
    assert_operator_name(c, 'C')
    # `P(x, y, z)`
    pred = choose.predicate
    assert pred.symbol == 'operator_application', pred
    assert pred.operator == 'P', pred.operator
    assert pred.arguments is not None, pred
    assert len(pred.arguments) == 3, pred.arguments
    x, y, z = pred.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    assert_operator_name(z, 'z')


def test_if_expression():
    text = '''
        ---- MODULE test ----
        A == IF x ++ y > 2
                THEN 5
                ELSE z + c
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    if_expr = a_def.definiens
    assert if_expr.symbol == 'if', if_expr
    assert if_expr.predicate is not None, if_expr
    assert_integer_numeral(if_expr.then, '5')
    assert if_expr.else_ is not None, if_expr
    # `x ++ y > 2`
    pred = if_expr.predicate
    assert_binary_op_app(pred, '>')
    xy, two = pred.arguments
    assert_integer_numeral(two, '2')
    assert_binary_op_app(xy, '++')
    x, y = xy.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # `z + c`
    zc = if_expr.else_
    assert_binary_op_app(zc, '+')
    z, c = zc.arguments
    assert_operator_name(z, 'z')
    assert_operator_name(c, 'c')


def test_case_expression():
    text = '''
        ---- MODULE test ----
        A == CASE x = 1 -> 1 [] x = 2 -> 2
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert expr.symbol == 'cases', expr
    assert expr.cases is not None, expr
    assert len(expr.cases) == 2, expr.cases
    assert expr.other is None, expr.other
    case_1, case_2 = expr.cases
    # `x = 1 -> 1`
    assert case_1.symbol == 'case_item', case_1
    assert case_1.predicate is not None, case_1
    assert_integer_numeral(case_1.expression, '1')
    pred = case_1.predicate
    assert_binary_op_app(pred, '=')
    x, one = pred.arguments
    assert_operator_name(x, 'x')
    assert_integer_numeral(one, '1')
    # `x = 2 -> 2`
    assert case_2.symbol == 'case_item', case_2
    assert case_2.predicate is not None, case_2
    assert_integer_numeral(case_2.expression, '2')
    pred = case_2.predicate
    assert_binary_op_app(pred, '=')
    x, two = pred.arguments
    assert_operator_name(x, 'x')
    assert_integer_numeral(two, '2')
    text = '''
        ---- MODULE test ----
        A == CASE x = 1 -> 1 [] x = 2 -> 2
                []OTHER -> 15
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert expr.symbol == 'cases', expr
    assert expr.cases is not None, expr
    assert len(expr.cases) == 2, expr.cases
    assert expr.other is not None, expr
    case_1, case_2 = expr.cases
    # `x = 1 -> 1`
    assert case_1.symbol == 'case_item', case_1
    assert case_1.predicate is not None, case_1
    assert_integer_numeral(case_1.expression, '1')
    pred = case_1.predicate
    assert_binary_op_app(pred, '=')
    x, one = pred.arguments
    assert_operator_name(x, 'x')
    assert_integer_numeral(one, '1')
    # `x = 2 -> 2`
    assert case_2.symbol == 'case_item', case_2
    assert case_2.predicate is not None, case_2
    assert_integer_numeral(case_2.expression, '2')
    pred = case_2.predicate
    assert_binary_op_app(pred, '=')
    x, two = pred.arguments
    assert_operator_name(x, 'x')
    assert_integer_numeral(two, '2')
    # `OTHER -> 15`
    assert_integer_numeral(expr.other, '15')


def test_lambda_operator():
    text = '''
        ---- MODULE test ----
        A == f(LAMBDA x: x + 1, y)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    f_app = a_def.definiens
    assert_binary_op_app(f_app, 'f')
    lambda_op, y = f_app.arguments
    assert_operator_name(y, 'y')
    # `LAMBDA x: x + 1`
    assert lambda_op.symbol == 'lambda', lambda_op
    assert lambda_op.parameters is not None, lambda_op
    assert lambda_op.expression is not None, lambda_op
    x, = lambda_op.parameters
    assert_operator_name(x, 'x')
    x_plus_1 = lambda_op.expression
    assert_binary_op_app(x_plus_1, '+')
    x, one = x_plus_1.arguments
    assert_operator_name(x, 'x')
    assert_integer_numeral(one, '1')


def test_let_expr_as_arg_2():
    text = '''
        ---- MODULE test ----
        A == P(x, LET u == 1 IN u + 4)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert_binary_op_app(expr, 'P')
    x, let_expr = expr.arguments
    assert_operator_name(x, 'x')
    assert let_expr.symbol == 'let', let_expr
    assert let_expr.definitions is not None, let_expr
    assert let_expr.expression is not None, let_expr
    defs = let_expr.definitions
    expr = let_expr.expression
    # `u == 1`
    assert len(defs) == 1, defs
    u_def, = defs
    assert_op_def(u_def, 'u')
    assert_integer_numeral(u_def.definiens, '1')
    # `u + 4`
    assert_binary_op_app(expr, '+')
    u, four = expr.arguments
    assert_operator_name(u, 'u')
    assert_integer_numeral(four, '4')


def test_recursive_inside_let():
    text = '''
        ---- MODULE recursive ----
        A == LET
                RECURSIVE B(_)
                B(x) == 1
             IN
                B(2)
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol == 'module', module
    assert module.name == 'recursive', module.name
    assert module.extendees is None, module.extendees
    assert module.units is not None, module.units
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    assert a_def.arity is None, a_def.arity
    expr = a_def.definiens
    assert expr.symbol == 'let', expr
    assert expr.definitions is not None, expr.definitions
    assert len(expr.definitions) == 2, expr.definitions
    assert expr.expression is not None, expr.expression
    recursive, b_def = expr.definitions
    b2 = expr.expression
    # `RECURSIVE B(_)`
    assert recursive.symbol == 'recursive_operators', (
        recursive)
    assert recursive.names is not None, recursive
    assert len(recursive.names) == 1, recursive.names
    b_sig, = recursive.names
    assert_unary_op_app(b_sig, 'B')
    arg, = b_sig.arguments
    assert arg == '_', arg
    # `B(x) == 1`
    assert b_def.symbol == 'operator_definition', b_def
    assert b_def.name == 'B', b_def.name
    assert b_def.arity is not None, b_def
    assert len(b_def.arity) == 1, b_def.arity
    assert b_def.local is None, b_def.local
    assert b_def.function is None, b_def.function
    x, = b_def.arity
    assert_operator_name(x, 'x')
    one = b_def.definiens
    assert_integer_numeral(one, '1')
    # `B(2)`
    assert_unary_op_app(b2, 'B')
    two, = b2.arguments
    assert_integer_numeral(two, '2')


def test_lambda_inside_undelimited():
    module_name = 'lambda_inside_undelimited'
    source = rf'''
        ---- MODULE {module_name} ----
        B(r(_)) == r(1)
        A == \A x:  B(LAMBDA y: TRUE) /\ FALSE
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol.name == 'MODULE', module
    assert module.name == module_name, module
    assert len(module.units) == 2, module
    b_def, a_def = module.units
    # `B` definition
    assert (b_def.symbol.name ==
        'OPERATOR_DEFINITION'), b_def
    assert b_def.name == 'B', b_def
    assert b_def.arity is not None, b_def
    assert b_def.local is None, b_def
    # `B` signature
    b_parameters = b_def.arity
    assert len(b_parameters) == 1, b_parameters
    # parameter `r`
    r_param, = b_parameters
    assert (r_param.symbol.name ==
        'OPERATOR_APPLICATION'), r_param
    assert r_param.operator == 'r', r_param
    assert r_param.arguments == ['_'], r_param
    # `B` definiens
    b_definiens = b_def.definiens
    assert (b_definiens.symbol.name ==
        'OPERATOR_APPLICATION'), b_definiens
    assert b_definiens.operator == 'r', b_definiens
    assert len(
        b_definiens.arguments) == 1, b_definiens
    # argument of `r(1)`
    one, = b_definiens.arguments
    assert one.symbol.name == 'INTEGRAL_NUMERAL', one
    assert one.value == '1', one
    # `B` definition
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def
    assert a_def.arity is None, a_def
    assert a_def.local is None, a_def
    # `A` definiens
    a_definiens = a_def.definiens
    assert (a_definiens.symbol.name ==
        'QUANTIFICATION'), a_definiens
    assert a_definiens.quantifier == '\\A', a_definiens
    # quantifier declaree `x`
    a_declarations = a_definiens.declarations
    assert len(a_declarations) == 1, a_declarations
    x_declaration, = a_declarations
    assert (x_declaration.symbol.name ==
        'OPERATOR_APPLICATION'), x_declaration
    assert x_declaration.operator == 'x', x_declaration
    assert x_declaration.arguments is None, x_declaration
    # quantifier predicate
    a_predicate = a_definiens.predicate
    assert (a_predicate.symbol.name ==
        'OPERATOR_APPLICATION'), a_predicate
    assert a_predicate.operator == '/\\', a_predicate
    assert len(a_predicate.arguments) == 2, a_predicate
    arg1, arg2 = a_predicate.arguments
    # expression `B(LAMBDA y: TRUE)`
    assert (arg1.symbol.name ==
        'OPERATOR_APPLICATION'), arg1
    assert arg1.operator == 'B', arg1
    assert len(arg1.arguments) == 1, arg1
    # operator `LAMBDA y: TRUE`
    lambda_y, = arg1.arguments
    assert lambda_y.symbol.name == 'LAMBDA', lambda_y
    assert len(lambda_y.parameters) == 1, lambda_y
    # `LAMBDA` parameter: `y`
    y_param, = lambda_y.parameters
    assert (y_param.symbol.name ==
        'OPERATOR_APPLICATION'), y_param
    assert y_param.operator == 'y', y_param
    assert y_param.arguments is None, y_param
    # `LAMBDA` expression: `TRUE`
    lambda_expr = lambda_y.expression
    assert (lambda_expr.symbol.name ==
        'BOOLEAN_LITERAL'), lambda_expr
    assert lambda_expr.value == 'TRUE', lambda_expr
    # conjunct `FALSE`
    assert (arg2.symbol.name ==
        'BOOLEAN_LITERAL'), arg2
    assert arg2.value == 'FALSE', arg2


def test_nested_undelimited():
    source = r'''
        ---- MODULE let_quantification ----
        EXTENDS
            Integers

        A == LET
                b == FALSE
             IN
                \A x, y \in S:  b
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol.name == 'MODULE', module
    assert module.name == 'let_quantification', module.name
    assert len(module.extendees) == 1, module.extendees
    integers, = module.extendees
    assert_operator_name(integers, 'Integers')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert a_def.symbol == 'operator_definition', (
        a_def.symbol)
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.function is None, a_def.function
    let = a_def.definiens
    # `LET`
    assert let.symbol.name == 'LET', let.symbol
    assert len(let.definitions) == 1, let.definitions
    b_def, = let.definitions
    qexpr = let.expression
    # `b == FALSE`
    assert b_def.symbol.name == 'OPERATOR_DEFINITION', (
        b_def.symbol)
    assert b_def.arity is None, b_def.arity
    assert b_def.local is None, b_def.local
    assert b_def.function is None, b_def.function
    expr = b_def.definiens
    assert_boolean_literal(expr, 'FALSE')
    # `\A x, y \in S:  b`
    assert qexpr.symbol.name == 'QUANTIFICATION', (
        qexpr.symbol)
    assert qexpr.quantifier == '\\A', qexpr.quantifier
    assert len(qexpr.declarations) == 2, qexpr.declarations
    decls = qexpr.declarations
    pred = qexpr.predicate
    # `x, y \in S`
    x, y_in_s = decls
    assert_operator_name(x, 'x')
    assert_binary_op_app(y_in_s, '\\in')
    y, s = y_in_s.arguments
    assert_operator_name(y, 'y')
    assert_operator_name(s, 'S')
    # `b`
    assert_operator_name(pred, 'b')
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_let_expression_inside_theorem():
    source = '''
        ---- MODULE let_expr ----
        THEOREM
            LET a == FALSE IN TRUE
        BY TRUE
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol == 'module', module.symbol
    assert module.name == 'let_expr', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    theorem, = module.units
    assert theorem.symbol == 'theorem', theorem.symbol
    assert theorem.name is None, theorem.name
    assert theorem.theorem_keyword == 'THEOREM', (
        theorem.theorem_keyword)
    let = theorem.goal
    proof = theorem.proof
    # theorem assertion
    assert let.symbol == 'let', let.symbol
    assert len(let.definitions) == 1, len(let.definitions)
    defn, = let.definitions
    in_expr = let.expression
    # `a == FALSE`
    assert defn.symbol == 'operator_definition', (
        defn.symbol)
    assert defn.name == 'a', defn.name
    assert defn.arity is None, defn.arity
    assert defn.local is None, defn.local
    assert defn.function is None, defn.function
    expr = defn.definiens
    assert_boolean_literal(expr, 'FALSE')
    # `TRUE`
    assert_boolean_literal(in_expr, 'TRUE')
    # proof
    assert proof.symbol == 'proof', proof.symbol
    assert proof.proof_keyword is None, proof.proof_keyword
    assert len(proof.steps) == 1, proof.steps
    leaf_proof, = proof.steps
    assert leaf_proof.symbol == 'by', leaf_proof.symbol
    assert leaf_proof.only is False, leaf_proof.only
    assert leaf_proof.names is None, leaf_proof.names
    assert len(leaf_proof.facts) == 1, leaf_proof.facts
    expr, = leaf_proof.facts
    assert_boolean_literal(expr, 'TRUE')
    # print
    text = _pp.pformat_ast(module)
    print(text)


def test_definition_inside_vertical_operator():
    parser = _lr.Parser()
    # module-scope definition indented less
    # than the preceeding vertical operator
    source = r'''
        ---- MODULE smaller_indent ----
        A == /\ 1
             /\ 2

        B == 3
        ====
        '''
    module = parser.parse(source)
    _check_def_inside_vop(
        module, 'smaller_indent')
    # module-scope definition indented more
    # than the preceeding vertical operator
    source = r'''
        ---- MODULE larger_indent ----
        A == /\ 1
             /\ 2

                B == 3
        ====
        '''
    module = parser.parse(source)
    _check_def_inside_vop(
        module, 'larger_indent')
    # definition on the same line
    # with a vertical operator
    source = r'''
        ---- MODULE same_line ----
        A == /\ 1
             /\ 2     B == 3
        ====
        '''
    module = parser.parse(source)
    _check_def_inside_vop(
        module, 'same_line')
    # definition inside `LET` that
    # is within a vertical operator
    source = r'''
        ---- MODULE let_inside_vertical ----
        A == /\ LET B == 3 IN B
        ====
        '''
    module = parser.parse(source)
    _check_def_inside_let(
        module, 'let_inside_vertical')


def _check_def_inside_let(
        module, module_name):
    # module
    assert module.symbol.name == 'MODULE', module
    assert module.name == module_name, module
    assert len(module.units) == 1, module
    # `A` definition
    a_def, = module.units
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def
    assert a_def.arity is None, a_def
    assert a_def.local is None, a_def
    # `A` definiens
    a_definiens = a_def.definiens
    assert (a_definiens.symbol.name ==
        'VERTICAL_LIST'), a_definiens
    assert a_definiens.operator == '/\\', a_definiens
    assert len(a_definiens.arguments) == 1, a_definiens
    # first conjunct
    item, = a_definiens.arguments
    assert item.symbol.name == 'VERTICAL_ITEM', item
    assert item.operator == '/\\', item
    # `LET` expression
    let = item.expression
    assert let.symbol.name == 'LET', let
    assert len(let.definitions) == 1, let
    # `B` definition
    b_def, = let.definitions
    assert (b_def.symbol.name ==
        'OPERATOR_DEFINITION'), b_def
    assert b_def.name == 'B', b_def
    assert b_def.arity is None, b_def
    assert b_def.local is None, b_def
    # `B` definiens
    b_definiens = b_def.definiens
    assert (b_definiens.symbol.name ==
        'INTEGRAL_NUMERAL'), b_definiens
    assert b_definiens.value == '3', b_definiens
    # `IN` expression
    in_expr = let.expression
    assert (in_expr.symbol.name ==
        'OPERATOR_APPLICATION'), in_expr
    assert in_expr.operator == 'B', in_expr
    assert in_expr.arguments == None, in_expr


def _check_def_inside_vop(
        module, module_name):
    # module
    assert module.symbol.name == 'MODULE', module
    assert module.name == module_name, module
    assert len(module.units) == 2, module
    a_def, b_def = module.units
    # `A` definition
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def
    assert a_def.arity is None, a_def
    assert a_def.local is None, a_def
    # `A` definiens
    a_definiens = a_def.definiens
    assert (a_definiens.symbol.name ==
        'VERTICAL_LIST'), a_definiens
    assert a_definiens.operator == '/\\', a_definiens
    assert len(a_definiens.arguments) == 2, a_definiens
    item_1, item_2 = a_definiens.arguments
    # first conjunct
    assert (item_1.symbol.name ==
        'VERTICAL_ITEM'), item_1
    assert item_1.operator == '/\\', item_1
    one = item_1.expression
    assert (one.symbol.name ==
        'INTEGRAL_NUMERAL'), one
    assert one.value == '1', one
    # second conjunct
    assert (item_2.symbol.name ==
        'VERTICAL_ITEM'), item_2
    assert item_2.operator == '/\\', item_2
    two = item_2.expression
    assert (two.symbol.name ==
        'INTEGRAL_NUMERAL'), two
    assert two.value == '2', two
    # `B` definition
    assert (b_def.symbol.name ==
        'OPERATOR_DEFINITION'), b_def
    assert b_def.name == 'B', b_def
    assert b_def.arity is None, b_def
    assert b_def.local is None, b_def
    # `B` definiens
    b_definiens = b_def.definiens
    assert (b_definiens.symbol.name ==
        'INTEGRAL_NUMERAL'), b_definiens
    assert b_definiens.value == '3', b_definiens


def test_present_proof_keyword_define():
    # `DEFINE` keyword in proof step
    text = '''
        ---- MODULE present_DEFINE ----
        THEOREM TRUE
        <1> DEFINE A == 1 B == 2
                C == 3
        <1> QED
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.name == 'present_DEFINE', module.name
    assert len(module.units) == 1, module.units
    thm, = module.units
    # theorem
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    # goal
    assert_boolean_literal(thm.goal, 'TRUE')
    # proof
    assert thm.proof is not None
    proof = thm.proof
    assert proof.symbol == 'proof'
    assert proof.proof_keyword is None, proof.proof_keyword
    assert len(proof.steps) == 2, proof.steps
    define_step, qed = proof.steps
    # `DEFINE` step
    assert define_step.symbol == 'proof_step', define_step
    assert define_step.name == '<1>', define_step.name
    assert define_step.proof is None, define_step.proof
    assert define_step.proof_keyword is None, (
        define_step.proof_keyword)
    assert define_step.main is not None, define_step
    define = define_step.main
    assert define.symbol == 'define', define
    assert define.keyword == 'DEFINE', define.keyword
    assert define.definitions is not None, define
    assert len(define.definitions) == 3, define.definitions
    # definitions
    # operator A
    a_def, b_def, c_def = define.definitions
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.function is None, a_def.function
    a_expr = a_def.definiens
    assert_integer_numeral(a_expr, '1')
    # operator B
    assert b_def.symbol == 'operator_definition', b_def
    assert b_def.name == 'B', b_def.name
    assert b_def.arity is None, b_def.arity
    assert b_def.local is None, b_def.local
    assert b_def.function is None, b_def.function
    b_expr = b_def.definiens
    assert_integer_numeral(b_expr, '2')
    # operator C
    assert c_def.symbol == 'operator_definition', c_def
    assert c_def.name == 'C', c_def.name
    assert c_def.arity is None, c_def.arity
    assert c_def.local is None, c_def.local
    assert c_def.function is None, c_def.function
    c_expr = c_def.definiens
    assert_integer_numeral(c_expr, '3')
    # `QED` step
    assert qed.symbol == 'proof_step', qed
    assert qed.name == '<1>', qed.name
    assert qed.main == 'QED', qed.main
    assert qed.proof is None, qed.proof
    assert qed.proof_keyword is None, qed.proof_keyword


def test_optional_proof_keyword_define():
    # no `DEFINE` keyword in proof step
    source = '''
        ---- MODULE optional_DEFINE ----
        THEOREM TRUE
        <1> A == 1
            B == 2
        <1> QED

        C == 3
        ====
        '''
    module = _lr.parse(source)
    # module
    assert module.symbol.name == 'MODULE', module
    assert module.name == 'optional_DEFINE', module
    assert module.extendees is None, module.extendees
    assert len(module.units) == 2, module
    thm, c_def = module.units
    # theorem
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm
    # theorem assertion
    goal = thm.goal
    assert (goal.symbol.name ==
        'BOOLEAN_LITERAL'), goal
    assert goal.value == 'TRUE', goal
    # proof
    proof = thm.proof
    assert proof.symbol.name == 'PROOF', proof
    assert len(proof.steps) == 2, proof
    # steps
    defs_step, qed_step = proof.steps
    # proof first step
    assert (defs_step.symbol.name ==
        'PROOF_STEP'), defs_step
    assert defs_step.proof is None, defs_step
    # step number of first step
    step_num = defs_step.name
    # definitions
    define_main = defs_step.main
    assert define_main.symbol == 'define', define_main
    assert define_main.keyword is None, (
        define_main.keyword)
    assert len(
        define_main.definitions) == 2, define_main
    a_def, b_def = define_main.definitions
    # `A` definition
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    # `A` definiens
    a_definiens = a_def.definiens
    assert (a_definiens.symbol.name ==
        'INTEGRAL_NUMERAL'), a_definiens
    assert a_definiens.value == '1', a_definiens
    # `B` definition
    assert (b_def.symbol.name ==
        'OPERATOR_DEFINITION'), b_def
    assert b_def.name == 'B', b_def.name
    assert b_def.arity is None, b_def.arity
    assert b_def.local is None, b_def.local
    # `B` definiens
    b_definiens = b_def.definiens
    assert (b_definiens.symbol.name ==
        'INTEGRAL_NUMERAL'), b_definiens
    assert b_definiens.value == '2', b_definiens
    # QED step
    assert qed_step.main == 'QED', qed_step


def test_define_without_next_proof_step():
    # NOTE: The TLA+2 grammar requires that
    # proofs include a QED step.
    # So there is no ambiguity where `DEFINE`
    # definitions end, and where module-scope
    # definitions start.
    #
    # The parser can parse also incomplete
    # proofs, i.e., without QED step.
    text = '''
        ---- MODULE no_qed ----
        LEMMA TRUE
        <1> a == 1 b == 2
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'no_qed', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    lemma, = module.units
    # LEMMA
    assert lemma.symbol == 'theorem', lemma
    assert lemma.theorem_keyword == 'LEMMA', (
        lemma.theorem_keyword)
    assert lemma.name is None, lemma.name
    assert lemma.goal is not None, lemma
    assert_boolean_literal(lemma.goal, 'TRUE')
    assert lemma.proof is not None, lemma
    proof = lemma.proof
    assert proof.symbol == 'proof', proof.symbol
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step, = proof.steps
    # `DEFINE` step
    assert step.symbol == 'proof_step', step
    assert step.name == '<1>', step.name
    assert step.proof is None, step.proof
    assert step.proof_keyword is None, step.proof_keyword
    assert step.main is not None, step
    define = step.main
    assert define.symbol == 'define', define
    assert define.keyword is None, define.keyword
    assert define.definitions is not None, define
    assert len(define.definitions) == 2, define.definitions
    # definitions
    # operator A
    a_def, b_def = define.definitions
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'a', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.function is None, a_def.function
    a_expr = a_def.definiens
    assert_integer_numeral(a_expr, '1')
    # operator B
    assert b_def.symbol == 'operator_definition', b_def
    assert b_def.name == 'b', b_def.name
    assert b_def.arity is None, b_def.arity
    assert b_def.local is None, b_def.local
    assert b_def.function is None, b_def.function
    b_expr = b_def.definiens
    assert_integer_numeral(b_expr, '2')


def test_define_proof_step_then_theorem():
    text = '''
        ---- MODULE no_qed ----
        PROPOSITION TRUE
        <1>2. a == 1 THEOREM TRUE
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'no_qed', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 2, module.units
    lemma, thm = module.units
    # LEMMA
    assert lemma.symbol == 'theorem', lemma
    assert lemma.theorem_keyword == 'PROPOSITION', (
        lemma.theorem_keyword)
    assert lemma.name is None, lemma.name
    assert lemma.goal is not None, lemma
    assert_boolean_literal(lemma.goal, 'TRUE')
    assert lemma.proof is not None, lemma
    proof = lemma.proof
    assert proof.symbol == 'proof', proof.symbol
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step, = proof.steps
    assert step.symbol == 'proof_step', step
    assert step.name == '<1>2.', step.name
    assert step.proof is None, step.proof
    assert step.proof_keyword is None, step.proof_keyword
    assert step.main is not None, step
    define = step.main
    assert define.symbol == 'define', define
    assert define.keyword is None, define.keyword
    assert define.definitions is not None, define
    assert len(define.definitions) == 1, define.definitions
    # definition
    # operator A
    a_def, = define.definitions
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'a', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.function is None, a_def.function
    a_expr = a_def.definiens
    assert_integer_numeral(a_expr, '1')
    # THEOREM
    assert thm.symbol == 'theorem', thm
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.name is None, thm.name
    assert thm.goal is not None, thm
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is None, thm.proof


def test_define_proof_step_then_hline():
    text = '''
        ---- MODULE no_qed ----
        LEMMA TRUE
        <1>1 a == 1 -----
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'no_qed', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 2, module.units
    lemma, hline = module.units
    assert lemma.symbol == 'theorem', lemma
    assert lemma.theorem_keyword == 'LEMMA', (
        lemma.theorem_keyword)
    assert lemma.name is None, lemma.name
    assert lemma.goal is not None, lemma
    assert_boolean_literal(lemma.goal, 'TRUE')
    assert lemma.proof is not None, lemma
    proof = lemma.proof
    assert proof.symbol == 'proof', proof.symbol
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step, = proof.steps
    assert step.symbol == 'proof_step', step
    assert step.name == '<1>1', step.name
    assert step.proof is None, step.proof
    assert step.proof_keyword is None, step.proof_keyword
    assert step.main is not None, step
    define = step.main
    assert define.symbol == 'define', define
    assert define.keyword is None, define.keyword
    assert define.definitions is not None, define
    assert len(define.definitions) == 1, define.definitions
    # definition
    # operator A
    a_def, = define.definitions
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'a', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.function is None, a_def.function
    a_expr = a_def.definiens
    assert_integer_numeral(a_expr, '1')
    assert hline == '-----', hline


def test_define_proof_step_then_variables_decl():
    text = '''
        ---- MODULE no_qed ----
        LEMMA TRUE
        <1>abc a == 1 VARIABLES x, y
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'no_qed', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 2, module.units
    lemma, decl = module.units
    # LEMMA
    assert lemma.symbol == 'theorem', lemma
    assert lemma.theorem_keyword == 'LEMMA', (
        lemma.theorem_keyword)
    assert lemma.name is None, lemma.name
    assert lemma.goal is not None, lemma
    assert_boolean_literal(lemma.goal, 'TRUE')
    assert lemma.proof is not None, lemma
    proof = lemma.proof
    assert proof.symbol == 'proof', proof.symbol
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step, = proof.steps
    assert step.symbol == 'proof_step', step
    assert step.name == '<1>abc', step.name
    assert step.proof is None, step.proof
    assert step.proof_keyword is None, step.proof_keyword
    assert step.main is not None, step
    define = step.main
    assert define.symbol == 'define', define
    assert define.keyword is None, define.keyword
    assert define.definitions is not None, define
    assert len(define.definitions) == 1, define.definitions
    # definition
    # operator A
    a_def, = define.definitions
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'a', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.function is None, a_def.function
    a_expr = a_def.definiens
    assert_integer_numeral(a_expr, '1')
    #  VARIABLES
    assert decl.symbol == 'variables', decl
    assert decl.keyword == 'VARIABLES', decl.keyword
    assert decl.names is not None, decl.names
    assert len(decl.names) == 2, decl.names
    x, y = decl.names
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')


def test_parsing_of_proofs():
    source = '''
        ---- MODULE theorem_and_proof ----
        THEOREM TRUE
        PROOF
        <1>1. TRUE
        <1> QED
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol.name == 'MODULE', module
    assert module.name == 'theorem_and_proof', module
    assert len(module.units) == 1, module
    theorem, = module.units
    # `THEOREM`
    assert (theorem.symbol.name ==
        'THEOREM'), theorem
    assert theorem.name is None, theorem
    # goal of theorem
    goal = theorem.goal
    assert goal.symbol.name == 'BOOLEAN_LITERAL', goal
    assert goal.value == 'TRUE', goal
    # `PROOF`
    proof = theorem.proof
    assert proof.symbol.name == 'PROOF', proof
    assert len(proof.steps) == 2, proof
    step, qed_step = proof.steps
    # step `<1>1`
    assert (step.symbol.name ==
        'PROOF_STEP'), step
    assert step.proof is None, step
    # step number `<1>1.`
    assert step.name == '<1>1.', step.name
    # expression `TRUE` in step `<1>1`
    main = step.main
    # `QED` step
    assert (qed_step.symbol.name ==
        'PROOF_STEP'), qed_step
    assert qed_step.main == 'QED', qed_step
    assert qed_step.proof is None, qed_step
    # step number `<1>` of `QED` step
    assert qed_step.name == '<1>', qed_step
    # theorem with a leaf proof
    source = '''
        ---- MODULE theorem_and_proof ----
        THEOREM TRUE
        PROOF
        <1>1. TRUE
        <1> QED
            BY <1>1
        ====
        '''
    module = _lr.parse(source)
    theorem, = module.units
    proof = theorem.proof
    _, qed_step = proof.steps
    assert (qed_step.symbol.name ==
        'PROOF_STEP'), qed_step
    assert qed_step.main == 'QED', qed_step
    assert qed_step.proof is not None, qed_step
    # `BY`
    by = qed_step.proof
    assert (by.symbol.name == 'BY'), by
    assert by.names is None, by
    # expressions of `BY`
    facts = by.facts
    assert len(facts) == 1, facts
    # fact `<1>1` in the leaf proof `BY <1>1`
    fact, = facts
    assert (fact.symbol.name ==
        'OPERATOR_APPLICATION'), fact
    assert fact.operator == '<1>1', fact
    assert fact.arguments is None, fact


def test_dot_prime():
    text = f'''
        ---- MODULE test ----
        A == f.x'
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert_unary_op_app(expr, "'")
    fx, = expr.arguments
    assert fx.symbol == 'field', fx
    assert fx.name == 'x', fx.name
    assert_operator_name(fx.expression, 'f')


def test_prime_dot():
    text = f'''
        ---- MODULE test ----
        A == f'.b
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert expr.symbol == 'field', expr
    assert expr.name == 'b', expr.name
    assert expr.expression is not None, expr
    fp = expr.expression
    assert_unary_op_app(fp, "'")
    f, = fp.arguments
    assert_operator_name(f, 'f')


def test_dot_function_application_prime():
    # The expression in this test is from
    # page 284 of the book "Specifying Systems".
    module_name = 'dot_func_prime'
    source = f'''
        ---- MODULE {module_name} ----
        A == a + b.c[d]'
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol == 'module', module
    assert module.name == module_name, module
    assert len(module.units) == 1, module.units
    # `A` definition
    a_def, = module.units
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def
    assert a_def.arity is None, a_def
    assert a_def.local is None, a_def
    # `A` definiens: `a + b.c[d]'`
    a_definiens = a_def.definiens
    assert (a_definiens.symbol.name ==
        'OPERATOR_APPLICATION'), a_definiens
    assert a_definiens.operator == '+', a_definiens
    assert len(a_definiens.arguments) == 2, a_definiens
    first, second = a_definiens.arguments
    # first summand: `a`
    assert (first.symbol.name ==
        'OPERATOR_APPLICATION'), first
    assert first.operator == 'a', first
    assert first.arguments is None, first
    # second summand: `b.c[d]'`
    assert (second.symbol.name ==
        'OPERATOR_APPLICATION'), second
    assert second.operator == "'", second
    assert len(second.arguments) == 1, second
    app, = second.arguments
    # function application `b.c[d]`
    assert (app.symbol.name ==
        'FUNCTION_APPLICATION'), app
    assert len(app.arguments) == 1, app
    func = app.function
    d_expr, = app.arguments
    # `d` expression
    assert (d_expr.symbol.name ==
        'OPERATOR_APPLICATION'), d_expr
    assert d_expr.operator == 'd', d_expr
    assert d_expr.arguments is None, d_expr
    # `b.c` expression
    assert func.symbol.name == 'FIELD', func
    b_expr = func.expression
    c_expr = func.name
    # expression `b`
    assert (b_expr.symbol.name ==
        'OPERATOR_APPLICATION'), b_expr
    assert b_expr.operator == 'b', b_expr
    assert b_expr.arguments is None, b_expr
    # field `c` of `b.c`
    assert c_expr == 'c', c_expr


def test_function_application_dot():
    module_name = 'dot_func_prime'
    source = f'''
        ---- MODULE {module_name} ----
        A == a[x].name
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol.name == 'MODULE', module
    assert module.name == module_name, module
    assert len(module.units) == 1, module
    # `A` definition
    a_def, = module.units
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def
    assert a_def.arity is None, a_def
    assert a_def.local is None, a_def
    # `A` definiens: `a[x].name`
    a_definiens = a_def.definiens
    assert (a_definiens.symbol.name ==
        'FIELD'), a_definiens
    a_x = a_definiens.expression
    name = a_definiens.name
    assert name == 'name', name
    # `a[x]`
    assert (a_x.symbol.name ==
        'FUNCTION_APPLICATION'), a_x
    assert len(a_x.arguments) == 1, a_x.arguments
    a_expr = a_x.function
    x_expr, = a_x.arguments
    assert_operator_name(a_expr, 'a')
    assert_operator_name(x_expr, 'x')


def test_nested_record_field_then_function():
    text = '''
        ---- MODULE test ----
        nested == f.x[y]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'nested')
    expr = op_def.definiens
    assert expr.symbol == 'function_application', expr
    assert expr.function is not None, expr
    assert expr.arguments is not None, expr
    assert len(expr.arguments) == 1, expr.arguments
    y, = expr.arguments
    assert_operator_name(y, 'y')
    func = expr.function
    assert func.symbol == 'field', func
    assert func.name == 'x', func.name
    assert func.expression is not None, func
    assert_operator_name(func.expression, 'f')


def test_record_fields():
    source = '''
        ---- MODULE record_fields ----
        A == LET b == FALSE IN b.c
        ====
        '''
    module = _lr.parse(source)
    assert module.symbol.name == 'MODULE', module.symbol
    assert module.name == 'record_fields', module.name
    assert len(module.units) == 1, module
    # `A` definition
    a_def, = module.units
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    assert a_def.name == 'A', a_def
    assert a_def.arity is None, a_def
    assert a_def.local is None, a_def
    # definiens of `A`
    a_definiens = a_def.definiens
    assert (a_definiens.symbol.name ==
        'LET'), a_definiens
    # definitions of `LET` expression
    definitions = a_definiens.definitions
    assert len(definitions) == 1, definitions
    # `b` definition
    b_def, = definitions
    assert (b_def.symbol.name ==
        'OPERATOR_DEFINITION'), b_def
    assert b_def.arity is None, b_def
    assert b_def.local is None, b_def
    # definiens of `b`
    b_definiens = b_def.definiens
    assert (b_definiens.symbol.name ==
        'BOOLEAN_LITERAL'), b_definiens
    assert b_definiens.value == 'FALSE', b_definiens
    # `IN` expression of `LET`
    b_c = a_definiens.expression
    assert (b_c.symbol.name ==
        'FIELD'), b_c
    assert b_c.name == 'c', b_c
    # expression `b`
    b_expr = b_c.expression
    assert (b_expr.symbol.name ==
        'OPERATOR_APPLICATION'), b_expr
    assert b_expr.operator == 'b', b_expr
    assert b_expr.arguments is None, b_expr
    #
    # multiple dots
    source = '''
        ---- MODULE record_fields ----
        A == a.b.c
        ====
        '''
    module = _lr.parse(source)
    assert len(module.units) == 1, module
    a_def, = module.units
    assert (a_def.symbol.name ==
        'OPERATOR_DEFINITION'), a_def
    # expression `a.b.c`
    a_b_c = a_def.definiens
    assert (a_b_c.symbol.name == 'FIELD'), a_b_c
    assert a_b_c.name == 'c', a_b_c
    # expression `a.b`
    a_b = a_b_c.expression
    assert (a_b.symbol.name == 'FIELD'), a_b
    assert a_b.name == 'b', a_b
    # expression `a`
    a_expr = a_b.expression
    assert (a_expr.symbol.name ==
        'OPERATOR_APPLICATION'), a_expr
    assert a_expr.operator =='a', a_expr
    assert a_expr.arguments is None, a_expr


def test_record_field_after_op_app():
    text = '''
        ---- MODULE test ----
        A == Op(1, 2).B
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert expr.symbol == 'field', expr
    assert expr.name == 'B', expr.name
    assert expr.expression is not None, expr
    op_app = expr.expression
    assert_binary_op_app(op_app, 'Op')
    one, two = op_app.arguments
    assert_integer_numeral(one, '1')
    assert_integer_numeral(two, '2')


def test_record_field_name_is_keyword():
    #
    # in record field
    text = '''
        ---- MODULE let_kw ----
        A == f.LET
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'let_kw')
    assert len(module.units) == 1, module.units
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert expr.symbol == 'field', expr
    assert expr.name == 'LET', expr.name
    assert expr.expression is not None, expr
    f = expr.expression
    assert_operator_name(f, 'f')
    #
    # in `EXCEPT`
    text = '''
        ---- MODULE module_kw ----
        g == [f EXCEPT !.MODULE = 4]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'module_kw')
    assert len(module.units) == 1, module.units
    g_def, = module.units
    assert_op_def(g_def, 'g')
    definiens = g_def.definiens
    assert definiens.symbol == 'except', definiens
    assert_operator_name(definiens.function, 'f')
    changes = definiens.changes
    assert len(changes) == 1, changes
    change, = changes
    assert change.symbol == 'function_change', change
    assert change.item is not None, change
    assert len(change.item) == 1, change.item
    func_arg, = change.item
    assert func_arg == 'MODULE', func_arg
    assert change.expression is not None, change
    assert_integer_numeral(change.expression, '4')


def test_at_symbol_within_except():
    text = '''
        ---- MODULE at_in_except ----
        R == [q EXCEPT ![d] = @ + 1]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'at_in_except')
    assert len(module.units) == 1, module.units
    r_def, = module.units
    assert_op_def(r_def, 'R')
    r_expr = r_def.definiens
    assert r_expr.symbol == 'except', r_expr
    assert_operator_name(r_expr.function, 'q')
    # `![d] = @ + 1`
    assert len(r_expr.changes) == 1, r_expr.changes
    change, = r_expr.changes
    assert change.symbol == 'function_change', change
    assert change.item is not None, change
    assert len(change.item) == 1, change.item
    # `d`
    func_args, = change.item
    assert len(func_args) == 1, func_args
    func_arg, = func_args
    assert_operator_name(func_arg, 'd')
    # `@ + 1`
    expr = change.expression
    assert expr is not None, change
    assert_binary_op_app(expr, '+')
    at, one = expr.arguments
    assert at == '@', at
    assert_integer_numeral(one, '1')


def test_at_symbol_within_proof():
    text = '''
        ---- MODULE at_in_proof_step ----
        THEOREM test == TRUE
        PROOF
        <1>1. TRUE
        <1>2. @ <=> TRUE
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'at_in_proof_step')
    assert len(module.units) == 1, module.units
    # `THEOREM`
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.name == 'test', thm.name
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.goal is not None, thm
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is not None, thm
    # `PROOF`
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is True, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 2, proof.steps
    step1, step2 = proof.steps
    # `<1>1`
    assert step1.symbol == 'proof_step', step1
    assert step1.name == '<1>1.', step1.name
    assert step1.proof_keyword is None, step1.proof_keyword
    assert step1.proof is None, step1.proof
    assert_boolean_literal(step1.main, 'TRUE')
    # `<1>2`
    assert step2.symbol == 'proof_step', step2
    assert step2.name == '<1>2.', step2.name
    assert step2.proof_keyword is None, step2.proof_keyword
    assert step2.proof is None, step2.proof
    assert step2.main is not None, step2
    expr = step2.main
    assert_binary_op_app(expr, '<=>')
    at, true = expr.arguments
    assert at == '@', at
    assert_boolean_literal(true, 'TRUE')


def test_instance_in_proof_step():
    text = '''
        ---- MODULE instance ----
        THEOREM TRUE
        <1>1. INSTANCE ModuleName
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'instance')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.name is None, thm.name
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.goal is not None, thm
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is not None, thm
    # `PROOF`
    proof = thm.proof
    assert proof.symbol == 'proof', proof
    assert proof.proof_keyword is None, proof.proof_keyword
    assert proof.steps is not None, proof
    assert len(proof.steps) == 1, proof.steps
    step1, = proof.steps
    # `<1>1`
    assert step1.symbol == 'proof_step', step1
    assert step1.name == '<1>1.', step1.name
    assert step1.proof_keyword is None, step1.proof_keyword
    assert step1.proof is None, step1.proof
    instance = step1.main
    assert instance.symbol == 'instance', instance
    assert instance.name == 'ModuleName', instance.name
    assert instance.with_substitution is None, (
        instance.with_substitution)
    assert instance.local is None, instance.local


def test_extends_subpackage():
    # This is a syntax experiment.
    text = '''
        ---- MODULE experiment ----
        EXTENDS package!subpackage!module_name
        ====
        '''
    module = _lr.parse(text)
    assert module.symbol == 'module', module
    assert module.name == 'experiment', module.name
    assert module.units is None, module.units
    assert module.extendees is not None, module
    assert len(module.extendees) == 1, module.extendees
    path, = module.extendees
    assert path.symbol == 'subexpression_reference', path
    assert len(path.items) == 3, path
    pkg, subpkg, module_name = path.items
    assert_operator_name(pkg, 'package')
    assert subpkg == 'subpackage', subpkg
    assert module_name == 'module_name', module_name


def test_neg_operator_precedence():
    text = r'''
        ---- MODULE prec_arg2 ----
        A == TRUE # ~ TRUE
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'prec_arg2')
    assert len(module.units) == 1, module
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert_binary_op_app(expr, '#')
    true, neg_true = expr.arguments
    assert_boolean_literal(true, 'TRUE')
    assert_unary_op_app(neg_true, '~')
    true, = neg_true.arguments
    assert_boolean_literal(true, 'TRUE')


def test_unary_minus_operator_precedence():
    source = r'''
        ---- MODULE experiment ----
        A == 1 * - 2
        ====
        '''
    module = _lr.parse(source)
    assert module is not None
    assert len(module.units) == 1, module
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert_binary_op_app(expr, '*')
    one, minus_two = expr.arguments
    assert_integer_numeral(one, '1')
    assert_unary_op_app(minus_two, '-')
    two, = minus_two.arguments
    assert_integer_numeral(two, '2')
    # unary minus has precedence 12
    # binary plus has precedence 10
    source = '-x + y'
    expr = _lr.parse_expr(source)
    assert expr is not None
    assert_binary_op_app(expr, '+')
    minus_x, y = expr.arguments
    assert_unary_op_app(minus_x, '-')
    x, = minus_x.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # unary minus has precedence 12
    # binary minus has precedence 11
    source = '-x - y'
    expr = _lr.parse_expr(source)
    assert expr is not None
    assert_binary_op_app(expr, '-')
    minus_x, y = expr.arguments
    assert_unary_op_app(minus_x, '-')
    x, = minus_x.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')
    # unary minus has precedence 12
    # binary * has precedence 13
    source = '-x * y'
    expr = _lr.parse_expr(source)
    assert expr is not None
    assert_unary_op_app(expr, '-')
    prod, = expr.arguments
    assert_binary_op_app(prod, '*')
    x, y = prod.arguments
    assert_operator_name(x, 'x')
    assert_operator_name(y, 'y')


def test_prime_function_application():
    text = " f[x]' "
    expr = _lr.parse_expr(text)
    assert expr is not None
    assert_unary_op_app(expr, "'")
    fx, = expr.arguments
    assert (fx.symbol.name ==
        'FUNCTION_APPLICATION'), fx
    assert len(fx.arguments) == 1, fx.arguments
    f_expr = fx.function
    x_expr, = fx.arguments
    assert_operator_name(f_expr, 'f')
    assert_operator_name(x_expr, 'x')
    text = " f'[x] "
    expr = _lr.parse_expr(text)
    assert (expr.symbol.name ==
        'FUNCTION_APPLICATION'), expr
    assert len(expr.arguments) == 1, expr.arguments
    f_primed = expr.function
    x_expr, = expr.arguments
    assert_operator_name(x_expr, 'x')
    assert_unary_op_app(f_primed, "'")
    f_expr, = f_primed.arguments
    assert_operator_name(f_expr, 'f')


def test_wf_name_subscript():
    text = '''
        ---- MODULE test ----
        A == WF_v(Next)
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    a_def, = module.units
    # definition: operator name
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.function is None, a_def.function
    # definition: expression
    expr = a_def.definiens
    assert expr.symbol == 'fairness', expr
    assert expr.operator == 'WF_', expr.operator
    # subscript
    assert_operator_name(expr.subscript, 'v')
    # action
    assert_operator_name(expr.action, 'Next')
    # format
    text = _pp.pformat_ast(module)
    print(text)


def test_wf_op_app_subscript():
    text = '''
        ---- MODULE test ----
        A == WF_f(x)(Next)
        ====
        '''
    module = _lr.parse(text)
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == 'test', module.name
    assert module.extendees is None, module.extendees
    assert len(module.units) == 1, module.units
    a_def, = module.units
    # definition: operator name
    assert a_def.symbol == 'operator_definition', a_def
    assert a_def.name == 'A', a_def.name
    assert a_def.arity is None, a_def.arity
    assert a_def.local is None, a_def.local
    assert a_def.function is None, a_def.function
    # definition: expression
    expr = a_def.definiens
    assert expr.symbol == 'fairness', expr
    assert expr.operator == 'WF_', expr.operator
    # subscript
    sub = expr.subscript
    assert sub.symbol == 'operator_application', sub
    assert sub.operator == 'f', sub
    assert len(sub.arguments) == 1, sub
    x, = sub.arguments
    assert_operator_name(x, 'x')
    # action
    assert_operator_name(expr.action, 'Next')
    # format
    text = _pp.pformat_ast(module)
    print(text)


def test_wf_instantiated_name_as_subscript():
    text = '''
        ---- MODULE test ----
        A == WF_M!vars(Next)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module
    a_def, = module.units
    assert_op_def(a_def, 'A')
    expr = a_def.definiens
    assert expr.symbol == 'fairness', expr
    assert expr.operator == 'WF_', expr.operator
    assert_operator_name(expr.action, 'Next')
    assert expr.subscript is not None, expr
    sub = expr.subscript
    assert sub.symbol == 'subexpression_reference', sub
    assert sub.items is not None, sub
    assert len(sub.items) == 2, sub
    m, vars_ = sub.items
    assert_operator_name(m, 'M')
    assert vars_ == 'vars', vars_


def test_wf_followed_by_infix():
    text = '''
        ---- MODULE test ----
        P == WF_v + 1(Next)
        ====
        '''
    with pytest.raises(ValueError):
        _lr.parse(text)


def test_wf_function_app_as_subscript():
    # Example from page 286 of "Specifying Systems"
    text = '''
        ---- MODULE test ----
        P == WF_f[x](Next)
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'P')
    # `WF_`
    expr = op_def.definiens
    assert expr.symbol == 'fairness', expr
    assert expr.operator == 'WF_', expr.operator
    assert_operator_name(expr.action, 'Next')
    assert expr.subscript is not None, expr
    # `f[x]`
    sub = expr.subscript
    assert sub.symbol == 'function_application', sub
    assert_operator_name(sub.function, 'f')
    assert sub.arguments is not None, sub
    assert len(sub.arguments) == 1, sub.arguments
    x, = sub.arguments
    assert_operator_name(x, 'x')


def test_subscripted_action_function_app_as_subscript():
    # As noted on page 286 of "Specifying Systems"
    # `[A]_f[x]` means `[A]_(f[x])`
    text = '''
        ---- MODULE test ----
        Action == [A]_f[x]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'Action')
    expr = op_def.definiens
    assert expr.symbol == 'subscripted_action', expr
    assert expr.operator == '[', expr
    assert_operator_name(expr.action, 'A')
    sub = expr.subscript
    assert sub.symbol == 'function_application', sub
    assert_operator_name(sub.function, 'f')
    assert sub.arguments is not None, sub
    assert len(sub.arguments) == 1, sub.arguments
    x, = sub.arguments
    assert_operator_name(x, 'x')
    text = '''
        ---- MODULE test ----
        Action == <<A>>_f[x]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'Action')
    expr = op_def.definiens
    assert expr.symbol == 'subscripted_action', expr
    assert expr.operator == '<<', expr
    assert_operator_name(expr.action, 'A')
    sub = expr.subscript
    assert sub.symbol == 'function_application', sub
    assert_operator_name(sub.function, 'f')
    assert sub.arguments is not None, sub
    assert len(sub.arguments) == 1, sub.arguments
    x, = sub.arguments
    assert_operator_name(x, 'x')


def test_nested_function_application():
    text = '''
        ---- MODULE test ----
        nested == f[x][y]
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'nested')
    expr = op_def.definiens
    assert expr.symbol == 'function_application', expr
    assert expr.function is not None, expr
    assert expr.arguments is not None, expr
    assert len(expr.arguments) == 1, expr.arguments
    y, = expr.arguments
    assert_operator_name(y, 'y')
    func = expr.function
    assert func.symbol == 'function_application', func
    assert_operator_name(func.function, 'f')
    assert func.arguments is not None, func
    args = func.arguments
    assert len(args) == 1, args
    x, = args
    assert_operator_name(x, 'x')


def test_subscripted_action_followed_by_infix():
    # As noted on page 285 of "Specifying Systems"
    # `<<A>>_x /\ B` means `(<<A>>_x) /\ B`
    text = r'''
        ---- MODULE test ----
        Action == <<A>>_x /\ B
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    op_def, = module.units
    assert_op_def(op_def, 'Action')
    conj = op_def.definiens
    assert_binary_op_app(conj, '/\\')
    expr, b = conj.arguments
    assert_operator_name(b, 'B')
    assert expr.symbol == 'subscripted_action', expr
    assert expr.operator == '<<', expr
    assert_operator_name(expr.action, 'A')
    x = expr.subscript
    assert_operator_name(x, 'x')


def test_module_name_in_def():
    text = '''
        ---- MODULE test ----
        THEOREM TRUE
        BY MODULE Integers DEF MODULE Sequences
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    thm, = module.units
    assert thm.symbol == 'theorem', thm
    assert thm.name is None, thm.name
    assert thm.theorem_keyword == 'THEOREM', (
        thm.theorem_keyword)
    assert thm.goal is not None, thm
    assert_boolean_literal(thm.goal, 'TRUE')
    assert thm.proof is not None, thm
    # `PROOF`
    proof = thm.proof
    assert proof.symbol == 'proof', proof.symbol
    assert proof.proof_keyword is None, proof.proof_keyword
    assert len(proof.steps) == 1, proof.steps
    leaf_proof, = proof.steps
    assert leaf_proof.symbol == 'by', leaf_proof.symbol
    assert leaf_proof.only is False, leaf_proof.only
    assert leaf_proof.names is not None, leaf_proof
    assert len(leaf_proof.names) == 1, leaf_proof.names
    assert leaf_proof.facts is not None, leaf_proof
    assert len(leaf_proof.facts) == 1, leaf_proof.facts
    modname, = leaf_proof.facts
    assert modname.symbol == 'module_name', modname
    assert modname.name == 'Integers', modname.name
    modname, = leaf_proof.names
    assert modname.symbol == 'module_name', modname
    assert modname.name == 'Sequences', modname.name


def test_module_name_in_use():
    text = '''
        ---- MODULE test ----
        USE DEF MODULE Integers
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    use, = module.units
    assert use.symbol == 'use', use
    assert use.facts is None, use.facts
    assert use.names is not None, use.names
    assert len(use.names) == 1, use.names
    modname, = use.names
    assert modname.symbol == 'module_name', modname
    assert modname.name == 'Integers', modname.name


def test_module_name_in_hide():
    text = '''
        ---- MODULE test ----
        HIDE DEF MODULE Integers
        ====
        '''
    module = _lr.parse(text)
    assert_module(module, 'test')
    assert len(module.units) == 1, module.units
    hide, = module.units
    assert hide.symbol == 'hide', hide
    assert hide.facts is None, hide.facts
    assert hide.names is not None, hide.names
    assert len(hide.names) == 1, hide.names
    modname, = hide.names
    assert modname.symbol == 'module_name', modname
    assert modname.name == 'Integers', modname.name


def test_tree_position_values():
    text = '''
        ---- MODULE test ----
        A == 15
        ====
        '''
    tree = _lr.parse(text)
    nodes = tla._ast.make_nodes()
    number = nodes.IntegralNumeral(
        value='15',
        start=_ast.Position(line=2, column=13),
        end=_ast.Position(line=2, column=15))
    op_def = nodes.OperatorDefinition(
        name='A',
        definiens=number,
        start=_ast.Position(line=2, column=8),
        end=_ast.Position(line=2, column=15))
    module = nodes.Module(
        name='test',
        units=[op_def],
        start=_ast.Position(line=1, column=8),
        end=_ast.Position(line=3, column=12))
    assert tree == module, tree


def test_tree_positions_nest():
    text = '''
        ---- MODULE test ----
        A(x, y) == x + y

        B == 25

        THEOREM TRUE
        <1>1. x = 1
            <2>1. TRUE
                OBVIOUS
        <1> QED
        ====
        '''
    tree = _lr.parse(text)
    _assert_subtree_positions_nest(tree)


def _assert_subtree_positions_nest(
        tree):
    """Raise `AssertionError` otherwise."""
    traversal = TreePositionCheck()
    traversal.traverse(tree)


class TreePositionCheck(
        tla._utils.Traversal):
    """Assert that subtree positions nest."""

    def p_default_check(
            self,
            tree,
            start=None,
            end=None):
        """_"""
        # init
        if start is None and end is None:
            start = tree.start
            end = tree.end
        if start is None or end is None:
            raise AssertionError(start, end)
        if tree.start is None:
            raise AssertionError(tree)
        if tree.end is None:
            raise AssertionError(tree)
        # tree node ?
        if hasattr(tree, 'symbol'):
            assert start <= tree.start, (
                start, tree.start)
            assert tree.end <= end, (
                tree.end, end)
        # recurse
        start = tree.start
        end = tree.end
        for item in tree:
            self.traverse(
                item,
                start=start,
                end=end)


def assert_module(
        module,
        module_name:
            str):
    """Assert module tree.

    With units.
    """
    assert module is not None
    assert module.symbol == 'module', module
    assert module.name == module_name, module.name
    assert module.extendees is None, module.extendees
    assert module.units is not None, module


def assert_op_def(
        op_def,
        operator_name:
            str):
    """Assert definition of operator,

    without parameters.
    """
    assert op_def.symbol == 'operator_definition', (
        op_def.symbol)
    assert op_def.name == operator_name, op_def.name
    assert op_def.arity is None, op_def.arity
    assert op_def.local is None, op_def.local
    assert op_def.function is None, op_def.function


def assert_unary_op_app(
        expr,
        operator_name:
            str):
    """Assert unary operator application."""
    assert expr.symbol == 'operator_application', (
        expr.symbol)
    assert expr.operator == operator_name, expr.operator
    assert len(expr.arguments) == 1, expr.arguments


def assert_binary_op_app(
        expr,
        operator_name:
            str):
    """Assert binary operator application."""
    assert expr.symbol == 'operator_application', (
        expr.symbol)
    assert expr.operator == operator_name, expr.operator
    assert len(expr.arguments) == 2, expr.arguments


def assert_operator_name(
        expr,
        operator_name:
            str):
    """Assert nullary operator application."""
    assert expr.symbol == 'operator_application', (
        expr.symbol)
    assert expr.operator == operator_name, expr.operator
    assert expr.arguments is None, expr.arguments


def assert_boolean_literal(
        expr,
        value:
            str):
    """Assert Boolean literal with `value`."""
    assert expr.symbol == 'boolean_literal', expr.symbol
    assert expr.value == value, expr.value


def assert_integer_numeral(
        expr,
        value:
            str):
    """Assert integral numeral with `value`."""
    assert expr.symbol == 'integral_numeral', expr.symbol
    assert expr.value == value, expr.value


def assert_tuple(
        expr,
        length:
            int):
    """Assert tuple with `length`-many items."""
    assert expr is not None
    assert expr.symbol == 'tuple', expr
    assert expr.items is not None, expr
    assert len(expr.items) == length, expr.items


def assert_quantification(
        expr,
        quantifier:
            str,
        n_declarations:
            int):
    """Assert constant quantification."""
    assert expr is not None
    assert expr.symbol == 'quantification', expr
    assert expr.quantifier == quantifier, expr.quantifier
    assert expr.declarations is not None, expr
    assert len(expr.declarations) == n_declarations, (
        expr.declarations)
    assert expr.predicate is not None, expr


def assert_temporal_quantification(
        expr,
        quantifier:
            str,
        n_declarations:
            int):
    """Assert temporal quantification."""
    assert expr is not None
    assert expr.symbol == 'temporal_quantification', expr
    assert expr.quantifier == quantifier, expr.quantifier
    assert expr.declarations is not None, expr
    assert len(expr.declarations) == n_declarations, (
        expr.declarations)
    assert expr.predicate is not None, expr


def assert_choose(
        expr):
    """Assert `CHOOSE` expression."""
    assert expr is not None
    assert expr.symbol == 'choose', expr
    assert expr.declaration is not None, expr
    assert expr.predicate is not None, expr


def assert_proof_step(
        step,
        name:
            str):
    """Assert `step` is a proof step.

    Without proof.
    """
    assert step is not None
    assert step.symbol == 'proof_step', step
    assert step.name == name, step.name
    assert step.proof_keyword is None, step.proof_keyword
    assert step.proof is None, step.proof
    assert step.main is not None, step


if __name__ == '__main__':
    # test_preamble_comments()
    # test_vertical_operators()
    # test_set_of_tuples()
    # test_unary_minus_as_argument()
    # test_set_theory_operators()
    # test_keyword_unary_operators()
    # test_unary_minus_as_operator()
    # test_set_slice_operator()
    # test_set_comprehension_operator()
    # test_quantifier_vertical_expression()
    # test_vertical_expr_proof_step()
    # test_quantifier_vertical_expression()
    # test_named_theorem()
    # test_quantifier_temporal()
    # test_unary_minus_operator_definition()
    # test_binary_operator_definition()
    # test_nested_proofs()
    # test_pipe_instantiation()
    # test_lambda_inside_undelimited()
    # test_eventually_always()
    # test_let_expression()
    # test_definition_inside_vertical_operator()
    # test_optional_proof_keyword_define()
    # test_dot_function_application_prime()
    # test_parsing_of_proofs()
    # test_record_fields()
    # test_define_without_next_proof_step_error()
    test_tree_positions_nest()
    print('tests completed')
