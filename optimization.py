from crossplatform_ir_generation import CIRProgram, CIRInstruction, CIRLabel

PUSHING_INSTRUCTIONS_WITHOUT_SIDE_EFFECTS = set(
    ('push',),
)

def push_drop_optimization(ir):
    ir = tuple(ir)

    i = 0

    while i < len(ir):
        if isinstance(ir[i], CIRInstruction)\
                and ir[i].instruction in PUSHING_INSTRUCTIONS_WITHOUT_SIDE_EFFECTS\
                and i + 1 < len(ir)\
                and isinstance(ir[i + 1], CIRInstruction)\
                and ir[i + 1].instruction == 'drop':
            i += 2
        else:
            yield ir[i]
            i += 1

# TODO This can be smarter
def unused_pop_optimization(ir):
    ir = tuple(ir)

    used_symbols = set()

    for entry in ir:
        # TODO Having symbols be a string starting with "sym" is a bit hacky
        if isinstance(entry, CIRInstruction)\
                and entry.instruction != 'pop'\
                and isinstance(entry.argument, str)\
                and entry.argument.startswith('sym'):
            used_symbols.add(entry.argument)

    for entry in ir:
        if isinstance(entry, CIRInstruction) and entry.instruction == 'pop' and entry.argument not in used_symbols:
            yield CIRInstruction(instruction='drop', argument=None)
        else:
            yield entry

def optimize(cir_program):
    ir = cir_program.entry_list

    ir = push_drop_optimization(ir)
    ir = unused_pop_optimization(ir)

    return CIRProgram(entry_list=tuple(ir))
