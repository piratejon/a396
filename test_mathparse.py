
import unittest

import mathparse

class TestMathParse(unittest.TestCase):

    def test_ex_const(self):
        f = "def ex_const(): return 33"
        self.assertEqual(mathparse.mathparse_string(f), {
                "_ex_const": 33
            }
        )

    def test_ex_identity(self):
        f = "def ex_identity(z): return z"
        self.assertEqual(mathparse.mathparse_string(f), {
                "_ex_identity": "[_ex_identity_arg_z]",
                "_ex_identity_arg_z": "z"
            }
        )

    def test_ex_simple_func(self):
        f = "def ex_add(z): return z + 1"
        self.assertEqual(mathparse.mathparse_string(f), {
                "_ex_add": "([_ex_add_arg_z] + 1)",
                "_ex_add_arg_z": "z"
            }
        )

        f = "def ex_add(z): return 1 + z"
        self.assertEqual(mathparse.mathparse_string(f), {
                "_ex_add": "(1 + [_ex_add_arg_z])",
                "_ex_add_arg_z": "z"
            }
        )

        f = "def ex_add_mult(z): return 3 * z + 1"
        self.assertEqual(mathparse.mathparse_string(f), {
                "_ex_add_mult": "((3 * [_ex_add_mult_arg_z]) + 1)",
                "_ex_add_mult_arg_z": "z"
            }
        )

    def test_ex_multiple_params(self):
        f = "def ex_add(a, b): return a + b"
        self.assertEqual(mathparse.mathparse_string(f), {
                "_ex_add": "([_ex_add_arg_a] + [_ex_add_arg_b])",
                "_ex_add_arg_a": "a",
                "_ex_add_arg_b": "b",
            }
        )

if __name__ == '__main__':
    unittest.main()

