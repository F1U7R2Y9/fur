import collections

import conversion

CIRProgram = collections.namedtuple(
    'CIRProgram',
    (
        'entry_list',
    ),
)

CIREntry = collections.namedtuple(
    'CIREntry',
    (
        'name',
        'instruction_list',
    ),
)

CIRInstruction = collections.namedtuple(
    'CIRInstruction',
    (
        'instruction',
        'argument',
    ),
)

def generate_integer_literal(integer):
    return integer

def generate_string_literal(string):
    return '"{}"'.format(string)

def generate_symbol_literal(symbol):
    return 'sym({})'.format(symbol)

def generate_function_call_expression(expression):
    return generate_expression(expression.function_expression) + (
        CIRInstruction(
            instruction='call',
            argument=expression.argument_count,
        ),
    )

def generate_integer_literal_expression(expression):
    return (CIRInstruction(
        instruction='push_value',
        argument=generate_integer_literal(expression.integer),
    ),)

def generate_string_literal_expression(expression):
    return (CIRInstruction(
        instruction='push_value',
        argument=generate_string_literal(expression.string),
    ),)

def generate_symbol_expression(expression):
    return (CIRInstruction(
        instruction='push',
        argument=generate_symbol_literal(expression.symbol),
    ),)

def generate_variable_expression(expression):
    return (CIRInstruction(
        instruction='push',
        argument=generate_symbol_literal(expression.variable),
    ),)

def generate_expression(expression):
    return {
        conversion.CPSFunctionCallExpression: generate_function_call_expression,
        conversion.CPSIntegerLiteralExpression: generate_integer_literal_expression,
        conversion.CPSStringLiteralExpression: generate_string_literal_expression,
        conversion.CPSSymbolExpression: generate_symbol_expression,
        conversion.CPSVariableExpression: generate_variable_expression,
    }[type(expression)](expression)

def generate_expression_statement(statement):
    return (
        (),
        generate_expression(statement.expression) + (
            CIRInstruction(
                instruction='drop',
                argument=None,
            ),
        ),
    )

def generate_if_else_statement(statement):
    import ipdb; ipdb.set_trace()

def generate_assignment_statement(statement):
    return (
        (),
        generate_expression(statement.expression) + (
            CIRInstruction(
                instruction='pop',
                argument=generate_symbol_literal(statement.target),
            ),
        ),
    )

def generate_push_statement(statement):
    return (
        (),
        generate_expression(statement.expression),
    )

def generate_variable_initialization_statement(statement):
    return (
        (),
        generate_expression(statement.expression) + (
            CIRInstruction(
                instruction='pop',
                argument=generate_symbol_literal(statement.variable),
            ),
        ),
    )

def generate_statement(statement):
    return {
        conversion.CPSAssignmentStatement: generate_assignment_statement,
        conversion.CPSExpressionStatement: generate_expression_statement,
        conversion.CPSIfElseStatement: generate_if_else_statement,
        conversion.CPSPushStatement: generate_push_statement,
        conversion.CPSVariableInitializationStatement: generate_variable_initialization_statement,
    }[type(statement)](statement)

def generate(converted):
    referenced_entry_list_list = []
    instruction_list_list = []

    for statement in converted.statement_list:
        referenced_entry_list, instruction_list = generate_statement(statement)
        referenced_entry_list_list.append(referenced_entry_list)
        instruction_list_list.append(instruction_list)

    return CIRProgram(
        entry_list=tuple(
            entry
            for referenced_entry_list in referenced_entry_list_list
            for entry in referenced_entry_list
        ) + (CIREntry(
            name='__main__',
            instruction_list=tuple(
                instruction
                for instruction_list in instruction_list_list
                for instruction in instruction_list
            ),
        ),),
    )

def output(program):
    entry_outputs = []

    for entry in program.entry_list:
        statement_outputs = []

        for instruction in entry.instruction_list:
            statement_outputs.append('    {} {}'.format(
                instruction.instruction,
                instruction.argument,
            ))

        entry_outputs.append('{}:\n{}'.format(
            entry.name,
            '\n'.join(statement_outputs),
        ))

    return '\n\n'.join(entry_outputs)
