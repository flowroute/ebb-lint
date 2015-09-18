# coding: utf-8

from __future__ import unicode_literals

import bisect
import io
import sys
from lib2to3.pgen2 import driver, token, tokenize
from lib2to3 import patcomp, pygram, pytree

import pep8
import six
import venusian
from intervaltree import Interval, IntervalTree

from ebb_lint._version import __version__
from ebb_lint.errors import Errors
from ebb_lint import checkers


_pep8_noqa = pep8.noqa
# This is a blight. Disable it unconditionally.
pep8.noqa = lambda ign: False


# detect_future_features isn't fully covered, but I don't really care, because
# I don't want to rewrite it. Maybe if it becomes more relevant I'll pull it
# out of this suite and actually properly unit test it, but right now I feel
# like it's mostly just working around a lib2to3 deficiency so I don't care
# enough to do anything else. It's stolen from lib2to3 directly. Why was this a
# private function? Ugh.

def detect_future_features(infile):  # pragma: nocover
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


if six.PY3:  # ✘py27
    def grammar_for_future_features(future_features):
        return pygram.python_grammar_no_print_statement

else:  # ✘py33 ✘py34
    def grammar_for_future_features(future_features):
        if 'print_function' in future_features:
            return pygram.python_grammar_no_print_statement
        else:
            return pygram.python_grammar


def find_comments(s, base_byte=0):
    fobj = io.StringIO(six.text_type(s))
    lines = Lines(fobj)
    fobj.seek(0)
    for typ, tok, spos, epos, _ in tokenize.generate_tokens(fobj.readline):
        if typ == tokenize.COMMENT:
            yield tok, Interval(
                lines.byte_of_pos(*spos) + base_byte,
                lines.byte_of_pos(*epos) + base_byte)


def read_file_using_source_encoding(filename):
    with open(filename, 'rb') as infile:
        encoding = tokenize.detect_encoding(infile.readline)[0]
    with io.open(filename, 'r', encoding=encoding) as infile:
        return infile.read()


def parse_source(driver, source):
    trailing_newline = not source or source.endswith('\n')
    # Thanks for this, lib2to3.
    if not trailing_newline:
        source += '\n'
    return driver.parse_string(source), trailing_newline


class Lines(object):
    def __init__(self, infile):
        count = 0
        self.lines = [(0, '')]
        for line in infile:
            self.lines.append((count, line))
            count += len(line)
        self.last_pos = len(self.lines) - 1, len(self.lines[-1][1])
        self.last_byte = count

    def __getitem__(self, idx):
        return self.lines[idx]

    def __iter__(self):
        for e, (count, line) in enumerate(self.lines):
            if e == 0:
                continue
            yield e, count, line

    def position_of_byte(self, byte):
        lineno = bisect.bisect_left(self.lines, (byte + 1,)) - 1
        column = byte - self.lines[lineno][0]
        return lineno, column

    def byte_of_pos(self, lineno, column):
        # This requires a bit of explanation. The source passed to lib2to3's
        # parser has an extra newline added in some cases, to deal with a bug
        # in lib2to3 where it crashes hard if files don't end with a trailing
        # newline. When that extra line is added, the final DEDENT token in the
        # file will have a lineno equal to the lines in the file plus one,
        # becase it's "at" a location that doesn't exist in the real file. If
        # this case wasn't specifically caught, the self[lineno] would raise an
        # exception because lineno is beyond the last index in self.lines. So,
        # when that case is detected, return the final byte position.
        if lineno == len(self.lines) and column == 0:
            return self.last_byte
        byte, _ = self[lineno]
        byte += column
        return byte

    def byte_of_node(self, node):
        return self.byte_of_pos(node.lineno, node.column)


def byte_intersection(tree, lower, upper):
    ret = 0
    for i in tree.search(lower, upper):
        ret += min(i.end, upper) - max(i.begin, lower)
    return ret


