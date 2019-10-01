import os

import jinja2

import crossplatform_ir_generation

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

def separate_labels_and_instructions(entry_list):
    labels_to_instruction_indices = {}
    instruction_list = []

    for entry in entry_list:
        if isinstance(entry, crossplatform_ir_generation.CIRInstruction):
            instruction_list.append(entry)
        elif isinstance(entry, crossplatform_ir_generation.CIRLabel):
            labels_to_instruction_indices[entry.label] = len(instruction_list)

    return labels_to_instruction_indices, tuple(instruction_list)

def generate_integer_argument(argument):
    assert isinstance(argument, int)
    return '(int32_t){}'.format(argument)

def generate_null_argument(argument):
    assert argument is None
    return 'NULL'

def generate_size_t_argument(argument):
    assert isinstance(argument, int)
    return '(size_t){}'.format(argument)

def generate_string_argument(argument):
    return argument

def generate_symbol_argument(argument):
    assert argument.startswith('sym(') and argument.endswith(')')
    return '"{}"'.format(argument[4:-1])

def generate_argument(instruction):
    try:
        return {
            'add': generate_size_t_argument,
            'drop': generate_null_argument,
            'end': generate_null_argument,
            'call': generate_size_t_argument,
            'idiv': generate_size_t_argument,
            'mod': generate_size_t_argument,
            'mul': generate_size_t_argument,
            'neg': generate_size_t_argument,
            'pop': generate_symbol_argument,
            'push': generate_symbol_argument,
            'push_integer': generate_integer_argument,
            'push_string': generate_string_argument,
            'sub': generate_size_t_argument,
        }[instruction.instruction](instruction.argument)

    except KeyError:
        import ipdb; ipdb.set_trace()

def generate(ir):
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH))
    template = environment.get_template('program2.c')

    labels_to_instruction_indices, instruction_list = separate_labels_and_instructions(
        ir.entry_list,
    )

    return template.render(
        labels_to_instruction_indices=labels_to_instruction_indices,
        instruction_list=instruction_list,
        generate_argument=generate_argument,
    )
