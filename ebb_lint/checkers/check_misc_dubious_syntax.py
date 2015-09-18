# coding: utf-8

from __future__ import unicode_literals

import os

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


@register_checker(
    """

( import_from< 'from' mod=(NAME | dotted_name) any* >
| import_name< 'import' mod=(NAME | dotted_name) any* >
| dotted_as_name< mod=(NAME | dotted_name) any* >
)

    """,
    pass_filename=True, pass_future_features=True,
    python_disabled_version=(3, 0))
def check_for_implicit_relative_imports(
        filename, future_features, mod):  # ✘py33 ✘py34
    if 'absolute_import' in future_features:
        return
    [mod] = mod
    dirname = os.path.dirname(filename)
    segments = [l.value for l in mod.pre_order() if l.type == token.NAME]
    candidates = []
    candidates.extend(
        os.path.join(dirname,
                     *(segments[:-1] + ['{}.{}'.format(segments[-1], ext)]))
        for ext in ['py', 'pyc', 'pyo', 'pyd', 'so'])
    candidates.extend(
        os.path.join(dirname, *(segments + ['__init__.{}'.format(ext)]))
        for ext in ['py', 'pyc', 'pyo'])
    if not any(os.path.exists(candidate) for candidate in candidates):
        return

    node = next(mod.post_order())
    yield node, Errors.no_implicit_relative_imports, {}


@register_checker("""

( classdef< which='class' any* >
| funcdef< which='def' any* >
)

""", pass_filename=True)
def check_disallowed_dunder_init_statements(filename, which):
    if os.path.basename(filename) != '__init__.py':
        return
    yield which, Errors.no_definition_statements_in_dunder_init, {}


@register_checker("""

( suite< any* simple_stmt any* simple_stmt< p='pass' any > any* >
| if_stmt< 'if' any+ 'else' ':'
           suite< any* simple_stmt< p='pass' any > any* > >
| for_stmt< 'for' any+ 'else' ':'
            suite< any* simple_stmt< p='pass' any > any* > >
| while_stmt< 'while' any+ 'else' ':'
              suite< any* simple_stmt< p='pass' any > any* > >
| try_stmt< 'try' any+ 'finally' ':'
            suite< any* simple_stmt< p='pass' any > any* > >
)

""")
def check_useless_pass(p):
    yield p, Errors.useless_pass, {}


@register_checker("""

try_stmt< 'try' any+ 'except' ':'
          suite< any* simple_stmt< p='pass' any > any* >
          any* >

""")
def check_except_pass(p):
    yield p, Errors.no_except_pass, {}


@register_checker("""

( return_stmt< stmt='return' atom< lparen='(' any* ')' > >
| del_stmt< stmt='del' atom< lparen='(' any* ')' > >
| raise_stmt< stmt='raise' atom< lparen='(' any* ')' > >
| assert_stmt< stmt='assert' atom< lparen='(' any* ')' > >
| yield_expr< stmt='yield' atom< lparen='(' any* ')' > >
| print_stmt< stmt='print' atom< lparen='(' any* ')' > >
)

""")
def check_useless_parens(stmt, lparen):
    if lparen.prefix:
        return
    yield stmt, Errors.useless_parens, {'stmt': stmt.value}


@register_checker("""

yield_expr< stmt='yield' yield_arg< 'from' atom< lparen='(' any* ')' > > >

""", python_minimum_version=(3, 4))
def check_useless_parens_on_yield_from(stmt, lparen):  # ✘py27 ✘py33
    if lparen.prefix:
        return
    yield stmt, Errors.useless_parens, {'stmt': 'yield from'}


@register_checker("""

simple_stmt < power< f=('map' | 'filter') trailer< '(' any* ')' > any* > any* >

""")
def check_no_side_effects_function(f):
    [f] = f
    yield f, Errors.no_side_effects, {'thing': f.value}


_expr_type = {
    '[': 'a list comprehension',
    '{': 'a dict or set comprehension',
}


@register_checker("""

simple_stmt< ( atom< start='[' listmaker< any+ comp_for< any+ > > ']' >
             | atom< start='{' dictsetmaker< any+ comp_for< any+ > > '}' >
             ) any* >

""")
def check_no_side_effects_literal(start):
    yield start, Errors.no_side_effects, {'thing': _expr_type[start.value]}


@register_checker("""

power< f=('map' | 'filter') trailer< '(' arglist<
    lambdef ',' any*
> any* ')' > any* >

""")
def check_no_map_or_filter_with_lambda(f):
    [f] = f
    yield f, Errors.no_map_or_filter_with_lambda, {'func': f.value}


@register_checker("""

decorator< at='@' 'staticmethod' any* >

""")
def check_no_staticmethod_decorator(at):
    yield at, Errors.no_staticmethod_decorator, {}


# XXX: There's a bit of uncovered code below, but it's really just because I'm
# coding defensively. I don't know if it's possible to get lib2to3 to emit an
# AST that's in this particular shape, but I don't want to get caught offguard
# if it is. Maybe at some point I'll turn these into asserts or something?

class NoParentheizedGroup(Exception):
    pass


def parenthesized_group_leaves(container):
    if container is None or not container.children:  # pragma: nocover
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
            if child.type != token.STRING:  # pragma: nocover
                break
        else:
            # all leaves were string literals
            return
    except NoParentheizedGroup:
        pass
    yield first_string, Errors.no_unintentional_implicit_concatenation, {}
