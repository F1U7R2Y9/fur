import collections

import parsing

DesugaredFunctionCallExpression = collections.namedtuple(
    'DesugaredFunctionCallExpression',
    (
        'function',
        'argument_list',
    ),
)

DesugaredIfExpression = collections.namedtuple(
    'DesugaredIfExpression',
    (
        'condition_expression',
        'if_statement_list',
        'else_statement_list',
    ),
)

DesugaredIntegerLiteralExpression = collections.namedtuple(
    'DesugaredIntegerLiteralExpression',
    (
        'integer',
    ),
)

DesugaredListLiteralExpression = collections.namedtuple(
    'DesugaredListLiteralExpression',
    (
        'item_expression_list',
    ),
)

DesugaredStringLiteralExpression = collections.namedtuple(
    'DesugaredStringLiteralExpression',
    (
        'string',
    ),
)

DesugaredSymbolExpressionPair = collections.namedtuple(
    'DesugaredSymbolExpressionPair',
    (
        'symbol',
        'expression',
    ),
)

DesugaredStructureLiteralExpression = collections.namedtuple(
    'DesugaredStructureLiteralExpression',
    (
        'fields',
    ),
)

DesugaredSymbolExpression = collections.namedtuple(
    'DesugaredSymbolExpression',
    (
        'metadata',
        'symbol',
    ),
)

DesugaredAssignmentStatement = collections.namedtuple(
    'DesugaredAssignmentStatement',
    (
        'target',
        'expression',
    ),
)

DesugaredExpressionStatement = collections.namedtuple(
    'DesugaredExpressionStatement',
    (
        'expression',
    ),
)

DesugaredFunctionDefinitionStatement = collections.namedtuple(
    'DesugaredFunctionDefinitionStatement',
    (
        'name',
        'argument_name_list',
        'statement_list',
    ),
)

DesugaredProgram = collections.namedtuple(
    'DesugaredProgram',
    (
        'statement_list',
    ),
)

def desugar_function_call_expression(expression):
    return DesugaredFunctionCallExpression(
        function=desugar_expression(expression.function),
        argument_list=tuple(desugar_expression(e) for e in expression.arguments),
    )

def desugar_if_expression(expression):
    return DesugaredIfExpression(
        condition_expression=desugar_expression(expression.condition_expression),
        if_statement_list=tuple(desugar_statement(s) for s in expression.if_statement_list),
        else_statement_list=tuple(desugar_statement(s) for s in expression.else_statement_list),
    )

def desugar_infix_expression(expression):
    if expression.operator == 'and':
        return DesugaredIfExpression(
            condition_expression=desugar_expression(expression.left),
            if_statement_list=(
                DesugaredExpressionStatement(expression=desugar_expression(expression.right)),
            ),
            else_statement_list=(
                DesugaredExpressionStatement(
                    expression=DesugaredSymbolExpression(
                        metadata=expression.metadata,
                        symbol='false',
                    ),
                ),
            ),
        )

    if expression.operator == 'or':
        return DesugaredIfExpression(
            condition_expression=desugar_expression(expression.left),
            if_statement_list=(
                DesugaredExpressionStatement(
                    expression=DesugaredSymbolExpression(
                        metadata=expression.metadata,
                        symbol='true',
                    ),
                ),
            ),
            else_statement_list=(
                DesugaredExpressionStatement(expression=desugar_expression(expression.right)),
            ),
        )

    if expression.operator == '.':
        return DesugaredFunctionCallExpression(
            function=DesugaredSymbolExpression(
                metadata=expression.metadata,
                symbol='__field__',
            ),
            argument_list=(
                desugar_expression(expression.left),
                DesugaredStringLiteralExpression(string=expression.right.symbol),
            ),
        )

    function = {
        '++': '__concat__',
        '+': '__add__',
        '-': '__subtract__',
        '*': '__multiply__',
        '//': '__integer_divide__',
        '%': '__modular_divide__',
        '<': '__lt__',
        '>': '__gt__',
        '<=': '__lte__',
        '>=': '__gte__',
        '==': '__eq__',
        '!=': '__neq__',
    }[expression.operator]

    return DesugaredFunctionCallExpression(
        function=DesugaredSymbolExpression(
            metadata=expression.metadata,
            symbol=function,
        ),
        argument_list=(
            desugar_expression(expression.left),
            desugar_expression(expression.right),
        ),
    )

def desugar_integer_literal_expression(expression):
    return DesugaredIntegerLiteralExpression(
        integer=expression.integer,
    )

def desugar_list_item_expression(expression):
    return DesugaredFunctionCallExpression(
        function=DesugaredSymbolExpression(
            metadata=expression.metadata,
            symbol='__get__',
        ),
        argument_list=(
            desugar_expression(expression.list_expression),
            desugar_expression(expression.index_expression),
        ),
    )

def desugar_list_literal_expression(expression):
    return DesugaredListLiteralExpression(
        item_expression_list=tuple(desugar_expression(i) for i in expression.item_expression_list),
    )

def desugar_negation_expression(expression):
    return DesugaredFunctionCallExpression(
        function=DesugaredSymbolExpression(
            metadata=expression.metadata,
            symbol='__negate__',
        ),
        argument_list=(
            desugar_expression(expression.value),
        ),
    )

def desugar_string_literal_expression(expression):
    return DesugaredStringLiteralExpression(
        string=expression.string,
    )

def desugar_structure_literal_expression(expression):
    return DesugaredStructureLiteralExpression(
        fields=tuple(
            DesugaredSymbolExpressionPair(
                symbol=p.symbol,
                expression=desugar_expression(p.expression),
            ) for p in expression.fields
        ),
    )

def desugar_symbol_expression(expression):
    return DesugaredSymbolExpression(
        metadata=expression.metadata,
        symbol=expression.symbol,
    )

def desugar_expression(expression):
    return {
        parsing.FurFunctionCallExpression: desugar_function_call_expression,
        parsing.FurIfExpression: desugar_if_expression,
        parsing.FurInfixExpression: desugar_infix_expression,
        parsing.FurIntegerLiteralExpression: desugar_integer_literal_expression,
        parsing.FurListItemExpression: desugar_list_item_expression,
        parsing.FurListLiteralExpression: desugar_list_literal_expression,
        parsing.FurNegationExpression: desugar_negation_expression,
        parsing.FurStringLiteralExpression: desugar_string_literal_expression,
        parsing.FurStructureLiteralExpression: desugar_structure_literal_expression,
        parsing.FurSymbolExpression: desugar_symbol_expression,
    }[type(expression)](expression)

def desugar_assignment_statement(statement):
    return DesugaredAssignmentStatement(
        target=statement.target,
        expression=desugar_expression(statement.expression),
    )

def desugar_expression_statement(statement):
    return DesugaredExpressionStatement(
        expression=desugar_expression(statement.expression),
    )

def desugar_function_definition_statement(statement):
    return DesugaredFunctionDefinitionStatement(
        name=statement.name,
        argument_name_list=statement.argument_name_list,
        statement_list=tuple(desugar_statement(s) for s in statement.statement_list),
    )

def desugar_statement(statement):
    return {
        parsing.FurAssignmentStatement: desugar_assignment_statement,
        parsing.FurExpressionStatement: desugar_expression_statement,
        parsing.FurFunctionDefinitionStatement: desugar_function_definition_statement,
    }[type(statement)](statement)

def desugar(program):
    return DesugaredProgram(
        statement_list=[desugar_statement(s) for s in program.statement_list],
    )
