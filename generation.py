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
    return 'stringLiteral(STRING_LITERAL_LIST[{}] /* string: {} */)'.format(
        c_string_literal.index,
        repr(c_string_literal.value),
    )

def generate_symbol_expression(symbol_expression):
    return 'Environment_get(environment, SYMBOL_LIST[{}] /* symbol: {} */)'.format(
        symbol_expression.symbol_list_index,
        symbol_expression.symbol,
    )

def generate_variable_expression(expression):
    return expression.variable

def generate_structure_literal_expression(expression):
    return 'Structure_construct({}, {}, {})'.format(
        expression.field_count,
        expression.symbol_list_variable,
        expression.value_list_variable,
    )

def generate_lambda_expression(expression):
    return '(Object){{ CLOSURE, (Instance)(Closure){{ environment, user${}$implementation }} }}'.format(
        expression.name,
    )

def generate_list_construct_expression(expression):
    return 'List_construct({})'.format(expression.allocate)

def generate_expression(expression):
    return {
        transformation.CFunctionCallExpression: generate_function_call,
        transformation.CIntegerLiteral: generate_integer_literal,
        transformation.CLambdaExpression: generate_lambda_expression,
        transformation.CListConstructExpression: generate_list_construct_expression,
        transformation.CStringLiteral: generate_string_literal,
        transformation.CStructureLiteralExpression: generate_structure_literal_expression,
        transformation.CSymbolExpression: generate_symbol_expression,
        transformation.CVariableExpression: generate_variable_expression,
    }[type(expression)](expression)

def generate_function_call(function_call):
    # This gets called twice, so we want to be sure it is efficient and without side effects
    assert isinstance(function_call.function_expression, transformation.CVariableExpression)

    # TODO Check the type of the things being called
    function_expression = generate_variable_expression(function_call.function_expression)
    return '{}.instance.closure.call(environmentPool, {}.instance.closure.closed, {}, stack, {}, jump)'.format(
        function_expression,
        function_expression,
        function_call.argument_count,
        function_call.metadata.line,
    )

def generate_expression_statement(statement):
    return 'Object_deinitialize(&({}));'.format(generate_expression(statement.expression))

def generate_symbol_assignment_statement(statement):
    return 'Environment_set(environment, SYMBOL_LIST[{}] /* symbol: {} */, {});'.format(
        statement.target_symbol_list_index,
        statement.target,
        generate_expression(statement.expression),
    )

def generate_array_variable_initialization_statement(statement):
    return 'Object {}[] = {{ {} }};'.format(
        statement.variable,
        ', '.join(generate_expression(i) for i in statement.items),
    )

def generate_symbol_array_variable_initialization_statement(statement):
    return 'const char* {}[] = {{ {} }};'.format(
        statement.variable,
        ', '.join('SYMBOL_LIST[{}] /* symbol: "{}" */'.format(
            statement.symbol_list_indices[i],
            statement.symbol_list[i],
        ) for i in range(len(statement.symbol_list))),
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
    condition_expression = '{}.instance.boolean'.format(
        generate_expression(statement.condition_expression),
    )

    if len(statement.if_statement_list) == 0:
        condition_expression = '!({})'.format(condition_expression)
        if_statement_list = statement.else_statement_list
        else_statement_list = ()
    else:
        if_statement_list = statement.if_statement_list
        else_statement_list = statement.else_statement_list

    generated_if_clause = 'if({})'.format(condition_expression)

    if len(if_statement_list) == 0:
        generated_if_statement_list = ';'
    else:
        generated_if_statement_list = indent('\n{{\n{}\n}}'.format(
            indent('\n'.join(generate_statement(s) for s in if_statement_list)),
        ))

    if len(else_statement_list) == 0:
        generated_else_statement_list = ''
    else:
        generated_else_statement_list = indent('\nelse\n{{\n{}\n}}'.format(
            indent('\n'.join(generate_statement(s) for s in else_statement_list)),
        ))

    return generated_if_clause + generated_if_statement_list + generated_else_statement_list

def generate_list_append_statement(statement):
    return 'List_append(&{}, {});'.format(
        generate_expression(statement.list_expression),
        generate_expression(statement.item_expression),
    )

def generate_push_statement(statement):
    return 'Stack_push(stack, {});'.format(generate_expression(statement.expression))

def generate_statement(statement):
    return {
        transformation.CArrayVariableInitializationStatement: generate_array_variable_initialization_statement,
        transformation.CExpressionStatement: generate_expression_statement,
        transformation.CIfElseStatement: generate_if_else_statement,
        transformation.CListAppendStatement: generate_list_append_statement,
        transformation.CPushStatement: generate_push_statement,
        transformation.CSymbolAssignmentStatement: generate_symbol_assignment_statement,
        transformation.CSymbolArrayVariableInitializationStatement: generate_symbol_array_variable_initialization_statement,
        transformation.CVariableInitializationStatement: generate_variable_initialization_statement,
        transformation.CVariableReassignmentStatement: generate_variable_reassignment_statement,
    }[type(statement)](statement)

def generate_function_definition(definition):
    template = ENV.get_template('function_definition.c')
    return template.render(
        name=definition.name,
        argument_name_list=definition.argument_name_list,
        statement_list=list(generate_statement(s) for s in definition.statement_list),
    )
    return definition

C_ESCAPES = {
    '"':    r'\"',
}

def escape_character(ch):
    return C_ESCAPES.get(ch, ch)

def escape_string_literal(string_literal):
    return  ''.join(escape_character(ch) for ch in string_literal)

def generate(program):
    template = ENV.get_template('program.c')
    return template.render(
        builtins=tuple(sorted(program.builtin_set)),
        function_definition_list=list(generate_function_definition(fd) for fd in program.function_definition_list),
        infix_declarations=program.operator_declarations,
        statements=list(generate_statement(s) for s in program.statements),
        standard_libraries=list(sorted(program.standard_libraries)),
        string_literal_list=list(escape_string_literal(s) for s in program.string_literal_list),
        symbol_list=program.symbol_list,
    )

if __name__ == '__main__':
    import unittest

    unittest.main()
