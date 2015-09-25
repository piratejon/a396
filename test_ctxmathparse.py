#!/usr/bin/python3

import unittest

import ctxmathparse

class TestMathParse(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestMathParse, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def test_init(self):
        mpctx = ctxmathparse.MathParse()
        self.assertEqual(mpctx.functions, [])
        self.assertEqual(mpctx.source, {})
        self.assertEqual(mpctx.ast, None)

    def test_add_function_to_context(self):
        f = """
def f1(x):
    return x + 9
"""
        mpctx = ctxmathparse.MathParse()
        mpctx.parse_string(f)
        self.assertEqual(len(mpctx.functions), 1)
        self.assertEqual(mpctx.functions[0]['name'], "f1")

        f = """
def f1(x):
    return x + 9

def f2(x):
    return x * 99
"""
        mpctx = ctxmathparse.MathParse()
        mpctx.parse_string(f)
        self.assertEqual(len(mpctx.functions), 2)
        self.assertEqual(mpctx.functions[0]['name'], "f1")
        self.assertEqual(mpctx.functions[1]['name'], "f2")

if __name__ == '__main__':
    unittest.main()

