# windowRender.py
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import QTimer
import sys

from SortingTask import SortingTask
from inspectionTask import inspectionTask
from PackingTask import PackagingTask
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
        self.pTask = None
        self.iTask = None
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

    def _normalizePackaging(self, raw: dict) -> dict:
            
            s = dict(raw or {})

            # enabled flag (robust)
            enabled = None
            for k in ("packagingEnabled", "enabled"):
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
                n_raw = int(s.get("packageNum", s.get("packageNum", 4)))
            except Exception:
                n_raw = 4
            num_cols = max(4, n_raw)  # safety for builds that assume >=4

            # distractions
            distractions = list(s.get("distractions", []))

            return {
                "enabled": enabled,
                "errorRate": err,
                "speed": speed,
                "packageNum": num_cols,
                "distractions": distractions,
            }
    

    def _normalizeInspection(self, raw: dict) -> dict:
            
            s = dict(raw or {})

            # enabled flag (robust)
            enabled = None
            for k in ("inspectionEnabled", "enabled"):
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
                n_raw = int(s.get("sizeRange", s.get("sizeRange", 8)))
            except Exception:
                n_raw = 8
            num_cols = max(8, n_raw)  # safety for builds that assume >=4

            # distractions
            distractions = list(s.get("distractions", []))

            return {
                "enabled": enabled,
                "errorRate": err,
                "speed": speed,
                "sizeRange": num_cols,
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
        if self.pTask is None and self.iTask is None:
            self._taskStartedOnce = False
        self._isPaused = False
        self._isRunning = False
        self._set_start_enabled(True)
        print("[testWindow] SortingTask disposed.")

    def _dispose_packaging_task(self):
        """Stop timers, remove widget, drop reference, re-enable Start."""
        if not self.pTask:
            return
    

        # stop anything that looks like a loop/timer
        for name in ("stopTask", "stopTimer", "pauseTimer", "pause"):
            self._call_if(self.pTask, name)

        # remove render widget
        try:
            rw = getattr(self.pTask, "renderWindow", None)
            if rw is not None:
                self.grid.removeTaskWidget(rw)
        except Exception:
            pass

        self.pTask = None
        if self.sTask is None and self.iTask is None:
            self._taskStartedOnce = False
        self._isPaused = False
        self._isRunning = False
        self._set_start_enabled(True)
        print("[testWindow] PackagingTask disposed.")
    
    def _dispose_inspection_task(self):
        """Stop timers, remove widget, drop reference, re-enable Start."""
        if not self.iTask:
            return
    

        # stop anything that looks like a loop/timer
        for name in ("stopTask", "stopTimer", "pauseTimer", "pause"):
            self._call_if(self.iTask, name)

        # remove render widget
        try:
            rw = getattr(self.iTask, "renderWindow", None)
            if rw is not None:
                self.grid.removeTaskWidget(rw)
        except Exception:
            pass

        self.iTask = None
        if self.pTask is None and self.sTask is None:
            self._taskStartedOnce = False
        self._isPaused = False
        self._isRunning = False
        self._set_start_enabled(True)
        print("[testWindow] InspectionTask disposed.")



    def _nudge_resume(self):
        """Gently nudge timers used by some SortingTask builds to actually move."""
        for name in ("renableTimer", "resumeTimer", "resume"):
            if self._call_if(self.sTask, name):
                break
        rw = getattr(self.sTask, "renderWindow", None)
        if rw and hasattr(rw, "update"):
            try: rw.update()
            except Exception: pass

    # ---------------- Decipher Size for Individual Task -----------------
    def calculateTaskSize(self, maxResolution, activeTasks):
        taskWidth = (maxResolution[0] - (24 + (activeTasks - 1 * 10))) // activeTasks
        taskHeight = maxResolution[1]

        return [taskWidth, taskHeight]


    # ---------------- OCS settings handler (LIVE UPDATE) ----------------
    def _apply_settings_from_ocs(self, s: dict, source: str = "settings"):
        eff = self._normalize(s["sortingTask"])
        effI = self._normalizeInspection(s["inspectionTask"])
        effP = self._normalizePackaging(s["packagingTask"])
        self._last_ocs = dict(eff)
        print(f"[testWindow] OCS settings ({source}, normalized):", eff)

        print(eff)
        print(effI)
        print(effP)

        print(s["resolution"])

        taskNum = 0
        # If disabled -> immediately remove task & widget and re-enable Start
        if not eff["enabled"]:
            if self.sTask is not None:
                self._dispose_sorting_task()
        else:
            taskNum += 1
        
        if not effI["enabled"]:
            if self.iTask is not None:
                self._dispose_inspection_task()
        else:
            taskNum += 1

        if not effP["enabled"]:
            if self.pTask is not None:
                self._dispose_packaging_task()
        else:
            taskNum += 1

        if taskNum == 0:
            # No tasks exist, so why bother? Get outta here!
            return

        # Calculate resolution for tasks
        taskResolution = self.calculateTaskSize(s["resolution"], taskNum)
        self.resize(s["resolution"][0], s["resolution"][1])

        
        


        # Enabled and no task -> create (do not auto-start)
        if self.sTask is None and eff["enabled"]:
            try:
                print("[testWindow] Creating SortingTask:", eff["errorRate"], eff["speed"], eff["numColours"], eff["distractions"])
                self.sTask = SortingTask(eff["errorRate"], eff["speed"], eff["numColours"], eff["distractions"],taskResolution[0], taskResolution[1])
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

        if self.iTask is None and effI["enabled"]:
            print("Getting here, something else is wrong")
            try:
                self.iTask = inspectionTask(effI["errorRate"], effI["speed"], effI["sizeRange"], effI["distractions"], taskResolution[0], taskResolution[1])
                if hasattr(self.iTask, "renderWindow") and self.iTask.renderWindow:
                    self.grid.addTaskWidget(self.iTask.renderWindow)
            except Exception as e: 
                print("[testWindow] Failed to create Inspection Task", e)


        if self.pTask is None and effP["enabled"]:
            try:
                self.pTask = PackagingTask(effP["errorRate"], effP["speed"], effP["packageNum"], effP["distractions"], taskResolution[0], taskResolution[1])
                if hasattr(self.pTask, "renderWindow") and self.pTask.renderWindow:
                    self.grid.addTaskWidget(self.pTask.renderWindow)
            except Exception as e: 
                print("[testWindow] Failed to create Packaging Task", e)



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
        if not self.sTask and not self.iTask and not self.pTask:
            print("[testWindow] No Tasks enabled")
            return


        # First start
        if not self._taskStartedOnce:
            if self.sTask is not None:
                if self._call_if(self.sTask, "startTask"):
                    self._taskStartedOnce = True
                    self._isRunning = True
                    self._isPaused = False
                    self._set_start_enabled(False)    # disable Start while running
                    print("[testWindow] SortingTask started.")
                    # nudge to ensure motion on builds that need it
                    QTimer.singleShot(0, self._nudge_resume)

            if self.iTask is not None:
                if self._call_if(self.iTask, "startTask"):
                    self._taskStartedOnce = True
                    self._isRunning = True
                    self._isPaused = False
                    self._set_start_enabled(False) 
                    # nudge to ensure motion on builds that need it
                    QTimer.singleShot(0, self._nudge_resume)

            if self.pTask is not None:
                if self._call_if(self.pTask, "startTask"):
                    self._taskStartedOnce = True
                    self._isRunning = True
                    self._isPaused = False
                    self._set_start_enabled(False) 
                    # nudge to ensure motion on builds that need it
                    QTimer.singleShot(0, self._nudge_resume)
        else:
            if self.sTask is not None:
                if self._call_if(self.sTask, "resume"):
                    self._isRunning = True
                    self._isPaused = False
                    self._set_start_enabled(False)

                    QTimer.singleShot(0, self._nudge_resume)

            if self.iTask is not None:
                if self._call_if(self.iTask, "resume"):
                    self._isRunning = True
                    self._isPaused = False
                    self._set_start_enabled(False)

                    QTimer.singleShot(0, self._nudge_resume)

            if self.pTask is not None:        
                if self._call_if(self.pTask, "resume"):
                    self._isRunning = True
                    self._isPaused = False
                    self._set_start_enabled(False)
                    QTimer.singleShot(0, self._nudge_resume)

    def pause(self):
        print("[testWindow] Pause clicked")
        if not self.sTask:
            return

        if self.sTask is not None:
            if self._call_if(self.sTask, "pause"):
                self._isPaused = True
                self._isRunning = False
                print(f"[testWindow] Paused Sorting Task")
        
        if self.pTask is not None:
            if self._call_if(self.pTask, "pause"):
                self._isPaused = True
                self._isRunning = False
                print(f"[testWindow] Paused Packaging Task")

        if self.iTask is not None:
            if self._call_if(self.iTask, "pause"):
                self._isPaused = True
                self._isRunning = False
                print(f"[testWindow] Paused Inspection Task")



    def stop(self):
        print("[testWindow] Stop clicked")
        if self.sTask is not None:
            self._dispose_sorting_task()
        if self.iTask is not None:
            self._dispose_inspection_task()
        if self.pTask is not None:
            self._dispose_packaging_task()
        print("[testWindow] SortingTask fully stopped and removed.")


# -------------------------------- Entrypoint --------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = testWindow()
    w.show()
    sys.exit(app.exec())

