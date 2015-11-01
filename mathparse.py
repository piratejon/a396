#!/usr/bin/python3

"""Implementation of MathParse class"""

import types, ast

class StaticMathParse:
    """StaticMathParse holds testable stateless functions used in a MathParse context."""

    @staticmethod
    def unwrap_module_statements(module):
        """Given an ast.Module, return the top-level statements in its body."""
        for stmt in module.body:
            yield stmt

    @staticmethod
    def find_rhs_symbols(stmt):
        """Given an ast.Statement, return symbols in the right-hand side."""

        class RHSVisitor:
            """Traverse an AST expression, returning RHS symbols."""
            @classmethod
            def visit(cls, node):
                """Default visit method/dispatcher."""
                yield (getattr(cls, 'visit_' + node.__class__.__name__))(node)
            
            @classmethod
            def visit_Assign(cls, node):
                """Get into the RHS."""
                yield (getattr(cls, 'visit_' + node.__class__.__name__))(node)

        def evaluate_results(generator):
            """Run over a generator of generators of generators... returning the objects."""
            for gen in generator:
                if isinstance(gen, types.GeneratorType):
                    yield evaluate_results(gen)
                else:
                    yield gen

        yield set(evaluate_results(RHSVisitor.visit(stmt)))

class MathParse:
    """MathParse turns Python functions into Tableau calculations.

    For example:
    # Abramowitz and Stegun 7.1.28
    def erf_appx(z):
        a = [1, 0.0705230784, 0.0422820123, 0.0092705272, 0.0001520143, 0.0002765672, 0.0000430638]
        return sign(z)*(1 - (1/pow(sum([pow(abs(z), i)*a[i] for i in range(len(a))]),16)))

    yields:
        _erf_appx_arg_z: z
        _erf_appx: ...

    Function arguments are represented by Tableau expressions too. The z
    argument to erf_appx is represented in the _erf_appx expression as
    _erf_appx_arg_z. Because Tableau calculations do not have arguments,
    each time a translated function is referenced with a different argument
    it must be cloned, when it is prefixed with the name of the referencing
    function:

        def h(a):
            return sin(a)^2 + cos(a)^2

        def m(a):
            return h(a) * h(1 - a)

    yields:
        _h_arg_a: a
        _h: ((POW(SIN([_h_arg_a]), 2)) + (POW(COS([_h_arg_a]), 2)))
        _m_arg_a: a
        _m_h_1_arg_a: [_m_arg_a]
        _m_h_2_arg_a: (1 - [_m_arg_a])
        _m_h_1: ((POW(SIN([_m_h_1_arg_a]), 2)) + (POW(COS([_m_h_1_arg_a]), 2)))
        _m_h_2: ((POW(SIN([_m_h_2_arg_a]), 2)) + (POW(COS([_m_h_2_arg_a]), 2)))
        _m: ([_m_h_1] * [_m_h_2])

    Chi Squared CDF in terms of Gamma CDF:
      a = df*0.5D0
      xx = x*0.5D0
      CALL cumgam(xx,a,cum,ccum)
    """

    def __init__(self):
        """Initialize instance variables for this context."""
        self.formulae = {}

