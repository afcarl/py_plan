from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from itertools import product
from random import random
from random import shuffle

from concept_formation.utils import isNumber
from py_search.base import Problem
from py_search.base import Node
from py_search.uninformed import depth_first_search
from unification import is_variable
from unification import subst
from unification import unify


def build_index(facts):
    """
    Given an iterator of facts returns a dict index.
    """
    index = {}
    for fact in facts:
        key = index_key(fact)
        # print('KEY', key)
        for k in get_variablized_keys(key):
            # print('VB KEY', k)
            if k not in index:
                index[k] = []
            index[k].append(fact)
    return index


def index_key(fact):
    """
    A new total indexing of the fact. Just build the whole damn thing, assuming
    it doesn't explode the memory usage.

    >>> index_key('cell')
    'cell'

    >>> index_key(('cell',))
    ('cell',)

    >>> index_key(('cell', '5'))
    ('cell', '5')

    >>> index_key((('value', '?x'), '5'))
    (('value', '?'), '5')

    >>> index_key((('X',('Position','Block1')), 10))
    (('X',('Position','Block1')), '#NUM')

    >>> index_key((('value', ('Add', ('value', '?x'),
    ...                              ('value', '?y'))), '5'))
    (('value', ('Add', ('value', '?'), ('value', '?'))), '5')
    """
    if isinstance(fact, tuple):
        return tuple(index_key(ele) for ele in fact)
    elif is_variable(fact):
        return '?'
    elif isNumber(fact):
        return '#NUM'
    else:
        return fact


def get_variablized_keys(key):
    """
    Takes the triple key given above (fact[0], fact[1], value) and returns all
    the possible variablizations of it.

    >>> [k for k in get_variablized_keys(('value', 'cell', '5'))]
    [('value', 'cell', '5'), ('value', 'cell', '?'), \
('value', '?', '5'), ('value', '?', '?'), '?']

    >>> [k for k in get_variablized_keys(('value', '?', '5'))]
    [('value', '?', '5'), ('value', '?', '?'), '?']

    >>> [k for k in get_variablized_keys((('value',
    ...                                    ('Add', ('value', 'TableCell'),
    ...                                            ('value', 'TableCell'))),
    ...                                    '5'))]
    [(('value', ('Add', ('value', 'TableCell'), ('value', 'TableCell'))), \
'5'), (('value', ('Add', ('value', 'TableCell'), ('value', 'TableCell'))), \
'?'), (('value', ('Add', ('value', 'TableCell'), ('value', '?'))), '5'), \
(('value', ('Add', ('value', 'TableCell'), ('value', '?'))), '?'), (('value', \
('Add', ('value', 'TableCell'), '?')), '5'), (('value', ('Add', ('value', \
'TableCell'), '?')), '?'), (('value', ('Add', ('value', '?'), ('value', \
'TableCell'))), '5'), (('value', ('Add', ('value', '?'), ('value', \
'TableCell'))), '?'), (('value', ('Add', ('value', '?'), ('value', '?'))), \
'5'), (('value', ('Add', ('value', '?'), ('value', '?'))), '?'), (('value', \
('Add', ('value', '?'), '?')), '5'), (('value', ('Add', ('value', '?'), \
'?')), '?'), (('value', ('Add', '?', ('value', 'TableCell'))), '5'), ((\
'value', ('Add', '?', ('value', 'TableCell'))), '?'), (('value', ('Add', \
'?', ('value', '?'))), '5'), (('value', ('Add', '?', ('value', '?'))), '?'), \
(('value', ('Add', '?', '?')), '5'), (('value', ('Add', '?', '?')), '?'), \
(('value', '?'), '5'), (('value', '?'), '?'), ('?', '5'), ('?', '?'), '?']
    """
    yield key

    if isinstance(key, tuple):

        if isinstance(key[0], tuple):
            head = None
            body = key
        else:
            head = key[0]
            body = key[1:]

        possible_bodies = [list(get_variablized_keys(e)) for e in
                           body]
        for body in product(*possible_bodies):
            if head is None:
                new = tuple(body)
            else:
                new = (head,) + tuple(body)
            if new != key:
                yield new

    if not is_variable(key):
        yield '?'


def extract_strings(s):
    """
    Gets all of the string elements via iterator and depth first traversal.
    """
    if isinstance(s, (tuple, list)):
        for ele in s:
            for inner in extract_strings(ele):
                yield '%s' % inner
    else:
        yield s


def is_negated_term(term):
    """
    Checks if a provided element is a term and is a negated term.
    """
    return isinstance(term, tuple) and len(term) > 0 and term[0] == 'not'


def update_neg_pattern(neg_pattern, sub, index, epsilon):
    new_neg_pattern = []
    bound_set = set(sub)

    for term in neg_pattern:
        args = set(e for e in extract_strings(term) if is_variable(e))
        if args.issubset(bound_set):
            bterm = subst(sub, term)
            if bterm in index and len(index[bterm]) > 0:
                return None
        else:
            new_neg_pattern(term)

    return new_neg_pattern


def pattern_match(pattern, index, substitution, epsilon=0.0):
    """
    Find substitutions that yield a match of the pattern against the provided
    index. If no match is found then it returns None.
    """
    substitution = frozenset(substitution.items())
    pos_pattern = [t for t in pattern if not is_negated_term(t)]
    neg_pattern = [t[1] for t in pattern if is_negated_term(t)]

    problem = PatternMatchingProblem(substitution, extra=(pos_pattern,
                                                          neg_pattern, index,
                                                          epsilon))

    for solution in depth_first_search(problem):
        yield dict(solution.state)


class PatternMatchingProblem(Problem):
    """
    Used to unify a complex first-order pattern. Supports negations in
    patterns using negation-as-failure.
    """
    def successors(self, node):
        """
        Successor nodes are possible next pattern elements that can be unified.
        """
        sub = dict(node.state)
        pos_pattern, neg_pattern, index, epsilon = node.extra

        # Figure out best term to match (only need to choose 1 and don't need
        # to backtrack over choice).
        terms = [(len(index[term]) if term in index else 0, random(), term) for
                 term in pos_pattern]
        terms.sort()
        term = terms[0][2]

        facts = [f for f in index[index_key(term)]]
        shuffle(facts)

        for fact in facts:
            new_sub = unify(term, fact, sub, epsilon)
            if new_sub is None:
                continue

            new_neg_pattern = update_neg_pattern(neg_pattern, new_sub, index,
                                                 epsilon)
            if new_neg_pattern is None:
                continue

            pos_pattern = [other for other in pos_pattern if term != other]

            yield Node(frozenset(new_sub.items()), node, None, 0,
                       (pos_pattern, new_neg_pattern, index, epsilon))

    def goal_test(self, node):
        """
        If there are no positive patterns left to match, then we're done.
        """
        pos_patterns, _, _, _ = node.extra
        return len(pos_patterns) == 0


if __name__ == "__main__":

    kb = [('on', 'A', 'B'), ('on', 'B', 'C'), ('on', 'C', 'D')]
    q = [('on', '?x', '?y'), ('on', '?y', '?z'), ('not', ('on', '?y', '3'))]

    index = build_index(kb)

    from pprint import pprint
    for a in pattern_match(q, index, {}):
        pprint(a)
