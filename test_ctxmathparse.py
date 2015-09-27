#!/usr/bin/python3

import unittest

import ctxmathparse

class TestMathParse(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestMathParse, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def test_init(self):
        mpctx = ctxmathparse.MathParse()
        self.assertEqual(mpctx.function_list, [])
        self.assertEqual(mpctx.source, '')
        self.assertEqual(mpctx.objast, None)

    def test_objectify_ast(self):
        f = """
def f1(x):
    return x + 9
"""
        objast = ctxmathparse.objectify_string(f)

    def test_add_function_to_context(self):
        f = """
def f1(x):
    return x + 9
"""
        mpctx = ctxmathparse.MathParse()
        mpctx.parse_string(f)
        self.assertEqual(len(mpctx.function_list), 1)
        self.assertEqual(mpctx.function_list[0].name, "f1")

        self.assertEqual(mpctx.function_list[0].args, {
                "x": "_f1_arg_x"
            }
        )

        self.assertEqual(
            mpctx.function_list[0].translate_function_statement(0),
            "([_f1_arg_x] + 9)"
        )

        self.assertEqual(mpctx.function_list[0].collect_function_statements(), [
                "([_f1_arg_x] + 9)"
            ]
        )

        self.assertEqual(mpctx.function_list[0].get_function_statement(), "[_f1_stmt_0]")

        self.assertEqual(mpctx.translate(), {
                "_f1_arg_x": "x",
                "_f1_stmt_0": "([_f1_arg_x] + 9)",
                "_f1": "[_f1_stmt_0]"
            }
        )

        f = """
def f1(x):
    return x + 9

def f2(x):
    return x * 99
"""
        mpctx = ctxmathparse.MathParse()
        mpctx.parse_string(f)
        self.assertEqual(len(mpctx.function_list), 2)
        self.assertEqual(mpctx.function_list[0].name, "f1")
        self.assertEqual(mpctx.function_list[1].name, "f2")

        self.assertEqual(mpctx.function_list[0].args, {
                "x": "_f1_arg_x"
            }
        )

        self.assertEqual(mpctx.function_list[1].args, {
                "x": "_f2_arg_x"
            }
        )

        self.assertEqual(mpctx.translate(), {
                "_f1_arg_x": "x",
                "_f1_stmt_0": "([_f1_arg_x] + 9)",
                "_f1": "[_f1_stmt_0]",
                "_f2_arg_x": "x",
                "_f2_stmt_0": "([_f2_arg_x] * 99)",
                "_f2": "[_f2_stmt_0]"
            }
        )

    def test_two_statements_in_one_function(self):
        f = """
def f1(x, y):
    a = x * y
    return a + 5
"""
        mpctx = ctxmathparse.MathParse()
        mpctx.parse_string(f)
        self.assertEqual(mpctx.translate(), {
                "_f1_arg_x": "x",
                "_f1_arg_y": "y",
                "_f1_stmt_0": "([_f1_arg_x] * [_f1_arg_y])",
                "_f1_stmt_1": "([_f1_stmt_0] + 5)",
                "_f1": "[_f1_stmt_1]"
            }
        )

    def test_augadd(self):
        f = """
def f(a, x, y):
    a = x * y
    a -= 6
    return a + 7
"""

        # o = ctxmathparse.objectify_string(f)
        # print(o)
        mpctx = ctxmathparse.MathParse()
        mpctx.parse_string(f)
        self.assertEqual(mpctx.translate(), {
                "_f_arg_a": "a",
                "_f_arg_x": "x",
                "_f_arg_y": "y",
                "_f_stmt_0": "([_f_arg_x] * [_f_arg_y])",
                "_f_stmt_1": "([_f_stmt_0] - 6)",
                "_f_stmt_2": "([_f_stmt_1] + 7)",
                "_f": "[_f_stmt_2]"
            }
        )

#    def test_if(self):
#        f = """
#def f(a, x, y):
#    a = x * y
#    if x > 9:
#        a += 8
#    else:
#        a = a
#    return a + 7
#"""
#
#        mpctx = ctxmathparse.MathParse()
#        mpctx.parse_string(f)
#        print(mpctx.objast)
#        self.assertEqual(mpctx.translate(), {
#                "_f_arg_a": "a",
#                "_f_arg_x": "x",
#                "_f_arg_y": "y",
#                "_f_stmt_0": "([_f_arg_x] * [_f_arg_y])",
#                "_f_stmt_1_t": "([_f_stmt_0] + 8)",
#                "_f_stmt_1_f": "[_f_stmt_0]",
#                "_f_stmt_1": "IF ([_f_arg_x] > 9) THEN [_f_stmt_1_t] ELSE [_f_stmt_1_f] END",
#                "_f_stmt_2": "([_f_stmt_1] + 7)",
#                "_f": "[_f_stmt_2]"
#            }
#        )

    def test_translate_symbol_in_context(self):
        ctx = ctxmathparse.MathParseContext("enclosing_context")
        self.assertEqual(ctx.translate_symbol("a"), "_enclosing_context:a")

        childctx = ctx.create_child_context("enclosed_context")
        self.assertEqual(childctx.translate_symbol("b"), "_enclosing_context:enclosed_context:b")
        self.assertEqual(childctx.get_parent(), ctx)

        secondchild = childctx.create_child_context("2nd_context")
        self.assertEqual(secondchild.translate_symbol("c"), "_enclosing_context:enclosed_context:2nd_context:c")
        self.assertEqual(secondchild.get_parent(), childctx)

if __name__ == '__main__':
    unittest.main()

