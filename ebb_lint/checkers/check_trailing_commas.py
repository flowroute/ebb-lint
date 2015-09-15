from __future__ import unicode_literals

from lib2to3.pygram import python_symbols

from six.moves import reduce

from ebb_lint.checkers.registration import register_checker
from ebb_lint.errors import Errors


def last(seq):
    return reduce(lambda l, r: r, seq)


@register_checker("""

( atom< '(' contents=any+ end=')' >
| atom< '[' contents=any+ end=']' >
| atom< '{' contents=any+ end='}' >
)

""")
def check_trailing_commas(end, contents):
    last_element = contents[-1]
    if (last_element.children
            and last_element.children[-1].type == python_symbols.comp_for):
        # It's a comprehension, so ignore it.
        return
    last_element_leaf = last(last_element.pre_order())
    if last_element_leaf.value == ',':
        return
    if end.value == ')' and (
            len(contents) != 1
            or contents[0].type != python_symbols.testlist_gexp):
        # It's not a tuple or a generator expression; it's just something in
        # parentheses, so ignore it.
        return
    # If there's no trailing comma, the whitespace between the last element and
    # the closing delimiter must not contain a newline, as that would mean the
    # end of the last element and the closing delimiter are on different lines.
    if '\n' in end.prefix:
        yield last_element_leaf, Errors.no_trailing_comma_in_literal, {}
