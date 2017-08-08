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

def normalize_comparison_expression(counter, expression):
    stack = []

    while isinstance(expression.left, parsing.FurInfixExpression) and expression.order == 'comparison_level':
        stack.append((expression.operator, expression.order, expression.right))
        expression = expression.left

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

    counter, result_prestatements, result_expression = (
        counter,
        left_prestatements + right_prestatements + root_prestatements,
        # TODO Implement short-circuiting
        NormalInfixExpression(
            order=expression.order, # TODO Do we need this?
            operator=expression.operator,
            left=NormalVariableExpression(variable=left_variable),
            right=NormalVariableExpression(variable=right_variable),
        ),
    )

    while len(stack) > 0:
        right_operator, right_order, right_expression = stack.pop()
        and_right_expression = parsing.FurInfixExpression(
            operator=right_operator,
            order=right_order,
            left=NormalVariableExpression(variable=right_variable),
            right=right_expression,
        )

        and_expression = parsing.FurInfixExpression(
            operator='and',
            order='and_level',
            left=result_expression,
            right=and_right_expression,
        )

        counter, and_prestatements, result_expression = normalize_boolean_expression(
            counter,
            and_expression,
        )

        result_prestatements = result_prestatements + and_prestatements

    return (counter, result_prestatements, result_expression)

def normalize_boolean_expression(counter, expression):
    # TODO Unfake this
    return fake_normalization(counter, expression)

def normalize_infix_expression(counter, expression):
    return {
        'multiplication_level': normalize_basic_infix_operation,
        'addition_level': normalize_basic_infix_operation,
        'comparison_level': normalize_comparison_expression,
        'and_level': normalize_boolean_expression,
        'or_level': normalize_boolean_expression,
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
