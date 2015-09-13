#!/usr/bin/python3

import unittest
import A396

class TestA396(unittest.TestCase):
  def test_oob(self):
    a396 = A396.A396()
    try: a396.tquantile(-1, 0.95)
    except ValueError as e: self.assertEqual(e.args[0], "Invalid argument")
    try: a396.tquantile(5, 0)
    except ValueError as e: self.assertEqual(e.args[0], "Invalid argument")
    try: a396.tquantile(5, -0.5)
    except ValueError as e: self.assertEqual(e.args[0], "Invalid argument")
    try: a396.tquantile(5, 1.1)
    except ValueError as e: self.assertEqual(e.args[0], "Invalid argument")

    self.assertTrue(a396.compare(a396.tquantile(1, 0.05), 12.706204736174705, 1e-6))
    self.assertTrue(a396.compare(a396.tquantile(2, 0.05), 4.302652729749462, 1e-6))
    self.assertTrue(a396.compare(a396.tquantile(3, 0.05), 3.1824463052837038, 1e-5))
    self.assertTrue(a396.compare(a396.tquantile(3.5, 0.05), 2.9400886379827287, 1e-4))

if __name__=='__main__':
  unittest.main()

