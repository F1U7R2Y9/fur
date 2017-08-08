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

def generate_function_call(function_call):
    return '{}({}, {})'.format(
        function_call.name,
        function_call.argument_count,
        # TODO This is just a single item containing a reference to the items list--make that clearer
        generate_expression(function_call.argument_items),
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

def generate_array_variable_initialization_statement(statement):
    return 'Object {}[] = {{ {} }};'.format(
        statement.variable,
        ', '.join(generate_expression(i) for i in statement.items),
    )

def generate_variable_initialization_statement(statement):
    return 'Object {} = {};'.format(
        statement.variable,
        generate_expression(statement.expression),
    )

def generate_variable_reassignment_statement(statement):
    return '{} = {};'.format(
        statement.variable,
        generate_expression(statement.expression),
    )


def indent(s):
    return '\n'.join(' ' * 2 + l for l in s.split('\n'))

def generate_if_else_statement(statement):
    # TODO Check that the argument is boolean
    return 'if({}.instance.boolean)\n{{\n{}\n}}\nelse\n{{\n{}\n}}'.format(
        generate_expression(statement.condition_expression),
        indent('\n'.join(generate_statement(s) for s in statement.if_statements)),
        indent('\n'.join(generate_statement(s) for s in statement.else_statements)),
    )

def generate_statement(statement):
    return {
        transformation.CExpressionStatement: generate_expression_statement,
        transformation.CIfElseStatement: generate_if_else_statement,
        transformation.CSymbolAssignmentStatement: generate_symbol_assignment_statement,
        transformation.CArrayVariableInitializationStatement: generate_array_variable_initialization_statement,
        transformation.CVariableInitializationStatement: generate_variable_initialization_statement,
        transformation.CVariableReassignmentStatement: generate_variable_reassignment_statement,
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
