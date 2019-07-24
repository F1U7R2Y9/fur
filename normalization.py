import collections

import desugaring
import util

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
    [
        'symbol',
    ],
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

NormalArrayVariableInitializationStatement = collections.namedtuple(
    'NormalArrayVariableInitializationStatement',
    [
        'variable',
        'items',
    ],
)

NormalSymbolArrayVariableInitializationStatement = collections.namedtuple(
    'NormalSymbolArrayVariableInitializationStatement',
    [
        'variable',
        'symbol_list',
    ],
)

NormalVariableInitializationStatement = collections.namedtuple(
    'NormalVariableInitializationStatement',
    [
        'variable',
        'expression',
    ],
)

NormalVariableReassignmentStatement = collections.namedtuple(
    'NormalVariableReassignmentStatement',
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

NormalIfElseStatement = collections.namedtuple(
    'NormalIfElseStatement',
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

def normalize_integer_literal_expression(counter, expression):
    variable = '${}'.format(counter)
    return (
        counter + 1,
        (
            NormalVariableInitializationStatement(
                variable=variable,
                expression=NormalIntegerLiteralExpression(integer=expression.integer),
            ),
        ),
        NormalVariableExpression(variable=variable),
    )

def normalize_lambda_expression(counter, expression):
    variable = '${}'.format(counter)

    _, statement_list = normalize_statement_list(
        0,
        expression.statement_list,
        assign_result_to='result',
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

NormalListAppendStatement = collections.namedtuple(
    'NormalListAppendStatement',
    [
        'list_expression',
        'item_expression',
    ],
)

def normalize_list_literal_expression(counter, expression):
    list_variable = '${}'.format(counter)
    counter += 1

    prestatements = [
        NormalVariableInitializationStatement(
            variable=list_variable,
            expression=NormalListConstructExpression(allocate=len(expression.item_expression_list)),
        ),
    ]

    list_expression = NormalVariableExpression(variable=list_variable)

    for item_expression in expression.item_expression_list:
        counter, item_expression_prestatements, normalized = normalize_expression(
            counter,
            item_expression,
        )

        for p in item_expression_prestatements:
            prestatements.append(p)

        prestatements.append(
            NormalListAppendStatement(
                list_expression=list_expression,
                item_expression=normalized,
            )
        )

    return (
        counter,
        tuple(prestatements),
        list_expression,
    )

def normalize_string_literal_expression(counter, expression):
    return (
        counter,
        (),
        NormalStringLiteralExpression(string=expression.string),
    )

NormalStructureLiteralExpression = collections.namedtuple(
    'NormalStructureLiteralExpression',
    [
        'field_count',
        'symbol_list_variable',
        'value_list_variable',
    ],
)

def normalize_structure_literal_expression(counter, expression):
    prestatements = []
    field_symbol_array = []
    field_value_array = []

    for symbol_expression_pair in expression.fields:
        counter, field_prestatements, field_expression = normalize_expression(
            counter,
            symbol_expression_pair.expression,
        )

        for p in field_prestatements:
            prestatements.append(p)

        field_symbol_array.append(symbol_expression_pair.symbol)
        field_value_array.append(field_expression)

    symbol_array_variable = '${}'.format(counter)
    counter += 1

    prestatements.append(
        NormalSymbolArrayVariableInitializationStatement(
            variable=symbol_array_variable,
            symbol_list=tuple(field_symbol_array),
        )
    )

    value_array_variable = '${}'.format(counter)
    counter += 1

    prestatements.append(
        NormalArrayVariableInitializationStatement(
            variable=value_array_variable,
            items=tuple(field_value_array),
        )
    )

    variable = '${}'.format(counter)

    prestatements.append(
        NormalVariableInitializationStatement(
            variable=variable,
            expression=NormalStructureLiteralExpression(
                field_count=len(expression.fields),
                symbol_list_variable=symbol_array_variable,
                value_list_variable=value_array_variable,
            ),
        )
    )

    return (
        counter + 1,
        tuple(prestatements),
        NormalVariableExpression(variable=variable),
    )


def normalize_symbol_expression(counter, expression):
    variable = '${}'.format(counter)
    return (
        counter + 1,
        (
            NormalVariableInitializationStatement(
                variable=variable,
                expression=NormalSymbolExpression(symbol=expression.symbol),
            ),
        ),
        NormalVariableExpression(variable=variable),
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

    if not isinstance(function_expression, NormalVariableExpression):
        function_variable = '${}'.format(counter)

        prestatements.append(
            NormalVariableInitializationStatement(
                variable=function_variable,
                expression=function_expression,
            )
        )

        function_expression = NormalVariableExpression(variable=function_variable)
        counter += 1

    result_variable = '${}'.format(counter)

    prestatements.append(
        NormalVariableInitializationStatement(
            variable=result_variable,
            expression=NormalFunctionCallExpression(
                metadata=expression.metadata,
                function_expression=function_expression,
                argument_count=len(expression.argument_list),
            ),
        )
    )

    return (
        counter + 1,
        tuple(prestatements),
        NormalVariableExpression(variable=result_variable),
    )

def normalize_if_expression(counter, expression):
    counter, condition_prestatements, condition_expression = normalize_expression(
        counter,
        expression.condition_expression,
    )

    result_variable = '${}'.format(counter)
    counter += 1

    counter, if_statement_list = normalize_statement_list(
        counter,
        expression.if_statement_list,
        assign_result_to=result_variable,
    )
    counter, else_statement_list = normalize_statement_list(
        counter,
        expression.else_statement_list,
        assign_result_to=result_variable,
    )

    return (
        counter,
        condition_prestatements + (
            NormalVariableInitializationStatement(
                variable=result_variable,
                expression=NormalVariableExpression(variable='builtin$nil'),
            ),
            NormalIfElseStatement(
                condition_expression=condition_expression,
                if_statement_list=if_statement_list,
                else_statement_list=else_statement_list,
            ),
        ),
        NormalVariableExpression(variable=result_variable),
    )

def normalize_expression(counter, expression):
    return {
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
def normalize_statement_list(counter, statement_list, **kwargs):
    assign_result_to = kwargs.pop('assign_result_to', None)

    assert len(kwargs) == 0

    result_statement_list = []

    for statement in statement_list:
        counter, prestatements, normalized = normalize_statement(counter, statement)
        for s in prestatements:
            result_statement_list.append(s)
        result_statement_list.append(normalized)

    # TODO The way we fix the last statement is really confusing
    last_statement = result_statement_list[-1]

    if isinstance(last_statement, NormalExpressionStatement) and isinstance(last_statement.expression, NormalVariableExpression):
        if assign_result_to is not None:
            result_expression = result_statement_list.pop().expression
            result_statement_list.append(
                NormalVariableReassignmentStatement(
                    variable=assign_result_to,
                    expression=result_expression,
                )
            )

    return (
        counter,
        result_statement_list,
    )

def normalize(program):
    _, statement_list = normalize_statement_list(0, program.statement_list)

    return NormalProgram(
        statement_list=statement_list,
    )
