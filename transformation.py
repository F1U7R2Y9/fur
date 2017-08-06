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

CConstantExpression = collections.namedtuple(
    'CConstantExpression',
    [
        'value'
    ],
)

CSymbolExpression = collections.namedtuple(
    'CSymbolExpression',
    [
        'symbol',
        'symbol_list_index',
    ],
)

CNegationExpression = collections.namedtuple(
    'CNegationExpression',
    [
        'value',
    ],
)

CFunctionCallForFurInfixOperator = collections.namedtuple(
    'CFunctionCallForFurInfixOperator',
    [
        'name',
        'left',
        'right',
    ],
)

CFunctionCallExpression = collections.namedtuple(
    'CFunctionCallExpression',
    [
        'name',
        'arguments',
    ],
)

CAssignmentStatement = collections.namedtuple(
    'CAssignmentStatement',
    [
        'target',
        'target_symbol_list_index',
        'expression',
    ],
)

CProgram = collections.namedtuple(
    'CProgram',
    [
        'builtins',
        'statements',
        'standard_libraries',
        'symbol_list',
    ],
)

EQUALITY_LEVEL_OPERATOR_TO_FUNCTION_NAME_MAPPING = {
    '==':   'equals',
    '!=':   'notEquals',
    '<=':   'lessThanOrEqual',
    '>=':   'greaterThanOrEqual',
    '<':    'lessThan',
    '>':    'greaterThan',
}

def transform_equality_level_expression(builtin_dependencies, symbol_list, expression):
    # Transform expressions like 1 < 2 < 3 into expressions like 1 < 2 && 2 < 3
    if isinstance(expression.left, parsing.FurEqualityLevelExpression):
        left = transform_equality_level_expression(
            builtin_dependencies,
            symbol_list,
            expression.left
        )

        middle = left.right

        right = transform_expression(
            builtin_dependencies,
            symbol_list,
            expression.right,
        )

        # TODO Don't evaluate the middle expression twice
        return CFunctionCallForFurInfixOperator(
            name='and',
            left=left,
            right=CFunctionCallForFurInfixOperator(
                name=EQUALITY_LEVEL_OPERATOR_TO_FUNCTION_NAME_MAPPING[expression.operator],
                left=middle,
                right=right,
            ),
        )

    return CFunctionCallForFurInfixOperator(
        name=EQUALITY_LEVEL_OPERATOR_TO_FUNCTION_NAME_MAPPING[expression.operator],
        left=transform_expression(builtin_dependencies, symbol_list, expression.left),
        right=transform_expression(builtin_dependencies, symbol_list, expression.right),
    )

BUILTINS = {
    'false':    [],
    'pow':      ['math.h'],
    'print':    ['stdio.h'],
    'true':     [],
}

def transform_expression(builtin_dependencies, symbol_list, expression):
    if isinstance(expression, parsing.FurParenthesizedExpression):
        # Parentheses can be removed because everything in the C output is explicitly parenthesized
        return transform_expression(builtin_dependencies, symbol_list, expression.internal)

    if isinstance(expression, parsing.FurNegationExpression):
        return transform_negation_expression(builtin_dependencies, symbol_list, expression)

    if isinstance(expression, parsing.FurFunctionCallExpression):
        return transform_function_call_expression(builtin_dependencies, symbol_list, expression)

    if isinstance(expression, parsing.FurSymbolExpression):
        if expression.value in ['true', 'false']:
            return CConstantExpression(value=expression.value)

        if expression.value not in symbol_list:
            symbol_list.append(expression.value)

        return CSymbolExpression(
            symbol=expression.value,
            symbol_list_index=symbol_list.index(expression.value),
        )

    LITERAL_TYPE_MAPPING = {
        parsing.FurIntegerLiteralExpression: CIntegerLiteral,
        parsing.FurStringLiteralExpression: CStringLiteral,
    }

    if type(expression) in LITERAL_TYPE_MAPPING:
        return LITERAL_TYPE_MAPPING[type(expression)](value=expression.value)

    if isinstance(expression, parsing.FurEqualityLevelExpression):
        return transform_equality_level_expression(builtin_dependencies, symbol_list, expression)

    INFIX_OPERATOR_TO_FUNCTION_NAME = {
        '+': 'add',
        '-': 'subtract',
        '*': 'multiply',
        '//': 'integerDivide',
        '%': 'modularDivide',
    }

    return CFunctionCallForFurInfixOperator(
        name=INFIX_OPERATOR_TO_FUNCTION_NAME[expression.operator],
        left=transform_expression(builtin_dependencies, symbol_list, expression.left),
        right=transform_expression(builtin_dependencies, symbol_list, expression.right),
    )

def transform_assignment_statement(builtin_dependencies, symbol_list, assignment_statement):
    # TODO Check that target is not a builtin
    if assignment_statement.target not in symbol_list:
        symbol_list.append(assignment_statement.target)

    return CAssignmentStatement(
        target=assignment_statement.target,
        target_symbol_list_index=symbol_list.index(assignment_statement.target),
        expression=transform_expression(
            builtin_dependencies,
            symbol_list,
            assignment_statement.expression,
        ),
    )

def transform_negation_expression(builtin_dependencies, symbol_list, negation_expression):
    return CNegationExpression(
        value=transform_expression(builtin_dependencies, symbol_list, negation_expression.value),
    )

def transform_function_call_expression(builtin_dependencies, symbol_list, function_call):
    if function_call.function.value in BUILTINS.keys():
        # TODO Check that the builtin is actually callable
        builtin_dependencies.add(function_call.function.value)

        return CFunctionCallExpression(
            name='builtin$' + function_call.function.value,
            arguments=tuple(
                transform_expression(builtin_dependencies, symbol_list, arg)
                for arg in function_call.arguments
            ),
        )

    raise Exception()

def transform_statement(builtin_dependencies, symbol_list, statement):
    return {
        parsing.FurAssignmentStatement: transform_assignment_statement,
        parsing.FurFunctionCallExpression: transform_function_call_expression,
    }[type(statement)](builtin_dependencies, symbol_list, statement)

def transform(program):
    builtins = set()
    symbol_list = []

    c_statements = [
        transform_statement(builtins, symbol_list, statement) for statement in program.statement_list
    ]

    standard_libraries = set()
    for builtin in builtins:
        for standard_library in BUILTINS[builtin]:
            standard_libraries.add(standard_library)

    return CProgram(
        builtins=builtins,
        statements=c_statements,
        standard_libraries=standard_libraries,
        symbol_list=symbol_list,
    )


if __name__ == '__main__':
    import unittest

    unittest.main()
