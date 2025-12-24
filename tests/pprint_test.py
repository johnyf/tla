"""Tests of module `tla._pprint`."""
import textwrap as _tw

import pytest
import tla._ast
import tla._lre as _lr
import tla._pprint as _pp


nodes = tla._ast.make_nodes()
pformat = _pp.pformat_ast


def test_axiom():
    # named AXIOM
    expression = _boolean_expr()
    axiom = nodes.Axiom(
        name='name',
        expression=expression)
    text = pformat(axiom)
    text_ = (
        'AXIOM name ==\n'
        '    TRUE')
    assert text == text_, text
    # unnamed AXIOM
    axiom = nodes.Axiom(
        expression=expression)
    text = pformat(axiom)
    text_ = (
        'AXIOM\n'
        '    TRUE')
    assert text == text_, text
    # named ASSUMPTION
    axiom = nodes.Axiom(
        name='true',
        expression=expression,
        axiom_keyword='ASSUMPTION')
    text = pformat(axiom)
    text_ = (
        'ASSUMPTION true ==\n'
        '    TRUE')
    assert text == text_, text
    # named ASSUME
    axiom = nodes.Axiom(
        name='true',
        expression=expression,
        axiom_keyword='ASSUME')
    text = pformat(axiom)
    text_ = (
        'ASSUME true ==\n'
        '    TRUE')
    assert text == text_, text
    # other
    axiom = nodes.Axiom(
        name='axiom_name',
        expression=expression,
        axiom_keyword='AXIOMS')
    with pytest.raises(ValueError):
        pformat(axiom)


def test_boolean_literal():
    # FALSE
    false = nodes.BooleanLiteral(
        value='FALSE')
    text = pformat(false)
    text_ = 'FALSE'
    assert text == text_, text
    # TRUE
    true = nodes.BooleanLiteral(
        value='TRUE')
    text = pformat(true)
    text_ = 'TRUE'
    assert text == text_, text
    # other
    other = nodes.BooleanLiteral(
        value='TRUES')
    with pytest.raises(ValueError):
        pformat(other)


def test_by():
    indent = 4 * '\x20'
    # BY ONLY
    expr = _x_eq_one()
    op_name = nodes.OperatorApplication(
        operator='operator_name')
    facts = [expr]
    names = [op_name]
    by = nodes.By(
        only=True,
        facts=facts,
        names=names,
        keyword='DEF')
    text = pformat(by)
    text_ = f'{indent}BY ONLY x = 1 DEF operator_name'
    assert text == text_, text
    # with commas
    facts = [expr, op_name]
    by = nodes.By(
        facts=facts)
    text = pformat(by)
    text_ = f'{indent}BY x = 1, operator_name'
    assert text == text_, text
    # with commas in DEF
    other_op = nodes.OperatorApplication(
        operator='other_op')
    names = [op_name, other_op]
    by = nodes.By(
        names=names,
        keyword='DEFS')
    text = pformat(by)
    text_ = f'{indent}BY DEFS operator_name, other_op'
    assert text == text_, text


def test_cases():
    # 2 cases
    x = _opname('x')
    y = _opname('y')
    u = _opname('u')
    v = _opname('v')
    case_1 = nodes.CaseItem(
        predicate=x,
        expression=u)
    case_2 = nodes.CaseItem(
        predicate=y,
        expression=v)
    cases = [case_1, case_2]
    cases_tree = nodes.Cases(
        cases=cases)
    text = pformat(cases_tree)
    text_ = 'CASE x -> u [] y -> v'
    assert text == text_, text
    # 1 case, OTHER
    expr = _x_eq_one()
    cases = [case_2]
    cases_tree = nodes.Cases(
        cases=cases,
        other=expr)
    text = pformat(cases_tree)
    text_ = 'CASE y -> v [] OTHER -> x = 1'
    assert text == text_, text
    # 3 cases, OTHER
    x_in_s = _x_in_s()
    w = _opname('w')
    case_3 = nodes.CaseItem(
        predicate=x_in_s,
        expression=w)
    cases = [case_1, case_2, case_3]
    cases_tree = nodes.Cases(
        cases=cases,
        other=expr)
    text = pformat(cases_tree)
    text_ = (
        'CASE x -> u [] y -> v [] '
        r'x \in S -> w [] OTHER -> x = 1')
    assert text == text_, text


def test_case_item():
    predicate = _x_eq_one()
    expression = _boolean_expr()
    case_item = nodes.CaseItem(
        predicate=predicate,
        expression=expression)
    text = pformat(case_item)
    text_ = 'x = 1 -> TRUE'
    assert text == text_, text


