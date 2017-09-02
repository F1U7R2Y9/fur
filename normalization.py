import collections

import parsing
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

NormalNegationExpression = collections.namedtuple(
    'NormalNegationExpression',
    [
        'internal_expression',
    ],
)

NormalDotExpression = collections.namedtuple(
    'NormalDotExpression',
    [
        'instance',
        'field',
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

NormalPushStatement = collections.namedtuple(
    'NormalPushStatement',
    (
        'expression',
    ),
)

NormalFunctionCallExpression = collections.namedtuple(
    'NormalFunctionCallExpression',
    [
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

NormalFunctionDefinitionStatement = collections.namedtuple(
    'NormalFunctionDefinitionStatement',
    [
        'name',
        'argument_name_list',
        'statement_list',
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

NormalListGetExpression = collections.namedtuple(
    'NormalListGetExpression',
    [
        'list_expression',
        'index_expression',
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

def normalize_list_item_expression(counter, expression):
    counter, list_prestatements, list_expression = normalize_expression(counter, expression.list_expression)
    counter, index_prestatements, index_expression = normalize_expression(counter, expression.index_expression)

    result_variable = '${}'.format(counter)
    result_prestatement = NormalVariableInitializationStatement(
        variable=result_variable,
        expression=NormalListGetExpression(
            list_expression=list_expression,
            index_expression=index_expression,
        ),
    )

    return (
        counter + 1,
        list_prestatements + index_prestatements + (result_prestatement,),
        NormalVariableExpression(variable=result_variable),
    )

def normalize_string_literal_expression(counter, expression):
    variable = '${}'.format(counter)
    return (
        counter + 1,
        (
            NormalVariableInitializationStatement(
                variable=variable,
                expression=NormalStringLiteralExpression(string=expression.string),
            ),
        ),
        NormalVariableExpression(variable=variable),
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
    assert isinstance(expression, parsing.FurFunctionCallExpression)

    prestatements = []

    for argument in expression.arguments:
        counter, argument_prestatements, normalized_argument = normalize_expression(counter, argument)

        for s in argument_prestatements:
            prestatements.append(s)

        variable = '${}'.format(counter)
        prestatements.append(
            NormalVariableInitializationStatement(
                variable=variable,
                expression=normalized_argument,
            )
        )
        prestatements.append(
            NormalPushStatement(
                expression=NormalVariableExpression(
                    variable=variable,
                ),
            ),
        )
        counter += 1

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
                function_expression=function_expression,
                argument_count=len(expression.arguments),
            ),
        )
    )

    return (
        counter + 1,
        tuple(prestatements),
        NormalVariableExpression(variable=result_variable),
    )

def normalize_basic_infix_operation(counter, expression):
    counter, left_prestatements, left_expression = normalize_expression(counter, expression.left)
    counter, right_prestatements, right_expression = normalize_expression(counter, expression.right)

    left_variable = '${}'.format(counter)
    counter += 1
    right_variable = '${}'.format(counter)
    counter += 1
    center_variable = '${}'.format(counter)
    counter += 1

    root_prestatements = (
        NormalVariableInitializationStatement(
            variable=left_variable,
            expression=left_expression,
        ),
        NormalVariableInitializationStatement(
            variable=right_variable,
            expression=right_expression,
        ),
        NormalVariableInitializationStatement(
            variable=center_variable,
            expression=NormalInfixExpression(
                order=expression.order,
                operator=expression.operator,
                left=NormalVariableExpression(variable=left_variable),
                right=NormalVariableExpression(variable=right_variable),
            ),
        ),
    )

    return (
        counter,
        left_prestatements + right_prestatements + root_prestatements,
        NormalVariableExpression(variable=center_variable),
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
        NormalVariableInitializationStatement(
            variable=left_variable,
            expression=left_expression,
        ),
        NormalVariableInitializationStatement(
            variable=right_variable,
            expression=right_expression,
        ),
    )

    counter, result_prestatements, result_expression = (
        counter,
        left_prestatements + right_prestatements + root_prestatements,
        NormalInfixExpression(
            order=expression.order,
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
    counter, left_prestatements, left_expression = normalize_expression(counter, expression.left)
    counter, right_prestatements, right_expression = normalize_expression(counter, expression.right)

    result_variable = '${}'.format(counter)
    if_else_prestatment = NormalVariableInitializationStatement(
        variable=result_variable,
        expression=left_expression,
    )
    counter += 1

    condition_expression=NormalVariableExpression(variable=result_variable)
    short_circuited_statements = right_prestatements + (NormalVariableReassignmentStatement(variable=result_variable, expression=right_expression),)

    if expression.operator == 'and':
        if_else_statement = NormalIfElseStatement(
            condition_expression=condition_expression,
            if_statement_list=short_circuited_statements,
            else_statement_list=(),
        )

    elif expression.operator == 'or':
        if_else_statement = NormalIfElseStatement(
            condition_expression=condition_expression,
            if_statement_list=(),
            else_statement_list=short_circuited_statements,
        )

    else:
        raise Exception('Unable to handle operator "{}"'.format(expression.operator))

    return (
        counter,
        left_prestatements + (if_else_prestatment, if_else_statement),
        NormalVariableExpression(variable=result_variable),
    )

def normalize_dot_expression(counter, expression):
    assert isinstance(expression.right, parsing.FurSymbolExpression)

    counter, prestatements, left_expression = normalize_expression(counter, expression.left)

    variable = '${}'.format(counter)

    dot_expression_prestatement = NormalVariableInitializationStatement(
        variable=variable,
        expression=NormalDotExpression(
            instance=left_expression,
            field=expression.right.symbol,
        ),
    )

    return (
        counter + 1,
        prestatements + (dot_expression_prestatement,),
        NormalVariableExpression(variable=variable),
    )

def normalize_infix_expression(counter, expression):
    return {
        'multiplication_level': normalize_basic_infix_operation,
        'addition_level': normalize_basic_infix_operation,
        'comparison_level': normalize_comparison_expression,
        'dot_level': normalize_dot_expression,
        'and_level': normalize_boolean_expression,
        'or_level': normalize_boolean_expression,
    }[expression.order](counter, expression)

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

def normalize_negation_expression(counter, expression):
    counter, prestatements, internal_expression = normalize_expression(counter, expression.value)

    internal_variable = '${}'.format(counter)
    counter += 1

    return (
        counter,
        prestatements + (
            NormalVariableInitializationStatement(
                variable=internal_variable,
                expression=internal_expression,
            ),
        ),
        NormalNegationExpression(internal_expression=NormalVariableExpression(variable=internal_variable)),
    )

def normalize_expression(counter, expression):
    return {
        NormalInfixExpression: fake_normalization,
        NormalVariableExpression: fake_normalization,
        parsing.FurFunctionCallExpression: normalize_function_call_expression,
        parsing.FurIfExpression: normalize_if_expression,
        parsing.FurInfixExpression: normalize_infix_expression,
        parsing.FurIntegerLiteralExpression: normalize_integer_literal_expression,
        parsing.FurListLiteralExpression: normalize_list_literal_expression,
        parsing.FurListItemExpression: normalize_list_item_expression,
        parsing.FurNegationExpression: normalize_negation_expression,
        parsing.FurStringLiteralExpression: normalize_string_literal_expression,
        parsing.FurStructureLiteralExpression: normalize_structure_literal_expression,
        parsing.FurSymbolExpression: normalize_symbol_expression,
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

def normalize_function_definition_statement(counter, statement):
    _, statement_list = normalize_statement_list(
        0,
        statement.statement_list,
        assign_result_to='result',
    )
    return (
        counter,
        (),
        NormalFunctionDefinitionStatement(
            name=statement.name,
            argument_name_list=statement.argument_name_list,
            statement_list=statement_list,
        ),
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
        parsing.FurAssignmentStatement: normalize_assignment_statement,
        parsing.FurExpressionStatement: normalize_expression_statement,
        parsing.FurFunctionDefinitionStatement: normalize_function_definition_statement,
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
