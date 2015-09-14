#!/usr/bin/python3

"""Implementation of mathparse class"""

import copy # deepcopy function ast for clone
import sys
import ast

def fetch_args(args):
    """returns an ordered list of arguments excluding self from an ast.Arg list"""
    kept_args = []
    for i in range(len(args)):
        arg = args[i]
        if arg.arg != "self":
            kept_args.append(arg.arg)
    return kept_args

def make_arg_formulae(name, args):
    """look up variable terms to get the expression name"""
    return {arg: "{}_arg_{}".format(name, arg) for arg in args}

def get_last_statement(func):
    """temporary last-statement-retriever; replaced when we start collecting all statements"""
    return func.body[-1]

def build_func_table(body):
    """build lookup of top-level functions defined in this statement list"""
    return {body[i].name: body[i] for i in range(len(body))}


class MathParse:
    """MathParse turns Python code into Tableau expressions"""

    def __init__(self):
        pass

    def clone_function_as(self, func, new_name, real_funcs):
        """creates a deep copy of an ast.Function for duplicating where required by a new use"""
        func = copy.deepcopy(func)
        func.name = '{}_for_{}'.format(func.name, new_name)
        return {
            'name': func.name,
            'funcs': self.translate_single_function(func, real_funcs)
        }

    def expr(self, name, args, stmt, real_funcs):
        """recursively translates the elements of the passed AST"""
        if isinstance(stmt, ast.Num):
            return stmt.n

        elif isinstance(stmt, ast.Name):
            if stmt.id in args:
                return "[{}]".format(args[stmt.id])
            else:
                return stmt.id

        elif isinstance(stmt, ast.BinOp):
            if isinstance(stmt.op, ast.Pow):
                return "pow({}, {})".format(
                    self.expr(name, args, stmt.left, real_funcs),
                    self.expr(name, args, stmt.right, real_funcs)
                )
            else:
                return "({} {} {})".format(
                    self.expr(name, args, stmt.left, real_funcs),
                    self.expr(name, args, stmt.op, real_funcs),
                    self.expr(name, args, stmt.right, real_funcs)
                )

        elif isinstance(stmt, ast.UnaryOp):
            return "({} {})".format(
                self.expr(name, args, stmt.op, real_funcs),
                self.expr(name, args, stmt.operand, real_funcs)
            )

        elif isinstance(stmt, ast.Add):
            return '+'

        elif isinstance(stmt, ast.Mult):
            return '*'

        elif isinstance(stmt, ast.Sub):
            return '-'

        elif isinstance(stmt, ast.Div):
            return '/'

        elif isinstance(stmt, ast.USub):
            return '-'

        elif isinstance(stmt, ast.Call):
            return "{}({})".format(
                self.expr(name, args, stmt.func, real_funcs),
                ','.join([self.expr(name, args, arg, real_funcs) for arg in stmt.args]))
#map(lambda x: self.expr(name, args, x, real_funcs), stmt.args)))

        else:
            return "UNRECOGNIZED {} {}".format(stmt, ''.join(stmt._fields))

    def translate_single_function(self, func, real_functions):
        """create the expression object entry and fill it with the expanded,
        translated expression body"""
        name = '_{}'.format(func.name)
        args = make_arg_formulae(name, fetch_args(func.args.args))
        last_statement = get_last_statement(func)
        new_formula = {name: self.expr(func.name, args, last_statement.value, real_functions)}
        # include argument formulae in the output
        new_formula.update({args[k]: k for k in args})
        return new_formula

    def mathparse(self, tree):
        """kick off the parsing of the AST"""
        formulae = {}
        real_functions = build_func_table(tree.body)
        for i in range(len(tree.body)):
            new_formula = self.translate_single_function(tree.body[i], real_functions)
            formulae.update(new_formula)
        return formulae

    def mathparse_string(self, mathstr):
        """wrapper to parse Python code in a string"""
        return self.mathparse(ast.parse(mathstr))

    def mathparse_file(self, fname):
        """wrapper to parse Python code in a file"""
        with open(fname, 'r') as fin:
            return self.mathparse_string(fin.read())

def main(arg):
    """when run from the command line, parse the file"""
    mathparse = MathParse()
    print(mathparse.mathparse_file(arg))

if __name__ == '__main__':
    main(sys.argv[1])

