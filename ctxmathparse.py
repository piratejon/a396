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

def translate_binop(operator):
    """Convert a BinOp op object into the corresponding math symbol."""
    keylist = list(operator.keys())
    try:
        result = {
            "Mult": "*",
            "Add": "+",
        }[keylist[0]]
    except KeyError:
        result = keylist[0]

    return result

def translate_expression(fname, args, expr):
    """Recursively translate an expression for the given function and arguments."""
    if 'BinOp' in expr:
        return (
            '({} {} {})'.format(
                translate_expression(fname, args, expr['BinOp']['left']),
                translate_binop(expr['BinOp']['op']),
                translate_expression(fname, args, expr['BinOp']['right'])
            )
        )
    elif 'Name' in expr:
        name = expr['Name']['id']
        if name in args:
            return '[{}]'.format(args[name])
        else:
            return name
    elif 'Num' in expr:
        return expr['Num']['n']

    return 'unrecognized statement type ' + list(expr.keys())[0]

def translate_function_statement(func, stmt):
    """Translate a single statement in the given function's context."""
    args = get_function_args(func)
    if 'Return' in stmt:
        return translate_expression(func['name'], args, stmt['Return']['value'])
    else:
        return 'unknown statement type ' + (stmt.keys())[0]

def collect_function_statements(func):
    """
        Return an ordered list of expressions for each statement in the function.
    """
    return [
        translate_function_statement(func, func['body'][i])
        for i in range(len(func['body']))
    ]

def get_function_statement(func):
    """Compose the function's top-level statements into a final expression."""
    return '[_{}_stmt_{}]'.format(func['name'], 0)

def invert_dict(d):
    return {
        v: k for k, v in d.items()
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

    def translate(self):
        """Translate this context's function list."""
        result = {}
        for func in self.function_list:
            stmts = collect_function_statements(func)
            result.update(invert_dict(get_function_args(func)))
            result.update({
                    '_{}_stmt_{}'.format(func['name'], i): stmts[i]
                    for i in range(len(stmts))
                }
            )
            result.update({
                    '_{}'.format(func['name']): get_function_statement(func)
                }
            )
        return result

    def parse_string(self, mathstr):
        """Consume a string, keeping a source copy and storing its objast."""
        self.source = mathstr
        self.objast = objectify_string(mathstr)
        self.function_list = functions_from_ast(self.objast)

