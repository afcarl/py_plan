from py_search.utils import compare_searches
from py_search.uninformed import depth_first_search
from py_search.informed import best_first_search

from py_plan.total_order import StateSpacePlanningProblem
from py_plan.base import Operator

load = Operator('load',
                [('At', '?c', '?a'),
                 ('At', '?p', '?a'),
                 ('Cargo', '?c'),
                 ('Plane', '?p'),
                 ('Airport', '?a')],
                [('not', ('At', '?c', '?a')),
                 ('In', '?c', '?p')])

unload = Operator('unload',
                  [('In', '?c', '?p'),
                   ('At', '?p', '?a'),
                   ('Cargo', '?c'),
                   ('Plane', '?p'),
                   ('Airport', '?a')],
                  [('At', '?c', '?a'),
                   ('not', ('In', '?c', '?p'))])

fly = Operator('fly',
               [('At', '?p', '?from'),
                ('Plane', '?p'),
                ('Airport', '?from'),
                ('Airport', '?to')],
               [('not', ('At', '?p', '?from')),
                ('At', '?p', '?to')])

start = [('At', 'C1', 'SFO'),
         ('At', 'C2', 'JFK'),
         ('At', 'P1', 'SFO'),
         ('At', 'P2', 'JFK'),
         ('Cargo', 'C1'),
         ('Cargo', 'C2'),
         ('Plane', 'P1'),
         ('Plane', 'P2'),
         ('Airport', 'JFK'),
         ('Airport', 'SFO')]

goal = [('At', 'C1', 'JFK'),
        ('At', 'C2', 'SFO')]

p = StateSpacePlanningProblem(start, goal, [load, unload, fly])

compare_searches([p], [depth_first_search, best_first_search])
