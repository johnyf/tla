"""Formatting of expressions for printing."""
import functools as _ft
import logging as _log
import math
import textwrap as _tw
import typing as _ty

import parstools._lex as _lex

import tla._ast
import tla._langdef as _opdef
import tla._lex
import tla._preparser as _prp


LINE_WIDTH = 80
INDENT_WIDTH = 4
_INDENT = INDENT_WIDTH * '\x20'
_nodes = tla._ast.make_nodes()


def pformat_ast(
        tree:
            tuple,
        width:
            int=LINE_WIDTH
        ) -> str:
    """Return formatted tree.

    `width` is the desired text width
    to fit the formatted text into.
    """
    if isinstance(tree, str):
        return tree
    rec = _ft.partial(
        pformat_ast,
        width=width)
    enum_name = tla._ast.enum_to_class(
        tree.symbol.name)
    match enum_name:
        case 'Axiom':
            expr = rec(tree.expression)
            match tree.axiom_keyword:
                case None:
                    keyword = 'AXIOM'
                case (
                        'AXIOM' |
                        'ASSUME' |
                        'ASSUMPTION'):
                    keyword = str(
                        tree.axiom_keyword)
                case _:
                    raise ValueError(
                        tree.axiom_keyword)
            if tree.name is None:
                axiom = keyword
            else:
                axiom = f'{keyword} {tree.name} =='
            return _glue_prefix_box(
                axiom,
                f'\n{expr}',
                indent_width=INDENT_WIDTH)
        case 'BooleanLiteral':
            match tree.value:
                case 'FALSE':
                    if width < len('FALSE'):
                        raise AssertionError(width)
                    return 'FALSE'
                case 'TRUE':
                    if width < len('TRUE'):
                        raise AssertionError(width)
                    return 'TRUE'
                case _:
                    raise ValueError(
                        tree.value)
        case 'By':
            if tree.facts is None:
                facts = list()
            else:
                facts = list(map(
                    rec, tree.facts))
            if tree.names is None:
                names = list()
            else:
                names = list(map(
                    rec, tree.names))
            if tree.only:
                only = ' ONLY'
            else:
                only = ''
            prefix = f'{_INDENT}BY{only}'
            return _format_usable(
                facts, names, prefix,
                keyword=tree.keyword,
                width=width)
        case 'Cases':
            cases = list()
            for case_item in tree.cases:
                case_str = rec(case_item)
                cases.append(case_str)
            cases_str = ' [] '.join(cases)
            res = f'CASE {cases_str}'
            indent_width = 2
            res_width, _ = _box_dimensions(res)
            if res_width > width:
                cases_str = '\n[] '.join(cases)
                res = _glue_prefix_box(
                    'CASE ',
                    cases_str,
                    indent_width=indent_width)
            if tree.other is None:
                return res
            other = rec(tree.other)
            if res_width > width:
                return _glue_prefix_box(
                    res,
                    f'\n[] OTHER -> {other}',
                    indent_width=indent_width)
            return f'{res} [] OTHER -> {other}'
        case 'CaseItem':
            pred = rec(tree.predicate)
            expr = rec(tree.expression)
            return f'{pred} -> {expr}'
        case 'Choose':
            pred = rec(tree.predicate)
            decl = rec(tree.declaration)
            choose = f'CHOOSE {decl}:  '
            return _concatenate_boxes(
                choose, pred, width)
        case 'Constants':
            if not tree.names:
                raise ValueError(
                    tree.names)
            decls = list(map(
                rec, tree.names))
            decls_str = ',\n'.join(decls)
            # decls_str = _tw.fill(
            #     decls_str,
            #     width=width - len('CONSTANT '))
            return _glue_prefix_box(
                tree.keyword,
                '\n' + decls_str,
                indent_width=INDENT_WIDTH)
        case 'Define':
            indent_width = 2 * INDENT_WIDTH
            width -= 3 * INDENT_WIDTH
            defns_str = _format_definitions(
                tree.definitions,
                width=width)
            if tree.keyword is None:
                return defns_str
            return _glue_prefix_box(
                'DEFINE',
                f'\n{defns_str}',
                indent_width=indent_width)
        case 'Except':
            func = rec(tree.function)
            mods = list()
            for eq in tree.changes:
                mod = rec(eq)
                mods.append(mod)
            mods_str = ', '.join(mods)
            mods_width, _ = _box_dimensions(
                mods_str)
            if mods_width > width:
                mods_str = ',\n'.join(mods)
                return _glue_prefix_box(
                    f'[{func} EXCEPT',
                    f'\n{mods_str}]',
                    indent_width=INDENT_WIDTH)
            return f'[{func} EXCEPT {mods_str}]'
        case 'Fairness':
            op = tree.operator
            if op not in ('WF_', 'SF_'):
                raise ValueError(
                    tree.operator)
            subscript = rec(tree.subscript)
            action = rec(tree.action)
            return f'{op}{subscript}({action})'
        case 'Field':
            expr = rec(tree.expression)
            name = tree.name
            # parentheses needed ?
            needs_parentheses = (
                '\x20' in expr and
                not expr.startswith('(') and
                not expr.startswith('[') and
                not expr.startswith('{') and
                not expr.startswith('<<'))
            if needs_parentheses:
                _log.warn(
                    'Field expression needs '
                    f'parentheses: {expr}')
            return f'{expr}.{name}'
        case 'FloatNumeral':
            integer, mantissa = tree.value.split('.')
            if not mantissa:
                raise ValueError(tree.value)
            return tree.value
        case 'Function':
            new_width = width - INDENT_WIDTH
            rec = _ft.partial(
                pformat_ast,
                width=new_width)
            exprs = list(map(
                rec, tree.declaration))
            bounds_str = ', '.join(exprs)
            expr = rec(tree.value)
            start = _glue_prefix_box(
                '[',
                bounds_str,
                indent_width=INDENT_WIDTH)
            # combine with expr
            return _concatenate_boxes(
                f'{start} |-> ',
                f'{expr}]',
                width,
                INDENT_WIDTH,
                INDENT_WIDTH)
        case 'FunctionApplication':
            func = rec(tree.function)
            args_list = ', '.join(map(
                rec, tree.arguments))
            needs_parentheses = (
                '\x20' in func and
                not func.endswith(')') and
                    # includes nonfix-operator
                    # application
                not func.endswith(']') and
                not func.startswith('{') and
                not func.startswith('<<'))
            if needs_parentheses:
                print(
                    'WARNING: Function may need '
                    'parentheses in '
                    'function application of: '
                    f'{func}')
            return f'{func}[{args_list}]'
        case 'FunctionChange':
            args = list()
            for arg in tree.item:
                if isinstance(arg, str):
                    args.append(
                        f'.{arg}')
                elif isinstance(arg, list):
                    exprs = ', '.join(map(
                        rec, arg))
                    args.append(
                        f'[{exprs}]')
                else:
                    raise AssertionError(arg)
            expr = rec(tree.expression)
            args_str = ''.join(args)
            return f'!{args_str} = {expr}'
        case 'Have':
            expr = rec(tree.expression)
            return _glue_prefix_box(
                'HAVE ',
                expr,
                indent_width=2 * INDENT_WIDTH)
        case 'Hide':
            if tree.facts is None:
                facts = list()
            else:
                facts = list(map(
                    rec, tree.facts))
            if tree.names is None:
                names = list()
            else:
                names = list(map(
                    rec, tree.names))
            return _format_usable(
                facts, names,
                'HIDE',
                keyword=tree.keyword,
                width=width)
        case 'If':
            pred = rec(tree.predicate)
            then = rec(tree.then)
            else_ = rec(tree.else_)
            res = (
                f'IF {pred} THEN {then} '
                f'ELSE {else_}')
            res_width, _ = _box_dimensions(res)
            if res_width > width:
                res = _glue_prefix_box(
                    f'IF {pred}',
                    f'\nTHEN {then}',
                    indent_width=INDENT_WIDTH)
                res = _glue_prefix_box(
                    res,
                    f'\nELSE {else_}',
                    indent_width=INDENT_WIDTH)
            return res
        case 'IfItem':
            pred = rec(tree.predicate)
            expr = rec(tree.expression)
            return f'ELIF {pred} THEN {expr}'
        case 'Ifs':
            first, *rest = tree.cases
            else_ = rec(tree.other)
            pred = rec(first.predicate)
            expr = rec(first.expression)
            # elifs
            elifs = '\n'.join(map(rec, rest))
            elifs = f'\n{elifs}\nELSE {else_}'
            # combine
            res = f'IF {pred} THEN {expr}'
            return _glue_prefix_box(
                res,
                elifs,
                indent_width=INDENT_WIDTH)
        case 'Instance':
            inst = f'INSTANCE {tree.name}'
            if tree.local:
                inst = f'LOCAL {inst}'
            if tree.with_substitution is None:
                return inst
            substitutions = list(map(
                rec, tree.with_substitution))
            subs_str = ', '.join(substitutions)
            if subs_str:
                inst = f'{inst} WITH {subs_str}'
            return inst
        case 'IntegralNumeral':
            return f'{tree.value}'
        case 'KeyBound':
            expr = rec(tree.bound)
            return f'{tree.name}: {expr}'
        case 'Lambda':
            args = list(map(
                rec, tree.parameters))
            expr = rec(tree.expression)
            args = _format_lambda_signature(
                args, width)
            s = _glue_prefix_box(
                'LAMBDA ', args)
            return _glue_prefix_box(
                f'{s}:  ', expr)
        case 'Let':
            expr = rec(tree.expression)
            defns_str = '\n'.join(map(
                rec, tree.definitions))
            indent_width = len('LET ')
            res = _glue_prefix_box(
                '\nLET',
                f'\n{defns_str}',
                indent_width=indent_width)
            res += '\nIN'
            return _glue_prefix_box(
                res,
                f'\n{expr}',
                indent_width=indent_width)
        case 'Module':
            # module start
            n = (width - len(tree.name)
                - len(' MODULE  ')) / 2
            left = math.floor(n)
            right = math.ceil(n)
            title = ''.join([
                '-' * left,
                ' MODULE ',
                tree.name, ' ',
                '-' * right])
            # `EXTENDS` statement
            if tree.extendees is None:
                extends = None
            else:
                exts = [
                    _INDENT + rec(ext)
                    for ext in tree.extendees]
                exts_str = ',\n'.join(exts)
                extends = f'EXTENDS\n{exts_str}'
            # content
            if tree.units is None:
                units = None
            else:
                units = '\n'.join(map(
                    rec, tree.units))
            endline = width * '='
            parts = [
                title, extends,
                units, endline]
            parts = [p for p in parts if p is not None]
            return '\n'.join(parts)
        case 'ModuleName':
            return f'MODULE {tree.name}'
        case 'Obvious':
            return f'{_INDENT}OBVIOUS'
        case 'Omitted':
            return f'{_INDENT}OMITTED'
        case 'OperatorApplication':
            if isinstance(tree.operator, str):
                op = tree.operator
            elif tree.operator is None:
                # in subexpression reference
                op = ''
            else:
                op = rec(tree.operator)
            if tree.arguments is None:
                # avoid creating `(+)` if `+`
                # is inside parentheses
                if op in {'+', '-', '/'}:
                    op = f' {op}'
                # avoid creating `(*` or `*)`
                # from parenthesized `*`
                if op in {'*', '**'}:
                    op = f' {op} '
                return op
            args = list(map(
                rec, tree.arguments))
            n_args = len(args)
            # pre-defined symbol ?
            fixity = _opdef.OP_TO_FIXITY.get(op)
            if op == '-':
                match n_args:
                    case 1:
                        fixity = 'before'
                    case 2:
                        fixity = 'left'
                    case _:
                        raise ValueError(
                            op, n_args)
            if op == '-.':
                # op = '-'
                fixity = 'before'
            if op == '\\X':
                return f' {op} '.join(args)
            # labeled expression ?
            if op == '::':
                if len(args) != 2:
                    raise AssertionError(
                        op, args)
                return f'{args[0]} {op} {args[1]}'
            # nonfix application ?
            # This includes `+(x, y)`
            # i.e., nonfix application of
            # a fixal operator
            if tree.nonfix:
                fixity = None
            # nonfix operator ?
            if fixity is None:
                pass
            # infix operator ?
            elif n_args == 2:
                if fixity not in (
                        'infix', 'left',
                        'between', 'right'):
                    raise ValueError(
                        'prefix or postfix operator '
                        'applied to two arguments')
                arg0 = args[0]
                # not vertical expression as
                # first argument ?
                if not arg0.endswith('\n'):
                    arg0 = f'{arg0} '
                res = f'{arg0}{op} {args[1]}'
                res_width, _ = _box_dimensions(res)
                if res_width > width:
                    res = _glue_prefix_box(
                        args[0],
                        op)
                    res = _glue_prefix_box(
                        f'{res}\n',
                        args[1])
                return res
            elif n_args != 1:
                raise ValueError(
                    f'operator `{op}` applied to '
                    f'{n_args} arguments (expected 1)')
            # prefix operator ?
            elif fixity in ('prefix', 'before'):
                return f'{op} {args[0]}'
            # postfix operator ?
            elif fixity in ('postfix', 'after'):
                return f'{args[0]}{op}'
            else:
                raise AssertionError(
                    fixity, n_args)
            # nonfix-operator application
            if fixity is not None:
                raise AssertionError(
                    fixity, n_args)
            args_str = ', '.join(args)
            res = f'{op}({args_str})'
            res_width, _ = _box_dimensions(res)
            if res_width > width:
                args_str = ',\n'.join(
                    f'    {arg}'
                    for arg in args)
                res = f'{op}(\n{args_str})'
            return res
        case 'OperatorDeclaration':
            expr = rec(tree.name)
                # includes arity declaration
            match tree.level:
                case None:
                    if not tree.new_keyword:
                        raise ValueError(tree)
                    level = ''
                case (
                        'VARIABLE' |
                        'CONSTANT'|
                        'STATE' |
                        'ACTION' |
                        'TEMPORAL'):
                    level = tree.level
                case _:
                    raise ValueError(tree.level)
            if tree.new_keyword:
                new = 'NEW '
            else:
                new = ''
            return f'{new}{level} {expr}'
        case 'OperatorDefinition':
            if tree.function:
                # f[...] == ...
                definiens = rec(tree.definiens.value)
                decl = tree.definiens.declaration
                sig = _nodes.FunctionApplication(
                    function=tree.name,
                    arguments=decl)
            else:
                # f == ...
                # f(...) == ...
                definiens = rec(tree.definiens)
                sig = _nodes.OperatorApplication(
                    operator=tree.name,
                    arguments=tree.arity)
            sig = rec(sig)
            if tree.local:
                local = 'LOCAL '
            else:
                local = ''
            res = f'{local}{sig} == '
            res2 = _glue_prefix_box(
                res,
                definiens,
                indent_width=INDENT_WIDTH)
            res2_width, _ = _box_dimensions(res2)
            if res2_width > width:
                if not definiens.startswith('\n'):
                    definiens = f'\n{definiens}'
                res2 = _glue_prefix_box(
                    res,
                    definiens,
                    indent_width=INDENT_WIDTH)
            return res2
        case 'ParameterDeclaration':
            if tree.arity is None:
                return str(tree.name)
            else:
                arity = ['_'] * tree.arity
                arity = ', '.join(arity)
                return f'{tree.name}({arity})'
        case 'Parentheses':
            expr = rec(tree.expression)
            return f'({expr})'
        case 'Pick':
            # format parts
            exprs = list(map(
                rec, tree.declarations))
            decls = ', '.join(exprs)
            pred = rec(tree.predicate)
            # glue
            pick = f'PICK {decls}:  '
            pick_width, _ = _box_dimensions(pick)
            if pick_width > width:
                pick = _glue_prefix_box(
                    f'PICK',
                    f'\n{decls}:  ')
            res = _glue_prefix_box(
                pick,
                pred,
                indent_width=INDENT_WIDTH)
            res_width, _ = _box_dimensions(res)
            if res_width > width:
                res = _glue_prefix_box(
                    pick,
                    f'\n{pred}',
                    indent_width=INDENT_WIDTH)
            return res
        case 'Proof':
            new_width = width - INDENT_WIDTH
            rec = _ft.partial(
                pformat_ast,
                width=new_width)
            steps = list(map(
                rec, tree.steps))
            proof = '\n'.join(steps)
            if tree.proof_keyword:
                proof = f'PROOF\n{proof}'
            return _tw.indent(
                proof,
                prefix=_INDENT)
        case 'ProofCase':
            expr = rec(tree.expression)
            return f'CASE {expr}'
        case 'ProofStep':
            step_number = tree.name
            if tree.main == 'QED':
                main = tree.main
            else:
                main = rec(tree.main)
                assert main is not None
            pf_goal = _glue_prefix_box(
                f'{step_number} ', main)
            if tree.proof:
                leaf_proof = rec(tree.proof)
            else:
                leaf_proof = ''
            if tree.proof_keyword:
                pf = f'{_INDENT}PROOF\n'
            else:
                pf = ''
            return _glue_prefix_box(
                pf_goal,
                f'\n{pf}{leaf_proof}',
                indent_width=0)
        case 'Quantification':
            quantifier = tree.quantifier
            if quantifier not in (r'\A', r'\E'):
                raise ValueError(
                    tree.quantifier)
            # declarations
            decls_width = (
                width
                - len(quantifier)
                - len(' :'))
            rec = _ft.partial(
                pformat_ast,
                width=decls_width)
            decls = ', '.join(map(
                rec, tree.declarations))
            # expr
            expr_width = width - INDENT_WIDTH
            pred = pformat_ast(
                tree.predicate,
                width=expr_width)
            # combine
            res = _concatenate_boxes(
                f'{quantifier} ',
                f'{decls}:  ',
                width,
                INDENT_WIDTH,
                INDENT_WIDTH)
            res_width, _ = _box_dimensions(res)
            return _glue_prefix_box(
                res,
                pred,
                indent_width=res_width)
        case 'QuantifierWitness':
            exprs = ', '.join(map(
                rec, tree.expressions))
            return f'WITNESS {exprs}'
        case 'Record':
            pairs = list()
            for name, expr in tree.key_values:
                name = rec(name)
                expr = rec(expr)
                pair = f'{name} |-> {expr}'
                pairs.append(pair)
            items_str = ', '.join(pairs)
            return f'[{items_str}]'
        case 'RecursiveOperators':
            names = ', '.join(map(
                rec, tree.names))
            return f'RECURSIVE {names}'
        case 'Sequent':
            new_width = width - INDENT_WIDTH
            rec = _ft.partial(
                pformat_ast,
                width=new_width)
            assumptions = list(map(
                rec, tree.assume))
            goal = rec(tree.prove)
            res = _glue_prefix_box(
                'ASSUME',
                '\n' + _join_boxes_sep(
                    assumptions,
                    sep=', '),
                indent_width=INDENT_WIDTH)
            res_width, _ = _box_dimensions(res)
            if res_width > width:
                res = _glue_prefix_box(
                    'ASSUME',
                    '\n' + ',\n'.join(
                        assumptions),
                    indent_width=INDENT_WIDTH)
            return _glue_prefix_box(
                f'{res}\nPROVE',
                f'\n{goal}',
                indent_width=INDENT_WIDTH)
        case 'SetComprehension':
            decls = ', '.join(map(
                rec, tree.declarations))
            expr = rec(tree.item)
            res = _glue_prefix_box(
                '{' + expr + ':  ',
                decls + '}')
            res_width, _ = _box_dimensions(res)
            if res_width > width:
                res = _glue_prefix_box(
                    '{' + expr + ':',
                    '\n' + decls + '}',
                    indent_width=INDENT_WIDTH)
            return res
        case 'SetEnumeration':
            exprs = list(map(
                rec, tree.items))
            exprs_str = ', '.join(exprs)
            exprs_width, _ = _box_dimensions(
                exprs_str)
            if exprs_width > width:
                exprs_str = ',\n'.join(exprs)
            return '{' + exprs_str + '}'
        case 'SetOfBooleans':
            return 'BOOLEAN'
        case 'SetOfFunctions':
            domain = rec(tree.domain)
            codomain = rec(tree.codomain)
            return f'[{domain} -> {codomain}]'
        case 'SetOfRecords':
            key_bounds = list(map(
                rec, tree.key_bounds))
            items = ', '.join(map(
                rec, tree.key_bounds))
            comma_width, _ = _box_dimensions(items)
            if comma_width > width:
                items = ',\n'.join(key_bounds)
            return f'[{items}]'
        case 'SetOfStrings':
            return 'STRING'
        case 'SetSlice':
            # can be tuply
            decl = rec(tree.declaration)
            pred = rec(tree.predicate)
            decl_str = '{' + f'{decl}:  '
            res = _glue_prefix_box(
                decl_str,
                pred + '}',
                indent_width=INDENT_WIDTH)
            res_width, _ = _box_dimensions(res)
            if res_width > width:
                res = _glue_prefix_box(
                    decl_str,
                    '\n' + pred + '}',
                    indent_width=INDENT_WIDTH)
            return res
        case 'StringLiteral':
            return f'{tree.value}'
        case 'SubexpressionReference':
            items = list()
            for item in tree.items:
                if isinstance(item, str):
                    items.append(item)
                elif hasattr(item, 'operator'):
                    if item.arguments is not None:
                        args = list(map(
                            rec, item.arguments))
                        args_str = ', '.join(args)
                        if item.operator is None:
                            op = ''
                        else:
                            op = item.operator
                        # all operators as prefix,
                        # including infix, postfix
                        # e.g., `M!+(a, b)`
                        res = f'{op}({args_str})'
                    elif item.operator is not None:
                        res = item.operator
                    else:
                        raise AssertionError(item)
                    items.append(res)
                else:
                    raise AssertionError(
                        f'Unexpected case: {item}')
            spaced = list()
            for item in items:
                if item.endswith('!'):
                    raise AssertionError(item)
                if item.startswith('!'):
                    item = f' {item}'
                    # for the case `A! !!(1, 2)`
                spaced.append(item)
            return '!'.join(spaced)
        case 'SubscriptedAction':
            action = rec(tree.action)
            subscript = rec(tree.subscript)
            match tree.operator:
                case '[':
                    return f'[{action}]_{subscript}'
                case '<<':
                    return f'<<{action}>>_{subscript}'
                case _:
                    raise ValueError(
                        tree.operator)
        case 'Suffices':
            pred = rec(tree.predicate)
            return _glue_prefix_box(
                'SUFFICES',
                f'\n{pred}',
                indent_width=2 * INDENT_WIDTH)
        case 'Take':
            decls = ', '.join(map(
                rec, tree.declarations))
            return _glue_prefix_box(
                'TAKE ',
                decls,
                indent_width=2 * INDENT_WIDTH)
        case 'TemporalQuantification':
            quantifier = tree.quantifier
            if quantifier not in (r'\AA', r'\EE'):
                raise ValueError(
                    tree.quantifier)
            names = ', '.join(map(
                rec, tree.declarations))
            pred_width = width - INDENT_WIDTH
            pred = pformat_ast(
                tree.predicate,
                width=pred_width)
            qprefix = _concatenate_boxes(
                f'{quantifier} ',
                f'{names}:  ',
                width,
                INDENT_WIDTH,
                INDENT_WIDTH)
            return _concatenate_boxes(
                qprefix, pred, width,
                INDENT_WIDTH, INDENT_WIDTH)
        case 'Theorem':
            goal = pformat_ast(
                tree.goal,
                width=width - INDENT_WIDTH)
            theorem_keyword = tree.theorem_keyword
            if theorem_keyword not in (
                    'PROPOSITION',
                    'LEMMA',
                    'THEOREM',
                    'COROLLARY'):
                raise ValueError(
                    tree.theorem_keyword)
            if tree.name is None:
                theorem = theorem_keyword
            else:
                theorem = (
                    f'{theorem_keyword} '
                    f'{tree.name} ==')
            res = _glue_prefix_box(
                theorem,
                f'\n{goal}',
                indent_width=INDENT_WIDTH)
            if tree.proof is None:
                return res
            proof_str = rec(tree.proof)
            proof_str = _tw.dedent(proof_str)
            return _glue_prefix_box(
                res,
                f'\n{proof_str}',
                indent_width=0)
        case 'Tuple':
            items = list(map(
                rec, tree.items))
            items_str = ', '.join(items)
            tpl = f'<<{items_str}>>'
            tpl_width, _ = _box_dimensions(tpl)
            if tpl_width > width:
                tpl = ',\n'.join(items)
                tpl = _glue_prefix_box(
                    '<<',
                    f'\n{tpl}>>')
            return tpl
        case 'Use':
            if tree.facts is None:
                facts = list()
            else:
                facts = list(map(
                    rec, tree.facts))
            if tree.names is None:
                names = list()
            else:
                names = list(map(
                    rec, tree.names))
            if tree.only:
                only = ' ONLY'
            else:
                only = ''
            prefix = f'USE{only}'
            return _format_usable(
                facts, names, prefix,
                keyword=tree.keyword,
                width=width)
        case 'Variables':
            if not tree.names:
                raise ValueError(tree.names)
            vrs_str = ',\n'.join(map(
                rec, tree.names))
            return _glue_prefix_box(
                tree.keyword,
                '\n' + vrs_str,
                indent_width=INDENT_WIDTH)
        case 'VerticalList':
            if not tree.arguments:
                raise ValueError(
                    tree.arguments)
            op = tree.operator
            # assert same operator
            for other in tree.arguments:
                if other.operator == op:
                    continue
                raise ValueError(
                    other.operator, op)
            # format
            new_width = width - INDENT_WIDTH
            blocks = list()
            for expr in tree.arguments:
                expr = rec(
                    expr,
                    width=new_width)
                block = _glue_prefix_box(
                    f'{op} ',
                    expr)
                blocks.append(block)
            # combine
            return '\n' + '\n'.join(blocks) + '\n'
        case 'VerticalItem':
            return rec(tree.expression)
        case 'WithInstantiation':
            name = tree.name
            expr = rec(tree.expression)
            return f'{name} <- {expr}'
        case _:
            raise ValueError(
                tree.symbol.name)


