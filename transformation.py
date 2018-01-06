import collections

import conversion

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

CStructureLiteralExpression = collections.namedtuple(
    'CStructureLiteralExpression',
    [
        'field_count',
        'symbol_list_variable',
        'value_list_variable',
    ],
)

CPushStatement = collections.namedtuple(
    'CPushStatement',
    (
        'expression',
    ),
)

CFunctionCallExpression = collections.namedtuple(
    'CFunctionCallExpression',
    (
        'metadata',
        'function_expression',
        'argument_count',
    ),
)

# TODO We are currently not changing variables, just preventing them from being accessed.
CSymbolAssignmentStatement = collections.namedtuple(
    'CSymbolAssignmentStatement',
    [
        'target',
        'target_symbol_list_index',
        'expression',
    ],
)

CArrayVariableInitializationStatement = collections.namedtuple(
    'CArrayVariableInitializationStatement',
    [
        'variable',
        'items',
    ],
)

CSymbolArrayVariableInitializationStatement = collections.namedtuple(
    'CSymbolArrayVariableInitializationStatement',
    [
        'variable',
        'symbol_list',
        'symbol_list_indices',
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
        'if_statement_list',
        'else_statement_list',
    ],
)

# TODO If a function definition doesn't end with an expression, we have issues currently because we try to return statement.
# TODO Closures currently wrap entire defining environment, even symbols that are not used, which makes garbage collection ineffective.
CFunctionDefinition = collections.namedtuple(
    'CFunctionDefinition',
    [
        'name',
        'index',
        'argument_name_list',
        'statement_list',
    ],
)

CProgram = collections.namedtuple(
    'CProgram',
    [
        'builtin_set',
        'function_definition_list',
        'operator_declarations',
        'statements',
        'standard_libraries',
        'string_literal_list',
        'symbol_list',
    ],
)

BUILTINS = {
    'concatenate':      [],
    'false':            [],
    'pow':              ['math.h'],
    'print':            ['stdio.h'],
    'true':             [],
}

def transform_variable_expression(accumulators, expression):
    assert isinstance(expression, conversion.CPSVariableExpression)
    return CVariableExpression(variable=expression.variable)

def transform_string_literal_expression(accumulators, expression):
    value = expression.string

    try:
        index = accumulators.string_literal_list.index(value)
    except ValueError:
        index = len(accumulators.string_literal_list)
        accumulators.string_literal_list.append(value)

    return CStringLiteral(index=index, value=value)

def transform_symbol_expression(accumulators, expression):
    if expression.symbol in BUILTINS:
        accumulators.builtin_set.add(expression.symbol)

    try:
        symbol_list_index = accumulators.symbol_list.index(expression.symbol)
    except ValueError:
        symbol_list_index = len(accumulators.symbol_list)
        accumulators.symbol_list.append(expression.symbol)

    return CSymbolExpression(
        symbol=expression.symbol,
        symbol_list_index=symbol_list_index,
    )

def transform_integer_literal_expression(accumulators, expression):
    return CIntegerLiteral(value=expression.integer)

CListConstructExpression = collections.namedtuple(
    'CListConstructExpression',
    (
        'allocate',
    ),
)

CLambdaExpression = collections.namedtuple(
    'CLambdaExpression',
    (
        'name',
        'index',
    ),
)

CListAppendStatement = collections.namedtuple(
    'CListAppendStatement',
    (
        'list_expression',
        'item_expression',
    ),
)

def transform_structure_literal_expression(accumulators, expression):
    return CStructureLiteralExpression(
        field_count=expression.field_count,
        symbol_list_variable=expression.symbol_list_variable,
        value_list_variable=expression.value_list_variable,
    )

def transform_lambda_expression(accumulators, expression):
    if expression.name is None:
        name = '__lambda'
    else:
        name = expression.name

    index = accumulators.function_name_iterators.get(name, 0)
    accumulators.function_name_iterators[name] = index + 1

    accumulators.function_definition_list.append(CFunctionDefinition(
        name=name,
        index=index,
        argument_name_list=expression.argument_name_list,
        statement_list=tuple(transform_statement(accumulators, s) for s in expression.statement_list),
    ))

    return CLambdaExpression(
        name=name,
        index=index,
    )


def transform_list_construct_expression(accumulators, expression):
    return CListConstructExpression(allocate=expression.allocate)

def transform_list_append_statement(accumulators, expression):
    return CListAppendStatement(
        list_expression=transform_expression(accumulators, expression.list_expression),
        item_expression=transform_expression(accumulators, expression.item_expression),
    )