def test_choose():
    declaration = _x_in_s()
    predicate = _x_eq_one()
    choose = nodes.Choose(
        declaration=declaration,
        predicate=predicate)
    text = pformat(choose)
    text_ = r'CHOOSE x \in S:  x = 1'
    assert text == text_, text


def test_constants():
    x = _opname('x')
    y = _opname('y')
    names = [x, y]
    constants = nodes.Constants(
        keyword='CONSTANTS',
        names=names)
    text = pformat(constants)
    text_ = 'CONSTANTS\n    x,\n    y'
    assert text == text_, text
    constant = nodes.Constants(
        keyword='CONSTANT',
        names=[_opname('b')])
    text = pformat(constant)
    text_ = 'CONSTANT\n    b'
    assert text == text_, text


def test_define():
    x_in_s = _x_in_s()
    op_def = nodes.OperatorDefinition(
        name='A',
        definiens=x_in_s)
    definitions = [op_def]
    # with keyword `DEFINE`
    define = nodes.Define(
        definitions=definitions,
        keyword='DEFINE')
    text = pformat(define)
    indent = 8 * '\x20'
    text_ = (
        'DEFINE\n'
        rf'{indent}A == x \in S')
    assert text == text_, text
    # without keyword `DEFINE`
    define = nodes.Define(
        definitions=definitions)
    text = pformat(define)
    text_ = r'A == x \in S'
    assert text == text_, text


def test_except():
    # dot
    function = _opname('f')
    item = ['x']
    expression = _x_eq_one()
    change = nodes.FunctionChange(
        item=item,
        expression=expression)
    changes = [change]
    except_ = nodes.Except(
        function=function,
        changes=changes)
    text = pformat(except_)
    text_ = '[f EXCEPT !.x = x = 1]'
    assert text == text_, text
    # brackets
    string_literal = nodes.StringLiteral(
        value='"x"')
    item = [
        [string_literal],
        ]
    change = nodes.FunctionChange(
        item=item,
        expression=expression)
    changes = [change]
    except_ = nodes.Except(
        function=function,
        changes=changes)
    text = pformat(except_)
    text_ = '[f EXCEPT !["x"] = x = 1]'
    assert text == text_, text


def test_fairness():
    operator = 'SF_'
    subscript = _opname('x')
    action = _opname('A')
    fairness = nodes.Fairness(
        operator=operator,
        subscript=subscript,
        action=action)
    text = pformat(fairness)
    text_ = 'SF_x(A)'
    assert text == text_, text


def test_field():
    expression = _opname('f')
    name = 'field_name'
    field = nodes.Field(
        expression=expression,
        name=name)
    text = pformat(field)
    text_ = 'f.field_name'
    assert text == text_, text


def test_float_numeral():
    numeral = '1.2'
    float_numeral = nodes.FloatNumeral(
        value=numeral)
    text = pformat(float_numeral)
    assert text == numeral, text


def test_function_pformat():
    x = _opname('x')
    y = _opname('y')
    s = _opname('S')
    arguments = [y, s]
    y_in_s = nodes.OperatorApplication(
        operator=r'\in',
        arguments=arguments)
    decl_exprs = [x, y_in_s]
    func_value = nodes.OperatorApplication(
        operator='+',
        arguments=[x, y])
    func = nodes.Function(
        declaration=decl_exprs,
        value=func_value)
    text = pformat(func)
    text_ = r'[x, y \in S |-> x + y]'
    assert text == text_, text


def test_function_application():
    func = _opname('f')
    x = _opname('x')
    y = _opname('y')
    arguments = [x, y]
    tree = nodes.FunctionApplication(
        function=func,
        arguments=arguments)
    text = pformat(tree)
    text_ = 'f[x, y]'
    assert text == text_, text


def test_function_change():
    exprs = [_opname('x')]
    name = 'y'
    item = [exprs, name]
    expression = _opname('z')
    change = nodes.FunctionChange(
        item=item,
        expression=expression)
    text = pformat(change)
    text_ = '![x].y = z'
    assert text == text_, text


def test_have():
    expr = _x_in_s()
    have = nodes.Have(
        expression=expr)
    text = pformat(have)
    text_ = r'HAVE x \in S'
    assert text == text_, text


def test_hide():
    theorem_name = _opname('theorem')
    lemma_name = _opname('lemma')
    op_name = _opname('Op')
    facts = [
        theorem_name,
        lemma_name]
    names = [op_name]
    hide = nodes.Hide(
        facts=facts,
        names=names,
        keyword='DEF')
    text = pformat(hide)
    text_ = 'HIDE theorem, lemma DEF Op'
    assert text == text_, text


