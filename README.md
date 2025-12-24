About
=====

A parser for the Temporal Logic of Actions (TLA+). The parser
is based on the [LR(1) algorithm](
    https://en.wikipedia.org/wiki/LR_parser)
with state merging, and has time complexity [linear](
    https://en.wikipedia.org/wiki/Time_complexity#Linear_time)
in the size of the input. The lexer and parser are generated using
[`parstools`](https://pypi.org/project/parstools).

The syntax tree is represented as named-tuples, using
`typing.NamedTuple`. Each node has line and column
information for its start and end.


To install:

```shell
pip install tla
```

To parse a string:

```python
import tla

module_text = r'''
    ---- MODULE name ----
    operator == TRUE
    ====================
    '''

tree = tla.parse(module_text)
print(tree)
text = tla.pformat_ast(tree)
print(text)
```

More examples can be found in the directory `examples/`.
To implement a new translator of TLA+, as example the
module `tla._pprint` can be used, or the class
`tla._utils.Traversal`.


Documentation
=============

In the [Markdown](https://en.wikipedia.org/wiki/Markdown) file `doc.md`.


Tests
=====

Use [`pytest`](https://pypi.org/project/pytest). Run with:

```shell
cd tests/
pytest -v --continue-on-collection-errors .
```

Read also the file `tests/README.md`.


License
=======
[BSD-3](https://opensource.org/licenses/BSD-3-Clause), read `LICENSE` file.
