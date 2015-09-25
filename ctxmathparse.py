#!/usr/bin/python3

import ast

def objectify_node(node):
    """Get the tree into a friendly manipulable format we can easily
      compare in unit tests and does not have line/col info not needed
      here"""
    if node == None:
        return None

    elif isinstance(node, int) or isinstance(node, str):
        return node

    elif isinstance(node, list):
        return [
            objectify_node(node[i]) for i in range(len(node))
        ]

    else: # i hope this is an object!
        return {
            node.__class__.__name__: {
                fieldname: objectify_node(getattr(node, fieldname))
                    for fieldname in node._fields
            }
        }

def abstractify_tree(tree):
    return objectify_node(tree)

def abstractify_string(mathstr):
    return abstractify_tree(ast.parse(mathstr))

def functions_from_ast(objast):
    return [
        o['FunctionDef'] for o in objast['Module']['body'] if 'FunctionDef' in o
    ]

class MathParse:
    def __init__(self):
        self.functions = []
        self.source = {}
        self.ast = None

    def push_it_down(self, orig_tree):
        tree = copy.deepcopy(orig_tree)
        symbol = tree['Module']['body'][0]['FunctionDef']['body'][0]['Assign']['targets'][0]['Name']['id']
        value = tree['Module']['body'][0]['FunctionDef']['body'][0]['Assign']['value']
        tree['Module']['body'][0]['FunctionDef']['body'][1]['Return']['value']['Call']['args'][0] = value
        del tree['Module']['body'][0]['FunctionDef']['body'][0]
        return tree
 
    def parse_string(self, mathstr):
        self.source = mathstr
        self.ast = abstractify_string(mathstr)
        self.functions = functions_from_ast(self.ast)

