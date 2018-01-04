import collections

import normalization

CPSFunctionCallExpression = collections.namedtuple(
    'CPSFunctionCallExpression',
    (
        'metadata',
        'function_expression',
        'argument_count',
    ),
)

CPSIntegerLiteralExpression = collections.namedtuple(
    'CPSIntegerLiteralExpression',
    (
        'integer',
    ),
)

CPSListConstructExpression = collections.namedtuple(
    'CPSListConstructExpression',
    (
        'allocate',
    ),
)

CPSStringLiteralExpression = collections.namedtuple(
    'CPSStringLiteralExpression',
    (
        'string',
    ),
)

CPSStructureLiteralExpression = collections.namedtuple(
    'CPSStructureLiteralExpression',
    (
        'field_count',
        'symbol_list_variable',
        'value_list_variable',
    ),
)

CPSSymbolExpression = collections.namedtuple(
    'CPSSymbolExpression',
    (
        'symbol',
    ),
)

CPSVariableExpression = collections.namedtuple(
    'CPSVariableExpression',
    (
        'variable',
    ),
)

CPSArrayVariableInitializationStatement = collections.namedtuple(
    'CPSArrayVariableInitializationStatement',
    (
        'variable',
        'items',
    ),
)

CPSAssignmentStatement = collections.namedtuple(
    'CPSAssignmentStatement',
    (
        'target',
        'expression',
    ),
)

CPSExpressionStatement = collections.namedtuple(
    'CPSExpressionStatement',
    (
        'expression',
    ),
)

CPSFunctionDefinitionStatement = collections.namedtuple(
    'CPSFunctionDefinitionStatement',
    (
        'name',
        'argument_name_list',
        'statement_list',
    )
)

CPSIfElseStatement = collections.namedtuple(
    'CPSIfElseStatement',
    (
        'condition_expression',
        'if_statement_list',
        'else_statement_list',
    ),
)

CPSListAppendStatement = collections.namedtuple(
    'CPSListAppendStatement',
    (
        'list_expression',
        'item_expression',
    ),
)

CPSPushStatement = collections.namedtuple(
    'CPSPushStatement',
    (
        'expression',
    ),
)

CPSVariableInitializationStatement = collections.namedtuple(
    'CPSVariableInitializationStatement',
    (
        'variable',
        'expression',
    ),
)

CPSSymbolArrayVariableInitializationStatement = collections.namedtuple(
    'CPSSymbolArrayVariableInitializationStatement',
    (
        'variable',
        'symbol_list',
    ),
)

CPSVariableReassignmentStatement = collections.namedtuple(
    'CPSVariableReassignmentStatement',
    (
        'variable',
        'expression',
    ),
)

CPSProgram = collections.namedtuple(
    'CPSProgram',
    (
        'statement_list',
    ),
)

def convert_function_call_expression(expression):
    return CPSFunctionCallExpression(
        metadata=expression.metadata,
        function_expression=convert_expression(expression.function_expression),
        argument_count=expression.argument_count,
    )

def convert_integer_literal_expression(expression):
    return CPSIntegerLiteralExpression(integer=expression.integer)

def convert_list_construct_expression(expression):
    return CPSListConstructExpression(allocate=expression.allocate)

def convert_string_literal_expression(expression):
    return CPSStringLiteralExpression(string=expression.string)

def convert_structure_literal_expression(expression):
    return CPSStructureLiteralExpression(
        field_count=expression.field_count,
        symbol_list_variable=expression.symbol_list_variable,
        value_list_variable=expression.value_list_variable,
    )

def convert_symbol_expression(expression):
    return CPSSymbolExpression(symbol=expression.symbol)

def convert_variable_expression(expression):
    return CPSVariableExpression(variable=expression.variable)

def convert_expression(expression):
    return {
        normalization.NormalFunctionCallExpression: convert_function_call_expression,
        normalization.NormalIntegerLiteralExpression: convert_integer_literal_expression,
        normalization.NormalListConstructExpression: convert_list_construct_expression,
        normalization.NormalStringLiteralExpression: convert_string_literal_expression,
        normalization.NormalStructureLiteralExpression: convert_structure_literal_expression,
        normalization.NormalSymbolExpression: convert_symbol_expression,
        normalization.NormalVariableExpression: convert_variable_expression,
    }[type(expression)](expression)

def convert_array_variable_initialization_statement(statement):
    return CPSArrayVariableInitializationStatement(
        variable=statement.variable,
        items=tuple(convert_expression(e) for e in statement.items),
    )

def convert_assignment_statement(statement):
    return CPSAssignmentStatement(
        target=statement.target,
        expression=convert_expression(statement.expression),
    )

def convert_expression_statement(statement):
    return CPSExpressionStatement(
        expression=convert_expression(statement.expression),
    )

def convert_function_definition_statement(statement):
    return CPSFunctionDefinitionStatement(
        name=statement.name,
        argument_name_list=statement.argument_name_list,
        statement_list=tuple(convert_statement(s) for s in statement.statement_list),
    )

def convert_if_else_statement(statement):
    return CPSIfElseStatement(
        condition_expression=convert_expression(statement.condition_expression),
        if_statement_list=tuple(convert_statement(s) for s in statement.if_statement_list),
        else_statement_list=tuple(convert_statement(s) for s in statement.else_statement_list),
    )

def convert_list_append_statement(statement):
    return CPSListAppendStatement(
        list_expression=convert_expression(statement.list_expression),
        item_expression=convert_expression(statement.item_expression),
    )


def convert_push_statement(statement):
    return CPSPushStatement(
        expression=convert_expression(statement.expression),
    )

def convert_variable_initialization_statement(statement):
    return CPSVariableInitializationStatement(
        variable=statement.variable,
        expression=convert_expression(statement.expression),
    )

def convert_variable_reassignment_statement(statement):
    return CPSVariableReassignmentStatement(
        variable=statement.variable,
        expression=convert_expression(statement.expression),
    )

def convert_symbol_array_variable_initialization_statement(statement):
    return CPSSymbolArrayVariableInitializationStatement(
        variable=statement.variable,
        symbol_list=statement.symbol_list,
    )

def convert_statement(statement):
    return {
        normalization.NormalArrayVariableInitializationStatement: convert_array_variable_initialization_statement,
        normalization.NormalAssignmentStatement: convert_assignment_statement,
        normalization.NormalExpressionStatement: convert_expression_statement,
        normalization.NormalFunctionDefinitionStatement: convert_function_definition_statement,
        normalization.NormalIfElseStatement: convert_if_else_statement,
        normalization.NormalListAppendStatement: convert_list_append_statement,
        normalization.NormalPushStatement: convert_push_statement,
        normalization.NormalVariableInitializationStatement: convert_variable_initialization_statement,
        normalization.NormalVariableReassignmentStatement: convert_variable_reassignment_statement,
        normalization.NormalSymbolArrayVariableInitializationStatement: convert_symbol_array_variable_initialization_statement,
    }[type(statement)](statement)

def convert(program):
    return CPSProgram(
        statement_list=tuple(convert_statement(s) for s in program.statement_list),
    )
