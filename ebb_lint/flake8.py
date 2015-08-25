from __future__ import unicode_literals

import bisect
import io
import tokenize
from lib2to3.pgen2 import driver, token
from lib2to3 import patcomp, pygram, pytree

import six
import venusian

from ebb_lint._version import __version__
from ebb_lint import checkers


# Stolen from lib2to3 directly. Why was this a private function? Ugh.
def detect_future_features(infile):
    have_docstring = False
    gen = tokenize.generate_tokens(infile.readline)

    def advance():
        tok = next(gen)
        return tok[0], tok[1]

    ignore = frozenset((token.NEWLINE, tokenize.NL, token.COMMENT))
    features = set()
    try:
        while True:
            tp, value = advance()
            if tp in ignore:
                continue
            elif tp == token.STRING:
                if have_docstring:
                    break
                have_docstring = True
            elif tp == token.NAME and value == 'from':
                tp, value = advance()
                if tp != token.NAME or value != '__future__':
                    break
                tp, value = advance()
                if tp != token.NAME or value != 'import':
                    break
                tp, value = advance()
                if tp == token.OP and value == '(':
                    tp, value = advance()
                while tp == token.NAME:
                    features.add(value)
                    tp, value = advance()
                    if tp != token.OP or value != ',':
                        break
                    tp, value = advance()
            else:
                break
    except StopIteration:
        pass
    return frozenset(features)


if six.PY3:
    def grammar_for_filename(filename):
        return pygram.python_grammar_no_print_statement

else:
    def grammar_for_filename(filename):
        with open(filename, 'r') as infile:
            future_features = detect_future_features(infile)
        if 'print_function' in future_features:
            return pygram.python_grammar_no_print_statement
        else:
            return pygram.python_grammar


def find_comments(s):
    fobj = io.StringIO(six.text_type(s))
    for typ, tok, _, _, _ in tokenize.generate_tokens(fobj.readline):
        if typ == tokenize.COMMENT:
            yield tok


class Lines(object):
    def __init__(self, infile):
        count = 0
        self.lines = [(0, '')]
        for line in infile:
            self.lines.append((count, line))
            count += len(line)

    def __getitem__(self, idx):
        return self.lines[idx]

    def position_of_byte(self, byte):
        lineno = bisect.bisect_left(self.lines, (byte + 1,)) - 1
        column = byte - self.lines[lineno][0]
        return lineno, column


class EbbLint(object):
    name = 'ebb_lint'
    version = __version__

    _lines = None

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename

    @classmethod
    def add_options(cls, parser):
        pass

    @classmethod
    def parse_options(cls, options):
        collected_checkers = []

        def register_checker(pattern, checker, extra):
            pattern = patcomp.compile_pattern(pattern)
            collected_checkers.append((pattern, checker, extra))

        scanner = venusian.Scanner(register=register_checker)
        scanner.scan(checkers)
        cls.collected_checkers = collected_checkers

    @property
    def lines(self):
        if self._lines is None:
            with open(self.filename) as infile:
                self._lines = Lines(infile)
        return self._lines

    def _message_for(self, node, error, **kw):
        line_offset = kw.pop('line_offset', None)
        if line_offset is None:
            byte, _ = self.lines[node.lineno]
            byte += node.column + kw.pop('offset', 0)
            lineno, column = self.lines.position_of_byte(byte)
        else:
            lineno = node.lineno + line_offset
            column = kw.pop('column')
        message = 'L{:03d} {}'.format(
            error.value.code, error.value.message.format(**kw))
        return lineno, column, message, type(self)

    def run(self):
        d = driver.Driver(
            grammar_for_filename(self.filename), convert=pytree.convert)
        tree = d.parse_file(self.filename)
        for node in tree.pre_order():
            for pattern, checker, extra in self.collected_checkers:
                results = {}
                if not pattern.match(node, results):
                    continue
                for k in extra.get('comments_for', ()):
                    comments = list(find_comments(node.prefix))
                    results[k + '_comments'] = comments
                if extra.get('pass_filename', False):
                    results['filename'] = self.filename
                for error_node, error, kw in checker(**results):
                    yield self._message_for(error_node, error, **kw)
