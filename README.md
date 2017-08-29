# fur

Fur is a programming language for the next millenium. In 1000 years, humans will likely still like
furry animals, so Fur is named in their honor.

Example Fur programs are in the `examples/` folder. The main compiler (`main.py`) compiles Fur
programs to C. An example of usage:

    ~/fur$ python3 main.py examples/01_hello.fur
    ~/fur$ gcc examples/01_hello.fur.c 
    ~/fur$ ./a.out
    Hello, world~/fur$ 

Fur is GPL and will only ever target GPL compilers. Fur supports closures, integer math, boolean
logic, lists, structures (similar to objects), and strings (implemented as
[ropes](https://en.wikipedia.org/wiki/Rope_(data_structure)))).  It doesn't yet support
exceptions, multithreading, modules, or anything resembling a standard library.  If that sounds
like something you want to use in production code, good luck to you.
