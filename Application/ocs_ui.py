#!/usr/bin/env python3
# Observer Control System – Columns UI (with controls & stats)
# - Main class renamed to OCSWindow (per request)
# - Start/Pause/Stop buttons
# - File Load dropdown + Load button
# - Placeholder statistics layout
# - Same JSON schema & value mappings as before

import os, re, json, glob
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QComboBox, QSlider, QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout,
    QGroupBox, QMessageBox, QFrame, QFormLayout, QFileDialog
)

# ---------- Config ----------
FILENAME_REGEX = re.compile(r"^[A-Za-z0-9_-]+$")
SAVE_WITH_EXTENSION = True

# ---------- Mappings (unchanged spec) ----------
SPEED_OPTIONS = [("Slow (8s)", 8000), ("Medium (4s)", 4000), ("Fast (1s)", 1000)]
DISTRACTION_OPTIONS = {
    "None": [False, False],
    "Sound": [False, True],
    "Light": [True, False],
    "Sound + Light": [True, True],
}
SORTING_COLOURS = [("2 Colours", 2), ("3 Colours", 3)]
PACKAGING_SIZES = [("High (6 Items)", 6), ("Medium (5 Items)", 5), ("Low (4 Items)", 4)]

def combo_from_pairs(pairs):
    cb = QComboBox()
    for lbl, val in pairs:
        cb.addItem(lbl, val)
    return cb

def combo_from_dict(d):
    cb = QComboBox()
    for lbl, val in d.items():
        cb.addItem(lbl, val)
    return cb

class Legend(QWidget):
    """Left legend (title + G/Y/R squares) like the photo."""
    def __init__(self):
        super().__init__()
        def sq(color):
            f = QFrame(); f.setFixedSize(18, 18)
            f.setStyleSheet(f"background:{color}; border:1px solid #999; border-radius:3px;")
            return f
        title = QLabel("Observer Control System")
        title.setStyleSheet("font-weight:600; margin-bottom:6px;")
        colors = QHBoxLayout()
        colors.addWidget(sq("#4CAF50")); colors.addSpacing(8)
        colors.addWidget(sq("#FFC107")); colors.addSpacing(8)
        colors.addWidget(sq("#F44336"))
        v = QVBoxLayout(self)
        v.addWidget(title)
        v.addLayout(colors)
        v.addStretch(1)

class Header(QWidget):
    """Uppercase section title + Enable checkbox."""
    def __init__(self, text):
        super().__init__()
        lbl = QLabel(text.upper())
        lbl.setStyleSheet("font-weight:600; font-size:11px;")
        self.enable = QCheckBox("Enable")
        h = QHBoxLayout(self)
        h.addWidget(lbl); h.addStretch(1); h.addWidget(self.enable)

class SliderRow(QWidget):
    """Horizontal slider with live value label."""
    def __init__(self, minv, maxv, step, suffix, start):
        super().__init__()
        self.suffix = suffix
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(minv, maxv)
        self.slider.setSingleStep(step)
        self.slider.setTickInterval(step)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setValue(start)
        self.value_lbl = QLabel(f"{start}{suffix}")
        h = QHBoxLayout(self)
        h.addWidget(self.slider, 1)
        h.addWidget(self.value_lbl)
        self.slider.valueChanged.connect(lambda v: self.value_lbl.setText(f"{v}{self.suffix}"))

# ---------- Columns ----------
class SortingColumn(QWidget):
    def __init__(self):
        super().__init__()
        self.header = Header("Sorting")
        self.speed = combo_from_pairs(SPEED_OPTIONS)
        self.error = SliderRow(5, 15, 1, "%", 10)  # Base Error Rate
        self.distraction = combo_from_dict(DISTRACTION_OPTIONS)
        self.num_colours = combo_from_pairs(SORTING_COLOURS)

        form = QFormLayout()
        form.addRow(self.header)
        form.addRow("Speed", self.speed)
        form.addRow("Base Error Rate", self.error)
        form.addRow("Distraction", self.distraction)
        form.addRow("Colours", self.num_colours)

        box = QGroupBox(); box.setLayout(form)
        v = QVBoxLayout(self); v.addWidget(box)

    def to_dict(self):
        return {
            "active": self.header.enable.isChecked(),
            "speed": self.speed.currentData(),
            "errorRate": int(self.error.slider.value()),
            "numColours": self.num_colours.currentData(),
            "distraction": self.distraction.currentData(),
        }

    def from_dict(self, d):
        self.header.enable.setChecked(bool(d.get("active", False)))
        _set_combo_by_data(self.speed, d.get("speed", 8000))
        self.error.slider.setValue(int(d.get("errorRate", 10)))
        _set_combo_by_data(self.num_colours, d.get("numColours", 2))
        _set_combo_by_data(self.distraction, d.get("distraction", [False, False]))

