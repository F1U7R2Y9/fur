import collections

DesugaredProgram = collections.namedtuple(
    'DesugaredProgram',
    (
        'statement_list',
    ),
)

def desugar(program):
    return DesugaredProgram(
        statement_list=program.statement_list,
    )