def _box_dimensions(
        string:
            str
        ) -> tuple[int, int]:
    r"""Return width, height of `string`.

    Width is the number of characters in the
    longest line. Height is the number of lines,
    which includes a newline (`\n`) at the end.
    """
    lines = string.split('\n')
        # counts the `\n` at end
    widths = [
        len(line)
        for line in lines]
    width = max(widths)
    height = len(lines)
    return (
        width,
        height)


def _glue_prefix_box(
        prefix:
            str,
        box:
            str,
        indent_width:
            int |
            None=None
        ) -> str:
    """Concatenate strings with proper indentation."""
    lines = box.split('\n')
    if indent_width is None:
        prefix_lines = prefix.split('\n')
        indent_width = len(prefix_lines[-1])
    indent = indent_width * '\x20'
    res_lines = [prefix + lines[0]]
    res_lines.extend(
        indent + line
        for line in lines[1:])
    return '\n'.join(res_lines)


def _concatenate_boxes(
        box1:
            str,
        box2:
            str,
        width:
            int,
        indent_width:
            int=INDENT_WIDTH,
        alt_indent_width:
            int=INDENT_WIDTH
        ) -> str:
    """Concatenate `box1` and `box2` within `width`.

    Introduce a newline if the result would be
    wider than `width`. Use `indent_width` to indent
    `box2` if concatenated without newline,
    otherwise `alt_indent_width`.
    """
    res = _glue_prefix_box(
        box1, box2, indent_width)
    res_width, _ = _box_dimensions(res)
    if res_width <= width:
        return res
    return _glue_prefix_box(
        box1,
        f'\n{box2}',
        alt_indent_width)


