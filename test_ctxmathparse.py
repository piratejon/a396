#!/usr/bin/python3

import unittest
import ast

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

    def test_find_modified_symbols(self):
        f = """
a += b
c = 99
a = b * c
"""
        mathparse = ctxmathparse.MathParse()
        mathparse.context_parse_string(f)
        self.assertEqual(mathparse.context.name, '_')
        self.assertEqual(mathparse.context.modified_symbols, set({'a', 'c'}))
        self.assertEqual(mathparse.context.symbols, set({'a', 'b', 'c'}))

        f = """
a = 99
if b > 75:
    c += 99
elif b > 60:
    c += 50
elif b < d:
    pass
else:
    c += 25
a += c
"""
        mathparse = ctxmathparse.MathParse()
        mathparse.context_parse_string(f)
        self.assertEqual(mathparse.context.modified_symbols, set({'a', 'c'}))
        self.assertEqual(mathparse.context.symbols, set({'a', 'b', 'c', 'd'}))

    def test_find_returns(self):
        f = """
return x + 5
"""
        return
        mathparse = ctxmathparse.MathParse()
        mathparse.context_parse_string(f)
        returns = mathparse.context_returns()
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns, {
                "_f1:return:0": "([_f1:x] + 5)"
            }
        )

    def test_find_symbols_in_normal_ast(self):
        f = "return x + 5"
        mathparse = ctxmathparse.ASTMathParse()
        mathparse.parse_string(f)
        self.assertEqual(mathparse.symbols, set('x'))

        f = "def lalala(x, y, z): return x + y"
        mathparse = ctxmathparse.ASTMathParse()
        mathparse.parse_string(f)
        self.assertEqual(mathparse.symbols, set({'lalala', 'x', 'y', 'z'}))

    def test_find_modified_symbols(self):
        f = "return x + 5"
        mathparse = ctxmathparse.ASTMathParse()
        mathparse.parse_string(f)
        self.assertEqual(mathparse.symbols, set('x'))
        self.assertEqual(mathparse.target_symbols, set())

        f = "x = 5\na = x"
        mathparse = ctxmathparse.ASTMathParse()
        mathparse.parse_string(f)
        self.assertEqual(mathparse.symbols, set({'a', 'x'}))
        self.assertEqual(mathparse.target_symbols, set({'a', 'x'}))

        f = "x = 5 + b\nc = b * x"
        mathparse = ctxmathparse.ASTMathParse()
        mathparse.parse_string(f)
        self.assertEqual(mathparse.symbols, set({'x', 'b', 'c'}))
        self.assertEqual(mathparse.target_symbols, set({'x', 'c'}))

    def test_imbue_symbols_with_context(self):
        f = "x, y, z"
        mathparse = ctxmathparse.ASTMathParse()
        mathparse.parse_string(f)
        self.assertEqual(mathparse.symbols, set({'x', 'y', 'z'}))
        self.assertEqual(mathparse.export_symbols(), set({'_x', '_y', '_z'}))

    def test_bind_symbols_in_context(self):
        ctx0 = ctxmathparse.ASTMathParse('ctx0')
        ctx0.symbols.add('a')
        ctx1 = ctx0.create_child_context('ctx1')
        ctx1.symbols.add('b')
        self.assertEqual(ctx0.qualified_context_name, 'ctx0')
        self.assertEqual(ctx1.qualified_context_name, 'ctx0:ctx1')
        self.assertEqual(ctx0.resolve_symbol('a'), '_ctx0:a')
        self.assertEqual(ctx1.resolve_symbol('a'), '_ctx0:a')
        self.assertEqual(ctx1.resolve_symbol('b'), '_ctx0:ctx1:b')
        with self.assertRaises(KeyError):
            ctx0.resolve_symbol('b')

    def test_separate_out_statements(self):
        mathparse = ctxmathparse.ASTMathParse()
        mathparse.parse_string("x + 5")
        self.assertEqual(len(mathparse.statements), 1)
        mathparse.parse_string("x + 5\ny + 150 * 99\ninvoke_a_thingy(99 * y, x/y)")
        self.assertEqual(len(mathparse.statements), 3)

    def test_define_statement_symbols(self):
        mathparse = ctxmathparse.ASTMathParse('s')
        mathparse.parse_string('x + 5')
        self.assertEqual(mathparse.symbol_table, {
                'x': '_s:x'
            }
        )

    def test_translate_one_statement(self):
        mathparse = ctxmathparse.ASTMathParse('s')
        mathparse.parse_string("x + 5")
        self.assertEqual(mathparse.symbols, set({'x'}))
        self.assertEqual(mathparse.translate_statements(), {
                "_s:stmt0": "([_s:x] + 5)",
            }
        )

    def test_translate_two_statements(self):
        mathparse = ctxmathparse.ASTMathParse('t')
        mathparse.parse_string('x + 5\ny * 9')
        self.assertEqual(mathparse.translate_statements(), {
                '_t:stmt0': '([_t:x] + 5)',
                '_t:stmt1': '([_t:y] * 9)'
            }
        )

    def test_translate_assignment_statement(self):
        mathparse = ctxmathparse.ASTMathParse('t')
        mathparse.parse_string('x = 99 * b')
        self.assertEqual(mathparse.translate_statements(), {
                '_t:stmt0': '(99 * [_t:b])',
                '_t:x': '[_t:stmt0]'
            }
        )

    def test_translate_another_assignment_statement(self):
        mathparse = ctxmathparse.ASTMathParse('t')
        mathparse.parse_string('x = 99 * b\ny = x * 38 + 15')
        self.assertEqual(mathparse.translate_statements(), {
                '_t:stmt0': '(99 * [_t:b])',
                '_t:x': '[_t:stmt0]',
                '_t:stmt1': '(([_t:x] * 38) + 15)',
                '_t:y': '[_t:stmt1]'
            }
        )

    def test_sort_free_and_bound(self):
        mathparse = ctxmathparse.ASTMathParse('t')
        mytree = ast.parse('x = 99 * b')
        self.assertEqual(mathparse.find_free_variables(mytree), {'b'})
        self.assertEqual(mathparse.find_lhs_name(mytree), 'x')

if __name__ == '__main__':
    unittest.main()

