import ast

from ebb_devtools._version import __version__
from ebb_devtools.lint.errors import Errors
from ebb_devtools.lint import docstrings


class EbbLint(object):
    name = 'ebb_devtools lint'
    version = __version__

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename

    @classmethod
    def add_options(cls, parser):
        pass

    @classmethod
    def parse_options(cls, options):
        pass

    def _message_for(self, node, error, **kw):
        message = 'L{:03d} {}'.format(
            error.value.code, error.value.message.format(**kw))
        return node.lineno, node.col_offset, message, type(self)

    def _docstring_errors(self, node):
        docstring = ast.get_docstring(node, clean=False)
        if isinstance(node, ast.FunctionDef) and node.name == '__init__':
            if docstring is not None:
                yield self._message_for(node, Errors.no_docstring_on_init)
            return
        elif docstring is None:
            return
        purpose = docstrings.DocstringPurpose.other
        if (isinstance(node, ast.FunctionDef)
                and node.name.startswith('test_')):
            purpose = docstrings.DocstringPurpose.test
        for error, kw in docstrings.docstring_errors(purpose, docstring):
            yield self._message_for(node, error, **kw)

    def run(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                for error in self._docstring_errors(node):
                    yield error
