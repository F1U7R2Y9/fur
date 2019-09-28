import sys

import conversion
import crossplatform_ir_generation
import desugaring
import c_generation
import normalization
import optimization
import parsing
import tokenization

source_path = sys.argv[1]

with open(source_path, 'r') as f:
    source = f.read()

tokens = tokenization.tokenize(source)
parsed = parsing.parse(tokens)
desugared = desugaring.desugar(parsed)
normalized = normalization.normalize(desugared)
converted = conversion.convert(normalized)

crossplatform_ir = crossplatform_ir_generation.generate(converted)
optimized = optimization.optimize(crossplatform_ir)
outputted = crossplatform_ir_generation.output(optimized)
print(outputted)

generated = c_generation.generate(optimized)

assert source_path.endswith('.fur')
destination_path = source_path + '.c'

with open(destination_path, 'w') as f:
    f.write(generated)