def test_if_pformat():
    predicate = _opname('x')
    then = _opname('y')
    else_ = _opname('z')
    if_ = nodes.If(
        predicate=predicate,
        then=then,
        else_=else_)
    text = pformat(if_)
    text_ = 'IF x THEN y ELSE z'
    assert text == text_, text


def test_ifs():
    x = _opname('x')
    y = _opname('y')
    int_1 = nodes.IntegralNumeral(value='1')
    int_2 = nodes.IntegralNumeral(value='2')
    int_3 = nodes.IntegralNumeral(value='3')
    x_eq_1 = nodes.OperatorApplication(
        operator='=',
        arguments=[x, int_1])
    x_eq_2 = nodes.OperatorApplication(
        operator='=',
        arguments=[x, int_2])
    x_eq_3 = nodes.OperatorApplication(
        operator='=',
        arguments=[x, int_3])
    case_1 = nodes.IfItem(
        predicate=x,
        expression=x_eq_1)
    case_2 = nodes.IfItem(
        predicate=y,
        expression=x_eq_2)
    cases = [case_1, case_2]
    ifs_tree = nodes.Ifs(
        cases=cases,
        other=x_eq_3)
    text = pformat(ifs_tree)
    text_ = (
        'IF x THEN x = 1\n'
        '    ELIF y THEN x = 2\n'
        '    ELSE x = 3')
    assert text == text_, text


def test_if_item():
    x = _opname('x')
    x_in_s = _x_in_s()
    case = nodes.IfItem(
        predicate=x,
        expression=x_in_s)
    text = pformat(case)
    text_ = r'ELIF x THEN x \in S'
    assert text == text_, text


def test_instance():
    name = 'Module'
    instance = nodes.Instance(
        name=name)
    text = pformat(instance)
    text_ = 'INSTANCE Module'
    assert text == text_, text
    # WITH substitutions
    y = _opname('y')
    u = _opname('u')
    v = _opname('v')
    z_expr = nodes.OperatorApplication(
        operator='z',
        arguments=[u, v])
    substitute_x = nodes.WithInstantiation(
        name='x',
        expression=y)
    substitute_y = nodes.WithInstantiation(
        name='y',
        expression=z_expr)
    substitutions = [
        substitute_x,
        substitute_y]
    instance = nodes.Instance(
        name=name,
        with_substitution=substitutions)
    text = pformat(instance)
    text_ = (
        'INSTANCE Module WITH '
        'x <- y, y <- z(u, v)')
    assert text == text_, text
    # local
    instance = nodes.Instance(
        name=name,
        with_substitution=substitutions,
        local=True)
    text = pformat(instance)
    text_ = (
        'LOCAL INSTANCE Module WITH '
        'x <- y, y <- z(u, v)')
    assert text == text_, text


def test_integral_numeral():
    int_1 = nodes.IntegralNumeral(
        value='1')
    text = pformat(int_1)
    assert text == '1', text


def test_key_bound():
    s = _opname('S')
    tree = nodes.KeyBound(
        name='x',
        bound=s)
    text = pformat(tree)
    text_ = 'x: S'
    assert text == text_, text


def test_lambda():
    x = _opname('x')
    y = _opname('y')
    parameters = [x, y]
    expression = _x_in_s()
    tree = nodes.Lambda(
        parameters=parameters,
        expression=expression)
    text = pformat(tree)
    text_ = r'LAMBDA x, y:  x \in S'
    assert text == text_, text


def test_let():
    int_1 = nodes.IntegralNumeral(
        value='1')
    b_def = nodes.OperatorDefinition(
        name='b',
        definiens=int_1)
    definitions = [b_def]
    int_2 = nodes.IntegralNumeral(
        value='2')
    b = _opname('b')
    arguments = [int_2, b]
    expression = nodes.OperatorApplication(
        operator='*',
        arguments=arguments)
    let = nodes.Let(
        definitions=definitions,
        expression=expression)
    text = pformat(let)
    text_ = (
        '\nLET\n'
        '    b == 1\n'
        'IN\n'
        '    2 * b')
    assert text == text_, text


def test_module():
    int_1 = nodes.IntegralNumeral(
        value='1')
    a_def = nodes.OperatorDefinition(
        name='A',
        definiens=int_1)
    extendees = ['Integers']
    units = [a_def]
    module = nodes.Module(
        name='Module',
        extendees=extendees,
        units=units)
    text = pformat(module)
    text_ = (
        '--------------------------------'
        ' MODULE Module '
        '---------------------------------\n'
        'EXTENDS\n'
        '    Integers\n'
        'A == 1\n'
        '========================================'
        '========================================')
    assert text == text_, text


