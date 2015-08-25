from __future__ import unicode_literals

from lib2to3.pgen2 import token

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


class NoParentheizedGroup(Exception):
    pass


def parenthesized_group_leaves(container):
    if container is None or not container.children:
        raise NoParentheizedGroup()
    first_child = container.children[0]
    last_child = container.children[-1]
    if not ((not first_child.children and first_child.value == '(')
            and (not last_child.children and last_child.value == ')')):
        raise NoParentheizedGroup()
    for child in container.children[1:-1]:
        for subchild in child.pre_order():
            if not subchild.children:
                yield subchild


@register_checker("""

atom=atom< first_string=STRING STRING+ >

""")
def check_for_unintentional_implicit_concatenation(atom, first_string):
    try:
        for child in parenthesized_group_leaves(atom.parent):
            if child.type != token.STRING:
                break
        else:
            # all leaves were string literals
            return
    except NoParentheizedGroup:
        pass
    yield first_string, Errors.no_unintentional_implicit_concatenation, {}
