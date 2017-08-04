import sys

import generation
import parsing
import tokenization
import transformation

source_path = sys.argv[1]

with open(source_path, 'r') as f:
    source = f.read()

tokens = tokenization.tokenize(source)
parsed = parsing.parse(tokens)
transformed = transformation.transform(parsed)
generated = generation.generate(transformed)

assert source_path.endswith('.fur')
destination_path = source_path + '.c'

with open(destination_path, 'w') as f:
    f.write(generated)
