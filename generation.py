import jinja2

import transformation

ENV = jinja2.Environment(
    autoescape=jinja2.select_autoescape([]),
    loader=jinja2.FileSystemLoader('templates'),
    trim_blocks=True,
)

def generate_integer_literal(c_integer_literal):
    return 'integerLiteral({})'.format(c_integer_literal.value)

def generate_string_literal(c_string_literal):
    return 'stringLiteral(STRING_LITERAL_LIST[{}])'.format(c_string_literal.index)

CONSTANT_EXPRESSION_MAPPING = {
    'true':     'TRUE',
    'false':    'FALSE',
}

def generate_constant_expression(c_constant_expression):
    return CONSTANT_EXPRESSION_MAPPING[c_constant_expression.value]

def generate_symbol_expression(c_symbol_expression):
    return 'Environment_get(environment, SYMBOL_LIST[{}] /* symbol: {} */)'.format(
        c_symbol_expression.symbol_list_index,
        c_symbol_expression.symbol,
    )

def generate_variable_expression(expression):
    return expression.variable

def generate_expression(expression):
    if isinstance(expression, transformation.CNegationExpression):
        return generate_negation_expression(expression)

    if isinstance(expression, transformation.CFunctionCallExpression):
        return generate_function_call(expression)

    LITERAL_TYPE_MAPPING = {
        transformation.CIntegerLiteral: generate_integer_literal,
        transformation.CStringLiteral: generate_string_literal,
        transformation.CConstantExpression: generate_constant_expression,
        transformation.CSymbolExpression: generate_symbol_expression,
    }

    if type(expression) in LITERAL_TYPE_MAPPING:
        return LITERAL_TYPE_MAPPING[type(expression)](expression)

    if isinstance(expression, transformation.CFunctionCallForFurInfixOperator):
        return 'builtin${}({}, {})'.format(
            expression.name,
            generate_expression(expression.left),
            generate_expression(expression.right),
        )

    return {
        transformation.CVariableExpression: generate_variable_expression,
    }[type(expression)](expression)

def generate_negation_expression(c_negation_expression):
    return 'builtin$negate({})'.format(
        generate_expression(c_negation_expression.value)
    )

def generate_function_call(c_function_call):
    return '{}({})'.format(
        c_function_call.name,
        ', '.join(generate_expression(argument) for argument in c_function_call.arguments),
    )

def generate_expression_statement(statement):
    # TODO Do we need to garbage collect the results of arbitrary statements?
    return '{};'.format(generate_expression(statement.expression))

def generate_symbol_assignment_statement(c_assignment_statement):
    return 'Environment_set(environment, SYMBOL_LIST[{}] /* symbol: {} */, {});'.format(
        c_assignment_statement.target_symbol_list_index,
        c_assignment_statement.target,
        generate_expression(c_assignment_statement.expression),
    )

def generate_variable_initialization_statement(statement):
    return 'Object {} = {};'.format(
        statement.variable,
        generate_expression(statement.expression),
    )

def generate_statement(statement):
    return {
        transformation.CSymbolAssignmentStatement: generate_symbol_assignment_statement,
        transformation.CExpressionStatement: generate_expression_statement,
        transformation.CVariableInitializationStatement: generate_variable_initialization_statement,
    }[type(statement)](statement)

def generate(program):
    template = ENV.get_template('program.c')
    return template.render(
        builtins=list(sorted(program.builtin_set)),
        statements=[generate_statement(statement) for statement in program.statements],
        standard_libraries=list(sorted(program.standard_libraries)),
        string_literal_list=program.string_literal_list,
        symbol_list=program.symbol_list,
    )

if __name__ == '__main__':
    import unittest

    unittest.main()
