import collections

import conversion

def flatten(xses):
    return tuple(x for xs in xses for x in xs)

CIRProgram = collections.namedtuple(
    'CIRProgram',
    (
        'entry_list',
    ),
)

CIRLabel = collections.namedtuple(
    'CIRLabel',
    (
        'label',
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

def generate_expression_statement(counters, statement):
    return (
        (),
        generate_expression(statement.expression) + (
            CIRInstruction(
                instruction='drop',
                argument=None,
            ),
        ),
    )

def generate_if_else_statement(counters, statement):
    if_counter = counters['if']
    counters['if'] += 1

    referenced_entry_list_list = []

    if_instruction_list_list = []
    for if_statement in statement.if_statement_list:
        referenced_entry_list, instruction_list = generate_statement(counters, if_statement)
        referenced_entry_list_list.append(referenced_entry_list)
        if_instruction_list_list.append(instruction_list)

    else_instruction_list_list = []

    for else_statement in statement.else_statement_list:
        referenced_entry_list, instruction_list = generate_statement(counters, else_statement)
        referenced_entry_list_list.append(referenced_entry_list)
        else_instruction_list_list.append(instruction_list)

    if_label = '__if${}__'.format(if_counter)
    else_label = '__else${}__'.format(if_counter)
    endif_label = '__endif${}__'.format(if_counter)

    return (
        referenced_entry_list_list,
        generate_expression(statement.condition_expression) + (
            CIRInstruction(
                instruction='jump_if_false',
                argument=else_label,
            ),
            CIRLabel(label=if_label),
        ) + flatten(if_instruction_list_list) + (
            CIRInstruction(
                instruction='jump',
                argument=endif_label,
            ),
            CIRLabel(label=else_label),
        ) + flatten(else_instruction_list_list) + (
            CIRLabel(label=endif_label),
        ),
    )

def generate_assignment_statement(counters, statement):
    return (
        (),
        generate_expression(statement.expression) + (
            CIRInstruction(
                instruction='pop',
                argument=generate_symbol_literal(statement.target),
            ),
        ),
    )

def generate_push_statement(counters, statement):
    return (
        (),
        generate_expression(statement.expression),
    )

def generate_variable_initialization_statement(counters, statement):
    return (
        (),
        generate_expression(statement.expression) + (
            CIRInstruction(
                instruction='pop',
                argument=generate_symbol_literal(statement.variable),
            ),
        ),
    )

def generate_variable_reassignment_statement(counter, statement):
    return (
        (),
        generate_expression(statement.expression) + (
            CIRInstruction(
                instruction='pop',
                argument=generate_symbol_literal(statement.variable),
            ),
        ),
    )

def generate_statement(counters, statement):
    return {
        conversion.CPSAssignmentStatement: generate_assignment_statement,
        conversion.CPSExpressionStatement: generate_expression_statement,
        conversion.CPSIfElseStatement: generate_if_else_statement,
        conversion.CPSPushStatement: generate_push_statement,
        conversion.CPSVariableInitializationStatement: generate_variable_initialization_statement,
        conversion.CPSVariableReassignmentStatement: generate_variable_reassignment_statement,
    }[type(statement)](counters, statement)

def generate(converted):
    referenced_entry_list_list = []
    instruction_list_list = []
    counters = {
        'if': 0,
    }

    for statement in converted.statement_list:
        referenced_entry_list, instruction_list = generate_statement(counters, statement)
        referenced_entry_list_list.append(referenced_entry_list)
        instruction_list_list.append(instruction_list)

    return CIRProgram(
        entry_list=(
            CIRLabel(label='__main__'),
        ) + tuple(
            referenced_entry
            for referenced_entry_list in referenced_entry_list_list
            for referenced_entry in referenced_entry_list
        ) + tuple(
            instruction
            for instruction_list in instruction_list_list
            for instruction in instruction_list
        ),
    )

def output(program):
    lines = []

    for entry in program.entry_list:
        if isinstance(entry, CIRInstruction):
            lines.append('    {} {}'.format(entry.instruction, entry.argument))

        if isinstance(entry, CIRLabel):
            lines.append('\n{}:'.format(entry.label))

    return '\n'.join(lines).lstrip()
