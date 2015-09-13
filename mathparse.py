#!/usr/bin/python3

import copy # deepcopy function ast for clone
import sys
import ast

def fetch_args(args):
    kept_args = []
    for i in range(len(args)):
        arg = args[i]
        if arg.arg != "self":
            kept_args.append(arg.arg)
    return kept_args

# this lets us look up variable terms to get the expression name
def make_arg_formulae(name, args):
    return { arg: "{}_arg_{}".format(name, arg) for arg in args }

def get_last_statement(func):
    return func.body[-1]

def clone_function_as(func, formulae, func_name, func_table):
    func = copy.deepcopy(func)
    func.name = '{}_for_{}'.format(func.name, func_name)
    return {
      'name': func.name,
      'funcs': translate_single_function(func, func_table)
    }

def expr(stmt, args, func_name, in_func_table, helper_funcs):
    if isinstance(stmt, ast.Num):
        return stmt.n
    elif isinstance(stmt, ast.Name):
        if stmt.id in args:
            return "[{}]".format(args[stmt.id])
        else:
            return stmt.id
    elif isinstance(stmt, ast.BinOp):
        if isinstance(stmt.op, ast.Pow):
            return "pow({}, {})".format(expr(stmt.left, args, func_name, in_func_table, helper_funcs), expr(stmt.right, args, func_name, in_func_table, helper_funcs))
        else:
            return "({} {} {})".format(expr(stmt.left, args, func_name, in_func_table, helper_funcs), expr(stmt.op, args, func_name, in_func_table, helper_funcs), expr(stmt.right, args, func_name, in_func_table, helper_funcs))
    elif isinstance(stmt, ast.UnaryOp):
        return "({} {})".format(expr(stmt.op, args, func_name, in_func_table, helper_funcs), expr(stmt.operand, args, func_name, in_func_table, helper_funcs))
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
        if stmt.func.id in in_func_table:
            cloned_func = clone_function_as(in_func_table[stmt.func.id], args, func_name, in_func_table)
            helper_funcs.update(cloned_func['funcs'])
            print(helper_funcs)
            return '[_{}]'.format(cloned_func['name'])
        else:
            return "{}({})".format(expr(stmt.func, args, func_name, in_func_table, helper_funcs), ','.join(map(lambda x: expr(x, args, func_name, in_func_table, helper_funcs), stmt.args)))
    else:
        return "UNRECOGNIZED {} {}".format(stmt, ''.join(stmt._fields))

def build_func_table(body):
    return { body[i].name: body[i] for i in range(len(body)) }

def translate_single_function(func, in_func_table):
    funcs = {}
    helper_funcs = {}
    name = '_{}'.format(func.name)
    formulae = make_arg_formulae(name, fetch_args(func.args.args))
    last_statement = func.body[-1]
    funcs.update({name: expr(last_statement.value, formulae, func.name, in_func_table, helper_funcs)})
    # let the expression names be the keys
    funcs.update({formulae[k]: k for k in formulae})
    print(funcs)
    print(helper_funcs)
    funcs.update(helper_funcs)
    return funcs

def mathparse(tree):
    funcs = {}
    in_func_table = build_func_table(tree.body)
    for i in range(len(tree.body)):
        funcs.update(translate_single_function(tree.body[i], in_func_table))
    return funcs

def mathparse_string(mathstr):
    return(mathparse(ast.parse(mathstr)))

def mathparse_file(fname):
    with open(fname, 'r') as fin:
        return mathparse_string(fin.read())

if __name__ == '__main__':
    print(mathparse_file(sys.argv[1]))

