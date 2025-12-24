"""Test `tla._preparser`."""
import parstools._lex as _lex
import pytest
import tla._preparser as _prp


Token = _lex.Token


def test_insert_def_sig_tokens_nullary():
    in_tokens = [
        Token('OP_15_POSTFIX', '^+'),
        Token('NAME', 'a'),
        Token('DOUBLE_EQ', '==')]
    tokens = _prp._insert_def_sig_tokens_fixal(
        reversed(in_tokens))
    tokens = list(reversed(list(tokens)))
    tokens_ = list(in_tokens)
    tokens_.insert(1, Token('DEF_SIG', 'DEF_SIG'))
    assert tokens == tokens_, tokens


def test_insert_def_sig_tokens_prefix():
    in_tokens = [
        Token('OP_12_PREFIX', '-.'),
        Token('NAME', 'a'),
        Token('DOUBLE_EQ', '==')]
    tokens = _prp._insert_def_sig_tokens_fixal(
        reversed(in_tokens))
    tokens = list(reversed(list(tokens)))
    tokens_ = list(in_tokens)
    tokens_.insert(0, Token('DEF_SIG', 'DEF_SIG'))
    assert tokens == tokens_, tokens


def test_insert_def_sig_tokens_infix():
    in_tokens = [
        Token('NAME', 'a'),
        Token('OP_10_LEFT', '+'),
        Token('NAME', 'b'),
        Token('DOUBLE_EQ', '==')]
    tokens = _prp._insert_def_sig_tokens_fixal(
        reversed(in_tokens))
    tokens = list(reversed(list(tokens)))
    tokens_ = list(in_tokens)
    tokens_.insert(0, Token('DEF_SIG', 'DEF_SIG'))
    assert tokens == tokens_, tokens


def test_insert_def_sig_tokens_postfix():
    in_tokens = [
        Token('NAME', 'a'),
        Token('OP_15_POSTFIX', '^*'),
        Token('DOUBLE_EQ', '==')]
    tokens = _prp._insert_def_sig_tokens_fixal(
        reversed(in_tokens))
    tokens = list(reversed(list(tokens)))
    tokens_ = list(in_tokens)
    tokens_.insert(0, Token('DEF_SIG', 'DEF_SIG'))
    assert tokens == tokens_, tokens


def test_insert_def_sig_tokens_nonfix():
    # one parameter
    in_tokens = [
        Token('NAME', 'Op'),
        Token('LPAREN', '('),
        Token('NAME', 'x'),
        Token('RPAREN', ')'),
        Token('DOUBLE_EQ', '==')]
    tokens = _prp._insert_def_sig_tokens_nonfix(
        reversed(in_tokens))
    tokens = list(reversed(list(tokens)))
    tokens_ = list(in_tokens)
    tokens_.insert(0, Token('DEF_SIG', 'DEF_SIG'))
    assert tokens == tokens_, tokens
    # multiple parameters
    in_tokens = [
        Token('NAME', 'Op'),
        Token('LPAREN', '('),
        Token('NAME', 'x'),
        Token('COMMA', ','),
        Token('NAME', 'y'),
        Token('RPAREN', ')'),
        Token('DOUBLE_EQ', '==')]
    tokens = _prp._insert_def_sig_tokens_nonfix(
        reversed(in_tokens))
    tokens = list(reversed(list(tokens)))
    tokens_ = list(in_tokens)
    tokens_.insert(0, Token('DEF_SIG', 'DEF_SIG'))
    assert tokens == tokens_, tokens
    # second-order operator
    # (so nested parentheses)
    in_tokens = [
        Token('NAME', 'Op'),
        Token('LPAREN', '('),
        Token('NAME', 'g'),
        Token('LPAREN', '('),
        Token('NAME', 'x'),
        Token('RPAREN', ')'),
        Token('COMMA', ','),
        Token('NAME', 'y'),
        Token('RPAREN', ')'),
        Token('DOUBLE_EQ', '==')]
    tokens = _prp._insert_def_sig_tokens_nonfix(
        reversed(in_tokens))
    tokens = list(reversed(list(tokens)))
    tokens_ = list(in_tokens)
    tokens_.insert(0, Token('DEF_SIG', 'DEF_SIG'))
    assert tokens == tokens_, tokens


def test_swap_local_keyword():
    in_tokens = [
        Token('LOCAL', 'LOCAL'),
        Token('DEF_SIG', 'DEF_SIG')]
    tokens = _prp.swap_local_keyword(in_tokens)
    tokens = list(tokens)
    tokens_ = [
        Token('DEF_SIG', 'DEF_SIG'),
        Token('LOCAL', 'LOCAL')]
    assert tokens == tokens_, tokens


