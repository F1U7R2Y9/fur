import sys

import conversion
import crossplatform_ir_generation
import desugaring
import generation
import normalization
import parsing
import tokenization
import transformation

source_path = sys.argv[1]

with open(source_path, 'r') as f:
    source = f.read()

tokens = tokenization.tokenize(source)
parsed = parsing.parse(tokens)
desugared = desugaring.desugar(parsed)
normalized = normalization.normalize(desugared)
converted = conversion.convert(normalized)

# This is the C generation path
transformed = transformation.transform(converted)
generated = generation.generate(transformed)

assert source_path.endswith('.fur')
destination_path = source_path + '.c'

with open(destination_path, 'w') as f:
    f.write(generated)

# This is the crossplatform IR generation path
crossplatform_ir = crossplatform_ir_generation.generate(converted)
outputted = crossplatform_ir_generation.output(crossplatform_ir)
print(outputted)
