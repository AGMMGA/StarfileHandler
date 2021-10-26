import tempfile
import unittest

import numpy as np

from cs_parser import CsParser


class test_parser(unittest.TestCase):
    def test_init_cs_file_exists(self):
        with tempfile.NamedTemporaryFile() as f:
            parser = CsParser(f.name)

    def test_init_cs_file_does_not_exist(self):
        with self.assertRaises(OSError):
            parser = CsParser("notafile")

    def test_basic_parser_works_on_array(self):
        x = np.array([0, 1, 2, 3], dtype=int)
        with tempfile.NamedTemporaryFile() as f:
            np.save(f, x, allow_pickle=True)
            f.seek(0)
            parser = CsParser(f.name)
            parser.parse_array()
            self.assertEqual(parser.columns, (int))

    def test_parser_fails_not_an_array(self):
        with tempfile.NamedTemporaryFile() as f:
            parser = CsParser(f.name)
            with self.assertRaises(OSError):
                parser.parse_array()


if __name__ == "__main__":
    unittest.main()
