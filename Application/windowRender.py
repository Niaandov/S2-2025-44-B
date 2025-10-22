# windowRender.py
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import QTimer
import sys

from SortingTask import SortingTask
from ocs_ui import OCSWindow


# ---------------- Simple grid to host task render widgets ----------------
class taskGrid(QWidget):
    def __init__(self, minTileWidth: int, hgap: int, vgap: int):
        super().__init__()
        self.minTileWidth = minTileWidth
        self.hgap = hgap
        self.vgap = vgap
        self._widgets = []

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(12, 12, 12, 12)
        self.grid.setHorizontalSpacing(self.hgap)
        self.grid.setVerticalSpacing(self.vgap)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def addTaskWidget(self, w):
        if w and w not in self._widgets:
            w.setParent(self)
            self._widgets.append(w)
            self._relayout()

    def removeTaskWidget(self, w):
        if w in self._widgets:
            self._widgets.remove(w)
            w.setParent(None)
            w.deleteLater()
            self._relayout()

    def clear(self):
        for w in list(self._widgets):
            self.removeTaskWidget(w)

    def _columns(self):
        w = max(1, self.width())
        return max(1, int((w - self.hgap) // (self.minTileWidth + self.hgap)))

    def _relayout(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it and it.widget():
                it.widget().setParent(self)
        cols = self._columns()
        for i, w in enumerate(self._widgets):
            r, c = divmod(i, cols)
            self.grid.addWidget(w, r, c)
        for c in range(cols):
            self.grid.setColumnStretch(c, 1)
        self.grid.setRowStretch(self.grid.rowCount(), 1)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._relayout()


# --------------------------------- Main Window ---------------------------------
class testWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitoring Window")
        self.resize(1280, 720)

        self.sTask = None
        self._taskStartedOnce = False
        self._isPaused = False
        self._isRunning = False          # for Start button gating
        self._last_ocs = {}

        # --- UI shell ---
        top = QWidget(); top_l = QHBoxLayout(top); top_l.setContentsMargins(8, 8, 8, 8)
        root = QWidget(); root_l = QVBoxLayout(root); root_l.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(root)
        root_l.addWidget(top)

        self.grid = taskGrid(600, 10, 10)
        root_l.addWidget(self.grid)

        btnOpen = QPushButton("Open OCS")
        btnOpen.clicked.connect(self.showOCSWindow)
        top_l.addWidget(btnOpen)

        self.OCSWindow = None
        self.showOCSWindow()

    # ---------------- OCS window wiring ----------------
    def showOCSWindow(self):
        if self.OCSWindow is None:
            self.OCSWindow = OCSWindow()

            # OCS control buttons -> our handlers
            self.OCSWindow.playClicked.connect(self.play)
            self.OCSWindow.pauseClicked.connect(self.pause)
            self.OCSWindow.stopClicked.connect(self.stop)

            # Live settings sync (whenever a slider/toggle changes)
            if hasattr(self.OCSWindow, "settingsChanged"):
                self.OCSWindow.settingsChanged.connect(
                    lambda s: QTimer.singleShot(0, lambda: self._apply_settings_from_ocs(dict(s), source="settings"))
                )

            # Do the same when a file/session is loaded (try several common signal names)
            for sig_name in ("fileLoaded", "fileApplied", "sessionLoaded", "appliedToMain"):
                if hasattr(self.OCSWindow, sig_name):
                    getattr(self.OCSWindow, sig_name).connect(
                        lambda s=None: QTimer.singleShot(
                            0,
                            # some UIs emit the full settings, some emit None -> in that case, ask OCS for its current settings if it has a getter
                            lambda: self._apply_settings_from_ocs(
                                dict(s) if isinstance(s, dict) else dict(getattr(self.OCSWindow, "currentSettings", lambda: {})()),
                                source=sig_name
                            )
                        )
                    )

        self.OCSWindow.show()
        self.OCSWindow.raise_()
        self.OCSWindow.activateWindow()

    # ---------------- Helpers ----------------
    def _call_if(self, obj, name):
        fn = getattr(obj, name, None)
        if callable(fn):
            try:
                fn()
                return True
            except Exception:
                return False
        return False

    def _set_start_enabled(self, enabled: bool):
        """Disable/enable the Start button in the OCS window (best-effort)."""
        if not self.OCSWindow:
            return
        # Preferred API
        if hasattr(self.OCSWindow, "setStartEnabled"):
            try:
                self.OCSWindow.setStartEnabled(enabled)
                return
            except Exception:
                pass
        # Fallback: common attribute name
        try:
            btn = getattr(self.OCSWindow, "btnStart", None)
            if btn is not None and hasattr(btn, "setEnabled"):
                btn.setEnabled(enabled)
        except Exception:
            pass

    def _normalize(self, raw: dict) -> dict:
        """Normalize OCS settings; robust enable key detection."""
        s = dict(raw or {})

        # enabled flag (robust)
        enabled = None
        for k in ("sortingEnabled", "enabled"):
            if k in s:
                enabled = bool(s[k]); break
        if enabled is None:
            for k, v in s.items():
                name = str(k).lower()
                if "sort" in name and "enab" in name:
                    enabled = bool(v)
                    break
        if enabled is None:
            enabled = False

        # error rate (percent or fraction)
        try:
            err = float(s.get("errorRate", 0.0))
            if err > 1.0:
                err = err / 100.0
        except Exception:
            err = 0.0

        # speed
        try:
            speed = int(s.get("speed", 8000))
        except Exception:
            speed = 8000

        # colours
        try:
            n_raw = int(s.get("numColours", s.get("numColour", 3)))
        except Exception:
            n_raw = 3
        num_cols = max(3, n_raw)  # safety for builds that assume >=3

        # distractions
        distractions = list(s.get("distractions", []))

        return {
            "enabled": enabled,
            "errorRate": err,
            "speed": speed,
            "numColours": num_cols,
            "distractions": distractions,
        }

    def _dispose_sorting_task(self):
        """Stop timers, remove widget, drop reference, re-enable Start."""
        if not self.sTask:
            return

        # stop anything that looks like a loop/timer
        for name in ("stopTask", "stopTimer", "pauseTimer", "pause"):
            self._call_if(self.sTask, name)

        # remove render widget
        try:
            rw = getattr(self.sTask, "renderWindow", None)
            if rw is not None:
                self.grid.removeTaskWidget(rw)
        except Exception:
            pass

        self.sTask = None
        self._taskStartedOnce = False
        self._isPaused = False
        self._isRunning = False
        self._set_start_enabled(True)
        print("[testWindow] SortingTask disposed.")

    def _nudge_resume(self):
        """Gently nudge timers used by some SortingTask builds to actually move."""
        for name in ("renableTimer", "resumeTimer", "resume"):
            if self._call_if(self.sTask, name):
                break
        rw = getattr(self.sTask, "renderWindow", None)
        if rw and hasattr(rw, "update"):
            try: rw.update()
            except Exception: pass

    # ---------------- OCS settings handler (LIVE UPDATE) ----------------
    def _apply_settings_from_ocs(self, s: dict, source: str = "settings"):
        eff = self._normalize(s)
        self._last_ocs = dict(eff)
        print(f"[testWindow] OCS settings ({source}, normalized):", eff)

        print(eff)

        # If disabled -> immediately remove task & widget and re-enable Start
        if not eff["enabled"]:
            if self.sTask is not None:
                self._dispose_sorting_task()
            return

        # Enabled and no task -> create (do not auto-start)
        if self.sTask is None:
            try:
                print("[testWindow] Creating SortingTask:", eff["errorRate"], eff["speed"], eff["numColours"], eff["distractions"])
                self.sTask = SortingTask(eff["errorRate"], eff["speed"], eff["numColours"], eff["distractions"])
                if hasattr(self.sTask, "renderWindow") and self.sTask.renderWindow:
                    self.grid.addTaskWidget(self.sTask.renderWindow)

                # one natural init/update (teammate API)
                if hasattr(self.sTask, "updateTask"):
                    self.sTask.updateTask(
                        eff["errorRate"], eff["speed"], eff["numColours"], eff["distractions"]
                    )

                self._taskStartedOnce = False
                self._isPaused = False
                self._isRunning = False
                self._set_start_enabled(True)
                print("[testWindow] SortingTask ready; press Start to run.")
            except Exception as e:
                print("[testWindow] Failed to create SortingTask:", e)
            return

        # Enabled and task exists -> **LIVE UPDATE** immediately (as requested)
        try:
            if hasattr(self.sTask, "updateTask"):
                self.sTask.updateTask(
                    eff["errorRate"], eff["speed"], eff["numColours"], eff["distractions"]
                )
                print("[testWindow] updateTask() applied.")
                # If currently running, give a tiny nudge so visual changes reflect right away
                if self._isRunning:
                    QTimer.singleShot(0, self._nudge_resume)
        except Exception as e:
            print("[testWindow] Error applying updateTask:", e)

    # ---------------- Controls ----------------
    def play(self):
        print("[testWindow] Play clicked")
        if not self.sTask:
            print("[testWindow] No task. Enable Sorting in OCS to create it first.")
            return


        # First start
        if not self._taskStartedOnce:
            if self._call_if(self.sTask, "startTask"):
                self._taskStartedOnce = True
                self._isRunning = True
                self._isPaused = False
                self._set_start_enabled(False)    # disable Start while running
                print("[testWindow] SortingTask started.")
                # nudge to ensure motion on builds that need it
                QTimer.singleShot(0, self._nudge_resume)
                return

        # Resume path
        for name in ("renableTimer", "resumeTimer", "resume"):
            if self._call_if(self.sTask, name):
                self._isRunning = True
                self._isPaused = False
                self._set_start_enabled(False)
                print(f"[testWindow] SortingTask resumed via {name}.")
                QTimer.singleShot(0, self._nudge_resume)
                return

        print("[testWindow] No start/resume method found on SortingTask.")

    def pause(self):
        print("[testWindow] Pause clicked")
        if not self.sTask:
            return
        for name in ("stopTimer", "pauseTimer", "pauseTask", "pause"):
            if self._call_if(self.sTask, name):
                self._isPaused = True
                self._isRunning = False
                # keep Start disabled while paused? usually yes; resume should be used
                # if you want Start re-enabled on pause, change to True here
                print(f"[testWindow] Pause used {name}()")
                return
        print("[testWindow] No pause method found on SortingTask.")

    def stop(self):
        print("[testWindow] Stop clicked")
        if not self.sTask:
            return
        self._dispose_sorting_task()
        print("[testWindow] SortingTask fully stopped and removed.")


# -------------------------------- Entrypoint --------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = testWindow()
    w.show()
    sys.exit(app.exec())

