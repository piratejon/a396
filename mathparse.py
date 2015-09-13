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

def expr(stmt, args):
    if isinstance(stmt, ast.Num):
        return stmt.n
    elif isinstance(stmt, ast.Name):
        if stmt.id in args:
            return "[{}]".format(args[stmt.id])
        else:
            return stmt.id
    elif isinstance(stmt, ast.BinOp):
        return "({} {} {})".format(expr(stmt.left, args), expr(stmt.op, args), expr(stmt.right, args))
    elif isinstance(stmt, ast.Add):
        return '+'
    elif isinstance(stmt, ast.Mult):
        return '*'
    elif isinstance(stmt, ast.Call):
        return "{}({})".format(expr(stmt.func, args), ','.join(map(lambda x: expr(x, args), stmt.args)))
    else:
        print(stmt, stmt._fields)
        return "unrecognized statement type"

def mathparse(tree):
# ex_const:
# <_ast.FunctionDef object at 0x7f26b93a3160>
#   <_ast.arguments object at 0x7f26b93a3198>
#     <_ast.arg object at 0x7f26b93a31d0>
#   <_ast.Return object at 0x7f26b93a3278>
#     <_ast.Num object at 0x7f26b93a32b0>

# ex_identity:
# <_ast.FunctionDef object at 0x7fd768a26358>
#   <_ast.arguments object at 0x7fd768a26390>
#     <_ast.arg object at 0x7fd768a263c8>
#     <_ast.arg object at 0x7fd768a26400>
#   <_ast.Return object at 0x7fd768a26438>
#     <_ast.Name object at 0x7fd768a26470>
#       <_ast.Load object at 0x7fd768a19d68>

    func = tree.body[0]
    name = '_{}'.format(func.name)
    formulae = make_arg_formulae(name, fetch_args(func.args.args))
    last_statement = func.body[-1]
    result = {name: expr(last_statement.value, formulae)}

# let the expression names be the keys
    result.update({formulae[k]: k for k in formulae})
    return result

def mathparse_string(mathstr):
    return(mathparse(ast.parse(mathstr)))

def mathparse_file(fname):
    with open(fname, 'r') as fin:
        return mathparse_string(fin.read())

if __name__ == '__main__':
    print(mathparse_file(sys.argv[1]))