def transform_expression(accumulators, expression):
    return {
        conversion.CPSFunctionCallExpression: transform_function_call_expression,
        conversion.CPSIntegerLiteralExpression: transform_integer_literal_expression,
        conversion.CPSLambdaExpression: transform_lambda_expression,
        conversion.CPSListConstructExpression: transform_list_construct_expression,
        conversion.CPSStructureLiteralExpression: transform_structure_literal_expression,
        conversion.CPSStringLiteralExpression: transform_string_literal_expression,
        conversion.CPSSymbolExpression: transform_symbol_expression,
        conversion.CPSVariableExpression: transform_variable_expression,
    }[type(expression)](accumulators, expression)

def transform_symbol_assignment_statement(accumulators, assignment_statement):
    # TODO Check that target is not a builtin
    try:
        symbol_list_index = accumulators.symbol_list.index(assignment_statement.target)
    except ValueError:
        symbol_list_index = len(accumulators.symbol_list)
        accumulators.symbol_list.append(assignment_statement.target)

    return CSymbolAssignmentStatement(
        target=assignment_statement.target,
        target_symbol_list_index=symbol_list_index,
        expression=transform_expression(
            accumulators,
            assignment_statement.expression,
        ),
    )

def transform_function_call_expression(accumulators, function_call):
    # TODO Use the symbol from SYMBOL LIST
    return CFunctionCallExpression(
        metadata=function_call.metadata,
        function_expression=transform_expression(accumulators, function_call.function_expression),
        argument_count=function_call.argument_count,
    )

def transform_expression_statement(accumulators, statement):
    return CExpressionStatement(
        expression=transform_expression(accumulators, statement.expression),
    )

def transform_if_else_statement(accumulators, statement):
    return CIfElseStatement(
        condition_expression=transform_expression(accumulators, statement.condition_expression),
        if_statement_list=tuple(transform_statement(accumulators, s) for s in statement.if_statement_list),
        else_statement_list=tuple(transform_statement(accumulators, s) for s in statement.else_statement_list),
    )

def transform_array_variable_initialization_statement(accumulators, statement):
    return CArrayVariableInitializationStatement(
        variable=statement.variable,
        items=tuple(transform_expression(accumulators, i) for i in statement.items),
    )

def transform_symbol_array_variable_initialization_statement(accumulators, statement):
    symbol_list_indices = []

    for symbol in statement.symbol_list:
        try:
            symbol_list_index = accumulators.symbol_list.index(symbol)
        except ValueError:
            symbol_list_index = len(accumulators.symbol_list)
            accumulators.symbol_list.append(symbol)

        symbol_list_indices.append(symbol_list_index)

    return CSymbolArrayVariableInitializationStatement(
        variable=statement.variable,
        symbol_list=statement.symbol_list,
        symbol_list_indices=tuple(symbol_list_indices),
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

def transform_push_statement(accumulators, statement):
    return CPushStatement(expression=transform_expression(accumulators, statement.expression))

def transform_statement(accumulators, statement):
    return {
        conversion.CPSArrayVariableInitializationStatement: transform_array_variable_initialization_statement,
        conversion.CPSAssignmentStatement: transform_symbol_assignment_statement,
        conversion.CPSExpressionStatement: transform_expression_statement,
        conversion.CPSIfElseStatement: transform_if_else_statement,
        conversion.CPSListAppendStatement: transform_list_append_statement,
        conversion.CPSPushStatement: transform_push_statement,
        conversion.CPSSymbolArrayVariableInitializationStatement: transform_symbol_array_variable_initialization_statement,
        conversion.CPSVariableInitializationStatement: transform_variable_initialization_statement,
        conversion.CPSVariableReassignmentStatement: transform_variable_reassignment_statement,
    }[type(statement)](accumulators, statement)


Accumulators = collections.namedtuple(
    'Accumulators',
    [
        'builtin_set',
        'function_definition_list',
        'function_name_iterators',
        'operator_set',
        'symbol_list',
        'string_literal_list',
    ],
)

def transform(program):
    accumulators = Accumulators(
        builtin_set=set(),
        function_definition_list=[],
        function_name_iterators={},
        operator_set=set(),
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
        function_definition_list=accumulators.function_definition_list,
        operator_declarations=tuple(sorted(accumulators.operator_set)),
        statements=statement_list,
        standard_libraries=standard_library_set,
        string_literal_list=accumulators.string_literal_list,
        symbol_list=accumulators.symbol_list,
    )


if __name__ == '__main__':
    import unittest

    unittest.main()
