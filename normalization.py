import collections

import parsing

NormalVariableExpression = collections.namedtuple(
    'NormalVariableExpression',
    [
        'variable',
    ],
)

NormalVariableAssignmentStatement = collections.namedtuple(
    'NormalVariableAssignmentStatement',
    [
        'variable',
        'expression',
    ],
)

NormalFunctionCallExpression = collections.namedtuple(
    'NormalFunctionCallExpression',
    [
        'function',
        'arguments',
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

def normalize_function_call_expression(counter, expression):
    prestatements = []
    arguments = []

    for argument in expression.arguments:
        variable = '${}'.format(counter)
        prestatements.append(NormalVariableAssignmentStatement(
            variable=variable,
            expression=argument, # TODO Normalize each argument
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

def normalize_statement(counter, statement):
    if isinstance(statement, parsing.FurExpressionStatement):
        counter, prestatements, normalized = {
            parsing.FurFunctionCallExpression: normalize_function_call_expression,
        }[type(statement.expression)](counter, statement.expression)

        return (
            counter,
            prestatements,
            NormalExpressionStatement(expression=normalized),
        )

    return (counter, (), statement)

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
