"""Rearranging blankspace within TLA+ source.

How to take TLA+ source, parse it, and then
print the syntax tree as TLA+ source, rearranged
in a specific way according to formatting rules.
"""
import tla


TLA_TEXT = r'''
----
MODULE example
----
(* An example module. *)
EXTENDS
Integers A == LET
x ==1 y== 2 IN x+ y THEOREM
A*2 = 2* (1+2 ) BY DEF A, *, +
====
'''


def format_tla():
    """Example of formatting, with comments preserved."""
    formatted = tla.pformat_tla(TLA_TEXT)
    print(formatted)


if __name__ == '__main__':
    format_tla()
