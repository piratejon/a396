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

    def __init__(self):
        """Initialize this instance's translated formulae"""
        self.formulae = {}

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
        arg_names = build_arg_lookup(func_name, fetch_args(func.args.args))
        new_formulae = {} # this is the output
        local_names = {} # maps 'x' onto '_f_lX_cY_x'
        local_values = {} # maps '_f_lX_cY_x' onto "translated string"

        for stmt in func.body:
            stmt_value = self.expr(stmt.value, arg_names, real_functions)
            new_formulae.update({func_name: stmt_value})

        new_formulae.update({arg_names[k]: k for k in arg_names})
        new_formulae.update(local_values)
        return new_formulae

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

    def objectify_node(self, node):
        """Get the tree into a friendly manipulable format we can easily
          compare in unit tests and does not have line/col info not needed
          here"""
        if node == None:
            return None
        elif isinstance(node, int) or isinstance(node, str):
            return node
        elif isinstance(node, list):
            return [
                self.objectify_node(node[i]) for i in range(len(node))
            ]
        else: # i hope this is an object!
            return {
                node.__class__.__name__: {
                    fieldname: self.objectify_node(getattr(node, fieldname))
                        for fieldname in node._fields
                }
            }

    def push_it_down(self, orig_tree):
        tree = copy.deepcopy(orig_tree)
        symbol = tree['Module']['body'][0]['FunctionDef']['body'][0]['Assign']['targets'][0]['Name']['id']
        value = tree['Module']['body'][0]['FunctionDef']['body'][0]['Assign']['value']
        tree['Module']['body'][0]['FunctionDef']['body'][1]['Return']['value']['Call']['args'][0] = value
        del tree['Module']['body'][0]['FunctionDef']['body'][0]
        return tree
 
    def abstractify_tree(self, tree):
        return self.objectify_node(tree)

    def abstractify_string(self, mathstr):
        return self.abstractify_tree(ast.parse(mathstr))

    def arg_to_formula_map(self, name, args):
        return {
            arg: '_{}#{}'.format(name, arg)
                for arg in [
                    arg['arg']['arg']
                    for arg in args['arguments']['args']
                ]
        }

    def binop_lookup(self, binop):
        if 'Mult' in binop: return '*'
        if 'Div' in binop: return '/'
        if 'Sub' in binop: return '-'
        if 'Add' in binop: return '+'
        return list(binop.keys())[0]

    def unaryop_lookup(self, unaryop):
        if 'USub' in unaryop: return '-'
        return list(unaryop.keys())[0]

    def objast_expr(self, name, objast, args, functions):
        if 'body' in objast:
            return self.objast_expr(name, objast['body'][0], args, functions)
        if 'Return' in objast:
            return self.objast_expr(name, objast['Return']['value'], args, functions)
        if 'Call' in objast:
            if objast['Call']['func']['Name']['id'] in functions:
                copy_func = copy.deepcopy(functions[objast['Call']['func']['Name']['id']])
                copy_func['name'] = '{}:{}'.format(copy_func['name'], name)
                self.translate_objast(
                    {
                        "Module": {
                            "body": [
                                {
                                    "FunctionDef": copy_func
                                }
                            ]
                        }
                    }
                )
                return '[_{}]'.format(copy_func['name'])
            else:
                return '{}({})'.format(
                    objast['Call']['func']['Name']['id'],
                    ', '.join(
                            [
                                self.objast_expr(name, arg, args, functions)
                                    for arg in objast['Call']['args']
                            ]
                    )
                )
        if 'BinOp' in objast:
            return '({} {} {})'.format(
                self.objast_expr(name, objast['BinOp']['left'], args, functions),
                self.binop_lookup(objast['BinOp']['op']),
                self.objast_expr(name, objast['BinOp']['right'], args, functions)
            )

        if 'UnaryOp' in objast:
            return '({} {})'.format(
                self.unaryop_lookup(objast['UnaryOp']['op']),
                self.objast_expr(name, objast['UnaryOp']['operand'], args, functions)
            )

        if 'Num' in objast:
            return objast['Num']['n']

        if 'Name' in objast:
            if objast['Name']['id'] in args:
                return '[{}]'.format(args[objast['Name']['id']])
            else:
                return objast['Name']['id']

        return 'ERRR ' + ','.join(objast.keys())

    def dict_update_pipe(self, a, b):
        """Update and return a dictionary."""
        a.update(b)
        return a

    def translate_objast(self, objast):
        """Run through objast determining new formulae, updating self.formulae"""
        result_trees = {} # f1 -> abstractified FunctionDef
        for body_elt in objast['Module']['body']:
            func = body_elt['FunctionDef']
            name = func['name']
            formula_name = '_{}'.format(name)
            args = self.arg_to_formula_map(name, func['args'])
            # do bodies first and names second to prevent recursion for now
            self.formulae.update(
                {
                    formula_name: self.objast_expr(name, func, args, result_trees),
                }
            )

            self.formulae.update(
                {
                    args[arg]: arg for arg in args
                }
            )
            result_trees.update({name: func})
        return self.formulae

    def mathparse_string(self, mathstr):
        """wrapper to parse Python code in a string"""
        return self.translate_objast(self.abstractify_string(mathstr))
#return self.mathparse(ast.parse(mathstr))

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

