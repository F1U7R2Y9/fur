import collections

import desugaring
import util

NormalBuiltinExpression = collections.namedtuple(
    'NormalBuiltinExpression',
    (
        'symbol',
    ),
)

NormalVariableExpression = collections.namedtuple(
    'NormalVariableExpression',
    [
        'variable',
    ],
)

NormalIntegerLiteralExpression = collections.namedtuple(
    'NormalIntegerLiteralExpression',
    [
        'integer',
    ],
)

NormalLambdaExpression = collections.namedtuple(
    'NormalLambdaExpression',
    (
        'name',
        'argument_name_list',
        'statement_list',
    ),
)

NormalStringLiteralExpression = collections.namedtuple(
    'NormalStringLiteralExpression',
    [
        'string',
    ],
)

NormalSymbolExpression = collections.namedtuple(
    'NormalSymbolExpression',
    (
        'symbol',
    ),
)

NormalSymbolLiteralExpression = collections.namedtuple(
    'NormalSymbolLiteralExpression',
    (
        'symbol',
    ),
)

NormalPushStatement = collections.namedtuple(
    'NormalPushStatement',
    (
        'expression',
    ),
)

NormalFunctionCallExpression = collections.namedtuple(
    'NormalFunctionCallExpression',
    [
        'metadata',
        'function_expression',
        'argument_count',
    ],
)