class PackagingColumn(QWidget):
    def __init__(self):
        super().__init__()
        self.header = Header("Packaging")
        self.speed = combo_from_pairs(SPEED_OPTIONS)
        self.error = SliderRow(5, 15, 1, "%", 9)
        self.distraction = combo_from_dict(DISTRACTION_OPTIONS)
        self.package_num = combo_from_pairs(PACKAGING_SIZES)

        form = QFormLayout()
        form.addRow(self.header)
        form.addRow("Speed", self.speed)
        form.addRow("Base Error Rate", self.error)
        form.addRow("Distraction", self.distraction)
        form.addRow("Items / Package", self.package_num)

        box = QGroupBox(); box.setLayout(form)
        v = QVBoxLayout(self); v.addWidget(box)

    def to_dict(self):
        return {
            "active": self.header.enable.isChecked(),
            "speed": self.speed.currentData(),
            "errorRate": int(self.error.slider.value()),
            "packageNum": self.package_num.currentData(),
            "distraction": self.distraction.currentData(),
        }

    def from_dict(self, d):
        self.header.enable.setChecked(bool(d.get("active", False)))
        _set_combo_by_data(self.speed, d.get("speed", 8000))
        self.error.slider.setValue(int(d.get("errorRate", 9)))
        _set_combo_by_data(self.package_num, d.get("packageNum", 6))
        _set_combo_by_data(self.distraction, d.get("distraction", [False, False]))

class InspectionColumn(QWidget):
    def __init__(self):
        super().__init__()
        self.header = Header("Inspection")
        self.speed = combo_from_pairs(SPEED_OPTIONS)
        self.error = SliderRow(5, 15, 1, "%", 5)
        self.distraction = combo_from_dict(DISTRACTION_OPTIONS)
        self.size = SliderRow(8, 12, 1, " cm", 10)

        form = QFormLayout()
        form.addRow(self.header)
        form.addRow("Speed", self.speed)
        form.addRow("Base Error Rate", self.error)
        form.addRow("Distraction", self.distraction)
        form.addRow("Size Range", self.size)

        box = QGroupBox(); box.setLayout(form)
        v = QVBoxLayout(self); v.addWidget(box)

    def to_dict(self):
        return {
            "active": self.header.enable.isChecked(),
            "speed": self.speed.currentData(),
            "errorRate": int(self.error.slider.value()),
            "sizeRange": int(self.size.slider.value()),
            "distraction": self.distraction.currentData(),
        }

    def from_dict(self, d):
        self.header.enable.setChecked(bool(d.get("active", False)))
        _set_combo_by_data(self.speed, d.get("speed", 8000))
        self.error.slider.setValue(int(d.get("errorRate", 5)))
        self.size.slider.setValue(int(d.get("sizeRange", 10)))
        _set_combo_by_data(self.distraction, d.get("distraction", [False, False]))

def _set_combo_by_data(cb, value):
    for i in range(cb.count()):
        if cb.itemData(i) == value:
            cb.setCurrentIndex(i); break

# ---------- Stats (placeholder) ----------
def stats_panel(title, rows):
    gb = QGroupBox(title.upper())
    form = QFormLayout()
    for label, value in rows:
        form.addRow(label, QLabel(value))
    gb.setLayout(form)
    return gb

