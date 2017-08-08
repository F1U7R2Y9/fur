import collections

import normalization
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
        'index',
        'value',
    ],
)

CConstantExpression = collections.namedtuple(
    'CConstantExpression',
    [
        'value'
    ],
)

CVariableExpression = collections.namedtuple(
    'CVariableExpression',
    [
        'variable',
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

CSymbolAssignmentStatement = collections.namedtuple(
    'CSymbolAssignmentStatement',
    [
        'target',
        'target_symbol_list_index',
        'expression',
    ],
)

CVariableInitializationStatement = collections.namedtuple(
    'CVariableInitializationStatement',
    [
        'variable',
        'expression',
    ],
)

CVariableReassignmentStatement = collections.namedtuple(
    'CVariableReassignmentStatement',
    [
        'variable',
        'expression',
    ],
)

CExpressionStatement = collections.namedtuple(
    'CExpressionStatement',
    [
        'expression',
    ],
)

CIfElseStatement = collections.namedtuple(
    'CIfElseStatement',
    [
        'condition_expression',
        'if_statements',
        'else_statements',
    ],
)

CProgram = collections.namedtuple(
    'CProgram',
    [
        'builtin_set',
        'statements',
        'standard_libraries',
        'string_literal_list',
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

def transform_comparison_level_expression(accumulators, expression):
    # Transform expressions like 1 < 2 < 3 into expressions like 1 < 2 && 2 < 3
    if isinstance(expression.left, parsing.FurInfixExpression) and expression.left.order == 'comparison_level':
        left = transform_comparison_level_expression(
            accumulators,
            expression.left
        )

        middle = left.right

        right = transform_expression(
            accumulators,
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
        left=transform_expression(accumulators, expression.left),
        right=transform_expression(accumulators, expression.right),
    )

BUILTINS = {
    'false':    [],
    'pow':      ['math.h'],
    'print':    ['stdio.h'],
    'true':     [],
}

def transform_variable_expression(accumulators, expression):
    return CVariableExpression(variable=expression.variable)

def transform_infix_expression(accumulators, expression):
    if expression.order == 'comparison_level':
        return transform_comparison_level_expression(accumulators, expression)

    INFIX_OPERATOR_TO_FUNCTION_NAME = {
        '+':    'add',
        '-':    'subtract',
        '*':    'multiply',
        '//':   'integerDivide',
        '%':    'modularDivide',
        'and':  'and',
        'or':   'or',
    }

    return CFunctionCallForFurInfixOperator(
        name=INFIX_OPERATOR_TO_FUNCTION_NAME[expression.operator],
        left=transform_expression(accumulators, expression.left),
        right=transform_expression(accumulators, expression.right),
    )

def transform_expression(accumulators, expression):
    if isinstance(expression, parsing.FurParenthesizedExpression):
        # Parentheses can be removed because everything in the C output is explicitly parenthesized
        return transform_expression(accumulators, expression.internal)

    if isinstance(expression, parsing.FurNegationExpression):
        return transform_negation_expression(accumulators, expression)

    if isinstance(expression, parsing.FurFunctionCallExpression):
        return transform_function_call_expression(accumulators, expression)

    if isinstance(expression, parsing.FurSymbolExpression):
        if expression.value in ['true', 'false']:
            return CConstantExpression(value=expression.value)

        if expression.value not in accumulators.symbol_list:
            symbol_list.append(expression.value)

        return CSymbolExpression(
            symbol=expression.value,
            symbol_list_index=accumulators.symbol_list.index(expression.value),
        )

    if isinstance(expression, parsing.FurStringLiteralExpression):
        value = expression.value

        try:
            index = accumulators.string_literal_list.index(value)
        except ValueError:
            index = len(accumulators.string_literal_list)
            accumulators.string_literal_list.append(value)

        return CStringLiteral(index=index, value=value)

    LITERAL_TYPE_MAPPING = {
        parsing.FurIntegerLiteralExpression: CIntegerLiteral,
    }

    if type(expression) in LITERAL_TYPE_MAPPING:
        return LITERAL_TYPE_MAPPING[type(expression)](value=expression.value)

    # TODO Handle all possible types in this form
    return {
        parsing.FurInfixExpression: transform_infix_expression, # TODO Shouldn't need this
        normalization.NormalFunctionCallExpression: transform_function_call_expression,
        normalization.NormalInfixExpression: transform_infix_expression,
        normalization.NormalVariableExpression: transform_variable_expression,
    }[type(expression)](accumulators, expression)

def transform_symbol_assignment_statement(accumulators, assignment_statement):
    # TODO Check that target is not a builtin
    if assignment_statement.target not in accumulators.symbol_list:
        accumulators.symbol_list.append(assignment_statement.target)

    return CSymbolAssignmentStatement(
        target=assignment_statement.target,
        target_symbol_list_index=accumulators.symbol_list.index(assignment_statement.target),
        expression=transform_expression(
            accumulators,
            assignment_statement.expression,
        ),
    )

def transform_negation_expression(accumulators, negation_expression):
    return CNegationExpression(
        value=transform_expression(accumulators, negation_expression.value),
    )

def transform_function_call_expression(accumulators, function_call):
    # TODO Function should be a full expression
    if function_call.function.value in BUILTINS.keys():
        # TODO Check that the builtin is actually callable
        accumulators.builtin_set.add(function_call.function.value)

        return CFunctionCallExpression(
            name='builtin$' + function_call.function.value,
            arguments=tuple(
                transform_expression(accumulators, arg)
                for arg in function_call.arguments
            ),
        )

    raise Exception()

def transform_expression_statement(accumulators, statement):
    expression = {
        parsing.FurFunctionCallExpression: transform_function_call_expression,
        normalization.NormalFunctionCallExpression: transform_function_call_expression,
    }[type(statement.expression)](accumulators, statement.expression)

    return CExpressionStatement(
        expression=expression,
    )

def transform_if_else_statement(accumulators, statement):
    return CIfElseStatement(
        condition_expression=transform_expression(accumulators, statement.condition_expression),
        if_statements=tuple(transform_statement(accumulators, s) for s in statement.if_statements),
        else_statements=tuple(transform_statement(accumulators, s) for s in statement.else_statements),
    )

def transform_variable_initialization_statement(accumulators, statement):
    return CVariableInitializationStatement(
        variable=statement.variable,
        expression=transform_expression(accumulators, statement.expression),
    )

def transform_variable_reassignment_statement(accumulators, statement):
    return CVariableReassignmentStatement(
        variable=statement.variable,
        expression=transform_expression(accumulators, statement.expression),
    )

def transform_statement(accumulators, statement):
    return {
        parsing.FurAssignmentStatement: transform_symbol_assignment_statement,
        parsing.FurExpressionStatement: transform_expression_statement,
        normalization.NormalExpressionStatement: transform_expression_statement,
        normalization.NormalIfElseStatement: transform_if_else_statement,
        normalization.NormalVariableInitializationStatement: transform_variable_initialization_statement,
        normalization.NormalVariableReassignmentStatement: transform_variable_reassignment_statement,
    }[type(statement)](accumulators, statement)


Accumulators = collections.namedtuple(
    'Accumulators',
    [
        'builtin_set',
        'symbol_list',
        'string_literal_list',
    ],
)

def transform(program):
    accumulators = Accumulators(
        builtin_set=set(),
        symbol_list=[],
        string_literal_list=[],
    )

    statement_list = [
        transform_statement(accumulators, statement) for statement in program.statement_list
    ]

    standard_library_set = set()
    for builtin in accumulators.builtin_set:
        for standard_library in BUILTINS[builtin]:
            standard_library_set.add(standard_library)

    return CProgram(
        builtin_set=accumulators.builtin_set,
        statements=statement_list,
        standard_libraries=standard_library_set,
        string_literal_list=accumulators.string_literal_list,
        symbol_list=accumulators.symbol_list,
    )


if __name__ == '__main__':
    import unittest

    unittest.main()
