import collections

import parsing

NormalVariableExpression = collections.namedtuple(
    'NormalVariableExpression',
    [
        'variable',
    ],
)

NormalInfixExpression = collections.namedtuple(
    'NormalInfixExpression',
    [
        'order',
        'operator',
        'left',
        'right',
    ],
)

NormalFunctionCallExpression = collections.namedtuple(
    'NormalFunctionCallExpression',
    [
        'function',
        'arguments',
    ],
)

NormalVariableAssignmentStatement = collections.namedtuple(
    'NormalVariableAssignmentStatement',
    [
        'variable',
        'expression',
    ],
)

NormalExpressionStatement = collections.namedtuple(
    'NormalExpressionStatement',
    [
        'expression',
    ],
)

NormalProgram = collections.namedtuple(
    'NormalProgram',
    [
        'statement_list',
    ],
)

def fake_normalization(counter, thing):
    return (counter, (), thing)

def normalize_function_call_expression(counter, expression):
    assert isinstance(expression, parsing.FurFunctionCallExpression)

    prestatements = []
    arguments = []

    for argument in expression.arguments:
        counter, argument_prestatements, normalized_argument = normalize_expression(counter, argument)

        for s in argument_prestatements:
            prestatements.append(s)

        variable = '${}'.format(counter)
        prestatements.append(NormalVariableAssignmentStatement(
            variable=variable,
            expression=normalized_argument,
        ))
        arguments.append(NormalVariableExpression(
            variable=variable,
        ))
        counter += 1

    return (
        counter,
        tuple(prestatements),
        NormalFunctionCallExpression(
            expression.function, # TODO Normalize the function
            arguments=tuple(arguments),
        ),
    )

def normalize_basic_infix_operation(counter, expression):
    counter, left_prestatements, left_expression = normalize_expression(counter, expression.left)
    counter, right_prestatements, right_expression = normalize_expression(counter, expression.right)

    left_variable = '${}'.format(counter)
    counter += 1
    right_variable = '${}'.format(counter)
    counter += 1

    root_prestatements = (
        NormalVariableAssignmentStatement(
            variable=left_variable,
            expression=left_expression,
        ),
        NormalVariableAssignmentStatement(
            variable=right_variable,
            expression=right_expression,
        ),
    )

    return (
        counter,
        left_prestatements + right_prestatements + root_prestatements,
        NormalInfixExpression(
            order=expression.order, # TODO Do we need this?
            operator=expression.operator,
            left=NormalVariableExpression(variable=left_variable),
            right=NormalVariableExpression(variable=right_variable),
        ),
    )

def normalize_infix_expression(counter, expression):
    # TODO Unfake this normalization
    return {
        'multiplication_level': normalize_basic_infix_operation,
        'addition_level': normalize_basic_infix_operation,
        'comparison_level': fake_normalization,
        'and_level': fake_normalization,
        'or_level': fake_normalization,
    }[expression.order](counter, expression)

def normalize_expression(counter, expression):
    return {
        parsing.FurFunctionCallExpression: normalize_function_call_expression,
        parsing.FurInfixExpression: normalize_infix_expression,
        parsing.FurIntegerLiteralExpression: fake_normalization,
        parsing.FurNegationExpression: fake_normalization, # TODO Don't fake this
        parsing.FurParenthesizedExpression: fake_normalization, # TODO Don't fake this
        parsing.FurStringLiteralExpression: fake_normalization,
        parsing.FurSymbolExpression: fake_normalization,
    }[type(expression)](counter, expression)

def normalize_expression_statement(counter, statement):
    counter, prestatements, normalized = {
        parsing.FurFunctionCallExpression: normalize_function_call_expression,
    }[type(statement.expression)](counter, statement.expression)

    return (
        counter,
        prestatements,
        NormalExpressionStatement(expression=normalized),
    )

def normalize_statement(counter, statement):
    return {
        parsing.FurExpressionStatement: normalize_expression_statement,
        parsing.FurAssignmentStatement: fake_normalization,
    }[type(statement)](counter, statement)

def normalize(program):
    counter = 0
    statement_list = []

    for statement in program.statement_list:
        counter, prestatements, normalized = normalize_statement(counter, statement)
        for s in prestatements:
            statement_list.append(s)
        statement_list.append(normalized)

    return NormalProgram(
        statement_list=statement_list,
    )
