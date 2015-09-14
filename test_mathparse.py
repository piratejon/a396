
import unittest

import mathparse

class TestMathParse(unittest.TestCase):

    def test_ex_const(self):
        f = "def ex_const(): return 33"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_ex_const": 33
            }
        )

    def test_ex_identity(self):
        f = "def ex_identity(z): return z"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_ex_identity": "[_ex_identity_arg_z]",
                "_ex_identity_arg_z": "z"
            }
        )

    def test_ex_simple_func(self):
        f = "def ex_add(z): return z + 1"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_ex_add": "([_ex_add_arg_z] + 1)",
                "_ex_add_arg_z": "z"
            }
        )

        f = "def ex_add(z): return 1 + z"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_ex_add": "(1 + [_ex_add_arg_z])",
                "_ex_add_arg_z": "z"
            }
        )

        f = "def ex_add_mult(z): return 3 * z + 1"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_ex_add_mult": "((3 * [_ex_add_mult_arg_z]) + 1)",
                "_ex_add_mult_arg_z": "z"
            }
        )

    def test_ex_multiple_params(self):
        f = "def ex_add(a, b): return a + b"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_ex_add": "([_ex_add_arg_a] + [_ex_add_arg_b])",
                "_ex_add_arg_a": "a",
                "_ex_add_arg_b": "b",
            }
        )

    def test_ex_expressions(self):
        f = "def func(z): return sqrt(z)"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_func": "sqrt([_func_arg_z])",
                "_func_arg_z": "z",
            }
        )

        f = "def func(zed, wisk): return wisk - sqrt(zed / 10) * 99"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_func": "([_func_arg_wisk] - (sqrt(([_func_arg_zed] / 10)) * 99))",
                "_func_arg_zed": "zed",
                "_func_arg_wisk": "wisk",
            }
        )

        f = "def func(zed, wisk): return (wisk - sqrt(zed / 10)) * 99"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_func": "(([_func_arg_wisk] - sqrt(([_func_arg_zed] / 10))) * 99)",
                "_func_arg_zed": "zed",
                "_func_arg_wisk": "wisk",
            }
        )

    def test_translates_two_functions(self):
        f = """
def f1(z):
    return sin(z*9)/33

def f2(y):
    return cos(-y*9)/33
"""
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_f1": "(sin(([_f1_arg_z] * 9)) / 33)",
                "_f1_arg_z": "z",
                "_f2": "(cos(((- [_f2_arg_y]) * 9)) / 33)",
                "_f2_arg_y": "y",
            }
        )

    def test_reuses_a_function(self):
        f = """
def f1():
    return 33

def f2(z):
    return z + f1()
"""
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_f1": 33,
                "_f2": "([_f2_arg_z] + [_f1_for_f2])",
                "_f2_arg_z": "z",
                "_f1_for_f2": 33
            }
        )

        f = """
def f1(z):
    return 33 + z

def f2(z):
    return z + f1()
"""
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_f1": "(33 + [_f1_arg_z])",
                "_f1_arg_z": "z",
                "_f2": "([_f2_arg_z] + [_f1_for_f2])",
                "_f2_arg_z": "z",
                "_f1_for_f2": "(33 + [_f1_for_f2_arg_z])",
                "_f1_for_f2_arg_z": "z"
            }
        )

if __name__ == '__main__':
    unittest.main()

