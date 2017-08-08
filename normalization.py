import collections

NormalProgram = collections.namedtuple(
    'NormalProgram',
    [
        'statement_list',
    ],
)

def flatten(iterable):
    return tuple(item for internal in iterable for item in internal)

def normalize_statement(statement):
    return (statement,)

def normalize(program):
    return NormalProgram(
        statement_list=flatten(normalize_statement(s) for s in program.statement_list),
    )