# ---------- MAIN WINDOW (renamed) ----------
class OCSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Observer Control System – UI")
        self.setMinimumSize(1200, 620)

        # Left rail: legend + Save/Load + run controls + file load dropdown
        legend = Legend()

        # Session Save
        self.session_edit = QLineEdit(); self.session_edit.setPlaceholderText("Session Name")
        self.save_btn = QPushButton("SAVE"); self.save_btn.clicked.connect(self.save_json)

        # Load by file picker
        self.load_path_edit = QLineEdit(); self.load_path_edit.setPlaceholderText("Choose JSON to Load")
        self.load_btn = QPushButton("LOAD"); self.load_btn.clicked.connect(self.load_json_dialog)

        # Load by dropdown (lists *.json in CWD)
        self.file_combo = QComboBox()
        self.refresh_file_list()
        self.file_load_btn = QPushButton("File Load")
        self.file_load_btn.clicked.connect(self.load_from_combo)

        # Run controls
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn  = QPushButton("Stop")
        # (wire these to your runtime later)
        for b in (self.start_btn, self.pause_btn, self.stop_btn):
            b.setCursor(Qt.PointingHandCursor)

        rail = QVBoxLayout()
        rail.addWidget(legend)
        rail.addSpacing(8)
        rail.addWidget(QLabel("Session:"))
        rail.addWidget(self.session_edit)
        rail.addWidget(self.save_btn)
        rail.addSpacing(10)
        rail.addWidget(QLabel("Load (picker):"))
        rail.addWidget(self.load_path_edit)
        rail.addWidget(self.load_btn)
        rail.addSpacing(10)
        rail.addWidget(QLabel("File Load (dropdown):"))
        rail.addWidget(self.file_combo)
        rail.addWidget(self.file_load_btn)
        rail.addSpacing(10)
        rail.addWidget(QLabel("Controls:"))
        rail.addWidget(self.start_btn)
        rail.addWidget(self.pause_btn)
        rail.addWidget(self.stop_btn)
        rail.addStretch(1)
        rail_w = QWidget(); rail_w.setLayout(rail)

        # Three task columns
        self.sorting = SortingColumn()
        self.packaging = PackagingColumn()
        self.inspection = InspectionColumn()

        # Top grid: [rail | Sorting | Packaging | Inspection]
        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(18)
        top_grid.addWidget(rail_w,       0, 0)
        top_grid.addWidget(self.sorting, 0, 1)
        top_grid.addWidget(self.packaging, 0, 2)
        top_grid.addWidget(self.inspection, 0, 3)

        # Placeholder stats row (four panels)
        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(18)
        stats_grid.addWidget(stats_panel("Sorting", [
            ("Error Rate (observed)", "—"),
            ("Throughput (60s)", "—"),
            ("Corrections (G/R/B)", "—"),
        ]), 0, 0)
        stats_grid.addWidget(stats_panel("Packaging", [
            ("Error Rate (observed)", "—"),
            ("Throughput (60s)", "—"),
            ("Corrections (#)", "—"),
        ]), 0, 1)
        stats_grid.addWidget(stats_panel("Inspection", [
            ("Error Rate (observed)", "—"),
            ("Throughput (60s)", "—"),
            ("Corrections (#)", "—"),
        ]), 0, 2)
        stats_grid.addWidget(stats_panel("Participant", [
            ("Avg. Correctness (%)", "—"),
            ("Z-Score", "—"),
            ("Accuracy (%)", "—"),
        ]), 0, 3)

        # Status line
        self.status_lbl = QLabel("Ready.")
        self.status_lbl.setStyleSheet("color:#666;")

        # Root layout
        root = QWidget()
        v = QVBoxLayout(root)
        v.addLayout(top_grid)
        v.addSpacing(8)
        v.addLayout(stats_grid)
        v.addWidget(self.status_lbl)
        self.setCentralWidget(root)

    # ---------- helpers ----------
    def refresh_file_list(self):
        self.file_combo.clear()
        for p in sorted(glob.glob("*.json")):
            self.file_combo.addItem(p)

    # ---------- save / load ----------
    def save_json(self):
        name = self.session_edit.text().strip()
        if not name:
            return self._error("Enter a session name.")
        if not FILENAME_REGEX.match(name):
            return self._error("Use letters, numbers, _ or - only.")

        payload = {
            "sortingTask": self.sorting.to_dict(),
            "packagingTask": self.packaging.to_dict(),
            "inspectionTask": self.inspection.to_dict(),
        }
        filename = f"{name}.json" if SAVE_WITH_EXTENSION else name
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            self._info(f"Saved: {filename}")
            self.refresh_file_list()
        except Exception as e:
            self._error(f"Failed to save: {e}")

    def load_json_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open OCS JSON", "", "JSON Files (*.json);;All Files (*)")
        if not path: return
        self.load_json_from_path(path)

    def load_from_combo(self):
        if self.file_combo.currentText():
            self.load_json_from_path(self.file_combo.currentText())

    def load_json_from_path(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.sorting.from_dict(data.get("sortingTask", {}))
            self.packaging.from_dict(data.get("packagingTask", {}))
            self.inspection.from_dict(data.get("inspectionTask", {}))
            self._info(f"Loaded: {os.path.basename(path)}")
        except Exception as e:
            self._error(f"Failed to load: {e}")

    def _error(self, msg):
        QMessageBox.critical(self, "Error", msg)
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet("color:#b00020;")

    def _info(self, msg):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet("color:#2e7d32;")

# ---------- entry ----------
def main():
    import sys
    app = QApplication(sys.argv)
    w = OCSWindow()   # renamed class
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
