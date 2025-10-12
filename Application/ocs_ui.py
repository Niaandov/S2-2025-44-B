#!/usr/bin/env python3
# Observer Control System – compact width + mid-page stats + clear gaps
# JSON fields preserved:
#   sortingTask:   active, speed, errorRate, numColours, distraction
#   packagingTask: active, speed, errorRate, packageNum, distraction
#   inspectionTask:active, speed, errorRate, sizeRange,  distraction

import os, re, json, glob, sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QComboBox, QSlider, QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout,
    QGroupBox, QMessageBox, QFrame, QFormLayout, QFileDialog, QSizePolicy,
    QScrollArea
)

# ---------------- constants / config ----------------
FILENAME_REGEX = re.compile(r"^[A-Za-z0-9_-]+$")
SPEED_OPTIONS = [("Slow (8s)", 8000), ("Medium (4s)", 4000), ("Fast (1s)", 1000)]
DISTRACTION_OPTIONS = {
    "None": [False, False],
    "Sound": [False, True],
    "Light": [True, False],
    "Sound + Light": [True, True],
}
SCENARIOS_DIR = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Scenarios")  # <— required folder

# Ensure the scenarios directory exists
os.makedirs(SCENARIOS_DIR, exist_ok=True)

# ---------------- helpers ----------------
def set_combo_by_data(cb, value):
    for i in range(cb.count()):
        if cb.itemData(i) == value:
            cb.setCurrentIndex(i)
            break

class SliderRow(QWidget):
    def __init__(self, minv, maxv, step, suffix, start):
        super().__init__()
        self.suffix = suffix
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(minv, maxv)
        self.slider.setSingleStep(step)
        self.slider.setTickInterval(step)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setValue(start)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.value_lbl = QLabel(f"{start}{suffix}")
        self.value_lbl.setMinimumWidth(44)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)
        lay.addWidget(self.slider, 1)
        lay.addWidget(self.value_lbl)
        self.slider.valueChanged.connect(lambda v: self.value_lbl.setText(f"{v}{self.suffix}"))

class SectionHeader(QWidget):
    def __init__(self, title):
        super().__init__()
        self.enable = QCheckBox("Enable")
        lbl = QLabel(title.upper())
        lbl.setStyleSheet("font-weight:600; letter-spacing:.2px;")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(lbl)
        row.addStretch(1)
        row.addWidget(self.enable)

def legend_widget():
    def dot(color):
        f = QFrame()
        f.setFixedSize(18, 18)
        f.setStyleSheet(f"background:{color}; border:1px solid #999; border-radius:3px;")
        return f
    title = QLabel("Observer Control System")
    title.setStyleSheet("font-weight:600;")
    dots = QHBoxLayout()
    dots.setSpacing(14)
    dots.addWidget(dot("#4CAF50"))
    dots.addWidget(dot("#FFC107"))
    dots.addWidget(dot("#F44336"))
    w = QWidget()
    v = QVBoxLayout(w)
    v.setSpacing(10)
    v.addWidget(title)
    v.addLayout(dots)
    v.addSpacing(8)
    return w

# ---------------- columns (Bins sliders; compact width) ----------------
class SortingCol(QWidget):
    def __init__(self):
        super().__init__()
        self.hdr = SectionHeader("Sorting")
        self.speed = QComboBox(); [self.speed.addItem(a,b) for a,b in SPEED_OPTIONS]
        self.err  = SliderRow(5, 15, 1, "%", 10)
        self.bins = SliderRow(2, 3, 1, "", 2)      # -> numColours
        self.dist = QComboBox(); [self.dist.addItem(a,b) for a,b in DISTRACTION_OPTIONS.items()]
        self.dist.setMinimumWidth(260)  # compact

        form = QFormLayout()
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(18)
        form.addRow(self.hdr)
        form.addRow("Speed", self.speed)
        form.addRow("Base Error Rate", self.err)
        form.addRow("Bins", self.bins)
        form.addRow("Distractions", self.dist)

        box = QGroupBox(); box.setLayout(form)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0,0,0,0)
        outer.addWidget(box)
        outer.addStretch(1)

    def to_dict(self):
        return {
            "active": self.hdr.enable.isChecked(),
            "speed": self.speed.currentData(),
            "errorRate": int(self.err.slider.value()),
            "numColours": int(self.bins.slider.value()),
            "distraction": self.dist.currentData(),
        }

    def from_dict(self, d):
        self.hdr.enable.setChecked(bool(d.get("active", False)))
        set_combo_by_data(self.speed, d.get("speed", 8000))
        self.err.slider.setValue(int(d.get("errorRate", 10)))
        self.bins.slider.setValue(int(d.get("numColours", 2)))
        set_combo_by_data(self.dist, d.get("distraction", [False, False]))

