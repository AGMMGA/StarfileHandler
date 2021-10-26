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
        except OSError:
            raise
            # raise OSError(
            #     f"The file {self.cs_filename} does not seem to be a valid cryosparc cs file"
            # )
        # self.columns = self.cs_array.dtype
        return self

    def rename_columns(self):
        self.column_names = []
        # new_dtype = []
        for key, value in enumerate(self.cs_array.dtype.fields.items()):
            # value format: ('uid', (dtype('uint64'), 0)), i.e. (column_name, dtype tuple)
            # we immediately rename some known useful columns
            try:
                # print(value)
                # new_value = (mappings[value[0]], value[1])
                # new_dtype.append(new_value)
                self.column_names.append(mappings[value[0]])
            except KeyError:  # from mappings
                # new_dtype.append(value)
                self.column_names.append(value[0])
        # we re-decare the array with the new_dtype to save the updated labels
        # self.cs_array = np.array(self.cs_array[::], dtype=new_dtype)
        # return new_dtype
        return self

        # self.column_names = []
        # for _, value in enumerate(self.cs_array.dtype.fields.items()):
        #     # value format: ('uid', (dtype('uint64'), 0)), i.e. (column_name, dtype tuple)
        #     try:
        #         # we immediately rename some known useful columns
        #         if mappings[value[0]]:
        #             self.column_names.append(mappings[value[0]])
        #         else:
        #             self.column_names.append(value[0])
        #     except KeyError:
        #         # some columns might exist that are not in the mappings. We simply copy those
        #         self.column_names.append(value)
        return self

    def swap_coords(self, coord_x, coord_y):
        swapped_x, swapped_y = [], []
        return swapped_x, swapped_y

    def invert_coord(self, old_coord):
        return 1 - old_coord

    # def to_df(self):
    #     self.df = pd.DataFrame(self.cs_array, columns=self.column_names.keys())
    #     return self


def main():
    test_file = (
        "/mnt/DATA/andrea/20210226_NeCen_BRCA1A_Ub/relion4/extracted_particles.cs"
    )
    parser = CsParser(test_file)
    array = parser.parse_array()
    array = array.parse_columns()
    print(array.to_df())


if __name__ == "__main__":
    main()
