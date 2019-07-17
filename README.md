# fur

Fur is a programming language for the next millenium. In 1000 years, humans will likely still like
furry animals, so Fur is named in their honor.

## Installation

1. Create and activate a virtual environment with Python 3. On most systems, this will look something like `python3 -m venv .env/ && .env/bin/activate`.
2. Install dependencies from `requirements.txt` using `pip`: `pip install -r requirements.txt`.
3. That's all!

## Integration tests

To run the unit tests, run `python integration_tests.py`. You can test just the output of the examples or just the memory usage of the tests by running
`python integration_tests.py OutputTests` or `python integration_tests.py MemoryLeakTests` respectively.

# Running

Example Fur programs are in the `examples/` folder. The main compiler (`main.py`) compiles Fur
programs to C. An example of usage:

    ~/fur$ python main.py examples/01_hello.fur
    ~/fur$ gcc examples/01_hello.fur.c 
    ~/fur$ ./a.out
    Hello, world~/fur$ 

## Disclaimers

Fur is GPL 3 and will only ever target GPL compilers. Fur supports closures, integer math, boolean
logic, lists, structures (similar to objects), and strings (implemented as
[ropes](https://en.wikipedia.org/wiki/Rope_(data_structure))).  It doesn't yet support
exceptions, multithreading, modules, or anything resembling a standard library.  If that sounds
like something you want to use in production code, good luck to you.
