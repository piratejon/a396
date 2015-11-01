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

    def test_find_rhs_symbols(self):
        myast = ast.parse('x = 99 * b\ny = x + 17')
        stmts = list(mathparse.StaticMathParse.unwrap_module_statements(myast))
        rhs = mathparse.StaticMathParse.find_rhs_symbols(stmts[0])
        self.assertEqual(rhs, {'b'})

if __name__ == '__main__':
    unittest.main()

