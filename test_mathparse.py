
import unittest

import mathparse

class TestMathParse(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestMathParse, self).__init__(*args, **kwargs)
        self.maxDiff = None

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
                "_ex_identity": "[_ex_identity#z]",
                "_ex_identity#z": "z"
            }
        )

    def test_ex_simple_func(self):
        f = "def ex_add(z): return z + 1"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_ex_add": "([_ex_add#z] + 1)",
                "_ex_add#z": "z"
            }
        )

        f = "def ex_add(z): return 1 + z"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_ex_add": "(1 + [_ex_add#z])",
                "_ex_add#z": "z"
            }
        )

        f = "def ex_add_mult(z): return 3 * z + 1"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_ex_add_mult": "((3 * [_ex_add_mult#z]) + 1)",
                "_ex_add_mult#z": "z"
            }
        )

    def test_ex_multiple_params(self):
        f = "def ex_add(a, b): return a + b"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_ex_add": "([_ex_add#a] + [_ex_add#b])",
                "_ex_add#a": "a",
                "_ex_add#b": "b",
            }
        )

    def test_ex_expressions(self):
        f = "def func(z): return sqrt(z)"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_func": "sqrt([_func#z])",
                "_func#z": "z",
            }
        )

        f = "def func(zed, wisk): return wisk - sqrt(zed / 10) * 99"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_func": "([_func#wisk] - (sqrt(([_func#zed] / 10)) * 99))",
                "_func#zed": "zed",
                "_func#wisk": "wisk",
            }
        )

        f = "def func(zed, wisk): return (wisk - sqrt(zed / 10)) * 99"
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_func": "(([_func#wisk] - sqrt(([_func#zed] / 10))) * 99)",
                "_func#zed": "zed",
                "_func#wisk": "wisk",
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
                "_f1": "(sin(([_f1#z] * 9)) / 33)",
                "_f1#z": "z",
                "_f2": "(cos(((- [_f2#y]) * 9)) / 33)",
                "_f2#y": "y",
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
                "_f2": "([_f2#z] + [_f1:f2])",
                "_f2#z": "z",
                "_f1:f2": 33
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
                "_f1": "(33 + [_f1#z])",
                "_f1#z": "z",
                "_f2": "([_f2#z] + [_f1:f2])",
                "_f2#z": "z",
                "_f1:f2": "(33 + [_f1:f2#z])",
                "_f1:f2#z": "z"
            }
        )

    def test_objectifies_an_ast(self):
        f = """
def f1(z):
    x = 19*z
    return sqrt(x)
"""
        mp = mathparse.MathParse()
        self.assertEqual(
            mp.abstractify_string(f), {
                "Module": {
                    "body": [
                        {
                            "FunctionDef": {
                                "name": "f1",
                                "args": {
                                    "arguments": {
                                        "defaults": [],
                                        "args": [
                                            {
                                                "arg": {
                                                    "annotation": None,
                                                    "arg": "z"
                                                }
                                            }
                                        ], "kwarg": None,
                                        "vararg": None,
                                        "kw_defaults": [],
                                        "kwonlyargs": []
                                    }
                                }, "body": [
                                    {
                                        "Assign": {
                                            "targets": [
                                                {
                                                    "Name": {
                                                        "ctx": {
                                                            "Store": {}
                                                        }, "id": 'x'
                                                    }
                                                }
                                            ], "value": {
                                                "BinOp": {
                                                    "left": {
                                                        "Num": {
                                                            "n": 19
                                                        }
                                                    },
                                                    "op": {
                                                        "Mult": {}
                                                    },
                                                    "right": {
                                                        "Name": {
                                                            "ctx": {
                                                                "Load": {}
                                                            }, "id": "z"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "Return": {
                                            "value": {
                                                "Call": {
                                                    "args": [
                                                        {
                                                            "Name": {
                                                                "ctx": {
                                                                    "Load": {},
                                                                }, "id": "x"
                                                            }
                                                        }
                                                    ], "starargs": None,
                                                    "keywords": [],
                                                    "func": {
                                                        "Name": {
                                                            "ctx": {
                                                                "Load": {}
                                                            }, "id": "sqrt"
                                                        }
                                                    },
                                                    "kwargs": None
                                                }
                                            }
                                        }
                                    }
                                ], "decorator_list": [],
                                "returns": None
                            }
                        }
                    ]
                }
            }
        )

    def test_pushes_a_statement_down(self):
        """
          This test illustrates the transformation from

              def f1(z):
                  x = 19*z
                  return sqrt(x)

          to

              def f1(z):
                  return sqrt(19*z)
          """

        f = """
def f1(z):
    x = 19*z
    return sqrt(x)
"""
        mp = mathparse.MathParse()
        self.assertEqual(
          mp.push_it_down(
            mp.abstractify_string(f)
          ), {
                "Module": {
                    "body": [
                        {
                            "FunctionDef": {
                                "name": "f1",
                                "args": {
                                    "arguments": {
                                        "defaults": [],
                                        "args": [
                                            {
                                                "arg": {
                                                    "annotation": None,
                                                    "arg": "z"
                                                }
                                            }
                                        ], "kwarg": None,
                                        "vararg": None,
                                        "kw_defaults": [],
                                        "kwonlyargs": []
                                    }
                                }, "body": [
                                    {
                                        "Return": {
                                            "value": {
                                                "Call": {
                                                    "args": [
                                                        {
                                                            "BinOp": {
                                                                "left": {
                                                                    "Num": {
                                                                        "n": 19
                                                                    }
                                                                },
                                                                "op": {
                                                                    "Mult": {}
                                                                },
                                                                "right": {
                                                                    "Name": {
                                                                        "ctx": {
                                                                            "Load": {}
                                                                        }, "id": "z"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    ], "starargs": None,
                                                    "keywords": [],
                                                    "func": {
                                                        "Name": {
                                                            "ctx": {
                                                                "Load": {}
                                                            }, "id": "sqrt"
                                                        }
                                                    },
                                                    "kwargs": None
                                                }
                                            }
                                        }
                                    }
                                ], "decorator_list": [],
                                "returns": None
                            }
                        }
                    ]
                }
            }
        )

    def test_translates_objectified_ast(self):
        f = """
def f1(z):
    x = 19*z
    return sqrt(x)
"""
        mp = mathparse.MathParse()
        self.assertEqual(
            mp.translate_objast(
                mp.push_it_down(
                    mp.abstractify_string(f)
                )
            ),
            {
                "_f1#z": "z",
                "_f1": "sqrt((19 * [_f1#z]))"
            }
        )

    def test_pushes_a_statement_down(self):
        f = """
def f1(z):
    x = 19*z
    return sqrt(x)
"""
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_f1#z": "z",
                "_f1.x": "(19 * [_f1#z])",
                "_f1": "sqrt([_f1.x])"
            }
        )

    def test_overwrites_parameters(self):
        f = """
def f1(z):
    z = 19*z
    return sqrt(z)
"""
        mp = mathparse.MathParse()
        self.assertEqual(mp.mathparse_string(f), {
                "_f1#z": "z",
                "_f1_l3_c4_z": "(19 * [_f1#z])",
                "_f1": "sqrt([_f1_l3_c4_z])"
            }
        )

if __name__ == '__main__':
    unittest.main()

