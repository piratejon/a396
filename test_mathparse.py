
import unittest

import mathparse

class TestMathParse(unittest.TestCase):

    def test_ex_const(self):
        const_func = "def ex_const(): return 33"
        self.assertEqual(mathparse.mathparse_string(const_func), {"_ex_const": 33})

    def test_ex_identity(self):
        idfunc = "def ex_identity(z): return z"
        self.assertEqual(mathparse.mathparse_string(idfunc), {"_ex_identity": "[_ex_identity_arg_z]", "_ex_identity_arg_z": "z"})

if __name__ == '__main__':
    unittest.main()

