#!/usr/bin/python3

"""Implement the MathParse Python-to-Tableau translator and helper methods."""

import ast

def objectify_node(node):
    """Get the tree into a friendly manipulable format we can easily
      compare in unit tests and does not have line/col info not needed
      here"""
    if node is None:
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

#class MathParseContext:
#    """
#        Encapsulate the state associated with a single context.
#    """
#
#    def __init__(self, name, parent=None):
#        """Initialize the context's name."""
#        self.name = name
#        self.parent = parent
#        self.symbols = set()
#        self.modified_symbols = set()
#
#    def translate_symbol(self, symbol):
#        """Seek the symbol in the context or parent context and return its Tableau name."""
#        if symbol in self.symbols:
#            return '_{}:{}'.format(self.name, symbol)
#        elif self.parent is not None:
#            return self.parent.translate_symbol(symbol)
#        else:
#            raise ValueError(symbol)
#
#    def create_child_context(self, name):
#        """Return a new context with this context as the parent and the appropriate name."""
#        return MathParseContext("{}:{}".format(self.name, name), self)
#
#    def add_symbol(self, symbol):
#        """Add a symbol to the context."""
#        self.symbols.add(symbol)
#
#    def populate_modified_symbols(self, objast):
#        """Find out which symbols are modified in this objast."""
#        if 'Module' in objast:
#            self.populate_modified_symbols(objast['Module'])
#        elif 'body' in objast:
#            for stmt in objast['body']:
#                self.populate_modified_symbols(stmt)
#        elif 'AugAssign' in objast:
#            self.populate_modified_symbols(objast['AugAssign']['target'])
#        elif 'Name' in objast:
#            self.modified_symbols.add(objast['Name']['id'])
#        elif 'Assign' in objast:
#            for symbol in objast['Assign']['targets']:
#                self.populate_modified_symbols(symbol)
#        elif 'If' in objast:
#            for stmt in objast['If']['body']:
#                self.populate_modified_symbols(stmt)
#            for stmt in objast['If']['orelse']:
#                self.populate_modified_symbols(stmt)
#        elif 'Pass' in objast:
#            pass
#        elif 'FunctionDef' in objast:
#            pass
#        elif 'Return' in objast:
#            pass
#        else:
#            raise ValueError(objast.keys())
#
#    def populate_symbols(self, objast):
#        """Find all symbols mentioned in this objast."""
#        if 'Module' in objast:
#            self.populate_symbols(objast['Module'])
#        elif 'body' in objast:
#            for stmt in objast['body']:
#                self.populate_symbols(stmt)
#        elif 'AugAssign' in objast:
#            self.populate_symbols(objast['AugAssign']['target'])
#            self.populate_symbols(objast['AugAssign']['value'])
#        elif 'Name' in objast:
#            self.symbols.add(objast['Name']['id'])
#        elif 'Assign' in objast:
#            for stmt in objast['Assign']['targets']:
#                self.populate_symbols(stmt)
#            self.populate_symbols(objast['Assign']['value'])
#        elif 'Num' in objast:
#            pass
#        elif 'BinOp' in objast:
#            self.populate_symbols(objast['BinOp']['left'])
#            self.populate_symbols(objast['BinOp']['right'])
#        elif 'If' in objast:
#            for stmt in objast['If']['body']:
#                self.populate_symbols(stmt)
#            self.populate_symbols(objast['If']['test'])
#            for stmt in objast['If']['orelse']:
#                self.populate_symbols(stmt)
#        elif 'Compare' in objast:
#            self.populate_symbols(objast['Compare']['left'])
#            for expr in objast['Compare']['comparators']:
#                self.populate_symbols(expr)
#        elif 'Pass' in objast:
#            pass
#        elif 'Return' in objast:
#            self.populate_symbols(objast['Return']['value'])
#        else:
#            raise ValueError(objast)
#
#    def populate_returns(self):
#        pass

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

    def __init__(self, context_name='_'):
        """Set default empty values for instance variables."""
        self.context = MathParseContext(context_name)

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

    def context_parse_string(self, mathstr):
        """Consume a string, updating it into the context."""
        self.source = mathstr
        self.objast = objectify_string(mathstr)
        self.context.populate_modified_symbols(self.objast)
        self.context.populate_symbols(self.objast)
        self.context.populate_returns(self.objast)

    def parse_string(self, mathstr):
        """Consume a string, keeping a source copy and storing its objast."""
        self.source = mathstr
        self.objast = objectify_string(mathstr)
        self.function_list = functions_from_ast(self.objast)