def _join_boxes_sep(
        boxes:
            list,
        sep:
            str
        ) -> str:
    """Join boxes by iterative gluing."""
    res = ''
    for box in boxes:
        if res:
            res += sep
        res = _glue_prefix_box(
            res, box)
    return res


def _format_lambda_signature(
        args:
            list[str],
        width:
            int
        ) -> str:
    """Return `str` of `LAMBDA` signature."""
    res = ', '.join(args)
    res_width, _ = _box_dimensions(res)
    if res_width > width:
        res = ',\n'.join(args)
    return res


def _format_definitions(
        definitions:
            list,
        width:
            int
        ) -> str:
    r"""Return formatted `definitions`.

    Concatenate vertically the string
    representations of `definitions` by
    inserting newlines `\n`.
    """
    defns = list()
    for defn in definitions:
        defn_str = pformat_ast(
            defn,
            width=width)
        defns.append(defn_str)
    return '\n'.join(defns)


def _format_usable(
        facts:
            list[str],
        defs:
            list[str],
        prefix:
            str,
        *,
        keyword:
            str |
            None=None,
        width:
            int
        ) -> str:
    """Return formatted with `prefix`."""
    # facts
    facts_str = ', '.join(facts)
    # new_width = width - len(prefix) - INDENT_WIDTH
    # facts_str = _tw.fill(
    #     facts_str,
    #     width=new_width)
    if facts:
        res = _glue_prefix_box(
            prefix,
            f' {facts_str}',
            indent_width=INDENT_WIDTH)
    else:
        res = prefix
    # defs
    defs_str = ', '.join(defs)
    # new_width = (
    #     width - len('DEF ') - len(prefix)
    #     - INDENT_WIDTH)
    # defs_str = _tw.fill(
    #     defs_str,
    #     width=new_width)
    # combine
    if defs:
        if keyword not in {'DEF', 'DEFS'}:
            raise ValueError(keyword)
        defs_str = f'{keyword} {defs_str}'
        res = _glue_prefix_box(
            res,
            f' {defs_str}',
            indent_width=INDENT_WIDTH)
    elif keyword is not None:
        _log.warn(
            'no defs, so expected no DEF keyword',
            keyword, defs)
    res_width, _ = _box_dimensions(res)
    if res_width > width:
        res = _glue_prefix_box(
            f'{prefix} ',
            facts_str,
            indent_width=len(prefix) + 1)
        if defs:
            res = _glue_prefix_box(
                res,
                f'\n{defs_str}',
                indent_width=len(prefix) + 1)
    return res


