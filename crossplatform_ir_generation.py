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

def generate_function_call_expression(counters, expression):
    referenced_entry_list, instruction_list = generate_expression(
        counters,
        expression.function_expression,
    )

    instruction_list += (
        CIRInstruction(
            instruction='call',
            argument=expression.argument_count,
        ),
    )

    return referenced_entry_list, instruction_list

def generate_integer_literal_expression(counters, expression):
    referenced_entry_list = ()
    instruction_list = (CIRInstruction(
        instruction='push_value',
        argument=generate_integer_literal(expression.integer),
    ),)

    return referenced_entry_list, instruction_list

def generate_lambda_expression(counters, expression):
    if expression.name is None or 'lambda' in expression.name.lower():
        import ipdb; ipdb.set_trace()

    name_counter = counters.get(expression.name, 0)
    counters[expression.name] = name_counter + 1
    label = '{}${}'.format(expression.name, name_counter)

    for argument_name in expression.argument_name_list:
        import ipdb; ipdb.set_trace()

    referenced_entry_list_list = []
    instruction_list_list = []

    for statement in expression.statement_list:
        referenced_entry_list, instruction_list = generate_statement(counters, statement)
        referenced_entry_list_list.append(referenced_entry_list)
        instruction_list_list.append(instruction_list)

    referenced_entry_list_list.append(
        (CIRLabel(label=label),) + flatten(instruction_list_list),
    )

    instruction_list = (
        CIRInstruction(instruction='close', argument=label),
    )

    return flatten(referenced_entry_list_list), instruction_list

def generate_string_literal_expression(counters, expression):
    referenced_entry_list = ()
    instruction_list = (CIRInstruction(
        instruction='push_value',
        argument=generate_string_literal(expression.string),
    ),)

    return referenced_entry_list, instruction_list

def generate_symbol_expression(counters, expression):
    referenced_entry_list = ()
    instruction_list = (CIRInstruction(
        instruction='push',
        argument=generate_symbol_literal(expression.symbol),
    ),)

    return referenced_entry_list, instruction_list

def generate_variable_expression(counters, expression):
    referenced_entry_list = ()
    instruction_list = (CIRInstruction(
        instruction='push',
        argument=generate_symbol_literal(expression.variable),
    ),)

    return referenced_entry_list, instruction_list

def generate_expression(counters, expression):
    return {
        conversion.CPSFunctionCallExpression: generate_function_call_expression,
        conversion.CPSIntegerLiteralExpression: generate_integer_literal_expression,
        conversion.CPSLambdaExpression: generate_lambda_expression,
        conversion.CPSStringLiteralExpression: generate_string_literal_expression,
        conversion.CPSSymbolExpression: generate_symbol_expression,
        conversion.CPSVariableExpression: generate_variable_expression,
    }[type(expression)](counters, expression)

def generate_expression_statement(counters, statement):
    referenced_entry_list, instruction_list = generate_expression(
        counters,
        statement.expression,
    )

    instruction_list += (
        CIRInstruction(
            instruction='drop',
            argument=None,
        ),
    )

    return referenced_entry_list, instruction_list

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

    instruction_list = (
        referenced_entry_list_list,
        generate_expression(counters, statement.condition_expression) + (
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

    return flatten(referenced_entry_list_list), instruction_list

def generate_assignment_statement(counters, statement):
    referenced_entry_list, instruction_list = generate_expression(
        counters,
        statement.expression,
    )

    instruction_list += (
        CIRInstruction(
            instruction='pop',
            argument=generate_symbol_literal(statement.target),
        ),
    )

    return referenced_entry_list, instruction_list

def generate_push_statement(counters, statement):
    return generate_expression(counters, statement.expression)

def generate_variable_initialization_statement(counters, statement):
    referenced_entry_list, instruction_list = generate_expression(
        counters,
        statement.expression,
    )

    instruction_list += (
        CIRInstruction(
            instruction='pop',
            argument=generate_symbol_literal(statement.variable),
        ),
    )

    return referenced_entry_list, instruction_list

def generate_variable_reassignment_statement(counters, statement):
    referenced_entry_list, instruction_list = generate_expression(
        counters,
        statement.expression,
    )

    instruction_list += (
        CIRInstruction(
            instruction='pop',
            argument=generate_symbol_literal(statement.variable),
        ),
    )

    return referenced_entry_list, instruction_list

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
        ) + flatten(referenced_entry_list_list) + flatten(instruction_list_list),
    )

def output(program):
    lines = []

    for entry in program.entry_list:
        if isinstance(entry, CIRInstruction):
            lines.append('    {} {}'.format(entry.instruction, entry.argument))

        if isinstance(entry, CIRLabel):
            lines.append('\n{}:'.format(entry.label))

    return '\n'.join(lines).lstrip()