class SymbolSeekerVisitor(ast.NodeVisitor):
    """Find symbols in the AST."""
    def __init__(self, symbol_catcher):
        self.symbol_catcher = symbol_catcher

    def visit_Name(self, node):
        self.symbol_catcher(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.symbol_catcher(node.name)
        self.generic_visit(node)

    def visit_arg(self, node):
        self.symbol_catcher(node.arg)
        self.generic_visit(node)

class TargetSymbolSeekerVisitor(ast.NodeVisitor):
    """Find target symbols in the AST."""
    def __init__(self, symbol_catcher):
        self.symbol_catcher = symbol_catcher

    def visit_Assign(self, node):
        for t in node.targets:
            try:
                self.symbol_catcher(t.id)
            except AttributeError:
                pass

class RenderVisitor():
    """Run through the tree, returning a string formula."""

    def __init__(self, symbol_defs, context_name='_'):
        self.symbol_defs = symbol_defs
        self.context_name = context_name

    def visit(self, node):
        return (getattr(self, 'visit_' + node.__class__.__name__))(node)

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_BinOp(self, node):
        return '({} {} {})'.format(
            self.visit(node.left),
            self.decode_binop(node.op),
            self.visit(node.right)
        )

    def visit_Name(self, node):
        return '[{}]'.format(self.symbol_defs[node.id])

    def decode_binop(self, node_op):
        return {
            'Add': '+',
            'Mult': '*'
        }[node_op.__class__.__name__]

    def visit_Num(self, node):
        return node.n

def translate_ast_expression(ast_expr):
    """Translate one expression and generate any formulas."""
    symbols = {}
    ssv = SymbolSeekerVisitor(symbols.add)
    ssv.visit(ast_expr)
    formulae = {}
    rv = RenderVisitor(symbols)
    formulae.update({'_stmt_0': rv.visit(ast_expr)})
    return formulae

class ASTMathParse:
    """Translate on the normal AST not an objast."""

    def __init__(self, context_name='_', parent=None):
        """Initialize our instance variables."""
        self.src = ""
        self.ast = None
        self.symbols = set()
        self.target_symbols = set()
        self.statements = []

        self.symbol_table = {}
        self.context_name = context_name
        self.qualified_context_name = '{}:{}'.format(
            parent.qualified_context_name, context_name
        ) if parent else context_name
        self.parent = parent

    def find_symbols(self):
        """Visit all the nodes in the AST finding symbols referenced."""
        symbols = set()
        ssv = SymbolSeekerVisitor(symbols.add)
        ssv.visit(self.ast)
        return symbols

    def find_target_symbols(self):
        symbols = set()
        tssv = TargetSymbolSeekerVisitor(symbols.add)
        tssv.visit(self.ast)
        return symbols

    def export_symbols(self):
        return {'_' + a for a in self.symbols}

    def define_symbols(self, symbols):
        """Determine the symbol table mapping for the symbols in their contexts."""
        return {
            symbol: self.resolve_symbol(symbol) for symbol in symbols
        }

    def parse_string(self, mathstr):
        """Fill state from the AST of mathstr."""
        self.src = mathstr
        self.ast = ast.parse(mathstr)
        self.symbols = self.find_symbols()
        self.target_symbols = self.find_target_symbols()
        self.statements = self.ast.body
        self.symbol_table = self.define_symbols(self.symbols)

    def define_symbol(self, symboldef):
        """Add a symbol to the symbol table."""
        self.symbol_table.update(symboldef)

    def translate_expression(self, expr):
        """Translate an expression in context."""
        rv = RenderVisitor(self.symbol_table, self.context_name)
        return rv.visit(expr)

    def create_child_context(self, name):
        """Create a child context with given name and self as parent."""
        return ASTMathParse(name, self)

    def resolve_symbol(self, symbol):
        """Look up the symbol in the chain of contexts and return its qualified name."""
        if symbol in self.symbols:
            return '_{}:{}'.format(self.qualified_context_name, symbol)
        elif self.parent is not None:
            return self.parent.resolve_symbol(symbol)
        else:
            raise KeyError(symbol)

    def translate_statements(self):
        """Translate whatever is in our statement list."""
        stmts = {}
        for i, stmt in enumerate(self.statements):
            stmt_name = '_{}:stmt{}'.format(self.qualified_context_name, i)
            stmts.update(
                {
                    stmt_name: self.translate_expression(stmt.value)
                }
            )

            if isinstance(stmt, ast.Assign):
                stmts.update(
                    {
                        self.resolve_symbol(stmt.targets[0].id): '[{}]'.format(stmt_name)
                    }
                )

        return stmts

    def find_bound_variables(self, myast, ctx={}):
        """Identify the free variables in an assignment RHS."""

