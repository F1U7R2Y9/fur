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
            p = subprocess.Popen('./a.out', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            actual_stdout, actual_stderr = p.communicate()

            expected_stdout_path = os.path.join('examples', filename + '.stdout.txt')

            if os.path.isfile(expected_stdout_path):
                with open(expected_stdout_path, 'rb') as f:
                    expected_stdout = f.read()
            else:
                expected_stdout = b''

            expected_stderr_path = os.path.join('examples', filename + '.stderr.txt')

            if os.path.isfile(expected_stderr_path):
                with open(expected_stderr_path, 'rb') as f:
                    expected_stderr = f.read()
            else:
                expected_stderr = b''

            self.assertEqual(expected_stderr, actual_stderr)

            # We don't clean up the C file in the finally clause because it can be useful to have in case of errors
            os.remove(os.path.join('examples', filename + '.c'))

        finally:
            try:
                os.remove('a.out')
            except OSError:
                pass

    setattr(OutputTests, 'test_' + filename, test)

class MemoryLeakTest(unittest.TestCase):
    pass

def add_example_memory_leak_test(filename):
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
            '-ggdb3',
            os.path.join('examples', filename + '.c'),
        ])

        if compile_c_to_executable_result != 0:
            raise Exception('Example output "{}" did not compile'.format(filename + '.c'))

        try:
            with open(os.devnull, 'w') as devnull:
                expected_return = 0
                actual_return = subprocess.call(
                    [
                        'valgrind',
                        '--tool=memcheck',
                        '--leak-check=yes',
                        '--show-reachable=yes',
                        '--num-callers=20',
                        '--track-fds=yes',
                        '--error-exitcode=666',
                        '-q',
                        './a.out',
                    ],
                    stdout=devnull,
                    stderr=devnull,
                )

                self.assertEqual(expected_return, actual_return)

                # We don't clean up the C file in the finally clause because it can be useful to have in case of errors
                os.remove(os.path.join('examples', filename + '.c'))

        finally:
            try:
                os.remove('a.out')
            except OSError:
                pass

    setattr(MemoryLeakTest, 'test_' + filename, test)

filenames = (
    entry.name
    for entry in os.scandir('examples')
    if entry.is_file()
    if entry.name.endswith('.fur')
)

for filename in filenames:
    add_example_output_test(filename)
    add_example_memory_leak_test(filename)

unittest.main()
