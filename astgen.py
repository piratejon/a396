#!/usr/bin/python3

import sys
import ast

class visitor_printtree(ast.NodeVisitor):
    def __init__(self):
        self.indent = 0

    def visit(self, node):
        print(" "*self.indent, node)
        self.indent += 2
        self.generic_visit(node)
        self.indent -= 2

class visitor_func(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        name = node.name
        print("generating", name)
        self.generic_visit(node)

def mathparse(fname):
    with open(fname, 'r') as fin:
        tree = ast.parse(fin.read())
        visitor_printtree().visit(tree)

if __name__ == '__main__':
    mathparse(sys.argv[1])

