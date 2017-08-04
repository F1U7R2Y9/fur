import os
import os.path
import subprocess
import unittest

# Go to the directory of the current file so we know where we are in the filesystem
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class OutputTests(unittest.TestCase):
    pass

def add_example_output_test(filename):
    def test(self):
        compile_fur_to_c_result = subprocess.call([
            'python',
            'main.py',
            os.path.join('examples', filename),
        ])

        if compile_fur_to_c_result != 0:
            raise Exception('Example "{}" did not compile'.format(filename))

        compile_c_to_executable_result = subprocess.call([
            'gcc',
            os.path.join('examples', filename + '.c'),
        ])

        if compile_c_to_executable_result != 0:
            raise Exception('Example output "{}" did not compile'.format(filename + '.c'))

        try:
            actual_output = subprocess.check_output(['./a.out'])

            with open(os.path.join('examples', filename + '.output.txt'), 'rb') as f:
                expected_output = f.read()

            self.assertEqual(expected_output, actual_output)

            # We don't clean up the C file in the finally clause because it can be useful to have in case of errors
            os.remove(os.path.join('examples', filename + '.c'))

        finally:
            try:
                os.remove('a.out')
            except OSError:
                pass

    setattr(OutputTests, 'test_' + filename, test)

filenames = (
    entry.name
    for entry in os.scandir('examples')
    if entry.is_file()
    if entry.name.endswith('.fur')
)

for filename in filenames:
    add_example_output_test(filename)

unittest.main()
