#!/usr/bin/env python3
"""
OCS UI – Task Parameter Editor + JSON Saver
- PyQt5 desktop app
- Meets the exact UI + JSON spec you provided
"""

import json
import os
import re
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLabel, QComboBox, QSlider, QCheckBox, QLineEdit, QPushButton,
    QMessageBox, QSpacerItem, QSizePolicy
)

# ====== Config switches ======
SAVE_WITH_EXTENSION = True  # If False, saves exactly the session name with no ".json"

# ====== Mappings required by spec ======
SPEED_OPTIONS = [
    ("Slow (8s)", 8000),
    ("Medium (4s)", 4000),
    ("Fast (1s)", 1000),
]

DISTRACTION_OPTIONS = {
    "None":        [False, False],
    "Sound":       [False, True],
    "Light":       [True,  False],
    "Sound + Light":[True,  True],
}

SORTING_COLOURS = [
    ("2 Colours", 2),
    ("3 Colours", 3),
]

PACKAGING_SIZES = [
    ("High (6 Items)", 6),
    ("Medium (5 Items)", 5),
    ("Low (4 Items)", 4),
]

FILENAME_REGEX = re.compile(r"^[A-Za-z0-9_-]+$")


def combo_from_pairs(pairs):
    cb = QComboBox()
    for label, value in pairs:
        cb.addItem(label, userData=value)
    return cb


def combo_from_dict(d):
    cb = QComboBox()
    for label, value in d.items():
        cb.addItem(label, userData=value)
    return cb


class SortingTaskBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Sorting Task", parent)
        self.setCheckable(False)

        self.active = QCheckBox("Active")
        self.active.setChecked(True)

        self.speed = combo_from_pairs(SPEED_OPTIONS)

        # Error rate: 5–15, tick 1
        self.error = QSlider(Qt.Horizontal)
        self.error.setMinimum(5)
        self.error.setMaximum(15)
        self.error.setSingleStep(1)
        self.error.setTickInterval(1)
        self.error.setTickPosition(QSlider.TicksBelow)
        self.error.setValue(10)
        self.error_label = QLabel(f"{self.error.value()}%")
        self.error.valueChanged.connect(lambda v: self.error_label.setText(f"{v}%"))

        # Task-specific: number of colours
        self.num_colours = combo_from_pairs(SORTING_COLOURS)

        self.distraction = combo_from_dict(DISTRACTION_OPTIONS)

        form = QFormLayout()
        form.addRow(self.active)
        form.addRow("Speed:", self.speed)

        err_row = QHBoxLayout()
        err_row.addWidget(self.error)
        err_row.addWidget(self.error_label)
        form.addRow("Error Rate:", self._wrap(err_row))

        form.addRow("Number of Colours:", self.num_colours)
        form.addRow("Distraction:", self.distraction)

        self.setLayout(form)

    def _wrap(self, layout):
        w = QWidget()
        w.setLayout(layout)
        return w

    def to_dict(self):
        return {
            "active": self.active.isChecked(),
            "speed": self.speed.currentData(),            # 8000/4000/1000
            "errorRate": int(self.error.value()),         # 5..15
            "numColours": self.num_colours.currentData(), # 2 or 3
            "distraction": self.distraction.currentData() # [T,F] etc.
        }


class PackagingTaskBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Packaging Task", parent)
        self.setCheckable(False)

        self.active = QCheckBox("Active")
        self.active.setChecked(True)

        self.speed = combo_from_pairs(SPEED_OPTIONS)

        self.error = QSlider(Qt.Horizontal)
        self.error.setMinimum(5)
        self.error.setMaximum(15)
        self.error.setSingleStep(1)
        self.error.setTickInterval(1)
        self.error.setTickPosition(QSlider.TicksBelow)
        self.error.setValue(9)
        self.error_label = QLabel(f"{self.error.value()}%")
        self.error.valueChanged.connect(lambda v: self.error_label.setText(f"{v}%"))

        # Task-specific: package count
        self.package_num = combo_from_pairs(PACKAGING_SIZES)

        self.distraction = combo_from_dict(DISTRACTION_OPTIONS)

        form = QFormLayout()
        form.addRow(self.active)
        form.addRow("Speed:", self.speed)

        err_row = QHBoxLayout()
        err_row.addWidget(self.error)
        err_row.addWidget(self.error_label)
        form.addRow("Error Rate:", self._wrap(err_row))

        form.addRow("Package Count:", self.package_num)
        form.addRow("Distraction:", self.distraction)

        self.setLayout(form)

    def _wrap(self, layout):
        w = QWidget()
        w.setLayout(layout)
        return w

    def to_dict(self):
        return {
            "active": self.active.isChecked(),
            "speed": self.speed.currentData(),           # 8000/4000/1000
            "errorRate": int(self.error.value()),        # 5..15
            "packageNum": self.package_num.currentData(),# 4/5/6
            "distraction": self.distraction.currentData()
        }


class InspectionTaskBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Inspection Task", parent)
        self.setCheckable(False)

        self.active = QCheckBox("Active")
        self.active.setChecked(True)

        self.speed = combo_from_pairs(SPEED_OPTIONS)

        self.error = QSlider(Qt.Horizontal)
        self.error.setMinimum(5)
        self.error.setMaximum(15)
        self.error.setSingleStep(1)
        self.error.setTickInterval(1)
        self.error.setTickPosition(QSlider.TicksBelow)
        self.error.setValue(5)
        self.error_label = QLabel(f"{self.error.value()}%")
        self.error.valueChanged.connect(lambda v: self.error_label.setText(f"{v}%"))

        # Task-specific: size range slider 8..12 cm
        self.size = QSlider(Qt.Horizontal)
        self.size.setMinimum(8)
        self.size.setMaximum(12)
        self.size.setSingleStep(1)
        self.size.setTickInterval(1)
        self.size.setTickPosition(QSlider.TicksBelow)
        self.size.setValue(10)
        self.size_label = QLabel(f"{self.size.value()} cm")
        self.size.valueChanged.connect(lambda v: self.size_label.setText(f"{v} cm"))

        self.distraction = combo_from_dict(DISTRACTION_OPTIONS)

        form = QFormLayout()
        form.addRow(self.active)
        form.addRow("Speed:", self.speed)

        err_row = QHBoxLayout()
        err_row.addWidget(self.error)
        err_row.addWidget(self.error_label)
        form.addRow("Error Rate:", self._wrap(err_row))

        size_row = QHBoxLayout()
        size_row.addWidget(self.size)
        size_row.addWidget(self.size_label)
        form.addRow("Size Range (cm):", self._wrap(size_row))

        form.addRow("Distraction:", self.distraction)

        self.setLayout(form)

    def _wrap(self, layout):
        w = QWidget()
        w.setLayout(layout)
        return w

    def to_dict(self):
        return {
            "active": self.active.isChecked(),
            "speed": self.speed.currentData(),
            "errorRate": int(self.error.value()),
            "sizeRange": int(self.size.value()),  # 8..12
            "distraction": self.distraction.currentData()
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCS – Session Parameter Writer")
        self.setMinimumWidth(560)

        # Session bar
        session_row = QHBoxLayout()
        session_row.addWidget(QLabel("Session name:"))
        self.session_name = QLineEdit()
        self.session_name.setPlaceholderText("e.g., session_01")
        session_row.addWidget(self.session_name)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_json)
        session_row.addWidget(self.save_btn)

        # Task boxes
        self.sorting_box = SortingTaskBox()
        self.packaging_box = PackagingTaskBox()
        self.inspection_box = InspectionTaskBox()

        # Layout
        content = QWidget()
        v = QVBoxLayout(content)
        v.addLayout(session_row)
        v.addWidget(self.sorting_box)
        v.addWidget(self.packaging_box)
        v.addWidget(self.inspection_box)

        # Spacer + info
        v.addItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet("color: #555;")
        v.addWidget(self.status_label)

        self.setCentralWidget(content)

    def save_json(self):
        name = self.session_name.text().strip()

        if not name:
            self._error("Please enter a session name.")
            return

        if not FILENAME_REGEX.match(name):
            self._error("Invalid session name. Use only letters, numbers, underscores, or hyphens.")
            return

        # Build payload
        payload = {
            "sortingTask": self.sorting_box.to_dict(),
            "packagingTask": self.packaging_box.to_dict(),
            "inspectionTask": self.inspection_box.to_dict(),
        }

        # Decide path
        filename = f"{name}.json" if SAVE_WITH_EXTENSION else name
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            self._info(f"Saved: {filename}")
        except Exception as e:
            self._error(f"Failed to save: {e}")

    def _error(self, msg):
        QMessageBox.critical(self, "Error", msg)
        self.status_label.setText(msg)
        self.status_label.setStyleSheet("color: #b00020;")

    def _info(self, msg):
        QMessageBox.information(self, "Saved", msg)
        self.status_label.setText(msg)
        self.status_label.setStyleSheet("color: #2e7d32;")


def main():
    import sys
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
