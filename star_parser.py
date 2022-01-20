import re
import sys

import pandas as pd

from pathlib import Path


class Hell(BaseException):
    pass


class StarParser:
    def __init__(self, starfile, create=True):
        self.file_name = Path(starfile)
        if create:
            try:
                self.file_name.touch()
            except OSError as e:
                raise OSError(f"Cannot create file {self.file_name}") from e
        try:
            assert self.file_name.exists()
        except AssertionError as e:
            msg = f"The file {str(self.file_name)} does not exist. Exiting"
            raise AssertionError(msg)
        self.state_order = {
            "data": ["data", "newtab", "version"],
            "labels": ["labels", "data", "newtab"],
            "newtab": ["labels", "version"],
            "start": ["newtab", "labels", "version", "data"],
            "version": ["newtab", "labels", "data"],
        }
        self.state_token = {
            "data": re.compile(".+"),
            "labels": re.compile("^_rln|loop_"),
            "newtab": re.compile("^data_"),
            "version": re.compile("#\sversion\s"),
        }
        self.blob = self.read_file(self.file_name)

    def read_file(self, filename):
        with open(filename, "r") as f:
            return f.readlines()

    def check_state(self, line, current_state):
        for possible_state in self.state_order[current_state]:
            if self.state_token[possible_state].match(line):
                return possible_state
        raise Hell(
            f"Current state {self.state} expects to be followed by {self.state_order[current_state]}"
        )

    def parse(self, file_blob=None):
        if file_blob is None:
            file_blob = self.blob
        current_state = "start"
        version = ""
        tabs = {}
        for line in file_blob:
            line = line.strip()
            if not line:
                continue
            try:
                new_state = self.check_state(line, current_state)
            except Hell as e:
                raise NotImplemented("Format checking is not implemented yet") from e
            if new_state == "newtab":
                current_table = line
                if "_general" in current_table:  # define tab beyond first
                    tabs[current_table] = StarGeneralTab(current_table)
                else:
                    current_table = line
                    tabs[current_table] = StarTab(current_table)
                tabs[current_table].read_line(version, state="version")
            elif new_state == "version":
                version = line
            elif new_state in ["data", "labels"]:
                tabs[current_table].read_line(line, state=new_state)
        self.tabs = tabs
        return tabs

    def write_out(self, tabs="all", to_file=False, new_file=""):
        if new_file: #seems logical
            to_file=True
        if tabs == "all":
            requested = self.tabs
        else:
            if not isinstance(tabs, list):  # single tab requested
                tabs = [tabs]
            try:
                assert all([t in self.tabs.keys() for t in tabs])
                requested = {
                    key: value for key, value in self.tabs.items() if key in tabs
                }
            except AssertionError:
                sys.exit(f"Not all tabs in {tabs} exist in this data frame{self.tabs}")
        star = []
        for tab_name, tab_object in requested.items():
            star.append(tab_object.to_star())
        if not to_file:
            return "\n".join(star)
        else:
            if new_file:
                destination = Path(new_file)
            else:
                destination = self.file_name
            destination.write_text("\n".join(star))
            print(f"Data written to {destination}")

    def read_df(self, df):
        self.tabs = {}
        try:
            assert isinstance(df, pd.DataFrame)
            self.tabs["data_"] = StarTabDf(df)
        except AssertionError:
            raise TypeError(
                f"The object {df} does not appear to be a compatible pandas DataFrame"
            )
        return self.tabs


