#!/usr/bin/env python3
# Observer Control System – Columns UI (with controls & stats)
# - Class name: OCSWindow (imported by window_render.py)
# - __init__(self, taskWindow) per Week 12
# - Signals: playClicked, pauseClicked, stopClicked, settingsChanged
# - Start/Pause/Stop buttons
# - File Load dropdown + Load button
# - JSON save/load
# - settingsChanged emits: {
#       sortingEnabled: bool,
#       speed: int,             # ms per step (from speed combo)
#       numColours: int,
#       errorRate: int,         # %
#       distractions: list[str] # ["light","sound"] or []
#   }

import os, re, json, glob, sys
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QComboBox, QSlider, QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout,
    QGroupBox, QMessageBox, QFormLayout, QFileDialog, QFrame, QSpinBox
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


from DataCollection import dataCollection

# ---------- Config ----------
FILENAME_REGEX = re.compile(r"^[A-Za-z0-9_-]+$")
SAVE_WITH_EXTENSION = True
SCENARIOS_DIR = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Scenarios")

# ---------- Mappings ----------
SPEED_OPTIONS = [("Slow (8s)", 8000), ("Medium (4s)", 4000), ("Fast (1s)", 1000)]
# distraction value is [light, sound] -> we’ll convert to ["light","sound"]
DISTRACTION_OPTIONS = {
    "None": [False, False],
    "Sound": [False, True],
    "Light": [True, False],
    "Sound + Light": [True, True],
}
SORTING_COLOURS = [("2 Colours", 2), ("3 Colours", 3)]
PACKAGING_SIZES = [("High (6 Items)", 6), ("Medium (5 Items)", 5), ("Low (4 Items)", 4)]
RESOLUTIONS = [("2560x1440", [2560,1300]), ("1920x1080", [1920,980]), ("1366x768", [1366,668]),("1280x720", [1280,680])]

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
    """Left legend (title + G/Y/R squares)."""
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
            "speed": self.speed.currentData(),                  # ms
            "errorRate": int(self.error.slider.value()),        # %
            "numColours": self.num_colours.currentData(),       # 2 or 3
            "distraction": self.distraction.currentData(),      # [light, sound]
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


class MPLCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=5, dpi=100, ylimL=0, ylimU=20):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(1,1,1)

        self.axes.set_ylim([ylimL, ylimU])

        super().__init__(fig)
        