def test_module_name():
    module_name = 'Module'
    tree = nodes.ModuleName(
        name=module_name)
    text = pformat(tree)
    text_ = f'MODULE Module'
    assert text == text_, text


def test_obvious():
    tree = nodes.Obvious()
    text = pformat(tree)
    text_ = '    OBVIOUS'
    assert text == text_, text


def test_omitted():
    tree = nodes.Omitted()
    text = pformat(tree)
    text_ = '    OMITTED'
    assert text == text_, text


def test_operator_application():
    # prefix minus
    x = _opname('x')
    arguments = [x]
    tree = nodes.OperatorApplication(
        operator='-',
        arguments=arguments)
    text = pformat(tree)
    text_ = '- x'
    assert text == text_, text
    # infix minus
    y = _opname('y')
    arguments = [x, y]
    tree = nodes.OperatorApplication(
        operator='-',
        arguments=arguments)
    text = pformat(tree)
    text_ = 'x - y'
    assert text == text_, text
    # postfix `^*`
    arguments = [y]
    tree = nodes.OperatorApplication(
        operator='^*',
        arguments=arguments)
    text = pformat(tree)
    text_ = 'y^*'
    assert text == text_, text
    # infix conjunction
    arguments = [x, y]
    tree = nodes.OperatorApplication(
        operator='/\\',
        arguments=arguments)
    text = pformat(tree)
    text_ = r'x /\ y'
    assert text == text_, text
    # between-operator `\X`
    z = _opname('z')
    arguments = [x, y, z]
    tree = nodes.OperatorApplication(
        operator=r'\X',
        arguments=arguments)
    text = pformat(tree)
    text_ = r'x \X y \X z'
    assert text == text_, text
    # nonfix operator
    tree = nodes.OperatorApplication(
        operator='Op',
        arguments=arguments)
    text = pformat(tree)
    text_ = r'Op(x, y, z)'
    assert text == text_, text


def test_operator_application_infix_as_nonfix():
    # `+(x, y)` infix as nonfix
    x = _opname('x')
    y = _opname('y')
    arguments = [x, y]
    tree = nodes.OperatorApplication(
        operator='+',
        arguments=arguments,
        nonfix=True)
    text = pformat(tree)
    text_ = '+(x, y)'
    assert text == text_, text


def test_operator_application_prefix_as_nonfix():
    # `-(z)` prefix as nonfix
    z = _opname('z')
    arguments = [z]
    tree = nodes.OperatorApplication(
        operator='-',
        arguments=arguments,
        nonfix=True)
    text = pformat(tree)
    text_ = '-(z)'
    assert text == text_, text


def test_operator_application_postfix_as_nonfix():
    # `^*(z)` postfix as nonfix
    z = _opname('z')
    arguments = [z]
    tree = nodes.OperatorApplication(
        operator='^*',
        arguments=arguments,
        nonfix=True)
    text = pformat(tree)
    text_ = '^*(z)'
    assert text == text_, text


def test_operator_declaration():
    # nullary
    x = _opname('x')
    tree = nodes.OperatorDeclaration(
        name=x,
        level='CONSTANT')
    text = pformat(tree)
    text_ = 'CONSTANT x'
    assert text == text_, text
    # binary
    arguments = ['_', '_']
    y_binary = nodes.OperatorApplication(
        operator='y',
        arguments=arguments)
    tree = nodes.OperatorDeclaration(
        name=y_binary,
        level='ACTION',
        new_keyword=True)
    text = pformat(tree)
    text_ = 'NEW ACTION y(_, _)'
    assert text == text_, text
    # with operator as parameter
    arguments = [y_binary]
    op_arity = nodes.OperatorApplication(
        operator='Op',
        arguments=arguments)
    tree = nodes.OperatorDeclaration(
        name=op_arity,
        level='CONSTANT')
    text = pformat(tree)
    text_ = 'CONSTANT Op(y(_, _))'
    assert text == text_, text


def test_operator_definition():
    name = 'Op'
    x = _opname('x')
    y = _opname('y')
    arguments = [x, y]
    definiens = nodes.OperatorApplication(
        operator='++',
        arguments=arguments)
    x = _opname('x')  # to ensure tree
    y = _opname('y')
    arity = [x, y]
    tree = nodes.OperatorDefinition(
        name=name,
        arity=arity,
        definiens=definiens)
    text = pformat(tree)
    text_ = 'Op(x, y) == x ++ y'
    assert text == text_, text
    # `LOCAL` definition
    x = _opname('x')
    y = _opname('y')
    arguments = [x, y]
    expr = nodes.OperatorApplication(
        operator='<=>',
        arguments=arguments)
    definiens = nodes.Parentheses(
        expression=expr)
    x = _opname('x')  # to ensure tree
    y = _opname('y')
    arity = [x, y]
    tree = nodes.OperatorDefinition(
        name=name,
        arity=arity,
        definiens=definiens,
        local=True)
    text = pformat(tree)
    text_ = 'LOCAL Op(x, y) == (x <=> y)'
    assert text == text_, text


