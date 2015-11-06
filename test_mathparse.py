#!/usr/bin/python3

import unittest
import ast

import mathparse

class TestMathParse(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestMathParse, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def test_unwrap_statements(self):
        myast = ast.parse('x = 99 * b\ny = x + 17')
        stmts = list(mathparse.StaticMathParse.unwrap_module_statements(myast))
        self.assertEqual(len(stmts), 2)

    def test_find_lhs_and_rhs_symbols(self):
        myast = ast.parse('x = 99 * b\ny = x + 17 * dag + yo / ribbit + frobnitz\na,b,c=some_goofy_tuple_thing(x, y, z)')
        stmts = list(mathparse.StaticMathParse.unwrap_module_statements(myast))

        self.assertEqual(mathparse.StaticMathParse.find_rhs_symbols(stmts[0]), {'b'})
        self.assertEqual(mathparse.StaticMathParse.find_lhs_symbols(stmts[0]), {'x'})

        self.assertEqual(mathparse.StaticMathParse.find_rhs_symbols(stmts[1]), {
            'x', 'dag', 'yo', 'ribbit', 'frobnitz'
        })
        self.assertEqual(mathparse.StaticMathParse.find_lhs_symbols(stmts[1]), {'y'})

        self.assertEqual(mathparse.StaticMathParse.find_rhs_symbols(stmts[2]), {'x', 'y', 'z'})
        self.assertEqual(mathparse.StaticMathParse.find_lhs_symbols(stmts[2]), {'a', 'b', 'c'})

    def test_update_context_from_statement(self):
        myast = ast.parse('x = 99 * b\ny = x + 17 * dag + yo / ribbit + frobnitz\na,b,c=some_goofy_tuple_thing(x, y, z)')
        stmts = list(mathparse.StaticMathParse.unwrap_module_statements(myast))

        ctx = [mathparse.StaticMathParse.update_context(stmt) for stmt in stmts]
        self.assertEqual(ctx[0].free_variables, {'b'})
        self.assertEqual(ctx[0].bound_variables, {'x'})
        self.assertEqual(ctx[0].statement, stmts[0])

        self.assertEqual(ctx[1].free_variables, {'x', 'dag', 'yo', 'ribbit', 'frobnitz'})
        self.assertEqual(ctx[1].bound_variables, {'y'})
        self.assertEqual(ctx[1].statement, stmts[1])

        self.assertEqual(ctx[2].free_variables, {'x', 'y', 'z'})
        self.assertEqual(ctx[2].bound_variables, {'a', 'b', 'c'})
        self.assertEqual(ctx[2].statement, stmts[2])

    def test_render_expression(self):
        myast = ast.parse('x = 99 * b\ny = x + 17 * dag + yo / ribbit + frobnitz\na,b,c=some_goofy_tuple_thing(x, y, z)')
        stmts = list(mathparse.StaticMathParse.unwrap_module_statements(myast))

        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[0].value),
            '(99 * [_b])'
        )
        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[1].value),
            '((([_x] + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz])'
        )
        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[2].value),
            'some_goofy_tuple_thing([_x], [_y], [_z])'
        )

    def test_identify_substituting_context(self):
        myast = ast.parse('x = 99 * b\ny = x + 17 * dag + yo / ribbit + frobnitz\na,b,c=some_goofy_tuple_thing(x, y, z)\nx = 33 + y\ny = 7 / x')
        stmts = list(mathparse.StaticMathParse.unwrap_module_statements(myast))
        ctx = [mathparse.StaticMathParse.update_context(stmt) for stmt in stmts]

        # stmt 0
        self.assertEqual(mathparse.StaticMathParse.find_substitution_context('b', ctx[0:0]), -1)

        # stmt 1
        self.assertEqual(mathparse.StaticMathParse.find_substitution_context('x', ctx[0:1]), 0)

        # stmt 2
        self.assertEqual(mathparse.StaticMathParse.find_substitution_context('x', ctx[0:2]), 0)
        # stmt 2
        self.assertEqual(mathparse.StaticMathParse.find_substitution_context('y', ctx[0:2]), 1)

        # stmt 3
        self.assertEqual(mathparse.StaticMathParse.find_substitution_context('y', ctx[0:3]), 1)

        # stmt 4
        self.assertEqual(mathparse.StaticMathParse.find_substitution_context('x', ctx[0:4]), 3)

        myast = ast.parse('x = 55\nx = 99 * x')
        stmts = list(mathparse.StaticMathParse.unwrap_module_statements(myast))
        ctx = [mathparse.StaticMathParse.update_context(stmt) for stmt in stmts]
        # avoid some circular symbol lookups
        self.assertEqual(mathparse.StaticMathParse.find_substitution_context('x', ctx[0:0]), -1)
        self.assertEqual(mathparse.StaticMathParse.find_substitution_context('x', ctx[0:1]), 0)

    def test_generate_context_substituted_expression(self):
        myast = ast.parse('x = 99 * b\ny = x + 17 * dag + yo / ribbit + frobnitz\na,b,c=some_goofy_tuple_thing(x, y, z)')
        stmts = list(mathparse.StaticMathParse.unwrap_module_statements(myast))
        ctx = [mathparse.StaticMathParse.update_context(stmt) for stmt in stmts]

        stmt1 = mathparse.StaticMathParse.context_substitute(stmts[1], ctx[0:1])
        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmt1.value),
            '((((99 * [_b]) + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz])'
        )

        stmt2 = mathparse.StaticMathParse.context_substitute(stmts[2], ctx[0:2])
        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmt2.value),
            'some_goofy_tuple_thing((99 * [_b]), ((((99 * [_b]) + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz]), [_z])'
        )

    def test_redefining_a_symbol(self):
        myast = ast.parse('x = 99 * b\ny = x + 17 * dag + yo / ribbit + frobnitz\na,b,c=some_goofy_tuple_thing(x, y, z)\nx = 33 + y\ny = 7 / x')
        stmts = list(mathparse.StaticMathParse.unwrap_module_statements(myast))

        ctx = []
        ctx.append(mathparse.StaticMathParse.update_context(stmts[0]))
        ctx.append(mathparse.StaticMathParse.update_context(stmts[1]))
        stmts[1] = mathparse.StaticMathParse.context_substitute(stmts[1], ctx[0:1])
        ctx.append(mathparse.StaticMathParse.update_context(stmts[2]))
        stmts[2] = mathparse.StaticMathParse.context_substitute(stmts[2], ctx[0:2])
        ctx.append(mathparse.StaticMathParse.update_context(stmts[3]))
        stmts[3] = mathparse.StaticMathParse.context_substitute(stmts[3], ctx[0:3])
        ctx.append(mathparse.StaticMathParse.update_context(stmts[4]))
        stmts[4] = mathparse.StaticMathParse.context_substitute(stmts[4], ctx[0:4])

        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[1].value),
            '((((99 * [_b]) + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz])'
        )

        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[2].value),
            'some_goofy_tuple_thing((99 * [_b]), ((((99 * [_b]) + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz]), [_z])'
        )

        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[3].value),
            '(33 + ((((99 * [_b]) + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz]))'
        )

        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[4].value),
            '(7 / (33 + ((((99 * [_b]) + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz])))'
        )

    def test_redefine_symbols_with_help(self):
        myast = ast.parse('x = 99 * b\ny = x + 17 * dag + yo / ribbit + frobnitz\na,b,c=some_goofy_tuple_thing(x, y, z)\nx = 33 + y\ny = 7 / x')

        stmts = list(
            mathparse.StaticMathParse.substitution_wrapper(
                mathparse.StaticMathParse.unwrap_module_statements(myast)
            )
        )

        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[1].value),
            '((((99 * [_b]) + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz])'
        )

        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[2].value),
            'some_goofy_tuple_thing((99 * [_b]), ((((99 * [_b]) + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz]), [_z])'
        )

        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[3].value),
            '(33 + ((((99 * [_b]) + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz]))'
        )

        self.assertEqual(
            mathparse.StaticMathParse.render_expression(stmts[4].value),
            '(7 / (33 + ((((99 * [_b]) + (17 * [_dag])) + ([_yo] / [_ribbit])) + [_frobnitz])))'
        )

        

if __name__ == '__main__':
    unittest.main()

