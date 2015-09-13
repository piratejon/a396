#!/usr/bin/python3

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

def expr(stmt, args, func_table):
    if isinstance(stmt, ast.Num):
        return stmt.n
    elif isinstance(stmt, ast.Name):
        if stmt.id in args:
            return "[{}]".format(args[stmt.id])
        else:
            return stmt.id
    elif isinstance(stmt, ast.BinOp):
        if isinstance(stmt.op, ast.Pow):
            return "pow({}, {})".format(expr(stmt.left, args, func_table), expr(stmt.right, args, func_table))
        else:
            return "({} {} {})".format(expr(stmt.left, args, func_table), expr(stmt.op, args, func_table), expr(stmt.right, args, func_table))
    elif isinstance(stmt, ast.UnaryOp):
        return "({} {})".format(expr(stmt.op, args, func_table), expr(stmt.operand, args, func_table))
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
        if stmt.func.id in func_table:
            print("need to clone:", stmt.func.id)
            return '[_{}_for_{}]'.format(stmt.func.id, 'f2')
        else:
            return "{}({})".format(expr(stmt.func, args, func_table), ','.join(map(lambda x: expr(x, args, func_table), stmt.args)))
    else:
        print("UNRECOGNIZED:", stmt, stmt._fields)
        return "unrecognized statement type"

def build_func_table(body):
    return { body[i].name: body[i] for i in range(len(body)) }

def mathparse(tree):
    funcs = {}
    func_table = build_func_table(tree.body)
    for i in range(len(tree.body)):
        func = tree.body[i]
        name = '_{}'.format(func.name)
        formulae = make_arg_formulae(name, fetch_args(func.args.args))
        last_statement = func.body[-1]
        funcs.update({name: expr(last_statement.value, formulae, func_table)})
        # let the expression names be the keys
        funcs.update({formulae[k]: k for k in formulae})
    return funcs

def mathparse_string(mathstr):
    return(mathparse(ast.parse(mathstr)))

def mathparse_file(fname):
    with open(fname, 'r') as fin:
        return mathparse_string(fin.read())

if __name__ == '__main__':
    print(mathparse_file(sys.argv[1]))

