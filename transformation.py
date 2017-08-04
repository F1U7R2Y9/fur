import collections

import parsing

CIntegerLiteral = collections.namedtuple(
    'CIntegerLiteral',
    [
        'value',
    ],
)

CStringLiteral = collections.namedtuple(
    'CStringLiteral',
    [
        'value',
    ],
)

CFunctionCallStatement = collections.namedtuple(
    'CFunctionCallStatement',
    [
        'name',
        'arguments',
    ],
)

CProgram = collections.namedtuple(
    'CProgram',
    [
        'builtins',
        'statements',
        'standard_libraries',
    ],
)

BUILTINS = {
    'print': ['stdio.h.'],
}

def transform_argument(builtin_dependencies, argument):
    return {
        parsing.IntegerLiteral: CIntegerLiteral,
        parsing.StringLiteral: CStringLiteral,
    }[type(argument)](value=argument.value)

def transform_function_call_statement(builtin_dependencies, function_call):
    if function_call.name in BUILTINS.keys():
        builtin_dependencies.add(function_call.name)

        return CFunctionCallStatement(
            name='builtin$' + function_call.name,
            arguments=tuple(transform_argument(builtin_dependencies, arg) for arg in function_call.arguments),
        )

    raise Exception()


def transform(function_call):
    builtins = set()

    statement = transform_function_call_statement(builtins, function_call)

    standard_libraries = set()
    for builtin in builtins:
        for standard_library in BUILTINS[builtin]:
            standard_libraries.add(standard_library)

    return CProgram(
        builtins=builtins,
        statements=[statement],
        standard_libraries=standard_libraries,
    )


if __name__ == '__main__':
    import unittest

    unittest.main()
