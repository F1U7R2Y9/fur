import os
import os.path
import subprocess
import unittest

EXAMPLES_PATH = os.path.join(os.path.dirname(__file__), 'examples')

class OutputTests(unittest.TestCase):
    pass

def add_example_output_test(filename):
    def test(self):
        compile_fur_to_c_result = subprocess.call([
            'python',
            'main.py',
            os.path.join(EXAMPLES_PATH, filename),
        ])

        if compile_fur_to_c_result != 0:
            raise Exception('Example "{}" did not compile'.format(filename))

        compile_c_to_executable_result = subprocess.call([
            'gcc',
            os.path.join(EXAMPLES_PATH, filename + '.c'),
        ])

        if compile_c_to_executable_result != 0:
            raise Exception('Example output "{}" did not compile'.format(filename + '.c'))

        actual_output = subprocess.check_output(['./a.out'])

        with open(os.path.join(EXAMPLES_PATH, filename + '.output.txt'), 'rb') as f:
            expected_output = f.read()

        self.assertEqual(expected_output, actual_output)

    setattr(OutputTests, 'test_' + filename, test)

filenames = (
    entry.name
    for entry in os.scandir(EXAMPLES_PATH)
    if entry.is_file()
    if entry.name.endswith('.fur')
)

for filename in filenames:
    add_example_output_test(filename)

unittest.main()
