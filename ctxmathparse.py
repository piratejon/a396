#!/usr/bin/python3

"""Implement the MathParse Python-to-Tableau translator and helper methods."""

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
                fieldname:
                    objectify_node(getattr(node, fieldname))
                for fieldname in node._fields
            }
        }

def objectify_ast(astree):
    """Create a simple Python object representing the AST."""
    return objectify_node(astree)

def objectify_string(mathstr):
    """Return the Python object corresponding to the parsed string's AST."""
    return objectify_ast(ast.parse(mathstr))

def functions_from_ast(objast):
    """
        Return an ordered list of the top-level (immediate body-descended)
        functions in the objast.
    """
    return [
        o['FunctionDef'] for o in objast['Module']['body'] if 'FunctionDef' in o
    ]

def get_function_args(func):
    """Return a map of arg name -> Tableau function name."""
    return {
        arg['arg']['arg']: '_{}_arg_{}'.format(func['name'], arg['arg']['arg'])
        for arg in func['args']['arguments']['args']
    }

class MathParse:
    """
        Encapsulate the state required to translate a sequence of functions in
        a single context.
    """

    def __init__(self):
        """Set default empty values for instance variables."""
        self.function_list = []
        self.source = ""
        self.objast = None

#    def push_it_down(self, orig_tree):
#        tree = copy.deepcopy(orig_tree)
#        symbol = tree['Module']['body'][0]['FunctionDef']['body'][0]['Assign']['targets'][0]['Name']['id']
#        value = tree['Module']['body'][0]['FunctionDef']['body'][0]['Assign']['value']
#        tree['Module']['body'][0]['FunctionDef']['body'][1]['Return']['value']['Call']['args'][0] = value
#        del tree['Module']['body'][0]['FunctionDef']['body'][0]
#        return tree

    def parse_string(self, mathstr):
        """Consume a string, keeping a source copy and storing its objast."""
        self.source = mathstr
        self.objast = objectify_string(mathstr)
        self.function_list = functions_from_ast(self.objast)