class PackagingCol(QWidget):
    def __init__(self):
        super().__init__()
        self.hdr = SectionHeader("Packaging")
        self.speed = QComboBox(); [self.speed.addItem(a,b) for a,b in SPEED_OPTIONS]
        self.err  = SliderRow(5, 15, 1, "%", 9)
        self.bins = SliderRow(4, 6, 1, "", 6)      # -> packageNum
        self.dist = QComboBox(); [self.dist.addItem(a,b) for a,b in DISTRACTION_OPTIONS.items()]
        self.dist.setMinimumWidth(260)

        form = QFormLayout()
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(18)
        form.addRow(self.hdr)
        form.addRow("Speed", self.speed)
        form.addRow("Base Error Rate", self.err)
        form.addRow("Bins", self.bins)
        form.addRow("Distractions", self.dist)

        box = QGroupBox(); box.setLayout(form)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0,0,0,0)
        outer.addWidget(box)
        outer.addStretch(1)

    def to_dict(self):
        return {
            "active": self.hdr.enable.isChecked(),
            "speed": self.speed.currentData(),
            "errorRate": int(self.err.slider.value()),
            "packageNum": int(self.bins.slider.value()),
            "distraction": self.dist.currentData(),
        }

    def from_dict(self, d):
        self.hdr.enable.setChecked(bool(d.get("active", False)))
        set_combo_by_data(self.speed, d.get("speed", 8000))
        self.err.slider.setValue(int(d.get("errorRate", 9)))
        self.bins.slider.setValue(int(d.get("packageNum", 6)))
        set_combo_by_data(self.dist, d.get("distraction", [False, False]))

class InspectionCol(QWidget):
    def __init__(self):
        super().__init__()
        self.hdr = SectionHeader("Inspection")
        self.speed = QComboBox(); [self.speed.addItem(a,b) for a,b in SPEED_OPTIONS]
        self.err  = SliderRow(5, 15, 1, "%", 5)
        self.bins = SliderRow(8, 12, 1, "", 10)    # -> sizeRange
        self.dist = QComboBox(); [self.dist.addItem(a,b) for a,b in DISTRACTION_OPTIONS.items()]
        self.dist.setMinimumWidth(260)

        form = QFormLayout()
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(18)
        form.addRow(self.hdr)
        form.addRow("Speed", self.speed)
        form.addRow("Base Error Rate", self.err)
        form.addRow("Bins", self.bins)
        form.addRow("Distractions", self.dist)

        box = QGroupBox(); box.setLayout(form)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0,0,0,0)
        outer.addWidget(box)
        outer.addStretch(1)

    def to_dict(self):
        return {
            "active": self.hdr.enable.isChecked(),
            "speed": self.speed.currentData(),
            "errorRate": int(self.err.slider.value()),
            "sizeRange": int(self.bins.slider.value()),
            "distraction": self.dist.currentData(),
        }

    def from_dict(self, d):
        self.hdr.enable.setChecked(bool(d.get("active", False)))
        set_combo_by_data(self.speed, d.get("speed", 8000))
        self.err.slider.setValue(int(d.get("errorRate", 5)))
        self.bins.slider.setValue(int(d.get("sizeRange", 10)))
        set_combo_by_data(self.dist, d.get("distraction", [False, False]))

