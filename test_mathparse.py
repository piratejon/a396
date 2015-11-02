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

if __name__ == '__main__':
    unittest.main()

