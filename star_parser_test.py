import os
import re
import unittest

from pathlib import Path

import pandas as pd

from star_parser import StarParser


class testStarTab(unittest.TestCase):
    def setUp(self):
        working_dir = Path(os.path.abspath(__file__)).parent
        self.starfile = working_dir / "static/micrographs_ctf.star"
        self.parser = StarParser(self.starfile)
        self.tabs = self.parser.parse()
        self.first_tab = self.tabs["data_optics"]
        self.data_tab = self.tabs["data_micrographs"]

    def test_trim_column_values(self):
        # first line of 'MicrographName' is
        # MotionCorr/job017/Micrographs/FoilHole_26045257_Data_26043368_26043370_20210226_112817_fractions.mrc
        # stop=None
        res = self.data_tab.trim_column_values("MicrographName", start=1, stop=None)
        self.assertEqual(
            res["MicrographName"][0],
            "otionCorr/job017/Micrographs/FoilHole_26045257_Data_26043368_26043370_20210226_112817_fractions.mrc",
        )
        # start=None
        res = self.data_tab.trim_column_values("MicrographName", start=None, stop=9)
        self.assertEqual(res["MicrographName"][0], "MotionCorr")
        # start and stop are set
        res = self.data_tab.trim_column_values("MicrographName", start=1, stop=9)
        self.assertEqual(res["MicrographName"][0], "otionCorr")
        # store=True
        res = self.data_tab.trim_column_values(
            "MicrographName", start=1, stop=9, store=True
        )
        self.assertEqual(self.data_tab.to_df()["MicrographName"][0], "otionCorr")

    def test_trim_column_values_start_and_stop_are_None(self):
        with self.assertRaises(ValueError):
            res = self.data_tab.trim_column_values("MicrographName")

    def test_trim_column_values_start_and_stop_are_out_of_bounds(self):
        with self.assertRaises(ValueError):
            res = self.data_tab.trim_column_values("MicrographName", start=500)
        with self.assertRaises(ValueError):
            res = self.data_tab.trim_column_values("MicrographName", stop=500)
        with self.assertRaises(ValueError):
            res = self.data_tab.trim_column_values(
                "MicrographName", start=900, stop=-500
            )

    def test_get_columns(self):
        res = self.tabs["data_optics"].get_columns()
        exp = [
            "OpticsGroupName",
            "OpticsGroup",
            "MtfFileName",
            "MicrographOriginalPixelSize",
            "Voltage",
            "SphericalAberration",
            "AmplitudeContrast",
            "MicrographPixelSize",
        ]
        self.assertSequenceEqual(res, exp)
        res = self.tabs["data_micrographs"].get_columns()
        exp = [
            "MicrographName",
            "OpticsGroup",
            "CtfImage",
            "DefocusU",
            "DefocusV",
            "CtfAstigmatism",
            "DefocusAngle",
            "CtfFigureOfMerit",
            "CtfMaxResolution",
        ]
        self.assertSequenceEqual(res, exp)

    def test_get_labels(self):
        res = self.tabs["data_optics"].get_labels()
        exp = [
            "loop_",
            "_rlnOpticsGroupName #1",
            "_rlnOpticsGroup #2",
            "_rlnMtfFileName #3",
            "_rlnMicrographOriginalPixelSize #4",
            "_rlnVoltage #5",
            "_rlnSphericalAberration #6",
            "_rlnAmplitudeContrast #7",
            "_rlnMicrographPixelSize #8",
        ]
        self.assertSequenceEqual(res, exp)

    def test__update_labels(self):
        exp = [
            "loop_",
            "_rlnOpticsGroupName #1",
            "_rlnOpticsGroup #2",
            "_rlnMtfFileName #3",
        ]
        res = self.tabs["data_optics"]._update_labels(
            ["OpticsGroupName", "OpticsGroup", "MtfFileName"]
        )
        self.assertEqual(res, exp)

    def test_to_df(self):
        # columns are reasonable proxy for df comparison
        res = list(self.tabs["data_optics"].to_df().columns)
        exp = [
            "OpticsGroupName",
            "OpticsGroup",
            "MtfFileName",
            "MicrographOriginalPixelSize",
            "Voltage",
            "SphericalAberration",
            "AmplitudeContrast",
            "MicrographPixelSize",
        ]
        self.assertEqual(res, exp)
        # test that it does not generate the dataframe every time by mocking the df
        exp = pd.DataFrame([1, 2], [3, 4])
        self.tabs["data_optics"].df = exp
        # df has no clear ==, shape is a good enough proxy
        self.assertEqual(exp.shape, self.tabs["data_optics"].to_df().shape)

    def test_remove_columns(self):
        # this change should persist
        res = self.first_tab.remove_columns("MtfFileName", store=True)
        # this change should not persist in the tab, but return a df with the change
        res = self.first_tab.remove_columns(
            ["MicrographOriginalPixelSize", "Voltage"], store=False
        )
        returned = [
            "OpticsGroupName",
            "OpticsGroup",
            "SphericalAberration",
            "AmplitudeContrast",
            "MicrographPixelSize",
        ]
        self.assertSequenceEqual(list(res.columns), returned)
        in_object = [
            "OpticsGroupName",
            "OpticsGroup",
            "MicrographOriginalPixelSize",
            "Voltage",
            "SphericalAberration",
            "AmplitudeContrast",
            "MicrographPixelSize",
        ]
        self.assertSequenceEqual(list(self.first_tab.to_df().columns), in_object)

    def test_remove_missing_columns(self):
        with self.assertRaises(KeyError):
            res = self.first_tab.remove_columns("columnNotPresent")

    def test_add_columns(self):
        exp = [
            "OpticsGroupName",
            "OpticsGroup",
            "MtfFileName",
            "MicrographOriginalPixelSize",
            "Voltage",
            "SphericalAberration",
            "AmplitudeContrast",
            "MicrographPixelSize",
        ]
        # this change should not persist in the tab, but return a df with the change
        rows = self.first_tab.to_df().shape[0]
        df = pd.DataFrame({"Column1": ["a" * rows], "Column2": ["b" * rows]})
        returned = self.first_tab.add_columns(df["Column1"], store=False)
        exp_return = exp.copy() + ["Column1"]
        self.assertSequenceEqual(list(returned.columns), exp_return)
        self.assertSequenceEqual(list(self.first_tab.to_df().columns), exp)
        # this change should persist
        returned = self.first_tab.add_columns(df, store=True)
        exp_return = exp.copy() + ["Column1", "Column2"]
        self.assertSequenceEqual(list(returned.columns), exp_return)
        self.assertSequenceEqual(list(self.first_tab.to_df().columns), exp_return)

    def test_add_columns_not_df(self):
        with self.assertRaises(TypeError):
            self.first_tab.add_columns(["Column1"])

    def test_add_columns_wrong_shape(self):
        df = pd.DataFrame({"a": [1, 2, 3, 4]})
        # first tab has shape 1,1; df has 4,1
        with self.assertRaises(ValueError):
            self.first_tab.add_columns(df)

    def test_keep_only_columns(self):
        exp = [
            "OpticsGroupName",
            "OpticsGroup",
            "MtfFileName",
            "MicrographOriginalPixelSize",
            "Voltage",
            "SphericalAberration",
            "AmplitudeContrast",
            "MicrographPixelSize",
        ]
        # these are not permanent
        # single column
        returned = self.first_tab.keep_only_columns("OpticsGroupName")
        self.assertSequenceEqual(["OpticsGroupName"], list(returned.columns))
        self.assertSequenceEqual(list(self.first_tab.df.columns), exp)
        # list of columns
        returned = self.first_tab.keep_only_columns(["OpticsGroupName", "OpticsGroup"])
        self.assertSequenceEqual(
            ["OpticsGroupName", "OpticsGroup"], list(returned.columns)
        )
        # these should be permanent
        returned = self.first_tab.keep_only_columns(
            ["OpticsGroupName", "OpticsGroup"], store=True
        )
        self.assertSequenceEqual(
            ["OpticsGroupName", "OpticsGroup"], list(returned.columns)
        )
        self.assertSequenceEqual(
            ["OpticsGroupName", "OpticsGroup"], list(self.first_tab.df.columns)
        )

    def test_to_star(self):
        res = self.first_tab.to_star()
        res = re.sub(r"\s", "", res)
        exp = re.sub(r"\s", "", exp_star)
        self.assertEqual(res, exp)

    def test_substitute_columns_nonexisting_column(self):
        exp = [
            "OpticsGroupName",
            "OpticsGroup",
            "MtfFileName",
            "MicrographOriginalPixelSize",
            "Voltage",
            "SphericalAberration",
            "AmplitudeContrast",
            "MicrographPixelSize",
        ]
        df = pd.DataFrame({"OpticsGroup": ["YoLo"]})
        # non permanent
        res = self.first_tab.substitute_columns(df)
        self.assertEqual(res["OpticsGroup"], "YoLo")
        self.assertEqual(self.first_tab.df["OpticsGroup"], "1")
        # permanent
        res = self.first_tab.substitute_columns(df, store=True)
        self.assertEqual(res["OpticsGroup"], "YoLo")
        self.assertEqual(self.first_tab.df["OpticsGroup"], "YoLo")

    def test_substitute_columns_nonexisting_column(self):
        df = pd.DataFrame({"a": [1]})
        with self.assertRaises(AttributeError):
            self.first_tab.substitute_columns(df)

    def test_substitute_columns_wrong_argument(self):
        with self.assertRaises(TypeError):
            self.first_tab.substitute_columns("NotADataFrame")

    def test_substitute_columns_wrong_shape(self):
        df = pd.DataFrame({"a": [1, 2, 3, 4]})
        with self.assertRaises(ValueError):
            self.first_tab.substitute_columns(df)

    def test_fill_column_single_value(self):
        # not permanent
        res = self.first_tab.fill_column("OpticsGroup", "2", overwrite=True)
        self.assertEqual(res["OpticsGroup"][0], "2")
        self.assertEqual(self.first_tab.df["OpticsGroup"][0], "1")
        # permanent
        res = self.first_tab.fill_column("OpticsGroup", "2", overwrite=True, store=True)
        self.assertEqual(res["OpticsGroup"][0], "2")
        self.assertEqual(self.first_tab.df["OpticsGroup"][0], "2")

    def test_fill_column_create_false(self):
        with self.assertRaises(ValueError):
            self.first_tab.fill_column("NotExisting", "2")

    def test_fill_column_overwrite_false(self):
        with self.assertRaises(ValueError):
            self.first_tab.fill_column("OpticsGroup", "2")

    def test_reorder_columns(self):
        new_order = list(self.first_tab.columns())
        new_order.sort(reverse=True)
        # not permanent
        res = self.first_tab.reorder_columns(new_order)
        self.assertEqual(new_order, list(res.columns))
        self.assertNotEqual(new_order, list(self.first_tab.df.columns))
        # permanent
        res = self.first_tab.reorder_columns(new_order, store=True)
        self.assertEqual(new_order, list(res.columns))
        self.assertEqual(new_order, list(self.first_tab.df.columns))

    def test_reorder_columns_too_many_columns(self):
        new_order = list(self.first_tab.columns())
        new_order.append("extra")
        with self.assertRaises(ValueError):
            self.first_tab.reorder_columns(new_order)

    def test_reorder_columns_extra_columns(self):
        new_order = list(self.first_tab.columns())
        with self.assertRaises(ValueError):  # missing from input
            self.first_tab.reorder_columns(new_order[1:])
        new_order = new_order[1:] + ["NonExisting"]  # preserve length
        with self.assertRaises(ValueError):  # missing from table
            df = self.first_tab.reorder_columns(new_order)

    def test_add_prefix_to_column(self):
        # non permanent
        res = self.first_tab.add_prefix_to_column("vaffa", "OpticsGroup")
        self.assertEqual(res["OpticsGroup"][0], "vaffa1")
        self.assertEqual(self.first_tab.df["OpticsGroup"][0], "1")
        # permanent
        res = self.first_tab.add_prefix_to_column("vaffa", "OpticsGroup", store=True)
        self.assertEqual(res["OpticsGroup"][0], "vaffa1")
        self.assertEqual(self.first_tab.df["OpticsGroup"][0], "vaffa1")

    def test_add_prefix_to_nonexisting_column(self):
        with self.assertRaises(AttributeError):  # missing from input
            self.first_tab.add_prefix_to_column("prefix", "NotAColumn")

    def test_remove_string_from_column_name(self):
        # non permanent
        res = self.first_tab.remove_string_from_column_name("../../", "MtfFileName")
        self.assertEqual(res["MtfFileName"][0], "MTF/mtf_k3_CDS_300kV_FL1.star")
        self.assertEqual(
            self.first_tab.df["MtfFileName"][0], "../../MTF/mtf_k3_CDS_300kV_FL1.star"
        )
        # permanent
        res = self.first_tab.remove_string_from_column_name(
            "../../", "MtfFileName", store=True
        )
        self.assertEqual(res["MtfFileName"][0], "MTF/mtf_k3_CDS_300kV_FL1.star")
        self.assertEqual(
            self.first_tab.df["MtfFileName"][0], "MTF/mtf_k3_CDS_300kV_FL1.star"
        )

    def test_remove_string_from_nonexisting_column(self):
        with self.assertRaises(AttributeError):  # missing from input
            self.first_tab.remove_string_from_column_name("prefix", "NotAColumn")

    def test_rename_columns(self):
        old_names = ["OpticsGroupName", "OpticsGroup"]
        new_names = ["Change1", "Change2"]
        other_names = [
            "MtfFileName",
            "MicrographOriginalPixelSize",
            "Voltage",
            "SphericalAberration",
            "AmplitudeContrast",
            "MicrographPixelSize",
        ]
        unchanged = old_names + other_names
        changed = new_names + other_names
        # not stored
        df = self.first_tab.rename_columns(old_names, new_names, store=False)
        self.assertEqual(list(df.columns), changed)
        self.assertEqual(list(self.first_tab.columns()), unchanged)
        # stored
        df = self.first_tab.rename_columns(old_names, new_names, store=True)
        self.assertEqual(list(df.columns), changed)
        self.assertEqual(list(self.first_tab.columns()), changed)

    def test_rename_columns_not_lists(self):
        with self.assertRaises(TypeError):  # first not list
            self.first_tab.rename_columns("prefix", ["yalla"])
        with self.assertRaises(TypeError):  # second not list
            self.first_tab.rename_columns(["prefix"], "yalla")

    def test_rename_columns_different_length(self):
        with self.assertRaises(TypeError):  # lists of different length
            self.first_tab.rename_columns(["prefix", "foo"], ["yalla"])

    def test_rename_columns_missing(self):
        with self.assertRaises(ValueError):  # first not list
            self.first_tab.rename_columns(["prefix"], ["yalla"])

    def test_apply_regex_to_column(self):
        regex = re.compile("Micrographs/")
        pattern = "Movies/"
        column = "MicrographName"
        self.data_tab.apply_regex_to_column(regex, pattern, column, store=True)
        expected = "MotionCorr/job017/Movies/FoilHole_26045257_Data_26043368_26043370_20210226_112817_fractions.mrc"
        self.assertEqual(expected, self.data_tab.to_df()["MicrographName"][0])

    def test_apply_regex_to_missing_column(self):
        regex = re.compile("Micrographs/")
        pattern = "Movies/"
        column = "NotAColumn"
        with self.assertRaises(AttributeError):
            self.data_tab.apply_regex_to_column(regex, pattern, column, store=True)

    def test_apply_regex_to_missing_column_not_a_regex(self):
        regex = "Micrographs/"
        pattern = "Movies/"
        column = "NotAColumn"
        with self.assertRaises(AssertionError):
            self.data_tab.apply_regex_to_column(regex, pattern, column, store=True)

    def test_apply_regex_to_missing_column_replacement_not_a_string(self):
        regex = re.compile("Micrographs/")
        pattern = re.compile("Movies/")
        column = "NotAColumn"
        with self.assertRaises(AssertionError):
            self.data_tab.apply_regex_to_column(regex, pattern, column, store=True)


