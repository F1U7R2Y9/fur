import jinja2

ENV = jinja2.Environment(
    autoescape=jinja2.select_autoescape([]),
    loader=jinja2.FileSystemLoader('templates'),
    trim_blocks=True,
)

def generate_argument(c_string_literal):
    def c_escape(ch):
        return {
            '\n': r'\n',
            '"': r'\"',
            '\\': r'\\',
        }.get(ch, ch)

    return 'stringLiteral(runtime, "{}")'.format(
        ''.join(c_escape(ch for ch in c_string_literal.value)),
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
