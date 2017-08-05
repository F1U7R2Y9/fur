import jinja2

import parsing
import transformation

ENV = jinja2.Environment(
    autoescape=jinja2.select_autoescape([]),
    loader=jinja2.FileSystemLoader('templates'),
    trim_blocks=True,
)

def generate_integer_literal(c_integer_literal):
    return 'integerLiteral({})'.format(c_integer_literal.value)

def generate_string_literal(c_string_literal):
    def c_escape(ch):
        return {
            '\n': r'\n',
            '"': r'\"',
            '\\': r'\\',
        }.get(ch, ch)

    return 'stringLiteral(runtime, "{}")'.format(
        ''.join(c_escape(ch for ch in c_string_literal.value)),
    )

def generate_symbol_expression(c_symbol_expression):
    return 'Environment_get(environment, Runtime_symbol(runtime, "{}"))'.format(c_symbol_expression.value)

def generate_expression(c_argument):
    if isinstance(c_argument, transformation.CNegationExpression):
        return generate_negation_expression(c_argument)

    if isinstance(c_argument, transformation.CFunctionCallExpression):
        return generate_function_call(c_argument)

    LITERAL_TYPE_MAPPING = {
        transformation.CIntegerLiteral: generate_integer_literal,
        transformation.CStringLiteral: generate_string_literal,
        transformation.CSymbolExpression: generate_symbol_expression,
    }

    if type(c_argument) in LITERAL_TYPE_MAPPING:
        return LITERAL_TYPE_MAPPING[type(c_argument)](c_argument)

    INFIX_TYPE_MAPPING = {
        transformation.CAdditionExpression: 'add',
        transformation.CSubtractionExpression: 'subtract',
        transformation.CMultiplicationExpression: 'multiply',
        transformation.CIntegerDivisionExpression: 'integerDivide',
        transformation.CModularDivisionExpression: 'modularDivide',
    }

    return 'builtin${}({}, {})'.format(
        INFIX_TYPE_MAPPING[type(c_argument)],
        generate_expression(c_argument.left),
        generate_expression(c_argument.right),
    )

def generate_negation_expression(c_negation_expression):
    return 'builtin$negate({})'.format(
        generate_expression(c_negation_expression.value)
    )

def generate_function_call(c_function_call):
    return '{}({})'.format(
        c_function_call.name,
        ', '.join(generate_expression(argument) for argument in c_function_call.arguments),
    )

def generate_expression_statement(c_function_call_statement):
    # TODO Do we need to garbage collect the results of arbitrary statements?
    return '{};'.format(generate_expression(c_function_call_statement))

def generate_assignment_statement(c_assignment_statement):
    return 'Environment_set(environment, Runtime_symbol(runtime, "{}"), {});'.format(
        c_assignment_statement.target,
        generate_expression(c_assignment_statement.expression),
    )

def generate_statement(statement):
    if isinstance(statement, transformation.CAssignmentStatement):
        return generate_assignment_statement(statement)

    return generate_expression_statement(statement)

def generate(c_program):
    template = ENV.get_template('program.c')
    return template.render(
        MAX_SYMBOL_LENGTH=parsing.MAX_SYMBOL_LENGTH,
        builtins=list(sorted(c_program.builtins)),
        statements=[generate_statement(statement) for statement in c_program.statements],
        standard_libraries=list(sorted(c_program.standard_libraries)),
    )

if __name__ == '__main__':
    import unittest

    unittest.main()