def _print_overwide_lines(
        text:
            str,
        max_width:
            int
        ) -> None:
    """Print lines wider than `max_width`.

    Print 5 lines of context before and after the
    widest lines in `text`. Print the width of the
    widest line in `text`.
    """
    width, _ = _box_dimensions(text)
    print(f'Width of text: {width}')
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if len(line) <= max_width:
            continue
        span = '\n'.join(lines[i - 5: i + 6])
        print(span)


def pformat_tla(
        text:
            str
        ) -> str:
    """Return formatted `text` with comments.

    The comments are inserted again after
    formatting.
    """
    # input tokens
    lexer = tla.Lexer()
    main_text = _prp.filter_preamble(text)
    tokens = lexer.parse(main_text)
    tokens = _prp.filter_postamble(tokens)
    tokens = list(tokens)
    # check tokens
    if not tokens:
        raise ValueError('No tokens found.')
    token = tokens[-1]
    if token.symbol != 'EQ_LINE':
        raise ValueError(
            f'Unexpected token: {token}')
    # text before and after main module
    start = _prp.find_module_start(text)
    preamble = text[:start]
    n_newlines = preamble.count('\n')
    *_, last_preamble_line = preamble.rsplit('\n', 1)
    # for type checking
    if token.start is None:
        raise AssertionError(token)
    end = (
        start - n_newlines -
        len(last_preamble_line) +
        token.start + len(token.value))
        # `filter_preamble()` above includes
        # newlines from the preamble,
        # hence the `-n_newlines` here.
        #
        # It also includes spaces to position
        # the MODULE line so that column numbers
        # remain unchanged,
        # hence the `len(last_preamble_line)`.
    postamble = text[end:]
    # tokens of formatted text
    tree = tla.parse(text)
    formatted_text = tla.pformat_ast(tree)
    ptokens = list(lexer.parse(
        formatted_text))
    # copy comments
    ctokens = _zip_tokens(tokens, ptokens)
    ctokens = _reposition_tokens(ctokens)
    formatted = _lex.join_tokens(ctokens)
    # add text outside main module
    if preamble and not preamble.endswith('\n'):
        # the `endswith()` ensures idempotent
        preamble = f'{preamble}\n'
    if postamble and not postamble.startswith('\n'):
        # the `startswith()` ensures idempotent
        postamble = f'\n{postamble}'
    all_text = f'{preamble}{formatted}{postamble}'
    return all_text


