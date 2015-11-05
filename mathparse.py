#!/usr/bin/python3

"""Implementation of MathParse class"""

import types
import ast

class YieldingVisitor:
    """YieldingVisitor implements an AST visitor which returns values through yield."""

    @classmethod
    def evaluate_generated_values(cls, generator):
        """Flattens the generator of generators."""
        if isinstance(generator, types.GeneratorType) and not isinstance(generator, str):
            for gen in generator:
                yield from cls.evaluate_generated_values(gen)
        else:
            yield generator

    @classmethod
    def find_symbols(cls, expr):
        """Sponge the generated symbols into a result."""
        return set(
            symbol for symbol in cls.evaluate_generated_values(
                cls.visit(expr)
            )
        )

    @classmethod
    def visit(cls, node):
        """Visit the nodes."""
        yield (
            getattr(cls, 'visit_' + node.__class__.__name__.lower(), cls.generic_visit)
        )(node)

    @classmethod
    def generic_visit(cls, node):
        """
            The node does not have a special handler so make sure to visit its children.
            Adapted from:
            <http://svn.python.org/projects/python/branches/release26-maint/Lib/ast.py>
            Visited 2015-11-01.
        """
        if isinstance(node, ast.AST):
            for _, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            yield cls.visit(item)
                elif isinstance(value, ast.AST):
                    yield cls.visit(value)
        else:
            try:
                iterator = iter(node)
            except TypeError:
                pass
            else:
                for item in iterator:
                    yield cls.visit(item)

class SymbolFinderVisitor(YieldingVisitor):
    """Traverse an AST expression for symbols."""

    @staticmethod
    def visit_name(node):
        """Fetch the symbol from a name node."""
        yield node.id

    @classmethod
    def visit_call(cls, node):
        """Skip function names but look at argument lists."""
        yield cls.visit(node.args)

class TranslatorVisitor(YieldingVisitor):
    """Convert an AST into a Tableau string."""

    @classmethod
    def return_string(cls, generator):
        """Join together generated strings."""
        strings = cls.evaluate_generated_values(generator)
        return ''.join(strings)

    @staticmethod
    def visit_name(node):
        """Translate a name node."""
        yield '[_{}]'.format(node.id)

    @staticmethod
    def visit_num(node):
        """Translate a number node."""
        yield str(node.n)

    @staticmethod
    def binop_token(operator):
        """Lookup the operator's token."""
        return {
            'Add': '+',
            'Sub': '-',
            'Mult': '*',
            'Div': '/',
            'Mod': '%',
        }[operator.__class__.__name__]

    @classmethod
    def visit_binop(cls, node):
        """Render a binop node."""
        yield '({} {} {})'.format(
            cls.return_string(cls.visit(node.left)),
            cls.binop_token(node.op),
            cls.return_string(cls.visit(node.right))
        )

    @classmethod
    def visit_call(cls, node):
        """Render a call."""
        yield '{}({})'.format(
            node.func.id,
            ', '.join([cls.return_string(cls.visit(arg)) for arg in node.args])
        )

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
        symbol_finder = SymbolFinderVisitor()
        return symbol_finder.find_symbols(stmt.value)

    @staticmethod
    def find_lhs_symbols(stmt):
        """Given an ast.Statement, return symbols from the left-hand side."""
        symbol_finder = SymbolFinderVisitor()
        return symbol_finder.find_symbols(stmt.targets[0])

    @classmethod
    def update_context(cls, stmt):
        """Fill out the context based on a statement."""

        class Context:
            """Contains the state associated with a statement's context."""

            def __init__(self, stmt, cls):
                self.free_variables = cls.find_rhs_symbols(stmt)
                self.bound_variables = cls.find_lhs_symbols(stmt)
                self.statement = stmt

        return Context(stmt, cls)

    @staticmethod
    def render_expression(expr):
        """Convert an expression AST into a Tableau expression string."""
        translator_visitor = TranslatorVisitor()
        return translator_visitor.return_string(translator_visitor.visit(expr))

    @staticmethod
    def find_substitution_context(symbol, context):
        """Figure out what context the symbol was defined in. -1 is not found."""
        for i, ctx in reversed(list(enumerate(context))):
            if symbol in ctx.bound_variables:
                return i
        return -1

    @classmethod
    def context_substitute(cls, statement, context):
        """Return a copy of the statement with the context substituted in."""

        class SubstituteExpressions(ast.NodeTransformer):
            """Replacing visitor."""

            def visit_Name(self, node):
                """Lookup this name in the context and substitute if possible."""
                location = cls.find_substitution_context(node.id, context)
                if location >= 0:
                    return context[location].statement.value
                else:
                    return node

        return SubstituteExpressions().visit(statement)

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

