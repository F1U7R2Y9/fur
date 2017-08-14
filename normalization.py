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
        'function_expression',
        'argument_count',
        'argument_items',
    ],
)

NormalArrayVariableInitializationStatement = collections.namedtuple(
    'NormalArrayVariableInitializationStatement',
    [
        'variable',
        'items',
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
        'if_statements',
        'else_statements',
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
    return (
        counter,
        (),
        NormalIntegerLiteralExpression(integer=expression.integer),
    )

def normalize_string_literal_expression(counter, expression):
    return (
        counter,
        (),
        NormalStringLiteralExpression(string=expression.string),
    )

def normalize_symbol_expression(counter, expression):
    variable = '${}'.format(counter)
    return (
        counter + 1,
        (NormalVariableInitializationStatement(
            variable=variable,
            expression=NormalSymbolExpression(symbol=expression.symbol),
        ),),
        NormalVariableExpression(variable=variable),
    )

def normalize_function_call_expression(counter, expression):
    assert isinstance(expression, parsing.FurFunctionCallExpression)

    prestatements = []
    arguments = []

    for argument in expression.arguments:
        counter, argument_prestatements, normalized_argument = normalize_expression(counter, argument)

        for s in argument_prestatements:
            prestatements.append(s)

        variable = '${}'.format(counter)
        prestatements.append(NormalVariableInitializationStatement(
            variable=variable,
            expression=normalized_argument,
        ))
        arguments.append(NormalVariableExpression(
            variable=variable,
        ))
        counter += 1

    arguments_variable = '${}'.format(counter)
    counter += 1

    prestatements.append(NormalArrayVariableInitializationStatement(
        variable=arguments_variable,
        items=tuple(arguments),
    ))

    counter, function_prestatements, function_expression = normalize_expression(
        counter,
        expression.function,
    )

    for ps in function_prestatements:
        prestatements.append(ps)

    if not isinstance(function_expression, NormalVariableExpression):
        function_variable = '${}'.format(counter)

        prestatements.append(NormalVariableInitializationStatement(
            variable=function_variable,
            expression=function_expression,
        ))

        function_expression = NormalVariableExpression(variable=function_variable)
        counter += 1

    return (
        counter,
        tuple(prestatements),
        NormalFunctionCallExpression(
            function_expression=function_expression,
            argument_count=len(arguments),
            argument_items=NormalVariableExpression(variable=arguments_variable),
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
        NormalVariableInitializationStatement(
            variable=left_variable,
            expression=left_expression,
        ),
        NormalVariableInitializationStatement(
            variable=right_variable,
            expression=right_expression,
        ),
    )

    return (
        counter,
        left_prestatements + right_prestatements + root_prestatements,
        NormalInfixExpression(
            order=expression.order,
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
    if_else_prestatment = NormalVariableInitializationStatement(variable=result_variable, expression=left_expression)
    counter += 1

    condition_expression=NormalVariableExpression(variable=result_variable)
    short_circuited_statements = right_prestatements + (NormalVariableReassignmentStatement(variable=result_variable, expression=right_expression),)

    if expression.operator == 'and':
        if_else_statement = NormalIfElseStatement(
            condition_expression=condition_expression,
            if_statements=short_circuited_statements,
            else_statements=(),
        )

    elif expression.operator == 'or':
        if_else_statement = NormalIfElseStatement(
            condition_expression=condition_expression,
            if_statements=(),
            else_statements=short_circuited_statements,
        )

    else:
        raise Exception('Unable to handle operator "{}"'.format(expression.operator))

    return (
        counter,
        left_prestatements + (if_else_prestatment, if_else_statement),
        NormalVariableExpression(variable=result_variable),
    )


def normalize_infix_expression(counter, expression):
    return {
        'multiplication_level': normalize_basic_infix_operation,
        'addition_level': normalize_basic_infix_operation,
        'comparison_level': normalize_comparison_expression,
        'and_level': normalize_boolean_expression,
        'or_level': normalize_boolean_expression,
    }[expression.order](counter, expression)

def normalize_negation_expression(counter, expression):
    counter, prestatements, internal_expression = normalize_expression(counter, expression.value)

    internal_variable = '${}'.format(counter)
    counter += 1

    return (
        counter,
        prestatements + (NormalVariableInitializationStatement(variable=internal_variable, expression=internal_expression),),
        NormalNegationExpression(internal_expression=NormalVariableExpression(variable=internal_variable)),
    )

def normalize_expression(counter, expression):
    return {
        NormalInfixExpression: fake_normalization,
        NormalVariableExpression: fake_normalization,
        parsing.FurFunctionCallExpression: normalize_function_call_expression,
        parsing.FurInfixExpression: normalize_infix_expression,
        parsing.FurIntegerLiteralExpression: normalize_integer_literal_expression,
        parsing.FurNegationExpression: normalize_negation_expression,
        parsing.FurStringLiteralExpression: normalize_string_literal_expression,
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
    return (
        counter,
        (),
        NormalFunctionDefinitionStatement(
            name=statement.name,
            argument_name_list=statement.argument_name_list,
            statement_list=normalize_statement_list(statement.statement_list),
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
def normalize_statement_list(statement_list):
    counter = 0

    for statement in statement_list:
        counter, prestatements, normalized = normalize_statement(counter, statement)
        for s in prestatements:
            yield s
        yield normalized

def normalize(program):
    return NormalProgram(
        statement_list=normalize_statement_list(program.statement_list),
    )
