import re
import sys

import pandas as pd

from pathlib import Path


class Hell(BaseException):
    pass


class StarParser:
    def __init__(self, starfile):
        self.file_name = Path(starfile)
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
            "newtab": re.compile("data_"),
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
            f"Current state {state} expects to be followed by {self.state_order[current_state]}"
        )

    def parse(self, file_blob=None):
        if file_blob is None:
            file_blob = self.blob
        current_state = "start"
        current_table = "data_"  # default name for a starfile single table
        # some star files do not have a table defined - we need to define one up front and maybe
        # substitute in a new table later once we have a name
        tabs = {current_table: StarTab(current_table, [], [], version=None)}
        for line in file_blob:
            line = line.strip()
            if not line:
                continue
            try:
                new_state = self.check_state(line, current_state)
            except Hell as e:
                raise NotImplemented("Format checking is not implemented yet") from e
            if new_state == "data":
                tabs[current_table].body.append(line.strip().split())
            elif new_state == "labels":
                tabs[current_table].labels.append(line)
            elif new_state == "version":
                tabs[current_table].version = line
            elif new_state == "newtab":
                if current_table == "data_":
                    version = tabs[
                        current_table
                    ].version  # version, if present, comes before table name
                    assert not tabs[
                        current_table
                    ].body  # we have not parsed any table yet, we MUST be empty
                    assert not tabs[
                        current_table
                    ].labels  # we have not parsed any table yet, we MUST be empty
                    tabs = {line: StarTab(line, [], [], version=version)}
                    current_table = line
                else:  # define tab beyond first
                    current_table = line
                    tabs[current_table] = StarTab(line, [], [], version=None)
        self.tabs = tabs
        return tabs

    def write_out(self, tabs="all"):
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
        return "\n".join(star)


class StarTab:
    def __init__(self, name, labels, body, version=None):
        self.body = body
        self.labels = labels
        self.version = version
        self.name = name

    def _update_from_df(self, df):
        self.labels = self._update_labels(list(df.columns))
        self.version = ""
        self.name = "data_"
        self.body = self._update_body(df)

    def _update_body(self, df):
        return [list(r)[1:] for r in df.to_records()]

    def __repr__(self):
        return f"StarTable {self.name} with {len(self.get_columns()) -1 } columns and {len(self.body)} record(s)"

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
            star.append(self.version)
        star.append(self.name)
        star = star + self.labels
        star = star + [" ".join(i) for i in (self.body + ["\n"])]
        return "\n".join(star)

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

    def remove_prefix_from_column(self, prefix, column, store=False):
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


def main():
    x = StarTabDf(pd.DataFrame({"aad": ["c"], "asda": ["a"]}))
    print(x)


if __name__ == "__main__":
    main()