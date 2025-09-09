# ui_metrics_panel.py
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QTimer
from sorting_metrics import metrics

GREEN = "#2e7d32"
RED   = "#c62828"
BLUE  = "#1565c0"

def _style_solid(btn: QPushButton, bg: str, fg: str = "white"):
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border: none;
            padding: 6px 10px;
            border-radius: 6px;
        }}
        QPushButton:pressed {{ opacity: 0.9; }}
    """)

def _style_outline(btn: QPushButton, color: str):
    btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {color};
            border: 2px solid {color};
            padding: 6px 10px;
            border-radius: 6px;
        }}
        QPushButton:hover {{ background-color: rgba(0,0,0,0.05); }}
    """)

class MetricsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)

        self.acc_label = QLabel("Accuracy: 0.0%")
        self.aer_label = QLabel("Actual error rate: 0.0%")
        self.thr_label = QLabel("Throughput (last 60s): 0 items/min")

        # colour-coded error labels
        row_err = QHBoxLayout()
        self.err_g = QLabel("G:0"); self.err_g.setStyleSheet(f"color:{GREEN}; font-weight:600;")
        self.err_r = QLabel("R:0"); self.err_r.setStyleSheet(f"color:{RED};   font-weight:600;")
        self.err_b = QLabel("B:0"); self.err_b.setStyleSheet(f"color:{BLUE};  font-weight:600;")
        row_err.addWidget(QLabel("Errors —"))
        row_err.addWidget(self.err_g); row_err.addWidget(self.err_r); row_err.addWidget(self.err_b)
        row_err.addStretch(1)

        # event buttons (optional; handy for demos)
        row_events = QHBoxLayout()
        btn_ok = QPushButton("Mark Correct"); _style_solid(btn_ok, "#4a4a4a")
        btn_e_g = QPushButton("Error: Green"); _style_solid(btn_e_g, GREEN)
        btn_e_r = QPushButton("Error: Red");   _style_solid(btn_e_r, RED)
        btn_e_b = QPushButton("Error: Blue");  _style_solid(btn_e_b, BLUE)
        for b in (btn_ok, btn_e_g, btn_e_r, btn_e_b): row_events.addWidget(b)

        # fix buttons
        row_fix = QHBoxLayout()
        btn_f_g = QPushButton("Fix Green"); _style_outline(btn_f_g, GREEN)
        btn_f_r = QPushButton("Fix Red");   _style_outline(btn_f_r, RED)
        btn_f_b = QPushButton("Fix Blue");  _style_outline(btn_f_b, BLUE)
        for b in (btn_f_g, btn_f_r, btn_f_b): row_fix.addWidget(b)

        # layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.acc_label)
        layout.addWidget(self.aer_label)
        layout.addWidget(self.thr_label)
        layout.addLayout(row_err)
        layout.addSpacing(6)
        layout.addLayout(row_events)
        layout.addLayout(row_fix)

        # wire demo buttons
        btn_ok.clicked.connect(lambda: (metrics.record_correct(), self.refresh()))
        btn_e_g.clicked.connect(lambda: (metrics.record_error("green"), self.refresh()))
        btn_e_r.clicked.connect(lambda: (metrics.record_error("red"),   self.refresh()))
        btn_e_b.clicked.connect(lambda: (metrics.record_error("blue"),  self.refresh()))
        btn_f_g.clicked.connect(lambda: (metrics.fix_error("green"), self.refresh()))
        btn_f_r.clicked.connect(lambda: (metrics.fix_error("red"),   self.refresh()))
        btn_f_b.clicked.connect(lambda: (metrics.fix_error("blue"),  self.refresh()))

        # auto-refresh so throughput stays current
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(500)
        self.refresh()

    def refresh(self):
        acc = metrics.accuracy
        acc_color = GREEN if acc >= 0.9 else ("#f57c00" if acc >= 0.7 else RED)
        self.acc_label.setText(f"Accuracy: {acc*100:.1f}%")
        self.acc_label.setStyleSheet(f"color:{acc_color}; font-weight:600;")
        self.aer_label.setText(f"Actual error rate: {metrics.actual_error_rate*100:.1f}%")
        self.thr_label.setText(f"Throughput (last 60s): {metrics.throughput_per_min} items/min")
        self.err_g.setText(f"G:{metrics.error_count.get('green',0)}")
        self.err_r.setText(f"R:{metrics.error_count.get('red',0)}")
        self.err_b.setText(f"B:{metrics.error_count.get('blue',0)}")