_COMMENT_TOKENS = {
    'UNILINE_COMMENT',
    'MULTILINE_COMMENT'}


def _zip_tokens(
        tokens:
            list,
        ptokens:
            list
        ) -> list:
    """Copy comments from `tokens` to `ptokens`.

    Comments are copied with relative positions.
    """
    rest = iter(ptokens)
    ctokens = list()
        # tokens with comments inserted
    last_token = _lex.make_none_token()
    for token in tokens:
        if token.symbol in _COMMENT_TOKENS:
            start, line, column = _pos_diff(
                last_token, token)
            ctoken = _lex.Token(
                symbol=token.symbol,
                value=token.value,
                start=start,
                line=line,
                column=column)
            ctokens.append(ctoken)
            last_token = token
            continue
        ptoken = next(rest, None)
        if ptoken is None:
            raise AssertionError(
                'different number of '
                f'non-comment tokens at: {token}')
        # print(token, ptoken)
        if token.symbol != ptoken.symbol:
            raise AssertionError(
                token, ptoken)
        ctokens.append(ptoken)
        last_token = token
    ptoken = next(rest, None)
    if ptoken is not None:
        raise AssertionError(
            'different number of '
            f'non-comment tokens at: {ptoken}')
    return ctokens


def _pos_diff(
        last_token,
        token):
    """Return relative position."""
    span = len(last_token.value)
    start = (
        token.start
        - span
        - last_token.start)
    line = (
        token.line
        - last_token.line)
    # consecutive comments changed to
    # different lines
    comments_same_line = (
        last_token.symbol in
            _COMMENT_TOKENS and
        line == last_token.value.count('\n'))
    if comments_same_line:
        line += 1
    # same line ?
    if line == 0:
        column = (
            token.column
            - span
            - last_token.column)
    elif line < 0:
        raise AssertionError(
            last_token, token)
    else:
        column = token.column
    return (
        start,
        line,
        column)


