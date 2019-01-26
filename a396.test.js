const a396 = require('./a396');

test('identity assignment', () => {
    expect(a396.translate('var output = input;')).toEqual({
        'unbound': ['input'],
        'bound': {'output': '[input]'}
    });
});
