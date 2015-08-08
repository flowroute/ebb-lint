from ebb_devtools.lint.checkers.registration import register_checker
from ebb_devtools.lint.errors import Errors


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

( simple_stmt< any* p='print' any* >
| print_stmt< p='print' any* >
)

""")
def check_for_print(p):
    yield p, Errors.no_print, {}
