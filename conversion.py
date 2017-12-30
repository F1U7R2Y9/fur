import collections

CPSProgram = collections.namedtuple(
    'CPSProgram',
    (
        'statement_list',
    ),
)

def convert(program):
    return CPSProgram(
        statement_list=program.statement_list,
    )