def _reposition_tokens(
        tokens):
    """Update token coordinates.

    Based on relative positions and size of
    comments, update the positions of all
    tokens, including of comment tokens.
    """
    line = 0
    line_shift = 0
    ctokens = list()
    last_token = _lex.make_none_token()
    for index, token in enumerate(tokens):
        span = len(last_token.value)
        last_newlines = last_token.value.count('\n')
        if token.symbol in _COMMENT_TOKENS:
            line = (
                last_token.line +
                last_newlines + 1)
            if token.line:
                column = token.column
            else:
                column = (
                    last_token.column +
                    token.column +
                    span)
            n_newlines = token.value.count('\n')
            line_shift += n_newlines + 1
            # add newline after multiline comments
            # to avoid changing columns within
            # vertical expressions
            end_line = (
                line +
                n_newlines)
            if index + 1 < len(tokens):
                next_token = tokens[index + 1]
            else:
                next_token = None
            add_newline = (
                next_token is not None and
                next_token.symbol not in
                    _COMMENT_TOKENS and
                next_token.line + line_shift ==
                    end_line and
                token.symbol == 'MULTILINE_COMMENT')
                    # uniline comments end at a newline
            if add_newline:
                line_shift += 1
        else:
            line = token.line + line_shift
            column = token.column
                # column numbers unchanged to
                # keep alignment of vertical operators
        if ctokens and line < ctokens[-1].line:
            raise AssertionError(
                token, line, ctokens[-1])
        ctoken = _lex.Token(
            symbol=token.symbol,
            value=token.value,
            start=None,
            line=line,
            column=column)
        ctokens.append(ctoken)
        last_token = ctoken
    return ctokens