# ---------- MAIN WINDOW ----------
class OCSWindow(QMainWindow):
    # Week-12: expose signals so window_render.py can bind to them
    playClicked  = pyqtSignal()
    pauseClicked = pyqtSignal()
    stopClicked  = pyqtSignal()
    settingsChanged = pyqtSignal(dict)

    screenResolution = pyqtSignal()

    def __init__(self, taskWindow=None, parent=None):
        super().__init__(parent)
        self.taskWindow = taskWindow
        self.setWindowTitle("Observer Control System – UI")
        self.setMinimumSize(1200, 620)

        # Left rail: legend + Save/Load + run controls + file load dropdown
        legend = Legend()

        # Session Save
        self.session_edit = QLineEdit(); self.session_edit.setPlaceholderText("Session Name")
        self.save_btn = QPushButton("SAVE"); self.save_btn.clicked.connect(self.save_json)


        # Load by dropdown (lists *.json in CWD)
        self.file_combo = QComboBox()
        self.refresh_file_list()
        self.file_load_btn = QPushButton("File Load")
        self.file_load_btn.clicked.connect(self.load_from_combo)

        # Run controls
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn  = QPushButton("Stop")
        for b in (self.start_btn, self.pause_btn, self.stop_btn):
            b.setCursor(Qt.PointingHandCursor)

        # Screen Size Dropdown
        self.resolutionDrop = combo_from_pairs(RESOLUTIONS)

        # Data Collection 
        self.dataManager = dataCollection()
        self.collectionTimer = QTimer()
        self.collectionTimer.timeout.connect(self.manifestData)
        



        # Hook the buttons to signals (Week-12 binding)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.pause_btn.clicked.connect(lambda: self.pauseClicked.emit())
        self.stop_btn.clicked.connect(lambda: self.stopClicked.emit())

        self.getParNum = QSpinBox(self)


        # Left rail layout
        rail = QVBoxLayout()
        rail.addWidget(legend)
        rail.addSpacing(8)
        rail.addWidget(QLabel("Session:"))
        rail.addWidget(self.session_edit)
        rail.addWidget(self.save_btn)
        rail.addSpacing(10)
        rail.addSpacing(10)
        rail.addWidget(QLabel("File Load (dropdown):"))
        rail.addWidget(self.file_combo)
        rail.addWidget(self.file_load_btn)
        rail.addSpacing(10)
        rail.addWidget(QLabel("Controls:"))
        rail.addWidget(self.start_btn)
        rail.addWidget(self.pause_btn)
        rail.addWidget(self.stop_btn)
        rail.addWidget(self.resolutionDrop)
        rail.addSpacing(10)
        rail.addWidget(QLabel("Participant Number:"))
        rail.addWidget(self.getParNum)

        rail.addStretch(1)
        rail_w = QWidget(); rail_w.setLayout(rail)

        # Three task columns
        self.sorting = SortingColumn()
        self.packaging = PackagingColumn()
        self.inspection = InspectionColumn()

        # Top grid: [rail | Sorting | Packaging | Inspection]
        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(18)
        top_grid.addWidget(rail_w,         0, 0)
        top_grid.addWidget(self.sorting,   0, 1)
        top_grid.addWidget(self.packaging, 0, 2)
        top_grid.addWidget(self.inspection,0, 3)

        # Placeholder stats row (four panels)
        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(18)

        # Stats 
        iGb = QGroupBox('INSPECTION')
        iForm = QFormLayout()
        self.iErrorRate = QLabel("—")
        iForm.addRow("Error Rate (observed)", self.iErrorRate)
        self.iThroughput = QLabel("—")
        iForm.addRow("Throughput (Box/s)", self.iThroughput)
        self.iCorrections = QLabel("—")
        iForm.addRow("Corrections", self.iCorrections)
        iGb.setLayout(iForm)

        sGb = QGroupBox('SORTING')
        sForm = QFormLayout()
        self.sErrorRate = QLabel("—")
        sForm.addRow("Error Rate (observed)", self.sErrorRate)
        self.sThroughput = QLabel("—")
        sForm.addRow("Throughput (Box/s)", self.sThroughput)
        self.sCorrections = QLabel("—")
        sForm.addRow("Corrections", self.sCorrections)
        sGb.setLayout(sForm)

        pGb = QGroupBox('SORTING')
        pForm = QFormLayout()
        self.pErrorRate = QLabel("—")
        pForm.addRow("Error Rate (observed)", self.pErrorRate)
        self.pThroughput = QLabel("—")
        pForm.addRow("Throughput (Box/s)", self.pThroughput)
        self.pCorrections = QLabel("—")
        pForm.addRow("Corrections", self.pCorrections)
        pGb.setLayout(pForm)
        
        stats_grid.addWidget(sGb, 0, 0)
        stats_grid.addWidget(pGb, 0, 1)
        stats_grid.addWidget(iGb, 0, 2)

        # Status line
        self.status_lbl = QLabel("Ready.")
        self.status_lbl.setStyleSheet("color:#666;")

        # Charts !
        self.xAcc = list(range(10))
        self.yAccI = [0 for i in range(10)]
        self.yAccP = [0 for i in range(10)]
        self.yAccS = [0 for i in range(10)]

        self.xResp = list(range(10))
        self.yRespI = [0 for i in range(10)]
        self.yRespP = [0 for i in range(10)]
        self.yRespS = [0 for i in range(10)]

        self.iAccCanvas = MPLCanvas(self, width=5, height=5, dpi=100,ylimL = 0, ylimU =100)
        self._iAccRef = None

        self.iRespCanvas = MPLCanvas(self, width=5, height=5, dpi=100,ylimL = 0, ylimU =20)
        self._iRespRef = None

        self.pAccCanvas = MPLCanvas(self, width=5, height=5, dpi=100,ylimL = 0, ylimU =100)
        self._pAccRef = None

        self.pRespCanvas = MPLCanvas(self, width=5, height=5, dpi=100,ylimL = 0, ylimU =20)
        self._pRespRef = None

        self.sAccCanvas = MPLCanvas(self, width=5, height=5, dpi=100,ylimL = 0, ylimU =100)
        self._sAccRef = None

        self.sRespCanvas = MPLCanvas(self, width=5, height=5, dpi=100,ylimL = 0, ylimU =20)

        self._sRespRef = None

        stats_grid.addWidget(self.sAccCanvas, 1,0)
        self.updatePlot("sAcc", 0)
        stats_grid.addWidget(self.sRespCanvas, 1,1)
        self.updatePlot("sResp", 0)
        stats_grid.addWidget(self.iAccCanvas, 1,2)
        self.updatePlot("iAcc", 0)
        stats_grid.addWidget(self.iRespCanvas, 2,0)
        self.updatePlot("iResp", 0)
        stats_grid.addWidget(self.pAccCanvas,2,1)
        self.updatePlot("pAcc", 0)
        stats_grid.addWidget(self.pRespCanvas,2,2)
        self.updatePlot("pResp", 0)



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
        for p in sorted(glob.glob(SCENARIOS_DIR + "\\" + "*.json")):
            self.file_combo.addItem(p.replace(SCENARIOS_DIR + "\\", ""))

    # ---------- Data Collection -----------
    def manifestData(self):
        output = self.dataManager.retrieveMetrics()
        self.modifyAllMetricDisplay(output)
        return 
    
    def modifyAllMetricDisplay(self, data):
        if data["sortingTask"] is not None:
            sMetrics = data["sortingTask"]
            self.sErrorRate.setText(str(round(sMetrics[1],2)))
            self.sThroughput.setText(str(round(sMetrics[0],2)))
            self.sCorrections.setText(str(round(sMetrics[3],2)))
            if not self.yAccS[-1] == round(sMetrics[2],2):
                self.updatePlot("sAcc", round(sMetrics[2],2))
            if not self.yRespS[-1] == round(sMetrics[4],2):
                self.updatePlot("sResp", round(sMetrics[4],2))
        if data["packagingTask"] is not None:
            pMetrics = data["packagingTask"]
            self.pErrorRate.setText(str(round(pMetrics[1],2)))
            self.pThroughput.setText(str(round(pMetrics[0],2)))
            self.pCorrections.setText(str(round(pMetrics[3],2)))
            if not self.yAccP[-1] == round(pMetrics[2],2):
                self.updatePlot("pAcc", round(pMetrics[2],2))
            if not self.yRespP[-1] == round(pMetrics[4],2):
                self.updatePlot("pReso", round(pMetrics[4],2))
        if data["inspectionTask"] is not None:
            iMetrics = data["inspectionTask"]
            self.iErrorRate.setText(str(round(iMetrics[1],2)))
            self.iThroughput.setText(str(round(iMetrics[0],2)))
            self.iCorrections.setText(str(round(iMetrics[3],2)))
            if not self.yAccI[-1] == round(iMetrics[2],2):
                self.updatePlot("iAcc", round(iMetrics[2],2))
            if not self.yRespI[-1] == round(iMetrics[4],2):
                self.updatePlot("iResp", round(iMetrics[4],2))
        
    def updatePlot(self, graph, newData):

        match(graph):
            case "iAcc":
                self.iAccCanvas.axes.cla()
                self.yAccI = self.yAccI[1:] + [newData]
                if self._iAccRef is None:
                    plot_refs = self.iAccCanvas.axes.plot(self.xAcc, self.yAccI, 'r')
                else:
                    self._iAccRef.set_ydata(self.yAccI)
                self.iAccCanvas.axes.set_ylim([0,110])
                self.iAccCanvas.axes.title.set_text("Accuracy | Inspection")
                self.iAccCanvas.draw()
            case "iResp":
                self.iRespCanvas.axes.cla()
                self.yRespI = self.yRespI[1:] + [newData]
                if self._iRespRef is None:
                    plot_refs = self.iRespCanvas.axes.plot(self.xResp, self.yRespI, 'r')
                   
                else:
                    self._iRespRef.set_ydata(self.yRespI)
                self.iRespCanvas.axes.set_ylim([0,20])
                self.iRespCanvas.axes.title.set_text("Resp Time. | Inspection")
                self.iRespCanvas.draw()
           
            case "pAcc":
                self.pAccCanvas.axes.cla()
                self.yAccP = self.yAccP[1:] + [newData]
                if self._pAccRef is None:
                    plot_refs = self.pAccCanvas.axes.plot(self.xAcc, self.yAccP, 'r')
                    
                else:
                    self._pAccRef.set_ydata(self.yAccP)
                self.pAccCanvas.axes.set_ylim([0,110])
                self.pAccCanvas.axes.set_xlim([0,10])
                self.pAccCanvas.axes.title.set_text("Accuracy | Packaging")
                self.pAccCanvas.draw()
           
            case "pResp":
                self.pRespCanvas.axes.cla()
                self.yRespP = self.yRespP[1:] + [newData]
                if self._pRespRef is None:
                    plot_refs = self.pRespCanvas.axes.plot(self.xResp, self.yRespP, 'r')
                else:
                    self._pRespRef.set_ydata(self.yRespP)
                self.pRespCanvas.axes.set_ylim([0,20])
                self.pRespCanvas.axes.title.set_text("Resp. Time | Packaging")
                self.pRespCanvas.draw()
          
            case "sAcc":
                self.sAccCanvas.axes.cla()
                self.yAccS = self.yAccS[1:] + [newData]
                if self._sAccRef is None:
                    plot_refs = self.sAccCanvas.axes.plot(self.xAcc, self.yAccS, 'r')
                    
                else:
                    self._sAccRef.set_ydata(self.yAccS)
                self.sAccCanvas.axes.set_ylim([0,110])
                self.sAccCanvas.axes.title.set_text("Accuracy | Sorting")
                self.sAccCanvas.draw()
           
            case "sResp":
                self.sRespCanvas.axes.cla()
                self.yRespS = self.yRespS[1:] + [newData]
                if self._sRespRef is None:
                    plot_refs = self.sRespCanvas.axes.plot(self.xResp, self.yRespS, 'r')
                else:
                    self._sRespRef.set_ydata(self.yRespS)
                self.sRespCanvas.axes.set_ylim([0,20])
                self.sRespCanvas.axes.title.set_text("Resp. Time | Sorting")
                self.sRespCanvas.draw()

    def startCollectionTimer(self):
        self.collectionTimer.start(1000)
        

    def stopCollectionTimer(self, pause):
        if not pause:
            # Set Session once Task Stopped
            self.dataManager.getPreviousIDs()
        
        self.collectionTimer.stop()

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
        actualPath = os.path.join(SCENARIOS_DIR, filename)
        try:
            with open(actualPath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            self._info(f"Saved: {filename}")
            self.refresh_file_list()
        except Exception as e:
            self._error(f"Failed to save: {e}")

    def load_from_combo(self):
        if self.file_combo.currentText():
            self.load_json_from_path(SCENARIOS_DIR + "\\" + self.file_combo.currentText())

    def load_json_from_path(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.sorting.from_dict(data.get("sortingTask", {}))
            self.packaging.from_dict(data.get("packagingTask", {}))
            self.inspection.from_dict(data.get("inspectionTask", {}))
            self._info(f"Loaded: {os.path.basename(path)}")
            # also push settings to main when a file is loaded (Week-12)
            self._emit_settings()
        except Exception as e:
            self._error(f"Failed to load: {e}")

    # ---------- signal helpers ----------
    def _on_start_clicked(self):
        # emit settings first so main creates/updates task, then play
        self._emit_settings()
        self.playClicked.emit()
        self.dataManager.setNewParticipantID(self.getParNum.value())

    def _emit_settings(self):

        d = self.sorting.to_dict()
        dPack = self.packaging.to_dict()
        dInsp = self.inspection.to_dict()

        distractions = []
        if d.get("distraction", [False, False])[0]: distractions.append("light")
        if d.get("distraction", [False, False])[1]: distractions.append("sound")
        settings = {
            "sortingTask":{
                "sortingEnabled": bool(d.get("active", False)),
                "speed": int(d.get("speed", 4000)),              # ms per step
                "numColours": int(d.get("numColours", 2)),
                "errorRate": int(d.get("errorRate", 10)),
                "distractions": distractions,
            },
            "packagingTask": {
                "packagingEnabled": bool(dPack.get("active", False)),
                "speed": int(dPack.get("speed", 4000)),
                "errorRate": int(dPack.get("errorRate", 10)),
                "packageNum": int(dPack.get("packageNum", 4)),
                "distractions": dPack.get("distraction", [False, False])
            },
            "inspectionTask": {
                "inspectionEnabled": bool(dInsp.get("active", False)),
                "speed": int(dInsp.get("speed", 4000)),
                "sizeRange": int(dInsp.get("sizeRange", 8)),
                "errorRate": int(dInsp.get("errorRate", 10)),
                "distractions": dInsp.get("distraction", [False, False])
            },
            "resolution": self.resolutionDrop.currentData()
        }
        self.settingsChanged.emit(settings)

    # ---------- messaging ----------
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





