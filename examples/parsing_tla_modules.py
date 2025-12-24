"""How to parse a TLA+ module."""
import tla


TLA_FILE_PATH = 'Counter.tla'


def parse_module():
    """Parse a TLA+ module."""
    tla_text = _load_tla_module()
    tree = tla.parse(tla_text)
    print(tree)


def parse_module_and_format():
    """Parse, format, print a TLA+ module."""
    tla_text = _load_tla_module()
    tree = tla.parse(tla_text)
    text = tla.pformat_ast(tree)
    print(text)


def _load_tla_module():
    """Return contents of TLA+ file."""
    filepath = TLA_FILE_PATH
    with open(filepath,
                mode='r',
                encoding='utf-8') as fd:
        return fd.read()


if __name__ == '__main__':
    parse_module()
    parse_module_and_format()