def test_end_define_proof_steps():
    in_tokens = [
        Token('STEP_NUMBER', '<1>'),
        Token('DEFINE', 'DEFINE'),
        Token('NAME', 'a'),
        Token('DOUBLE_EQ', '=='),
        Token('FLOAT', '1.0'),
        Token('STEP_NUMBER', '<1>1.'),
        ]
    tokens = _prp.end_define_proof_steps(in_tokens)
    tokens = list(tokens)
    tokens = [
        token.symbol
        for token in tokens]
    tokens_ = [
        'STEP_NUMBER',
        'DEFINE',
        'NAME',
        'DOUBLE_EQ',
        'FLOAT',
        'END_DEFINE',  # inserted token
        'STEP_NUMBER']
    assert tokens == tokens_, tokens


def test_switch_step_identifiers():
    in_tokens = [
        Token('BY', 'BY'),
        Token('NAME', 'theorem_name'),
        Token('COMMA', ','),
        Token('STEP_NUMBER', '<1>1'),
        ]
    tokens = _prp.switch_step_identifiers(in_tokens)
    tokens = list(tokens)
    tokens_ = [
        Token('BY', 'BY'),
        Token('NAME', 'theorem_name'),
        Token('COMMA', ','),
        Token('NAME', '<1>1'),  # changed
        ]
    assert tokens == tokens_, tokens


def test_switch_fixal_operators():
    in_tokens = [
        Token('NAME', 'Op'),
        Token('LPAREN', '('),
        Token('OP_10_LEFT', '+'),
        Token('COMMA', ','),
        Token('INTEGRAL_NUMERAL', '1'),
        Token('COMMA', ','),
        Token('INTEGRAL_NUMERAL', '2'),
        Token('RPAREN', ')'),
        ]
    tokens = _prp.switch_fixal_operators(in_tokens)
    tokens = list(tokens)
    tokens_ = [
        Token('NAME', 'Op'),
        Token('LPAREN', '('),
        Token('NAME', '+'),  # changed
        Token('COMMA', ','),
        Token('INTEGRAL_NUMERAL', '1'),
        Token('COMMA', ','),
        Token('INTEGRAL_NUMERAL', '2'),
        Token('RPAREN', ')'),
        ]
    assert tokens == tokens_, tokens


def test_switch_keywords_after_dot():
    in_tokens = [
        Token('DOT', '.'),
        Token('LET', 'LET'),
        ]
    tokens = _prp.switch_keywords_after_dot(in_tokens)
    tokens = list(tokens)
    tokens_ = [
        Token('DOT', '.'),
        Token('NAME', 'LET'),  # changed
        ]
    assert tokens == tokens_, tokens


def test_filter_comments():
    in_tokens = [
        Token('UNILINE_COMMENT', r'\* comment\n'),
        Token('MULTILINE_COMMENT', '(* comment *)'),
        Token('LET', 'LET'),
        ]
    tokens = _prp.filter_comments(in_tokens)
    tokens = list(tokens)
    tokens_ = [
        Token('LET', 'LET'),
        ]
    assert tokens == tokens_, tokens


def test_filter_preamble():
    # no preamble
    text = '------ MODULE'
    main_text = _prp.filter_preamble(text)
    assert main_text == text, main_text
    # with preamble
    text = 'MODULE ----MODULE name -----'
    main_text = _prp.filter_preamble(text)
    main_text_ = '       ----MODULE name -----'
    assert main_text == main_text_, main_text
    # newlines in preamble
    text = '\n   \n ---- MODULE test ----'
    main_text = _prp.filter_preamble(text)
    main_text_ = '\n\n ---- MODULE test ----'
    assert main_text == main_text_, main_text


def test_find_module_start():
    # has module start
    text = '---- MODULE'
    start = _prp.find_module_start(text)
    assert start == 0, start
    # error
    text = '--- MODULE'
    with pytest.raises(ValueError):
        _prp.find_module_start(text)
    # error
    text = '---- MODLE'
    with pytest.raises(ValueError):
        _prp.find_module_start(text)
    # module start > 0
    text = '    ---- MODULE'
    start = _prp.find_module_start(text)
    assert start == 4, start
    # module start after preamble
    text = 'ab ` 1 )* ```*) (* 5---- MODULE'
    start = _prp.find_module_start(text)
    assert start == 20
    # with newlines
    text = '''
    ---- MODULE test
        '''
    start = _prp.find_module_start(text)
    assert start == 5, start  # 1 newline + 4 spaces
    text = '''
              ---- MODULE test'''
    start = _prp.find_module_start(text)
    assert start == 15, start  # 1 newline + 14 spaces


if __name__ == '__main__':
    # test_filter_comments()
    # test_insert_def_sig_tokens_infix()
    test_end_define_proof_steps()