def test_parameter_declaration():
    tree = nodes.ParameterDeclaration(
        name='Op',
        arity=2)
    text = pformat(tree)
    text_ = 'Op(_, _)'
    assert text == text_, text


def test_parentheses():
    x = _opname('x')
    tree = nodes.Parentheses(
        expression=x)
    text = pformat(tree)
    text_ = '(x)'
    assert text == text_, text


def test_pick():
    declarations = [_x_in_s()]
    predicate = _x_eq_one()
    tree = nodes.Pick(
        declarations=declarations,
        predicate=predicate)
    text = pformat(tree)
    text_ = r'PICK x \in S:  x = 1'
    assert text == text_, text


def test_proof():
    # step 1
    name = '<1>1.'
    main = _x_eq_one()
    facts = [_x_in_s()]
    proof = nodes.By(
        facts=facts)
    step_1 = nodes.ProofStep(
        name=name,
        main=main,
        proof=proof)
    # step 2
    name = '<1>2.'
    x = _opname('x')
    int_0 = nodes.IntegralNumeral(
        value='0')
    arguments = [x, int_0]
    main = nodes.OperatorApplication(
        operator='>',
        arguments=arguments)
    facts = [_opname('<1>1')]
    proof = nodes.By(
        facts=facts)
    step_2 = nodes.ProofStep(
        name=name,
        main=main,
        proof=proof,
        proof_keyword=True)
    # proof
    steps = [step_1, step_2]
    tree = nodes.Proof(
        steps=steps,
        proof_keyword=True)
    text = pformat(tree)
    text_ = (
        '    PROOF\n'
        '    <1>1. x = 1\n'
        '        BY x \\in S\n'
        '    <1>2. x > 0\n'
        '        PROOF\n'
        '        BY <1>1')
    assert text == text_


def test_proof_case():
    expression = _x_in_s()
    tree = nodes.ProofCase(
        expression=expression)
    text = pformat(tree)
    text_ = r'CASE x \in S'
    assert text == text_, text


def test_proof_step():
    # with `PROOF` keyword
    name = '<1>1.'
    main = _x_eq_one()
    facts = [_x_in_s()]
    proof = nodes.By(
        facts=facts)
    tree = nodes.ProofStep(
        name=name,
        main=main,
        proof=proof,
        proof_keyword=True)
    text = pformat(tree)
    text_ = (
        '<1>1. x = 1\n'
        '    PROOF\n'
        r'    BY x \in S')
    assert text == text_, text
    # without `PROOF` keyword
    tree = nodes.ProofStep(
        name=name,
        main=main,
        proof=proof)
    text = pformat(tree)
    text_ = (
        '<1>1. x = 1\n'
        r'    BY x \in S')
    # QED proof-step
    name = '<1>5.'
    tree = nodes.ProofStep(
        name=name,
        main='QED',
        proof=proof)
    text = pformat(tree)
    text_ = (
        '<1>5. QED\n'
        r'    BY x \in S')


def test_quantification():
    quantifier = r'\A'
    declarations = [_x_in_s()]
    x = _opname('x')
    int_2 = nodes.FloatNumeral(
        value='2.0')
    arguments = [x, int_2]
    predicate = nodes.OperatorApplication(
        operator='>',
        arguments=arguments)
    tree = nodes.Quantification(
        quantifier=quantifier,
        declarations=declarations,
        predicate=predicate)
    text = pformat(tree)
    text_ = r'\A x \in S:  x > 2.0'
    assert text == text_, text


def test_quantifier_witness():
    x_in_s = _x_in_s()
    y = _opname('y')
    r = _opname('R')
    arguments = [y, r]
    y_in_r = nodes.OperatorApplication(
        operator=r'\in',
        arguments=arguments)
    expressions = [x_in_s, y_in_r]
    tree = nodes.QuantifierWitness(
        expressions=expressions)
    text = pformat(tree)
    text_ = r'WITNESS x \in S, y \in R'
    assert text == text_, text


def test_record():
    int_1 = nodes.IntegralNumeral(
        value=1)
    abc = nodes.StringLiteral(
        value='"abc"')
    key_values = [
        ('x', int_1),
        ('y', abc)]
    tree = nodes.Record(
        key_values=key_values)
    text = pformat(tree)
    text_ = '[x |-> 1, y |-> "abc"]'
    assert text == text_, text


