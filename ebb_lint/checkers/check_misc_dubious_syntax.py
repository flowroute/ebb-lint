from __future__ import unicode_literals

from ebb_lint.checkers.registration import register_checker
from ebb_lint.errors import Errors


@register_checker("""

( import_from< 'from' pdb='pdb' any* >
| import_name< 'import' pdb='pdb' any* >
| dotted_as_name< pdb='pdb' any* >
)

""")
def check_for_pdb(pdb):
    yield pdb, Errors.no_debuggers, {}


@register_checker("""

power< any+ trailer< '.' func='set_trace' > trailer< '(' ')' > >

""")
def check_for_set_trace(func):
    yield func, Errors.no_debuggers, {}


@register_checker("""

f=file_input< any* >

""", comments_for=['f'])
def scan_top_level_comments(f, f_comments):
    if '# I sincerely swear that this is one-off code.' in f_comments:
        f.print_lint_ok = True
    return []


def scan_ancestry_for(node, attr, default):
    not_set = object()
    while node is not None:
        value = getattr(node, attr, not_set)
        if value is not not_set:
            return value
        node = node.parent
    return default


@register_checker("""

( simple_stmt< any* p='print' any* >
| print_stmt< p='print' any* >
| power< p='print' trailer< '(' any* ')' > any* >
)

""")
def check_for_print(p):
    if scan_ancestry_for(p, 'print_lint_ok', False):
        return
    yield p, Errors.no_print, {}
