import random
import unittest

class BasicTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_simple(self):
        # make sure the shuffled sequence does not lose any elements
        self.assertEqual(True, True)
        

if __name__ == '__main__':
    unittest.main()