def test_recursive_operators():
    names = [
        _opname('F'),
        _opname('G')]
    tree = nodes.RecursiveOperators(
        names=names)
    text = pformat(tree)
    text_ = 'RECURSIVE F, G'
    assert text == text_, text


def test_sequent():
    assume = [_opname('theorem_name')]
    prove = _x_in_s()
    tree = nodes.Sequent(
        assume=assume,
        prove=prove)
    text = pformat(tree)
    text_ = (
        'ASSUME\n'
        '    theorem_name\n'
        'PROVE\n'
        r'    x \in S')
    assert text == text_, text


def test_set_comprehension():
    arguments = [
        _opname('x'),
        _opname('y')]
    item = nodes.OperatorApplication(
        operator='^',
        arguments=arguments)
    declarations = [
        _x_in_s()]
    tree = nodes.SetComprehension(
        item=item,
        declarations=declarations)
    text = pformat(tree)
    text_ = r'{x ^ y:  x \in S}'
    assert text == text_, text


def test_set_enumeration():
    string = nodes.StringLiteral(
        value='"string literal"')
    integer = nodes.IntegralNumeral(
        value='100')
    float = nodes.FloatNumeral(
        value='1.00')
    items = [string, integer, float]
    tree = nodes.SetEnumeration(
        items=items)
    text = pformat(tree)
    text_ = '{"string literal", 100, 1.00}'
    assert text == text_, text


def test_set_of_booleans():
    booleans = nodes.SetOfBooleans()
    text = pformat(booleans)
    text_ = 'BOOLEAN'
    assert text == text_, text


def test_set_of_functions():
    domain = _opname('dom')
    codomain = _opname('codom')
    tree = nodes.SetOfFunctions(
        domain=domain,
        codomain=codomain)
    text = pformat(tree)
    text_ = '[dom -> codom]'
    assert text == text_, text


def test_set_of_records():
    x_s = nodes.KeyBound(
        name='x',
        bound=_opname('S'))
    y_r = nodes.KeyBound(
        name='y',
        bound=_opname('R'))
    key_bounds = [x_s, y_r]
    tree = nodes.SetOfRecords(
        key_bounds=key_bounds)
    text = pformat(tree)
    text_ = '[x: S, y: R]'
    assert text == text_, text


def test_set_of_strings():
    strings = nodes.SetOfStrings()
    text = pformat(strings)
    text_ = 'STRING'
    assert text == text_, text


def test_set_slice():
    declaration = _x_in_s()
    x = nodes.OperatorApplication(
        operator='x')
    one = nodes.IntegralNumeral(
        value='1')
    arguments = [x, one]
    predicate = nodes.OperatorApplication(
        operator='=',
        arguments=arguments)
    slice = nodes.SetSlice(
        declaration=declaration,
        predicate=predicate)
    text = pformat(slice)
    text_ = r'{x \in S:  x = 1}'
    assert text == text_, text


def test_string_literal():
    string_literal = '"string literal"'
    string = nodes.StringLiteral(
        value=string_literal)
    text = pformat(string)
    assert text == string_literal, text


def test_subexpression_reference():
    # without arguments
    items = ['<1>1', '2', ':']
    tree = nodes.SubexpressionReference(
        items=items)
    text = pformat(tree)
    text_ = '<1>1!2!:'
    assert text == text_, text
    # with arguments
    arguments = [
        _opname('x'),
        _opname('y')]
    op_app = nodes.OperatorApplication(
        operator=None,
        arguments=arguments)
    items = ['<1>2', '3', op_app]
    tree = nodes.SubexpressionReference(
        items=items)
    text = pformat(tree)
    text_ = '<1>2!3!(x, y)'
    assert text == text_, text


def test_subscripted_action():
    # `[...]_...`
    operator = '['
    action = _x_eq_one()
    subscript = _opname('x')
    tree = nodes.SubscriptedAction(
        operator=operator,
        action=action,
        subscript=subscript)
    text = pformat(tree)
    text_ = '[x = 1]_x'
    assert text == text_, text
    # `<<...>>_...`
    operator = '<<'
    tree = nodes.SubscriptedAction(
        operator=operator,
        action=action,
        subscript=subscript)
    text = pformat(tree)
    text_ = r'<<x = 1>>_x'
    assert text == text_, text


def test_suffices():
    predicate = _x_in_s()
    suffices = nodes.Suffices(
        predicate=predicate)
    text = pformat(suffices)
    text_ = (
        'SUFFICES\n'
        r'        x \in S')
    assert text == text_, text


