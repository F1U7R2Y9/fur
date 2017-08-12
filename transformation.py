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
        'argument_count',
        'argument_items',
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

CArrayVariableInitializationStatement = collections.namedtuple(
    'CArrayVariableInitializationStatement',
    [
        'variable',
        'items',
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

CFunctionDeclaration = collections.namedtuple(
    'CFunctionDeclaration',
    [
        'name',
    ],
)

CFunctionDefinition = collections.namedtuple(
    'CFunctionDefinition',
    [
        'name',
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
    'false':    [],
    'pow':      ['math.h'],
    'print':    ['stdio.h'],
    'true':     [],
}

def transform_variable_expression(accumulators, expression):
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
    if expression.value in ['true', 'false']:
        return CConstantExpression(value=expression.value)

    try:
        symbol_list_index = accumulators.symbol_list.index(expression.value)
    except ValueError:
        symbol_list_index = len(accumulators.symbol_list)
        accumulators.symbol_list.append(expression.value)

    return CSymbolExpression(
        symbol=expression.value,
        symbol_list_index=symbol_list_index,
    )

CInfixDeclaration = collections.namedtuple(
    'CInfixDeclaration',
    [
        'name',
        'in_type',
        'out_type',
        'operator',
    ],
)

INFIX_OPERATOR_TO_DECLARATION = {
    '+':    CInfixDeclaration(name='add', in_type='integer', out_type='integer', operator='+'),
    '-':    CInfixDeclaration(name='subtract', in_type='integer', out_type='integer', operator='-'),
    '*':    CInfixDeclaration(name='multiply', in_type='integer', out_type='integer', operator='*'),
    '//':   CInfixDeclaration(name='integerDivide', in_type='integer', out_type='integer', operator='/'),
    '%':    CInfixDeclaration(name='modularDivide', in_type='integer', out_type='integer', operator='%'),
    'and':  CInfixDeclaration(name='and', in_type='boolean', out_type='boolean', operator='&&'),
    'or':   CInfixDeclaration(name='or', in_type='boolean', out_type='boolean', operator='||'),
    '==':   CInfixDeclaration(name='equals', in_type='integer', out_type='boolean', operator='=='),
    '!=':   CInfixDeclaration(name='notEquals', in_type='integer', out_type='boolean', operator='!='),
    '<=':   CInfixDeclaration(name='lessThanOrEqual', in_type='integer', out_type='boolean', operator='<='),
    '>=':   CInfixDeclaration(name='greaterThanOrEqual', in_type='integer', out_type='boolean', operator='>='),
    '<':    CInfixDeclaration(name='lessThan', in_type='integer', out_type='boolean', operator='<'),
    '>':    CInfixDeclaration(name='greaterThan', in_type='integer', out_type='boolean', operator='>'),
}

def transform_comparison_level_expression(accumulators, expression):
    accumulators.operator_set.add(INFIX_OPERATOR_TO_DECLARATION[expression.operator])

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
                name=INFIX_OPERATOR_TO_DECLARATION[expression.operator].name,
                left=middle,
                right=right,
            ),
        )

    return CFunctionCallForFurInfixOperator(
        name=INFIX_OPERATOR_TO_DECLARATION[expression.operator].name,
        left=transform_expression(accumulators, expression.left),
        right=transform_expression(accumulators, expression.right),
    )

def transform_infix_expression(accumulators, expression):
    if expression.order == 'comparison_level':
        return transform_comparison_level_expression(accumulators, expression)

    accumulators.operator_set.add(INFIX_OPERATOR_TO_DECLARATION[expression.operator])

    return CFunctionCallForFurInfixOperator(
        name=INFIX_OPERATOR_TO_DECLARATION[expression.operator].name,
        left=transform_expression(accumulators, expression.left),
        right=transform_expression(accumulators, expression.right),
    )

def transform_integer_literal_expression(accumulators, expression):
    return CIntegerLiteral(value=expression.integer)

def transform_negation_expression(accumulators, expression):
    return CNegationExpression(
        value=transform_expression(accumulators, expression.internal_expression),
    )

def transform_expression(accumulators, expression):
    # TODO Clean up handlers for parsing expressions
    return {
        parsing.FurFunctionCallExpression: transform_function_call_expression,
        parsing.FurInfixExpression: transform_infix_expression,
        parsing.FurIntegerLiteralExpression: transform_integer_literal_expression,
        parsing.FurNegationExpression: transform_negation_expression,
        parsing.FurStringLiteralExpression: transform_string_literal_expression,
        parsing.FurSymbolExpression: transform_symbol_expression,
        normalization.NormalFunctionCallExpression: transform_function_call_expression,
        normalization.NormalInfixExpression: transform_infix_expression,
        normalization.NormalIntegerLiteralExpression: transform_integer_literal_expression,
        normalization.NormalNegationExpression: transform_negation_expression,
        normalization.NormalStringLiteralExpression: transform_string_literal_expression,
        normalization.NormalVariableExpression: transform_variable_expression,
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
    if isinstance(function_call.function, parsing.FurSymbolExpression):
        # TODO Move this check to transformation of symbol expressions so we can have builtins that aren't functions
        if function_call.function.value in BUILTINS.keys():
            # TODO Check that the builtin is actually callable
            accumulators.builtin_set.add(function_call.function.value)

    # TODO Use the symbol from SYMBOL LIST
    return CFunctionCallExpression(
        name=transform_expression(accumulators, function_call.function),
        argument_count=function_call.argument_count,
        argument_items=transform_expression(accumulators, function_call.argument_items),
    )

def transform_expression_statement(accumulators, statement):
    return CExpressionStatement(
        expression=transform_expression(accumulators, statement.expression),
    )

def transform_if_else_statement(accumulators, statement):
    return CIfElseStatement(
        condition_expression=transform_expression(accumulators, statement.condition_expression),
        if_statements=tuple(transform_statement(accumulators, s) for s in statement.if_statements),
        else_statements=tuple(transform_statement(accumulators, s) for s in statement.else_statements),
    )

def transform_array_variable_initialization_statement(accumulators, statement):
    return CArrayVariableInitializationStatement(
        variable=statement.variable,
        items=tuple(transform_expression(accumulators, i) for i in statement.items),
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

def transform_function_definition_statement(accumulators, statement):
    # TODO Allow defining the same function in different contexts
    if any(fd.name == statement.name for fd in accumulators.function_definition_list):
        raise Exception('A function with name "{}" already exists'.format(statement.name))

    # TODO Add argument names to the symbol table
    accumulators.function_definition_list.append(CFunctionDefinition(
        name=statement.name,
        argument_name_list=statement.argument_name_list,
        statement_list=tuple(transform_statement(accumulators, s) for s in statement.statement_list)
    ))

    return CFunctionDeclaration(name=statement.name)

def transform_statement(accumulators, statement):
    return {
        parsing.FurExpressionStatement: transform_expression_statement,
        normalization.NormalArrayVariableInitializationStatement: transform_array_variable_initialization_statement,
        normalization.NormalAssignmentStatement: transform_symbol_assignment_statement,
        normalization.NormalExpressionStatement: transform_expression_statement,
        normalization.NormalFunctionDefinitionStatement: transform_function_definition_statement,
        normalization.NormalIfElseStatement: transform_if_else_statement,
        normalization.NormalVariableInitializationStatement: transform_variable_initialization_statement,
        normalization.NormalVariableReassignmentStatement: transform_variable_reassignment_statement,
    }[type(statement)](accumulators, statement)


Accumulators = collections.namedtuple(
    'Accumulators',
    [
        'builtin_set',
        'function_definition_list',
        'operator_set',
        'symbol_list',
        'string_literal_list',
    ],
)

def transform(program):
    accumulators = Accumulators(
        builtin_set=set(),
        function_definition_list=[],
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
