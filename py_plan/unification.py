"""
Utilities for the py_plan library.
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from math import isclose


def is_variable(x):
    """
    Checks if the provided expression x is a variable, i.e., a string that
    starts with ?.

    >>> is_variable('?x')
    True
    >>> is_variable('x')
    False
    """
    return isinstance(x, str) and len(x) > 0 and x[0] == "?"


def subst(s, x):
    """
    Substitute the substitution s into the expression x.

    >>> subst({'?x': 42, '?y':0}, ('+', ('F', '?x'), '?y'))
    ('+', ('F', 42), 0)
    """
    if isinstance(x, tuple):
        return tuple(subst(s, xi) for xi in x)
    elif x in s:
        return s[x]
    else:
        return x


def unify(x, y, s=(), check=False, epsilon=0.0):
    """
    Unify expressions x and y given a provided mapping (s) and a numerical
    tolerance (epsilon). By default s is (), which gets recognized and replaced
    with an empty dictionary. Return a mapping (a dict) that will make x and y
    equal or, if this is not possible, then it returns None.

    >>> unify(('Value', '?a', '8'), ('Value', 'cell1', '8'), {})
    {'?a': 'cell1'}

    >>> unify(('Value', '?a', '8'), ('Value', 'cell1', '?b'), {})
    {'?a': 'cell1', '?b': '8'}
    """
    if s == ():
        s = {}

    if s is None:
        return None
    elif x == y:
        return s
    elif (isinstance(x, (int, float)) and isinstance(y, (int, float)) and
          isclose(x, y, abs_tol=epsilon)):
        return s
    elif is_variable(x):
        return unify_var(x, y, s, check)
    elif is_variable(y):
        return unify_var(y, x, s, check)
    elif (isinstance(x, tuple) and
          isinstance(y, tuple) and len(x) == len(y)):
        if not x:
            return s
        return unify(x[1:], y[1:], unify(x[0], y[0], s, epsilon), epsilon)
    else:
        return None


def unify_var(var, x, s, check=False):
    """
    Unify var with x using the mapping s. If check is True, then do an occurs
    check. By default the occurs check is turned off. Shutting the check off
    improves unification performance, but can sometimes result in unsound
    inference.

    >>> unify_var('?x', '?y', {})
    {'?x': '?y'}

    >>> unify_var('?x', ('relation', '?x'), {}, True)

    >>> unify_var('?x', ('relation', '?x'), {})
    {'?x': ('relation', '?x')}

    >>> unify_var('?x', ('relation', '?y'), {})
    {'?x': ('relation', '?y')}
    """
    if var in s:
        return unify(s[var], x, s)
    elif x in s:
        return unify(var, s[x], s)
    elif check and occur_check(var, x):
        return None
    else:
        return extend(s, var, x)


def occur_check(var, x):
    """
    Check if x contains var. This prevents binding a variable to an expression
    that contains the variable in an infinite loop.

    >>> occur_check('?x', '?x')
    True
    >>> occur_check('?x', '?y')
    False
    >>> occur_check('?x', ('relation', '?x'))
    True
    >>> occur_check('?x', ('relation', ('relation2', '?x')))
    True
    >>> occur_check('?x', ('relation', ('relation2', '?y')))
    False
    """
    if var == x:
        return True
    if isinstance(x, (list, tuple)):
        for e in x:
            if occur_check(var, e):
                return True
    return False


def extend(s, var, val):
    """
    Given a dictionary s and a variable and value, this returns a new dict with
    var:val added to the original dictionary.

    >>> extend({'a': 'b'}, 'c', 'd')
    {'a': 'b', 'c': 'd'}
    """
    s2 = {a: s[a] for a in s}
    s2[var] = val
    return s2


if __name__ == "__main__":

    print(unify('?x', ('relation', '?x'), {}))