def test_take():
    declarations = [
        _x_in_s(),
        _x_in_s()]
    tree = nodes.Take(
        declarations=declarations)
    text = pformat(tree)
    text_ = r'TAKE x \in S, x \in S'
    assert text == text_, text


def test_temporal_quantification():
    quantifier = r'\EE'
    declarations = [
        _opname('x'),
        _opname('y')]
    expr = _x_eq_one()
    expr = nodes.Parentheses(
        expression=expr)
    arguments = [expr]
    predicate = nodes.OperatorApplication(
        operator='[]',
        arguments=arguments)
    tree = nodes.TemporalQuantification(
        quantifier=quantifier,
        declarations=declarations,
        predicate=predicate)
    text = pformat(tree)
    text_ = r'\EE x, y:  [] (x = 1)'
    assert text == text_, text


def test_theorem():
    # named theorem
    name = 'theorem_name'
    goal = _x_in_s()
    tree = nodes.Theorem(
        name=name,
        goal=goal,
        theorem_keyword='LEMMA')
    text = pformat(tree)
    text_ = (
        'LEMMA theorem_name ==\n'
        r'    x \in S')
    assert text == text_, text
    # theorem with proof
    facts = [_x_eq_one()]
    proof = nodes.By(
        facts=facts)
    tree = nodes.Theorem(
        goal=goal,
        proof=proof,
        theorem_keyword='THEOREM')
    text = pformat(tree)
    text_ = (
        'THEOREM\n'
        '    x \\in S\n'
        'BY x = 1')
    assert text == text_, text
    # keyword error
    tree = nodes.Theorem(
        name=name,
        goal=goal,
        theorem_keyword='LEMMAS')
    with pytest.raises(ValueError):
        pformat(tree)


def test_tuple():
    abc = nodes.StringLiteral(
        value='"abc"')
    one = nodes.IntegralNumeral(
        value='1')
    one_two = nodes.FloatNumeral(
        value='1.2')
    items = [abc, one, one_two]
    tuple_ = nodes.Tuple(
        items=items)
    text = pformat(tuple_)
    text_ = '<<"abc", 1, 1.2>>'
    assert text == text_, text


def test_use():
    z = _opname('z')
    int_2 = nodes.IntegralNumeral(
        value='2')
    int_3 = nodes.IntegralNumeral(
        value='3')
    z_plus_2 = nodes.OperatorApplication(
        operator='+',
        arguments=[z, int_2])
    z_expr = nodes.OperatorApplication(
        operator='=',
        arguments=[z_plus_2, int_3])
    r = _opname('r')
    r_prime = nodes.OperatorApplication(
        operator="'",
        arguments=[r])
    r = _opname('r')  # tree property
    r_expr = nodes.OperatorApplication(
        operator='#',
        arguments=[r_prime, r])
    facts = [z_expr, r_expr]
    names = [_opname('Op')]
    tree = nodes.Use(
        facts=facts,
        names=names,
        keyword='DEF')
    text = pformat(tree)
    text_ = "USE z + 2 = 3, r' # r DEF Op"
    assert text == text_, text


def test_variables():
    var_names = ['x', 'y', 'z']
    var_names = [_opname(s) for s in var_names]
    variables = nodes.Variables(
        keyword='VARIABLES',
        names=var_names)
    text = pformat(variables)
    text_ = 'VARIABLES\n    x,\n    y,\n    z'
    assert text == text_, text
    variable = nodes.Variables(
        keyword='VARIABLE',
        names=[_opname('a')])
    text = pformat(variable)
    text_ = 'VARIABLE\n    a'
    assert text == text_, text


def test_vertical_list():
    expression = _x_eq_one()
    item_1 = nodes.VerticalItem(
        operator='\\/',
        expression=expression)
    expression = _x_in_s()
    item_2 = nodes.VerticalItem(
        operator='\\/',
        expression=expression)
    arguments = [item_1, item_2]
    tree = nodes.VerticalList(
        operator='\\/',
        arguments=arguments)
    text = pformat(tree)
    text_ = (
        '\n\\/ x = 1\n'
        '\\/ x \\in S\n')
    assert text == text_, text


def test_vertical_item():
    expression = _x_eq_one()
    tree = nodes.VerticalItem(
        operator='\\/',
        expression=expression)
    text = pformat(tree)
    text_ = 'x = 1'
    assert text == text_, text


def test_with_instantiation():
    name = 'x'
    y = _opname('y')
    int_2 = nodes.IntegralNumeral(
        value='2')
    arguments = [y, int_2]
    expr = nodes.OperatorApplication(
        operator='-',
        arguments=arguments)
    with_inst = nodes.WithInstantiation(
        name=name,
        expression=expr)
    text = pformat(with_inst)
    text_ = 'x <- y - 2'
    assert text == text_, text


