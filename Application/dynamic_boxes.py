## dynamic_boxes.py
# Dynamic boxes in PyQt5 with live sorting metrics integration.

import sys
from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QPushButton, QGridLayout, QScrollArea, QSizePolicy, QFrame, QLabel, QMenu
)

from ui_metrics_panel import MetricsPanel
from sorting_metrics import metrics


# ---------- A single box (uniform height) ----------
class Box(QFrame):
    _n = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Box._n += 1

        # look & size
        self.setObjectName("box")
        self.setStyleSheet("""
            QFrame#box { border: 1px solid #d0d0d0; border-radius: 8px; background: #fafafa; }
            QLabel     { font-size: 13px; }
            QPushButton{ padding: 4px 8px; }
        """)
        self.setMinimumWidth(240)
        self.setMinimumHeight(150)
        self.setMaximumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # layout & content
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        root.addWidget(QLabel(f"Box #{Box._n}"))

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        rm = QPushButton("Remove")
        rm.clicked.connect(self._remove_self)
        btn_row.addWidget(rm)
        root.addLayout(btn_row)

        # capture right-clicks anywhere inside this box (even over child widgets)
        self.installEventFilter(self)

    def _remove_self(self):
        """Count as correct, then remove via parent grid to keep bookkeeping clean."""
        metrics.record_correct()

        parent = self.parent()
        if hasattr(parent, "remove_box"):
            parent.remove_box(self)        # preferred path: updates the grid list + relayouts
        else:
            # fallback (shouldn't be needed)
            self.setParent(None)
            self.deleteLater()

        # refresh panel
        w = self.window()
        if hasattr(w, "metrics_panel"):
            w.metrics_panel.refresh()

    # ---- context menu via event filter ----
    def eventFilter(self, obj, event):
        if event.type() == QEvent.ContextMenu:
            self._show_error_menu(event.globalPos())
            return True
        return super().eventFilter(obj, event)

    def _show_error_menu(self, global_pos):
        menu = QMenu(self)
        menu.addAction("Log Error (Green)", lambda: self._log_error("green"))
        menu.addAction("Log Error (Red)",   lambda: self._log_error("red"))
        menu.addAction("Log Error (Blue)",  lambda: self._log_error("blue"))
        menu.exec_(global_pos)

    def _log_error(self, colour: str):
        metrics.record_error(colour)
        w = self.window()
        if hasattr(w, "metrics_panel"):
            w.metrics_panel.refresh()


# ---------- Responsive grid container ----------
class BoxGrid(QWidget):
    def __init__(self, min_tile_width=240, hgap=12, vgap=12):
        super().__init__()
        self.min_tile_width = min_tile_width
        self.hgap, self.vgap = hgap, vgap
        self._boxes = []

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(12, 12, 12, 12)
        self.grid.setHorizontalSpacing(self.hgap)
        self.grid.setVerticalSpacing(self.vgap)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # public API
    def add_box(self, box=None):
        box = box or Box()
        box.setParent(self)
        self._boxes.append(box)
        self._relayout()

    def remove_box(self, box):
        if box in self._boxes:
            self._boxes.remove(box)
            box.setParent(None)
            box.deleteLater()
            self._relayout()

    def clear(self):
        # remove *and* drop references so the list is truly empty
        while self._boxes:
            b = self._boxes.pop()
            b.setParent(None)
            b.deleteLater()
        self._relayout()

    # layout helpers
    def _columns(self):
        w = max(1, self.width())
        # how many min-width tiles fit with gaps
        cols = max(1, int((w - self.hgap) // (self.min_tile_width + self.hgap)))
        return cols

    def _relayout(self):
        # remove items from the grid layout, keep widgets alive (parent = self)
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it and it.widget():
                it.widget().setParent(self)

        cols = self._columns()

        for i, b in enumerate(self._boxes):
            r, c = divmod(i, cols)
            self.grid.addWidget(b, r, c)

        # make columns share space equally
        for c in range(cols):
            self.grid.setColumnStretch(c, 1)
        self.grid.setRowStretch(self.grid.rowCount(), 1)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._relayout()


# ---------- Main window ----------
class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Boxes (PyQt5)")
        self.resize(1160, 720)

        # ----- top controls -----
        top = QWidget()
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(8, 8, 8, 8)

        add_btn = QPushButton("Add Box")
        add_btn.clicked.connect(self._add)
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear)

        top_l.addWidget(add_btn)
        top_l.addWidget(clear_btn)
        top_l.addStretch(1)

        # ----- left side (scroll + grid) -----
        self.grid = BoxGrid(min_tile_width=240, hgap=12, vgap=12)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.grid)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.addWidget(top)
        left_l.addWidget(scroll)

        # ----- right side (metrics panel) -----
        self.metrics_panel = MetricsPanel(self)   # uses your existing panel

        # ----- root layout (left content + right panel) -----
        root = QWidget()
        root_h = QHBoxLayout(root)
        root_h.setContentsMargins(0, 0, 0, 0)
        root_h.addWidget(left, 1)                 # main content takes most space
        root_h.addWidget(self.metrics_panel, 0)   # compact metrics panel
        self.setCentralWidget(root)

        # start with a few boxes
        for _ in range(4):
            self._add()

    def _add(self):
        self.grid.add_box()

    def _clear(self):
        self.grid.clear()
        metrics.reset()                 # also reset counters
        self.metrics_panel.refresh()    # update panel immediately


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    sys.exit(app.exec_())
