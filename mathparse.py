#!/usr/bin/python3

"""Implementation of mathparse class"""

import copy # deepcopy function ast for clone
import sys
import ast

def fetch_args(args):
    """Return an ordered list of function arguments from an ast.Arg list."""
    return [arg.arg for arg in args if arg.arg != 'self']

def make_arg_local_name(funcname, symbol, tag = ''):
    """Return the name of the variable assigned to a function's argument or local."""
    return '{}_{}_{}'.format(funcname, tag, symbol)

def build_arg_lookup(funcname, symbols):
    """Build the lookup table for translated symbol names given a list of symbols."""
    return {symbol: make_arg_local_name(funcname, symbol, 'arg') for symbol in symbols}

def get_last_statement(func):
    """temporary last-statement-retriever; replaced when we start collecting all statements"""
    return func.body[-1]

def build_func_table(body):
    """Build lookup for top-level functions defined in this statement list."""
    return {body[i].name: body[i] for i in range(len(body))}

def clone_function_in_statement(stmt, func):
    """Create a deep copy of an ast.Function for duplicating where required by a distinct invocation."""
    func = copy.deepcopy(func)
    func.name = '{}_l{}_c{}'.format(func.name, stmt.lineno, stmt.col_offset)
    return func

def make_function_name(func):
    return '_{}'.format(func.name)

def make_statement_name(func, stmt):
    return '_{}_l{}_c{}'.format(func.name, stmt.lineno, stmt.col_offset)

class MathParse:
    """MathParse turns Python functions into Tableau calculations.

    For example:
    # Abramowitz and Stegun 7.1.28
    def erf_appx(z):
        a = [1, 0.0705230784, 0.0422820123, 0.0092705272, 0.0001520143, 0.0002765672, 0.0000430638]
        return sign(z)*(1 - (1/pow(sum([pow(abs(z), i)*a[i] for i in range(len(a))]),16)))

    yields:
        _erf_appx_arg_z: z
        _erf_appx: ...

    Function arguments are represented by Tableau expressions too. The z
    argument to erf_appx is represented in the _erf_appx expression as
    _erf_appx_arg_z. Because Tableau calculations do not have arguments,
    each time a translated function is referenced with a different argument
    it must be cloned, when it is prefixed with the name of the referencing
    function:

        def h(a):
            return sin(a)^2 + cos(a)^2

        def m(a):
            return h(a) * h(1 - a)

    yields:
        _h_arg_a: a
        _h: ((POW(SIN([_h_arg_a]), 2)) + (POW(COS([_h_arg_a]), 2)))
        _m_arg_a: a
        _m_h_1_arg_a: [_m_arg_a]
        _m_h_2_arg_a: (1 - [_m_arg_a])
        _m_h_1: ((POW(SIN([_m_h_1_arg_a]), 2)) + (POW(COS([_m_h_1_arg_a]), 2)))
        _m_h_2: ((POW(SIN([_m_h_2_arg_a]), 2)) + (POW(COS([_m_h_2_arg_a]), 2)))
        _m: ([_m_h_1] * [_m_h_2])

    Chi Squared CDF in terms of Gamma CDF:
      a = df*0.5D0
      xx = x*0.5D0
      CALL cumgam(xx,a,cum,ccum)
    """

    def expr(self, stmt, local_syms, real_funcs):
        """Return a Tableau expression string representing the stmt tree.
        
        Arguments:
        stmt -- the root of the expression tree being translated
        local_syms -- src -> dst symbol map (e.g. x -> _f1_arg_x)
        real_funcs -- func -> func_ast map for cloning
        """
        if isinstance(stmt, ast.Num):
            return stmt.n

        elif isinstance(stmt, ast.Name):
            if stmt.id in local_syms:
                return "[{}]".format(local_syms[stmt.id])
            else:
                return stmt.id

        elif isinstance(stmt, ast.BinOp):
            if isinstance(stmt.op, ast.Pow):
                return "pow({}, {})".format(
                    self.expr(stmt.left, local_syms, real_funcs),
                    self.expr(stmt.right, local_syms, real_funcs)
                )
            else:
                return "({} {} {})".format(
                    self.expr(stmt.left, local_syms, real_funcs),
                    self.expr(stmt.op, local_syms, real_funcs),
                    self.expr(stmt.right, local_syms, real_funcs)
                )

        elif isinstance(stmt, ast.UnaryOp):
            return "({} {})".format(
                self.expr(stmt.op, local_syms, real_funcs),
                self.expr(stmt.operand, local_syms, real_funcs)
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
            if stmt.func.id in real_funcs:
                new_function = clone_function_in_statement(stmt, real_funcs[stmt.func.id])
                self.func_build_set.add(new_function)
                return '[_{}]'.format(new_function.name)
            else:
                return "{}({})".format(
                    self.expr(stmt.func, local_syms, real_funcs),
                    ','.join([self.expr(arg, local_syms, real_funcs) for arg in stmt.args]))
        else:
            return "UNRECOGNIZED {}".format(stmt)

    def translate_single_function(self, func, real_functions):
        """create the expression object entry and fill it with the expanded,
        translated expression body"""
        func_name = make_function_name(func)
        args = build_arg_lookup(func_name, fetch_args(func.args.args))

        new_formula = {}
        local_values = {}

        for stmt in func.body:
            stmt_value = self.expr(stmt.value, args, real_functions)
            if isinstance(stmt, ast.Assign):
                stmt_name = make_arg_local_name(
                    func_name,
                    stmt.targets[0].id,
                    'l{}_c{}'.format(
                        stmt.lineno, stmt.col_offset
                    )
                )
                args[stmt.targets[0].id] = stmt_name
                local_values[stmt_name] = stmt_value
                new_formula.update({stmt_name: stmt_value})
            else:
                new_formula.update({func_name: stmt_value})

        new_formula.update({args[k]: k for k in args})
        new_formula.update(local_values)
        return new_formula

    def mathparse(self, tree):
        """kick off the parsing of the AST"""
        formulae = {}
        real_functions = build_func_table(tree.body)
        self.func_build_set = {tree.body[i] for i in range(len(tree.body))}
        while self.func_build_set:
            formulae.update(
                self.translate_single_function(
                    self.func_build_set.pop(), real_functions
                )
            )
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