def _x_eq_one(
        ) -> tuple:
    """Return tree for `x = 1`."""
    x = nodes.OperatorApplication(
        operator='x')
    one = nodes.IntegralNumeral(
        value='1')
    arguments = [x, one]
    return nodes.OperatorApplication(
        operator='=',
        arguments=arguments)


def _x_in_s(
        ) -> tuple:
    r"""Return tree for `x \in S`."""
    x = nodes.OperatorApplication(
        operator='x')
    bound = nodes.OperatorApplication(
        operator='S')
    arguments = [x, bound]
    return nodes.OperatorApplication(
        operator='\\in',
        arguments=arguments)


def _boolean_expr(
        ) -> tuple:
    """Return tree for `TRUE`."""
    return nodes.BooleanLiteral(
        value='TRUE')


def _wrap_as_module(
        expr_tree:
            tuple
        ) -> tuple:
    """Return tree for module.

    The module has one definition,
    whose definiens is `expr_tree`.
    """
    op_name = 'A'
    def_unit = nodes.OperatorDefinition(
        name=op_name,
        definiens=expr_tree)
    units = [expr_tree]
    module_name = nodes.ModuleName(
        name='module_name')
    return nodes.Module(
        name=module_name,
        extendees=None,
        units=units)


def _opname(
        name:
            str
        ) -> tuple:
    """Return tree for operator name."""
    return nodes.OperatorApplication(
        operator=name)


def test_pformat_tla_without_preamble():
    text = '''---- MODULE test ----
        A == 1
        ===='''
    formatted = _pp.pformat_tla(text)
    formatted_ = (
        '--------------------------------- '
        'MODULE test '
        '----------------------------------\n'
        'A == 1\n'
        '========================================'
        '========================================')
    assert formatted == formatted_, repr(formatted)


def test_pformat_tla_preamble():
    text = ''' ````
        ---- MODULE test ----
        B(f(_),x)==f(x)====
        '''
    formatted = _pp.pformat_tla(text)
    formatted_ = (
        ' ````\n        \n'
        '--------------------------------- '
        'MODULE test '
        '----------------------------------\n'
        'B(f(_), x) == f(x)\n'
        '========================================'
        '========================================'
        '\n        ')
    assert formatted == formatted_, repr(formatted)


def test_pformat_tla_text_after_main_module():
    text = '''*)
        (*---- MODULE pprint ----
        G(x) == 2+(x^*)
        ====
        `` (* '''
    formatted = _pp.pformat_tla(text)
    formatted_ = (
        '*)\n        (*\n'
        '-------------------------------- '
        'MODULE pprint '
        '---------------------------------\n'
        'G(x) == 2 + (x^*)\n'
        '========================================'
        '========================================'
        '\n        `` (* ')
    assert formatted == formatted_, repr(formatted)


def test_pformat_ast_is_idempotent():
    inputs = [
        '''
        ---- MODULE pprint ----
        EXTENDS Integers

        A(x) == x + 1
        ====
        ''',
        r'''
        ---- MODULE vertical ----
        P(y) == \E x:  /\ x > 1
                       /\ x <= y
        ====
        ''',
        r'''
        ---- MODULE quantification ----
        R(x, y) == (x \in Nat /\ y \in Nat) =>
            \/ x < y
            \/ x = y
            \/ x > y
        ====
        ''']
    for text in inputs:
        _assert_pformat_idempotent(text)


def _assert_pformat_idempotent(text):
    """Assert formatting is idempotent."""
    formatted_1 = _pformat_text(text)
    formatted_2 = _pformat_text(formatted_1)
    assert formatted_1 == formatted_2, (
        formatted_1, formatted_2)


def _pformat_text(
        text:
            str
        ) -> str:
    """Parse and format the syntax tree."""
    tree = _lr.parse(text)
    return _pp.pformat_ast(tree)


def test_pformat_tla_is_idempotent():
    text = r'''

        ---- MODULE test ----
        EXTENDS Integers, Sequences

        A(x, y, z) == (x + y) * z
        B(x) == {r \in Nat: r >= x}
        NatTuples == Seq(Nat)
        NatNat == UNION {
            [S -> Nat]:  S \in SUBSET Nat}
        ====

        '''
    formatted_1 = _pp.pformat_tla(text)
    formatted_2 = _pp.pformat_tla(formatted_1)
    assert formatted_1 == formatted_2, (
        formatted_1, formatted_2)


if __name__ == '__main__':
    test_pformat_tla_text_after_main_module()