class EbbLint(object):
    name = 'ebb_lint'
    version = __version__

    collected_checkers = None
    _source = None
    _lines = None

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename
        self._intervals = {
            'comments': IntervalTree(),
            'string literals': IntervalTree(),
        }

    @classmethod
    def add_options(cls, parser):
        parser.add_option('--hard-max-line-length', default=119, type=int,
                          metavar='n',
                          help='absolute maximum line length allowed')
        parser.config_options.append('hard-max-line-length')
        parser.add_option('--permissive-bulkiness-percentage', default=67,
                          type=int, metavar='p', help=(
                              'integer percentage of a line which must be '
                              'string literals or comments to be allowed to '
                              'pass the soft line limit'))
        parser.config_options.append('permissive-bulkiness-percentage')

    @classmethod
    def parse_options(cls, options):
        # We implement our own line-length checker because it's not possible to
        # customize how another checker does its checking.
        options.ignore += 'E501',
        cls.options = options

        # This vastly speeds up the test suite, since parse_options is called
        # on every test now, and venusian does a lot of work.
        if cls.collected_checkers is not None:
            return

        collected_checkers = []

        def register_checker(pattern, checker, extra):
            if ('python_minimum_version' in extra
                    and sys.version_info < extra['python_minimum_version']):
                return
            if ('python_disabled_version' in extra
                    and sys.version_info > extra['python_disabled_version']):
                return
            pattern = patcomp.compile_pattern(pattern)
            collected_checkers.append((pattern, checker, extra))

        scanner = venusian.Scanner(register=register_checker)
        scanner.scan(checkers)
        cls.collected_checkers = collected_checkers

    @property
    def source(self):
        if self._source is None:
            self._source = read_file_using_source_encoding(self.filename)
        return self._source

    @property
    def lines(self):
        if self._lines is None:
            self._lines = Lines(self.source.splitlines(True))
        return self._lines

    def _message_for_node(self, node, error, **kw):
        line_offset = kw.pop('line_offset', None)
        if line_offset is None:
            byte = self.lines.byte_of_node(node) + kw.pop('offset', 0)
            lineno, column = self.lines.position_of_byte(byte)
        else:
            lineno = node.lineno + line_offset
            column = kw.pop('column')
        return self._message_for_pos((lineno, column), error, **kw)

    def _message_for_pos(self, pos, error, **kw):
        lineno, column = pos
        message = 'L{:03d} {}'.format(
            error.value.code, error.value.message.format(**kw))
        return lineno, column, message, type(self)

    def run(self):
        with open(self.filename, 'r') as infile:
            self.future_features = detect_future_features(infile)
        d = driver.Driver(
            grammar_for_future_features(self.future_features),
            convert=pytree.convert)
        tree, trailing_newline = parse_source(d, self.source)
        if not trailing_newline:
            yield self._message_for_pos(
                self.lines.last_pos, Errors.no_trailing_newline)

        for error in self._check_tree(tree):
            yield error

        for error in self._check_line_lengths():
            yield error

    def _check_tree(self, tree):
        for node in tree.pre_order():
            for error in self._scan_node_for_ranges(node):
                yield error

            for pattern, checker, extra in self.collected_checkers:
                results = {}
                if not pattern.match(node, results):
                    continue
                for k in extra.get('comments_for', ()):
                    results[k + '_comments'] = [
                        c for c, _ in find_comments(node.prefix)]
                if extra.get('pass_filename', False):
                    results['filename'] = self.filename
                if extra.get('pass_future_features', False):
                    results['future_features'] = self.future_features
                for error_node, error, kw in checker(**results):
                    yield self._message_for_node(error_node, error, **kw)

    def _scan_node_for_ranges(self, node):
        if node.children or (node.type != token.STRING and not node.prefix):
            return

        byte = self.lines.byte_of_node(node)

        if node.type == token.STRING:
            self._intervals['string literals'].add(Interval(
                byte, byte + len(node.value)))

        comments = list(
            find_comments(node.prefix, byte - len(node.prefix)))
        for c, i in comments:
            self._intervals['comments'].add(i)
            m = _pep8_noqa(c)
            if m is not None:
                yield self._message_for_pos(
                    self.lines.position_of_byte(i.begin + m.start()),
                    Errors.no_noqa)

    def _check_line_lengths(self):
        soft_limit = self.options.max_line_length
        hard_limit = self.options.hard_max_line_length
        permitted_percentage = self.options.permissive_bulkiness_percentage
        for lineno, line_start, line in self.lines:
            line = line.rstrip('\r\n')
            if len(line) <= soft_limit:
                continue
            if len(line) > hard_limit:
                yield self._message_for_pos(
                    (lineno, hard_limit), Errors.line_too_long,
                    length=len(line), which_limit='hard', limit=hard_limit,
                    extra='')
                continue

            line_end = line_start + len(line)
            percentages = {}
            for name, i in self._intervals.items():
                n_bytes = byte_intersection(i, line_start, line_end)
                percentages[name] = p = n_bytes * 100 // len(line)
                assert 0 <= p <= 100, 'line percentage not in range'

            if any(p >= permitted_percentage for p in percentages.values()):
                continue

            extra = ' since the line has ' + '; '.join(
                '{p}% {name}'.format(p=p, name=name)
                for name, p in percentages.items())
            yield self._message_for_pos(
                (lineno, soft_limit), Errors.line_too_long,
                length=len(line), which_limit='soft', limit=soft_limit,
                extra=extra)