class testStarGeneralTab(unittest.TestCase):
    def setUp(self):
        working_dir = Path(os.path.abspath(__file__)).parent
        self.starfile = working_dir / "static/run_it025_model.star"
        self.parser = StarParser(self.starfile)
        self.tabs = self.parser.parse()

    def test_normal_init(self):
        self.assertIn("data_model_general", self.tabs.keys())

    def test_data_model_is_correct(self):
        exp_labels = [
            "_rlnReferenceDimensionality",
            "_rlnDataDimensionality",
            "_rlnOriginalImageSize",
            "_rlnCurrentResolution",
            "_rlnCurrentImageSize",
            "_rlnPaddingFactor",
            "_rlnIsHelix",
            "_rlnFourierSpaceInterpolator",
            "_rlnMinRadiusNnInterpolation",
            "_rlnPixelSize",
            "_rlnNrClasses",
            "_rlnNrBodies",
            "_rlnNrGroups",
            "_rlnNrOpticsGroups",
            "_rlnTau2FudgeFactor",
            "_rlnNormCorrectionAverage",
            "_rlnSigmaOffsetsAngst",
            "_rlnOrientationalPriorMode",
            "_rlnSigmaPriorRotAngle",
            "_rlnSigmaPriorTiltAngle",
            "_rlnSigmaPriorPsiAngle",
            "_rlnLogLikelihood",
            "_rlnAveragePmax",
        ]
        exp_body = [
            "3",
            "2",
            "420",
            "3.442353",
            "216",
            "2.000000",
            "0",
            "1",
            "10",
            "0.836000",
            "3",
            "1",
            "4421",
            "1",
            "100.000000",
            "0.763382",
            "5.175344",
            "0",
            "0.000000",
            "0.000000",
            "0.000000",
            "1.206244e+10",
            "0.455703",
        ]
        self.assertEqual(self.tabs["data_model_general"].labels, exp_labels)
        self.assertEqual(self.tabs["data_model_general"].body, exp_body)

    def test_to_star(self):
        # in starfiles that come from relion, the lines between startabs
        # can contain a random number of spaces,that are ignored.
        # these are not relevant. We output empty newlines.
        res = self.tabs["data_model_general"].to_star().split("\n")[:28]
        testfile = Path("static/run_it025_model.star")
        exp = testfile.read_text().split("\n")[:28]
        self.maxDiff = None
        self.assertEqual(res, exp)


exp_star = """# version 30001
data_optics
loop_
_rlnOpticsGroupName #1
_rlnOpticsGroup #2
_rlnMtfFileName #3
_rlnMicrographOriginalPixelSize #4
_rlnVoltage #5
_rlnSphericalAberration #6
_rlnAmplitudeContrast #7
_rlnMicrographPixelSize #8
opticsGroup1            1 ../../MTF/mtf_k3_CDS_300kV_FL1.star     0.418000   300.000000     2.700000     0.100000     0.836000"""

if __name__ == "__main__":
    unittest.main()
