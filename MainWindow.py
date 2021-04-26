import os
import sys

from pathlib import Path

from PyQt5 import QtWidgets, QtCore, uic

from star_parser import StarParser


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.work_folder = Path(os.path.abspath(__file__)).parent
        ui_file = self.work_folder / "ui/MainWindow.ui"
        uic.loadUi(ui_file, self)
        self.setup_ui()
        self.show()
        self.starFile1Parser = None
        self.starFile2Parser = None

    def setup_ui(self):
        self.starFile1Button.clicked.connect(self.browse_star)
        self.starFile2Button.clicked.connect(self.browse_star)
        self.starFile1ClearButton.clicked.connect(self.clear_browsed_star)
        self.starFile2ClearButton.clicked.connect(self.clear_browsed_star)

    def browse_star(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Single File",
            str(self.work_folder),
            "Star files *.star;;All files *.*",
        )
        filename = Path(filename)
        if self.sender() is self.starFile1Button:
            self.starFile1Text.setText(str(filename.resolve()))
            self.display_star(filename, self.starFile1TableViewer)
            self.starFile2Button.setEnabled(True)
            self.starFile2Text.setEnabled(True)
            self.starFile2ClearButton.setEnabled(True)
        elif self.sender() is self.starFile2Button:
            self.display_star(filename, self.starFile2TableViewer)
            self.starFile2Text.setText(str(filename.resolve()))

    def display_star(self, filename, tableWidget):
        if tableWidget is self.starFile1TableViewer:
            parser = StarParser(filename)
            self.starFile1Parser = parser
        elif tableWidget is self.starFile1TableViewer:
            parser = StarParser(filename)
            self.starFile2Parser = parser
        tabs = parser.parse(parser.blob)
        df = tabs[list(tabs.keys())[0]].to_df()
        rows, columns = df.shape
        if rows > 10:  # we only display the first 10 rows of data
            rows = 10
        tableWidget.setModel(QtCore.QAbstractTableModel())
        tableWidget.setRowCount(rows)
        tableWidget.setColumnCount(columns)
        self.setHorizontalHeaderLabels(list(df.columns))
        for column in range(columns):
            for row in range(rows):
                new_item = QWidgets.QTableWidgetItem(df.iloc[row, column])
                self.setItem(m, n, new_item)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def clear_browsed_star(self):
        if self.sender() is self.starFile1ClearButton:
            self.starFile2Button.setEnabled(False)
            self.starFile2Text.setEnabled(False)
            self.starFile2ClearButton.setEnabled(False)
            self.starFile1Text.setText("")
            self.starFile2Text.setText("")
            self.starFile1Parser = None
            self.starFile2Parser = None
        elif self.sender() is self.starFile2ClearButton:
            self.starFile2Text.setText("")
            self.starFile2Parser = None


if __name__ == "__main__":
    app = QtWidgets.QApplication(
        sys.argv
    )  # Create an instance of QtWidgets.QApplication
    window = MainWindow()  # Create an instance of our class
    app.exec_()  # Start the application
