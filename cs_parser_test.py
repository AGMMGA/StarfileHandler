import tempfile
import unittest

import numpy as np

from cs_parser import CsParser


class test_parser(unittest.TestCase):
    def setUp(self):
        self.test_file = "/mnt/DATA/andrea/20210226_NeCen_BRCA1A_Ub/relion4/P52_J977_passthrough_particles.cs"

    def test_init_cs_file_exists(self):
        with tempfile.NamedTemporaryFile() as f:
            parser = CsParser(f.name)

    def test_init_cs_file_does_not_exist(self):
        with self.assertRaises(OSError):
            parser = CsParser("notafile")

    # def test_basic_parser_works_on_array(self):
    #     x = np.array([0, 1, 2, 3], dtype=int)
    #     with tempfile.NamedTemporaryFile() as f:
    #         np.save(f, x, allow_pickle=True)
    #         f.seek(0)
    #         parser = CsParser(f.name)
    #         parser.parse_array()
    #         self.assertEqual(parser.columns, (int))

    def test_parser_fails_not_an_array(self):
        with tempfile.NamedTemporaryFile() as f:
            parser = CsParser(f.name)
            with self.assertRaises(OSError):
                parser.parse_array()

    def test_detect_colum_dimensionality(self):
        parser = CsParser(self.test_file)
        array = parser.parse_array().cs_array
        flat, multidimensional = parser.detect_column_dimensionality(array)
        self.assertIn("uid", flat)
        self.assertIn("blob/shape", multidimensional)

    def test_flatten_multidimensional_array(self):
        parser = CsParser(self.test_file)
        array = parser.parse_array().cs_array
        flat, multidimensional = parser.detect_column_dimensionality(array)
        flattened = parser.flatten_multidimensional_subarrays(array, multidimensional)
        self.assertTrue(
            set(["blob/shape_x", "blob/shape_y"]).issubset(set(flattened.columns))
        )
        self.assertTrue(
            set(
                [combi
                    "alignments_class_1/pose_alpha",
                    "alignments_class_1/pose_beta",
                    "alignments_class_1/pose_gamma",
                ]
            ).issubset(set(flattened.columns))
        )


if __name__ == "__main__":
    unittest.main()