class StarTab:
    def __init__(self, name):
        self.body = []
        self.labels = []
        self.version = None
        self.name = name

    def __repr__(self):
        return f"StarTable {self.name} with {len(self.get_columns())} columns and {len(self.body)} record(s)"

    def _update_from_df(self, df):
        self.labels = self._update_labels(list(df.columns))
        self.version = ""
        self.name = "data_"
        self.body = self._update_body(df)

    def _update_body(self, df):
        return [list(r)[1:] for r in df.to_records()]

    def read_line(self, line, state):
        if state == "data":
            self.read_data_line(line)
        elif state == "labels":
            self.read_label_line(line)
        elif state == "version":
            self.read_version_line(line)

    def read_version_line(self, line: str):
        self.version = line

    def read_data_line(self, line: str):
        self.body.append(line.strip().split())

    def read_label_line(self, line: str):
        self.labels.append(line)

    def get_labels(self):
        return self.labels

    def columns(self):  # easier to remember?
        return self.get_columns()

    def get_columns(self, update=False):
        if not update:
            try:
                return self.clean_labels
            except AttributeError:
                pass
        # clean_labels missing or update is True
        clean_labels = []
        for l in self.labels[1:]:  # first is loop_, which we ignore
            # format of l should be something like '_rlnCtfAstigmatism #6'
            # with #6 optional
            clean_labels.append(l.split()[0].replace("_rln", ""))
        self.clean_labels = clean_labels
        return clean_labels

    def _update_labels(self, new_columns):
        labels = ["loop_"]
        for index, column_name in enumerate(new_columns):
            labels.append(f"_rln{column_name} #{index+1}")
        self.labels = labels
        self.clean_labels = self.get_columns(update=True)
        return labels

    def to_df(self):
        try:
            return self.df
        except AttributeError:
            columns = self.get_columns()
            self.df = pd.DataFrame(self.body, columns=columns)
            return self.df

    def to_dataframe(self):  # easier to remember?
        return self.to_df()

    def remove_columns(self, columns, store=False):
        try:
            if not store:
                return self.to_df().copy().drop(columns=columns)
            else:
                self.to_df().drop(columns=columns, inplace=True)
                self.labels = self._update_labels(self.df.columns)
                self.body = self._update_body(self.df)
                return self.df
        except KeyError as e:
            raise KeyError(
                f"Some columns in {columns} are missing from the dataframe"
            ) from e

    def add_columns(self, dataframe, store=False):
        target = self.to_df()
        try:
            # we only work with the same number of records in both dataframes
            assert dataframe.shape[0] == target.shape[0]
        except AttributeError as e:
            raise TypeError(
                "A pandas DataFrame or Series are required for this operation"
            ) from e
        except AssertionError:
            raise ValueError(
                f"Cannot add a dataframe of shape {dataframe.shape} to a dataframe of shape {target.shape}"
            )
        if not store:
            return pd.concat([target, dataframe], axis=1, join="inner")
        else:
            self.df = pd.concat([target, dataframe], axis=1, join="inner")
            self._update_labels(self.df.columns)
            self.body = self._update_body(self.df)
            return self.df

    def keep_only_columns(self, keep, store=False):
        if not isinstance(keep, list):
            keep = [keep]
        discard = [c for c in self.to_df().columns if c not in keep]
        if not store:
            return self.to_df().copy().drop(columns=discard)
        else:
            self.to_df().drop(columns=discard, inplace=True)
            self._update_labels(self.df.columns)
            self.body = self._update_body(self.df)
            return self.df

    def to_star(self):
        star = []
        if self.version:
            star.append("\n" + self.version + "\n")
        star.append(self.name + "\n")
        star = star + self.labels
        star = star + [" ".join(i) for i in (self.body + ["\n"])]
        return "\n".join(star) + "\n\n"

    def substitute_columns(self, dataframe, store=False):
        target = self.to_df()
        try:
            # we only work with the same number of records in both dataframes
            assert dataframe.shape[0] == target.shape[0]
        except AssertionError:
            raise ValueError(
                f"Cannot add a dataframe of shape {dataframe.shape} to a dataframe of shape {target.shape}"
            )
        except AttributeError:
            raise TypeError(
                "A pandas Dataframe or Series is required for this operation"
            )
        try:
            # all columns must be present in source and destination
            assert all([False for i in dataframe.columns if i not in target.columns])
        except AssertionError:
            missing = [c for c in dataframe.columns if c not in target.columns]
            raise AttributeError(
                f"Columns {missing} are missing from the destination dataframe"
            )
        if not store:
            x = target.copy()
        else:
            x = self.df
        for c in dataframe.columns:
            x[c] = dataframe[c]
        if store:
            self._update_labels(self.df.columns)
            self.body = self._update_body(self.df)
        return x

    def fill_column(self, columns, values, overwrite=False, store=False, create=False):
        """
        Fills the specified column(s) with the specified value(s)
        overwrite = True overwrites existing valuse in a column if set
        """
        # string to list if necessary
        if not isinstance(columns, list):
            columns = [columns]
        # check for inplace change
        if not store:
            df = self.to_df().copy()
        else:
            df = self.to_df()
        # check for possible overwrite
        overlap = [i for i in columns if i in self.df.columns]
        if len(overlap) and not overwrite:
            raise ValueError(
                f"Column(s) {overlap} already exist(s) in the star file. Please set overwrite=True to overwrite"
            )
        # check if new columns would be created
        new_columns = [i for i in columns if i not in list(self.df.columns)]
        if len(new_columns) and not create:
            raise ValueError(
                f"Column(s) {overlap} do not exist(s) in the star file. Please set create=True to create them"
            )
        # we can either do all columns with same value or each column with a value
        if not isinstance(values, list):
            values = [values]
        if len(values) == 1:
            values = values * len(columns)
        else:
            try:
                assert len(columns) == len(values)
            except AssertionError:
                raise ValueError(
                    "Mismatch between the number of values and columns. Please give either a single value or a value for each column"
                )
        for index, c in enumerate(columns):
            df[c] = str(values[index])
        if store:
            self._update_labels(self.df.columns)
            self.body = self._update_body(self.df)
        return df

    def reorder_columns(self, new_order, store=False):
        # check for inplace change
        if not store:
            df = self.to_df().copy()
        else:
            df = self.to_df()
        try:
            assert len(new_order) == len(df.columns)
            assert list(sorted(new_order)) == list(sorted(df.columns))
        except AssertionError:
            raise ValueError(
                f"\nThe reordered list of columns:\n {new_order} of length {len(new_order)}\n does not match the existing columns:\n {list(df.columns)} of length {len(df.columns)}"
            )
        df = df[new_order]
        if store:
            self.df = df
            self._update_labels(self.df.columns)
            self.body = self._update_body(self.df)
        return df

    def add_prefix_to_column(self, prefix, column, store=False):
        self.df = self.to_df()
        if store:
            target = self.df
        else:
            target = self.to_df().copy()
        try:
            assert column in list(target.columns)
        except AssertionError:
            raise AttributeError(f"There is no column named {column} in the dataframe")
        target[column] = prefix + target[column].astype(str)
        if store:
            self._update_labels(self.df.columns)
            self.body = self._update_body(self.df)
        return target

    def substitute_string_in_column_name(
        self, pattern, new_pattern, column, store=False
    ):
        self.df = self.to_df()
        if store:
            target = self.df
        else:
            target = self.to_df().copy()
        try:
            assert column in list(target.columns)
        except AssertionError:
            raise AttributeError(f"There is no column named {column} in the dataframe")
        target[column] = target[column].replace(pattern, new_pattern).astype(str)
        if store:
            self._update_labels(self.df.columns)
            self.body = self._update_body(self.df)
        return target

    def apply_regex_to_column(self, pattern, new_pattern, column, store=False):
        assert isinstance(pattern, type(re.compile("")))
        assert isinstance(new_pattern, str)
        self.df = self.to_df()
        if store:
            target = self.df
        else:
            target = self.to_df().copy()
        try:
            assert column in list(target.columns)
        except AssertionError:
            raise AttributeError(f"There is no column named {column} in the dataframe")
        target[column] = target.copy()[column].str.replace(
            pattern, new_pattern, regex=True
        )
        if store:
            self._update_labels(self.df.columns)
            self.body = self._update_body(self.df)
        return target

    def remove_string_from_column_name(self, prefix, column, store=False):
        self.df = self.to_df()
        if store:
            target = self.df
        else:
            target = self.to_df().copy()
        try:
            assert column in list(target.columns)
        except AssertionError:
            raise AttributeError(f"There is no column named {column} in the dataframe")
        new_series = []
        for value in target[column]:
            new_series.append(str(value).replace(prefix, ""))
        target[column] = new_series
        if store:
            self._update_labels(self.df.columns)
            self.body = self._update_body(self.df)
        return target

    def trim_column_values(self, column, start=None, stop=None, store=False):
        _strt = start
        _stp = stop
        self.df = self.to_df()
        # check column exists
        if store:
            target = self.df
        else:
            target = self.to_df().copy()
        try:
            assert column in list(target.columns)
        except AssertionError:
            raise AttributeError(f"There is no column named {column} in the dataframe")
        # check start and stop make sense
        if start is None and stop is None:
            raise ValueError("Please specify at least a start or a stop")
        if start is None:
            start = 0
        if stop is None:
            stop = -1
        try:
            start = int(start)
            stop = int(stop)
        except ValueError:
            raise ValueError("Invalid values for start: {_strt}, stop: {_stp}")
        try:
            value = target[column][0]
            assert abs(start) < len(value)
            assert abs(stop) <= len(value)
        except AssertionError:
            raise ValueError(
                f"Invalid slice start: {start}, stop: {stop} for row value of length {len(value)}"
            )
        # actually do stuff
        new_series = []
        if stop != -1:
            for value in target[column]:
                new_series.append(str(value[start : stop + 1]))
        else:
            for value in target[column]:
                new_series.append(str(value[start:]))
        target[column] = new_series
        if store:
            self._update_labels(self.df.columns)
            self.body = self._update_body(self.df)
        return target

    def rename_columns(self, old_names, new_names, store=False):
        self.df = self.to_df()
        if store:
            target = self.df
        else:
            target = self.to_df().copy()
        try:
            assert isinstance(old_names, list)
            assert isinstance(new_names, list)
            assert len(old_names) == len(new_names)
        except AssertionError:
            raise TypeError(
                f"Please ensure that old_names and new_names are lists of the same length"
            )
        try:
            assert all([False for i in old_names if i not in list(self.df.columns)])
        except AssertionError:
            raise ValueError(
                f"Not all columns in {old_names} are currently present in the dataframe columns ({self.columns()})"
            )
        mapper = dict(zip(old_names, new_names))
        target.rename(columns=mapper, inplace=True)
        if store:
            self._update_labels(target.columns)
        return target


class StarTabDf(StarTab):
    def __init__(self, from_df):
        self._update_from_df(from_df)


class StarGeneralTab(StarTab):
    """
    Deals with _general tabs, which have a different format compared to normal
    tabs. This class is not expected to perform any data manipulation, merely helps
    to maintain metadata consistency in complex starfiles.
    """

    def __repr__(self):
        return f"StarTable {self.name} with {len(self.get_columns())} columns and 1 record(s)"

    def read_data_line(self, line: str):
        raise ValueError("General tabs contain no data - formatting error")

    def read_label_line(self, line: str):
        label, value = line.split()
        self.labels.append(f"{label}")
        self.body.append(value)

    def _update_labels(self, new_columns):
        return new_columns

    def to_star(self):
        star = []
        if self.version:
            star.append("\n" + self.version + "\n")
        star.append(self.name + "\n")
        for index, label in enumerate(self.labels):
            # standard line length is 52, with spaces
            value = self.body[index]
            spaces = 52 - (len(label) + len(value))
            star.append(f"{label}{' '*spaces}{value}")
        return "\n".join(star) + "\n\n"


def main():
    x = StarTabDf(pd.DataFrame({"aad": ["c"], "asda": ["a"]}))
    print(x)


if __name__ == "__main__":
    main()
