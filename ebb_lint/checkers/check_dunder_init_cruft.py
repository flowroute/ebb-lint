from __future__ import unicode_literals

import os

from ebb_lint.checkers.registration import register_checker
from ebb_lint.errors import Errors


@register_checker("""

( classdef< which='class' any* >
| funcdef< which='def' any* >
)

""", pass_filename=True)
def check_disallowed_dunder_init_statements(filename, which):
    if os.path.basename(filename) != '__init__.py':
        return
    yield which, Errors.no_definition_statements_in_dunder_init, {}
