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
    def c_escape(ch):
        return {
            '\n': r'\n',
            '"': r'\"',
            '\\': r'\\',
        }.get(ch, ch)

    return 'stringLiteral(runtime, "{}")'.format(
        ''.join(c_escape(ch for ch in c_string_literal.value)),
    )

def generate_argument(c_argument):
    LITERAL_TYPE_MAPPING = {
        transformation.CIntegerLiteral: generate_integer_literal,
        transformation.CStringLiteral: generate_string_literal,
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
        generate_argument(c_argument.left),
        generate_argument(c_argument.right),
    )

def generate_statement(c_function_call_statement):
    return '{}({});'.format(
        c_function_call_statement.name,
        ', '.join(generate_argument(argument) for argument in c_function_call_statement.arguments),
    )

def generate(c_program):
    template = ENV.get_template('program.c')
    return template.render(
        builtins=list(sorted(c_program.builtins)),
        statements=[generate_statement(statement) for statement in c_program.statements],
        standard_libraries=set(['stdio.h']),
    )

if __name__ == '__main__':
    import unittest

    unittest.main()
