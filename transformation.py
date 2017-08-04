import collections

import parsing

CIntegerLiteral = collections.namedtuple(
    'CIntegerLiteral',
    [
        'value',
    ],
)

CStringLiteral = collections.namedtuple(
    'CStringLiteral',
    [
        'value',
    ],
)

CAdditionExpression = collections.namedtuple(
    'CAdditionExpression',
    [
        'left',
        'right',
    ],
)

CSubtractionExpression = collections.namedtuple(
    'CSubtractionExpression',
    [
        'left',
        'right',
    ],
)

CMultiplicationExpression = collections.namedtuple(
    'CMultiplicationExpression',
    [
        'left',
        'right',
    ],
)

CIntegerDivisionExpression = collections.namedtuple(
    'CIntegerDivisionExpression',
    [
        'left',
        'right',
    ],
)

CModularDivisionExpression = collections.namedtuple(
    'CModularDivisionExpression',
    [
        'left',
        'right',
    ],
)

CFunctionCallStatement = collections.namedtuple(
    'CFunctionCallStatement',
    [
        'name',
        'arguments',
    ],
)

CProgram = collections.namedtuple(
    'CProgram',
    [
        'builtins',
        'statements',
        'standard_libraries',
    ],
)

BUILTINS = {
    'print': ['stdio.h.'],
}

def transform_expression(builtin_dependencies, expression):

    LITERAL_TYPE_MAPPING = {
        parsing.FurIntegerLiteralExpression: CIntegerLiteral,
        parsing.FurStringLiteralExpression: CStringLiteral,
    }

    if type(expression) in LITERAL_TYPE_MAPPING:
        return LITERAL_TYPE_MAPPING[type(expression)](value=expression.value)

    INFIX_TYPE_MAPPING = {
        parsing.FurAdditionExpression: CAdditionExpression,
        parsing.FurSubtractionExpression: CSubtractionExpression,
        parsing.FurMultiplicationExpression: CMultiplicationExpression,
        parsing.FurIntegerDivisionExpression: CIntegerDivisionExpression,
        parsing.FurModularDivisionExpression: CModularDivisionExpression,
    }

    return INFIX_TYPE_MAPPING[type(expression)](
        left=transform_expression(builtin_dependencies, expression.left),
        right=transform_expression(builtin_dependencies, expression.right),
    )

def transform_function_call_statement(builtin_dependencies, function_call):
    if function_call.name in BUILTINS.keys():
        builtin_dependencies.add(function_call.name)

        return CFunctionCallStatement(
            name='builtin$' + function_call.name,
            arguments=tuple(transform_expression(builtin_dependencies, arg) for arg in function_call.arguments),
        )

    raise Exception()

def transform(program):
    builtins = set()

    c_statements = [
        transform_function_call_statement(builtins, statement) for statement in program.statement_list
    ]

    standard_libraries = set()
    for builtin in builtins:
        for standard_library in BUILTINS[builtin]:
            standard_libraries.add(standard_library)

    return CProgram(
        builtins=builtins,
        statements=c_statements,
        standard_libraries=standard_libraries,
    )


if __name__ == '__main__':
    import unittest

    unittest.main()
