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
        self.assertEqual(mpctx.function_list[0]['name'], "f1")

        self.assertEqual(ctxmathparse.get_function_args(mpctx.function_list[0]), {
                "x": "_f1_arg_x"
            }
        )

#        self.assertEqual(mpctx.translate(), {
#                "_f1_arg_x": "x",
#                "_f1": "([_f1_arg_x] + 9)"
#            }
#        )

        f = """
def f1(x):
    return x + 9

def f2(x):
    return x * 99
"""
        mpctx = ctxmathparse.MathParse()
        mpctx.parse_string(f)
        self.assertEqual(len(mpctx.function_list), 2)
        self.assertEqual(mpctx.function_list[0]['name'], "f1")
        self.assertEqual(mpctx.function_list[1]['name'], "f2")

        self.assertEqual(ctxmathparse.get_function_args(mpctx.function_list[0]), {
                "x": "_f1_arg_x"
            }
        )

        self.assertEqual(ctxmathparse.get_function_args(mpctx.function_list[1]), {
                "x": "_f2_arg_x"
            }
        )

#        self.assertEqual(mpctx.translate(), {
#                "_f1_arg_x": "x",
#                "_f1": "([_f1_arg_x] + 9)",
#                "_f2_arg_x": "x",
#                "_f2": "([_f2_arg_x] * 99)"
#            }
#        )

if __name__ == '__main__':
    unittest.main()

