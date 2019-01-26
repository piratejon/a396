"use strict";

var cherow = require('cherow');

module.exports = (function () {

    function translate (expression) {
        return {
            'unbound': ['input'],
            'bound': {'output': '[input]'}
        };
    }

    return {
        translate: translate
    };
}());
