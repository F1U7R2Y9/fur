import functools

def force_generator(to_type):
    def decorator(generator_function):
        @functools.wraps(generator_function)
        def forced_generator(*args, **kwargs):
            return to_type(generator_function(*args, **kwargs))

        return forced_generator

    return decorator

if __name__ == '__main__':
    import unittest

    class ForceGeneratorTests(unittest.TestCase):
        def test_forces_generator(self):
            forced_range = force_generator(list)(range)

            self.assertEqual(
                forced_range(10),
                [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            )

    unittest.main()