# ---------------- stats block with clear gaps ----------------
def stats_block(title, rows):
    w = QWidget()
    v = QVBoxLayout(w)
    v.setSpacing(18)  # bigger internal spacing
    t = QLabel(title.upper())
    t.setStyleSheet("font-weight:600; letter-spacing:.2px;")
    v.addWidget(t)
    v.addSpacing(10)  # gap after title

    last = len(rows) - 1
    for i, label in enumerate(rows):
        line = QHBoxLayout()
        line.setSpacing(18)
        lab = QLabel(label)
        val = QLabel("—")
        line.addWidget(lab)
        line.addStretch(1)
        line.addWidget(val)
        v.addLayout(line)
        if i != last:
            v.addSpacing(10)  # gap between rows

    w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    return w

# ---------------- main window ----------------
class OCSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Observer Control System")
        self.resize(1250, 780)  # sensible default (no sideways scroll)
        self.setStyleSheet("""
            QGroupBox { border: 0; margin-top: 0; }
            QPushButton { min-height: 28px; }
        """)

        # Keep the latest loaded JSON in memory
        self.current_json = None

        # Left rail
        legend = legend_widget()
        self.session_edit = QLineEdit(); self.session_edit.setPlaceholderText("Session Name")
        self.save_btn = QPushButton("SAVE"); self.save_btn.clicked.connect(self.save_json)

        row_save = QHBoxLayout(); row_save.setSpacing(10)
        row_save.addWidget(self.session_edit, 1)
        row_save.addWidget(self.save_btn)

        self.load_edit = QLineEdit(); self.load_edit.setPlaceholderText("Session File")
        self.load_btn  = QPushButton("LOAD"); self.load_btn.clicked.connect(self.load_json_dialog)

        row_load = QHBoxLayout(); row_load.setSpacing(10)
        row_load.addWidget(self.load_edit, 1)
        row_load.addWidget(self.load_btn)

        self.file_combo = QComboBox(); self.refresh_file_list()
        self.file_load_btn = QPushButton("File Load"); self.file_load_btn.clicked.connect(self.load_from_combo)

        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn  = QPushButton("Stop")

        rail = QVBoxLayout()
        rail.setSpacing(16)
        rail.addWidget(legend)
        rail.addLayout(row_save)
        rail.addLayout(row_load)
        rail.addWidget(self.file_combo)
        rail.addWidget(self.file_load_btn)
        rail.addSpacing(10)
        rail.addWidget(self.start_btn)
        rail.addWidget(self.pause_btn)
        rail.addWidget(self.stop_btn)
        rail.addStretch(1)

        rail_w = QWidget(); rail_w.setLayout(rail)
        rail_w.setMinimumWidth(260)  # narrower rail to avoid horizontal scroll

        # Three task columns
        self.sorting    = SortingCol()
        self.packaging  = PackagingCol()
        self.inspection = InspectionCol()

        top = QGridLayout()
        top.setContentsMargins(20, 20, 20, 4)
        top.setHorizontalSpacing(56)   # compact gap between task columns
        top.setVerticalSpacing(22)
        top.addWidget(rail_w,          0, 0)
        top.addWidget(self.sorting,    0, 1)
        top.addWidget(self.packaging,  0, 2)
        top.addWidget(self.inspection, 0, 3)
        top.setColumnStretch(0, 1)   # rail
        top.setColumnStretch(1, 2)
        top.setColumnStretch(2, 2)
        top.setColumnStretch(3, 2)

        # Stats row (starts mid-page; clear gaps)
        stats = QGridLayout()
        stats.setContentsMargins(20, 8, 20, 16)
        stats.setHorizontalSpacing(56)
        stats.addWidget(stats_block("Sorting", [
            "Error Rate (errors/min)", "Throughput (items/min)", "Corrections (# of clicks)"
        ]), 0, 0)
        stats.addWidget(stats_block("Packaging", [
            "Error Rate (errors/min)", "Throughput (items/min)", "Corrections (# of clicks)"
        ]), 0, 1)
        stats.addWidget(stats_block("Inspection", [
            "Error Rate (errors/min)", "Throughput (items/min)", "Corrections (# of clicks)"
        ]), 0, 2)
        stats.addWidget(stats_block("Participant", [
            "Avg. Correction Time (s)", "Z-Score", "Accuracy (%)"
        ]), 0, 3)
        stats.setColumnStretch(0, 1)
        stats.setColumnStretch(1, 1)
        stats.setColumnStretch(2, 1)
        stats.setColumnStretch(3, 1)

        self.status = QLabel("Ready.")
        self.status.setStyleSheet("color:#666; margin-left:20px;")

        # Root → vertical-only scroll, stats start mid-page using stretches
        root = QWidget()
        root_v = QVBoxLayout(root)
        root_v.setSpacing(16)
        root_v.addLayout(top)

        # push stats toward the middle
        root_v.addStretch(2)

        root_v.addLayout(stats)

        # keep some space below before status
        root_v.addStretch(1)

        root_v.addWidget(self.status)

        scroll = QScrollArea()
        scroll.setWidget(root)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        # vertical-only scrolling
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.setCentralWidget(scroll)

    # ------------- save / load (Application/Scenarios) -------------
    def scenarios_path(self, filename):
        """Return absolute path for a file inside Application/Scenarios."""
        return os.path.join(SCENARIOS_DIR, filename)

    def refresh_file_list(self):
        """Populate dropdown with JSON files from Application/Scenarios."""
        self.file_combo.clear()
        files = sorted(glob.glob(os.path.join(SCENARIOS_DIR, "*.json")))
        for p in files:
            # show only the filename in the dropdown
            self.file_combo.addItem(os.path.basename(p))

    def save_json(self):
        """Save current settings to Application/Scenarios/<name>.json."""
        name = self.session_edit.text().strip()
        if not name:
            return self._err("Enter a session name.")
        if not FILENAME_REGEX.match(name):
            return self._err("Use letters, numbers, _ or - only.")

        payload = {
            "sortingTask": self.sorting.to_dict(),
            "packagingTask": self.packaging.to_dict(),
            "inspectionTask": self.inspection.to_dict(),
        }

        # Ensure folder exists and save there
        os.makedirs(SCENARIOS_DIR, exist_ok=True)
        fn = f"{name}.json"
        path = self.scenarios_path(fn)

        try:
            with open(path, "w+", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            self._ok(f"Saved: {path}")
            self.refresh_file_list()
        except Exception as e:
            self._err(f"Failed to save: {e}")

    def load_json_dialog(self):
        """Open file picker in Application/Scenarios and load the JSON."""
        os.makedirs(SCENARIOS_DIR, exist_ok=True)
        start_dir = os.path.abspath(SCENARIOS_DIR)
        path, _ = QFileDialog.getOpenFileName(
            self, "Open JSON",
            start_dir,
            "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        self.load_edit.setText(path)
        self.load_json_from_path(path)

    def load_from_combo(self):
        """Load the file selected in the dropdown (from Application/Scenarios)."""
        fn = self.file_combo.currentText().strip()
        if not fn:
            return
        path = self.scenarios_path(fn)
        self.load_edit.setText(path)
        self.load_json_from_path(path)

    def load_json_from_path(self, path):
        """Read JSON, apply settings to all columns, keep a copy in memory."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Apply to UI
            self.sorting.from_dict(data.get("sortingTask", {}))
            self.packaging.from_dict(data.get("packagingTask", {}))
            self.inspection.from_dict(data.get("inspectionTask", {}))

            # Store for later use
            self.current_json = data

            self._ok(f"Loaded: {os.path.basename(path)}")
        except Exception as e:
            self._err(f"Failed to load: {e}")

    # ------------- UI helpers -------------
    def _err(self, msg):
        QMessageBox.critical(self, "Error", msg)
        self.status.setText(msg)
        self.status.setStyleSheet("color:#b00020; margin-left:20px;")

    def _ok(self, msg):
        self.status.setText(msg)
        self.status.setStyleSheet("color:#2e7d32; margin-left:20px;")

# ------------- entry -------------
def main():
    import sys
    app = QApplication(sys.argv)
    w = OCSWindow()
    # w.showMaximized()  # optional
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
