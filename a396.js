'use strict';

let cherow = require('cherow');

const SCOPE = {
    LOCAL: 'local', // global when not enclosed
    BLOCK: 'block'
};

let Scope = class {
    constructor(type, line, pos, parent_scope) {
        this.type = type; // SCOPE.LOCAL, or .BLOCK
        this.line = line;
        this.pos = pos;
        this.parent_scope = parent_scope;
        this.child_scopes = [];
    }

    append_child(child_scope) {
        this.child_scopes.push(child_scope);
    }
};

module.exports = (function () {

    /*
    function trivial_translate(program) {
        return {
            'unbound': ['input'],
            'bound': {'output': '[input]'}
        };
    }
    */

    const scope = new Scope(SCOPE.GLOBAL);

    function interpret(ast) {

        function hoist_declaration(stmt) {
            /*
             * type=VariableDeclaration
             *
             * The declaration is pushed to the lowest enclosing block scope.
             *
             * Multiple declarations in the same scope are the same as one
             * declaration.
             * */
        }

        function add_to_scope(stmt) {
            // type=VariableDeclaration
            return ({
                'var': hoist_declaration,
                // 'let': block_declaration,
                // 'const': block_declaration
            })[stmt.kind](stmt);
        }

        for (const stmt of ast.body) {
            (({
                'VariableDeclaration': add_to_scope
            })[stmt.type])(stmt);
        }

        return ast;
    }

    function translate(program) {
        var ast = cherow.parse(program);
        return interpret(ast);
    }

    return {
        translate: translate
    };
}());
