
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

if __name__ == '__main__':
    unittest.main()