NormalVariableInitializationStatement = collections.namedtuple(
    'NormalVariableInitializationStatement',
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

NormalAssignmentStatement = collections.namedtuple(
    'NormalAssignmentStatement',
    [
        'target',
        'expression',
    ],
)

NormalIfElseExpression = collections.namedtuple(
    'NormalIfElseExpression',
    [
        'condition_expression',
        'if_statement_list',
        'else_statement_list',
    ],
)

NormalProgram = collections.namedtuple(
    'NormalProgram',
    [
        'statement_list',
    ],
)

def normalize_builtin_expression(counter, expression):
    return (
        counter,
        (),
        NormalBuiltinExpression(symbol=expression.symbol),
    )

def normalize_integer_literal_expression(counter, expression):
    return (
        counter,
        (),
        NormalIntegerLiteralExpression(integer=expression.integer),
    )

def normalize_lambda_expression(counter, expression):
    variable = '${}'.format(counter)

    _, statement_list = normalize_statement_list(
        0,
        expression.statement_list,
    )

    return (
        counter + 1,
        (
            NormalVariableInitializationStatement(
                variable=variable,
                expression=NormalLambdaExpression(
                    name=expression.name,
                    argument_name_list=expression.argument_name_list,
                    statement_list=statement_list,
                ),
            ),
        ),
        NormalVariableExpression(variable=variable),
    )

NormalListConstructExpression = collections.namedtuple(
    'NormalListConstructExpression',
    [
        'allocate',
    ],
)

def normalize_list_literal_expression(counter, expression):
    list_variable = '${}'.format(counter)
    counter += 1

    prestatements = []

    for item_expression in expression.item_expression_list:
        counter, item_expression_prestatements, normalized = normalize_expression(
            counter,
            item_expression,
        )

        for p in item_expression_prestatements:
            prestatements.append(p)

        prestatements.append(
            NormalPushStatement(
                expression=normalized,
            )
        )

    return (
        counter,
        tuple(prestatements),
        NormalListConstructExpression(allocate=len(expression.item_expression_list)),
    )

def normalize_string_literal_expression(counter, expression):
    return (
        counter,
        (),
        NormalStringLiteralExpression(string=expression.string),
    )

NormalStructureLiteralExpression = collections.namedtuple(
    'NormalStructureLiteralExpression',
    (
        'field_count',
    ),
)

def normalize_structure_literal_expression(counter, expression):
    prestatements = []

    for field in expression.fields:
        counter, field_expression_prestatements, field_expression = normalize_expression(
            counter,
            field.expression,
        )

        for p in field_expression_prestatements:
            prestatements.append(p)

        prestatements.append(NormalPushStatement(
            expression=field_expression,
        ))

        prestatements.append(NormalPushStatement(
            expression=NormalSymbolLiteralExpression(
                symbol=field.symbol,
            ),
        ))

    return (
        counter,
        tuple(prestatements),
        NormalStructureLiteralExpression(
            field_count=len(expression.fields),
        ),
    )

def normalize_symbol_expression(counter, expression):
    return (
        counter,
        (),
        NormalSymbolExpression(symbol=expression.symbol),
    )

def normalize_function_call_expression(counter, expression):
    prestatements = []

    for argument in expression.argument_list:
        counter, argument_prestatements, normalized_argument = normalize_expression(counter, argument)

        for s in argument_prestatements:
            prestatements.append(s)

        prestatements.append(
            NormalPushStatement(
                expression=normalized_argument,
            ),
        )

    counter, function_prestatements, function_expression = normalize_expression(
        counter,
        expression.function,
    )

    for ps in function_prestatements:
        prestatements.append(ps)

    return (
        counter,
        tuple(prestatements),
        NormalFunctionCallExpression(
            metadata=expression.metadata,
            function_expression=function_expression,
            argument_count=len(expression.argument_list),
        ),
    )

def normalize_if_expression(counter, expression):
    counter, condition_prestatements, condition_expression = normalize_expression(
        counter,
        expression.condition_expression,
    )

    counter, if_statement_list = normalize_statement_list(
        counter,
        expression.if_statement_list,
    )
    counter, else_statement_list = normalize_statement_list(
        counter,
        expression.else_statement_list,
    )

    return (
        counter,
        condition_prestatements,
        NormalIfElseExpression(
            condition_expression=condition_expression,
            if_statement_list=if_statement_list,
            else_statement_list=else_statement_list,
        ),
    )

def normalize_expression(counter, expression):
    return {
        desugaring.DesugaredBuiltinExpression: normalize_builtin_expression,
        desugaring.DesugaredFunctionCallExpression: normalize_function_call_expression,
        desugaring.DesugaredIfExpression: normalize_if_expression,
        desugaring.DesugaredIntegerLiteralExpression: normalize_integer_literal_expression,
        desugaring.DesugaredLambdaExpression: normalize_lambda_expression,
        desugaring.DesugaredListLiteralExpression: normalize_list_literal_expression,
        desugaring.DesugaredStringLiteralExpression: normalize_string_literal_expression,
        desugaring.DesugaredStructureLiteralExpression: normalize_structure_literal_expression,
        desugaring.DesugaredSymbolExpression: normalize_symbol_expression,
    }[type(expression)](counter, expression)

def normalize_expression_statement(counter, statement):
    # TODO Normalized will be a NormalVariableExpression, which will go unused
    # for expression statements in every case except when it's a return
    # statement. This cases warnings on C compilation. We should only generate
    # this variable when it will be used on return.
    counter, prestatements, normalized = normalize_expression(counter, statement.expression)

    return (
        counter,
        prestatements,
        NormalExpressionStatement(expression=normalized),
    )

def normalize_assignment_statement(counter, statement):
    counter, prestatements, normalized_expression = normalize_expression(counter, statement.expression)
    return (
        counter,
        prestatements,
        NormalAssignmentStatement(
            target=statement.target,
            expression=normalized_expression,
        ),
    )

def normalize_statement(counter, statement):
    return {
        desugaring.DesugaredAssignmentStatement: normalize_assignment_statement,
        desugaring.DesugaredExpressionStatement: normalize_expression_statement,
    }[type(statement)](counter, statement)

@util.force_generator(tuple)
def normalize_statement_list(counter, statement_list):
    result_statement_list = []

    for statement in statement_list:
        counter, prestatements, normalized = normalize_statement(counter, statement)
        for s in prestatements:
            result_statement_list.append(s)
        result_statement_list.append(normalized)

    return (
        counter,
        result_statement_list,
    )

def normalize(program):
    _, statement_list = normalize_statement_list(0, program.statement_list)

    return NormalProgram(
        statement_list=statement_list,
    )
