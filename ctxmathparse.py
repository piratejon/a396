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
        MathParseFunction(o['FunctionDef'])
        for o in objast['Module']['body'] if 'FunctionDef' in o
    ]

def get_astfunction_args(astfunc):
    """Return a map of arg name -> Tableau function name."""
    return {
        arg['arg']['arg']: '_{}_arg_{}'.format(astfunc['name'], arg['arg']['arg'])
        for arg in astfunc['args']['arguments']['args']
    }

def translate_binop(operator):
    """Convert a BinOp op object into the corresponding math symbol."""
    keylist = list(operator.keys())
    try:
        result = {
            "Mult": "*",
            "Add": "+",
            "Sub": "-",
        }[keylist[0]]
    except KeyError:
        result = keylist[0]

    return result

def translate_expression(fname, args, localvars, expr):
    """Recursively translate an expression for the given function and arguments."""
    if 'BinOp' in expr:
        return (
            '({} {} {})'.format(
                translate_expression(fname, args, localvars, expr['BinOp']['left']),
                translate_binop(expr['BinOp']['op']),
                translate_expression(fname, args, localvars, expr['BinOp']['right'])
            )
        )
    elif 'Name' in expr:
        name = expr['Name']['id']
        if name in localvars: # look in localvars to see if a symbol got overwritten
            return '[{}]'.format(localvars[name])
        elif name in args:
            return '[{}]'.format(args[name])
        else:
            return name
    elif 'Num' in expr:
        return expr['Num']['n']

    return 'unrecognized expression type ' + list(expr.keys())[0]

def invert_dict(swap_me):
    """Swap each key -> value pair in a dictionary."""
    return {v: k for k, v in swap_me.items()}

class MathParseContext:
    """
        Encapsulate the state associated with a single context.
    """

    def __init__(self, name, parent = None):
        """Initialize the context's name."""
        self.name = name
        self.parent = parent
        self.symbols = set()

    def translate_symbol(self, symbol):
        """Seek the symbol in the context or parent context and return its Tableau name."""
        if symbol in self.symbols:
            return '_{}:{}'.format(self.name, symbol)
        elif self.parent is not None:
            return self.parent.translate_symbol(symbol)
        else:
            raise ValueError(symbol)

    def create_child_context(self, name):
        return MathParseContext("{}:{}".format(self.name, name), self)

    def add_symbol(self, symbol):
        self.symbols.add(symbol)

class MathParseFunction:
    """
        Encapsulate the state associated with translating a single function.
    """

    def __init__(self, astfunc):
        """Initialize class instance from objast"""
        self.localvars = {}
        self.name = astfunc['name']
        self.args = get_astfunction_args(astfunc)
        self.body = astfunc['body']

    def translate_function_statement(self, i):
        """Translate a single statement in the given function's context."""
        stmt = self.body[i]
        if 'Return' in stmt:
            return translate_expression(
                self.name, self.args, self.localvars, stmt['Return']['value']
            )
        elif 'Assign' in stmt:
            new_local = {
                stmt['Assign']['targets'][0]['Name']['id']: '_{}_stmt_{}'.format(self.name, i)
            }
            expr_string = translate_expression(
                self.name, self.args, self.localvars, stmt['Assign']['value']
            )
            self.localvars.update(new_local)
            return expr_string
        elif 'AugAssign' in stmt:
            new_local = {
                stmt['AugAssign']['target']['Name']['id']: '_{}_stmt_{}'.format(self.name, i)
            }
            expr_string = translate_expression(
                self.name, self.args, self.localvars, {
                    "BinOp": {
                        "left": stmt['AugAssign']['target'],
                        "op": stmt['AugAssign']['op'],
                        "right": stmt['AugAssign']['value']
                    }
                }
            )
            self.localvars.update(new_local)
            return expr_string
        elif 'If' in stmt:
            new_local = {
                stmt['If']['body']
            }
        else:
            return 'unknown statement type ' + list(stmt.keys())[0]

    def collect_function_statements(self):
        """
            Return an ordered list of expressions for each statement in the function.
        """
        return [
            self.translate_function_statement(i)
            for i in range(len(self.body))
        ]

    def get_function_statement(self):
        """Compose the function's top-level statements into a final expression."""
        return '[_{}_stmt_{}]'.format(
            self.name, len(self.collect_function_statements()) - 1
        )

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
            stmts = func.body
            result.update(invert_dict(func.args))
            result.update(
                {
                    '_{}_stmt_{}'.format(func.name, i): func.translate_function_statement(i)
                    for i in range(len(stmts))
                }
            )
            result.update(
                {
                    '_{}'.format(func.name): func.get_function_statement()
                }
            )
        return result

    def parse_string(self, mathstr):
        """Consume a string, keeping a source copy and storing its objast."""
        self.source = mathstr
        self.objast = objectify_string(mathstr)
        self.function_list = functions_from_ast(self.objast)

