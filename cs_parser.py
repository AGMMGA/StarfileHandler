## Parses cryosparc cs files
from pathlib import Path

import numpy as np
import pandas as pd

mappings = {
    "uid": "uid",
    "blob/path": "ImageName",
    "blob/idx": "blob/idx",
    "blob/shape": "blob/shape",
    "blob/psize_A": "PixelSize",
    "blob/sign": "blob/sign",
    "blob/import_sig": "blob/import_sig",
    "location/micrograph_uid": "MicrographUid",
    "location/exp_group_id": "OpticsGroup",
    "location/micrograph_path": "MicrographName",
    "location/micrograph_shape": "BoxSize",
    "location/center_x_frac": "FracCoordinateX",
    "location/center_y_frac": "FracCoordinateY",
    "alignments2D/split": "alignments2D/split",
    "alignments2D/shift": "alignments2D/shift",
    "alignments2D/pose": "alignments2D/pose",
    "alignments2D/psize_A": "alignments2D/psize_A",
    "alignments2D/error": "alignments2D/error",
    "alignments2D/error_min": "alignments2D/error_min",
    "alignments2D/resid_pow": "alignments2D/resid_pow",
    "alignments2D/slice_pow": "alignments2D/slice_pow",
    "alignments2D/image_pow": "alignments2D/image_pow",
    "alignments2D/cross_cor": "alignments2D/cross_cor",
    "alignments2D/alpha": "alignments2D/alpha",
    "alignments2D/alpha_min": "alignments2D/alpha_min",
    "alignments2D/weight": "alignments2D/weight",
    "alignments2D/pose_ess": "alignments2D/pose_ess",
    "alignments2D/shift_ess": "alignments2D/shift_ess",
    "alignments2D/class_posterior": "alignments2D/class_posterior",
    "alignments2D/class": "ClassNumber",
    "alignments2D/class_ess": "alignments2D/class_ess",
    "alignments3D/split": "alignments3D/split",
    "alignments3D/shift": "alignments3D/shift",
    "alignments3D/pose": "alignments3D/pose",
    "alignments3D/psize_A": "alignments3D/psize_A",
    "alignments3D/error": "alignments3D/error",
    "alignments3D/error_min": "alignments3D/error_min",
    "alignments3D/resid_pow": "alignments3D/resid_pow",
    "alignments3D/slice_pow": "alignments3D/slice_pow",
    "alignments3D/image_pow": "alignments3D/image_pow",
    "alignments3D/cross_cor": "alignments3D/cross_cor",
    "alignments3D/alpha": "alignments3D/alpha",
    "alignments3D/alpha_min": "alignments3D/alpha_min",
    "alignments3D/weight": "alignments3D/weight",
    "alignments3D/pose_ess": "alignments3D/pose_ess",
    "alignments3D/shift_ess": "alignments3D/shift_ess",
    "alignments3D/class_posterior": "alignments3D/class_posterior",
    "alignments3D/class": "alignments3D/class",
    "alignments3D/class_ess": "alignments3D/class_ess",
}


class CsParser:
    def __init__(self, cs_file) -> None:
        self.cs_filename = Path(cs_file)
        try:
            assert self.cs_filename.exists()
        except AssertionError:
            raise OSError(f"{str(self.cs_filename)} does not exist")

    def parse_array(self):
        try:
            self.cs_array = np.load(self.cs_filename)
        except OSError:  # not immediately obvious that this is the exception that gets raised...
            raise
        return self

    def clean_array(self):
        a = self.cs_array.copy()
        flat_keys, multidimensional_keys = self.detect_column_dimensionality(a)
        flattened = self.flatten_multidimensional_subarrays(a, multidimensional_keys)
        cleaned = self.rename_array_keys(a, flat_keys)
        return cleaned

    def detect_column_dimensionality(self, array):
        # get which keys correspond to multidimensional arrays
        dtypes = array.dtype.fields  # ('ColumnName', (dtype, dimensions))
        multidimensional = []
        flat = []
        for index, value in enumerate(list(array[0])):
            if isinstance(value, np.ndarray):  #
                key = list(array.dtype.fields.keys())[index]
                multidimensional.append(key)
            else:
                key = list(array.dtype.fields.keys())[index]
                flat.append(key)
        return flat, multidimensional

    def flatten_multidimensional_subarrays(
        self, parent_array, multidimensional_array_keys
    ):
        a = parent_array
        # make a dataframe after flattening coordinate and angles arrays
        mapping_coords = {0: "x", 1: "y", 2: "z"}
        mapping_angles = {0: "alpha", 1: "beta", 2: "gamma"}
        rascals = a[multidimensional_array_keys]
        index_column = range(a.shape[0])
        # make dummy index dataframe of correct size
        reformed = pd.DataFrame(index_column)
        for key in multidimensional_array_keys:
            # if the name of the column is poses, they are angles;
            # otherwise they are shifts
            if "pose" in key:  # these are angles
                mapping = mapping_angles
            else:  # these are coordinates or shifts
                mapping = mapping_coords
            # split the array into a list of n single columns
            split_arrays = np.hsplit(rascals[key], rascals[key].shape[-1])
            # rename their index
            for index, array in enumerate(split_arrays):
                new_dtype = f"{key}_{mapping[index]}"
                reformed[new_dtype] = pd.DataFrame(array)
        return reformed

    def rename_array_keys(self, array, keys):
        good = array[keys]
        df = pd.DataFrame(good)
        new_columns = []
        for c in df.columns:
            if c in mappings and mappings[c]:
                new_columns.append(mappings[c])
            else:
                new_columns.append(c)
        df.columns = new_columns
        return df

    def swap_coords(self, coord_x, coord_y):
        swapped_x, swapped_y = [], []
        return swapped_x, swapped_y

    def invert_coord(self, old_coord):
        return 1 - old_coord

    # def to_df(self):
    #     self.df = pd.DataFrame(self.cs_array, columns=self.column_names.keys())
    #     return self


def main():
    test_file = "/mnt/DATA/andrea/20210226_NeCen_BRCA1A_Ub/relion4/P52_J977_passthrough_particles.cs"
    parser = CsParser(test_file)
    array = parser.parse_array()
    print(array.to_df())


if __name__ == "__main__":
    main()
