# window_render.py
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import QTimer
import sys

from SortingTask import SortingTask
from ocs_ui import OCSWindow

SAFE_MODE_IGNORE_SETTINGS = True  # keep True until settings flow is tested


class taskGrid(QWidget):
    def __init__(self, minTileWidth, hgap, vgap):
        super().__init__()
        self.minTileWidth = minTileWidth
        self.hgap = hgap
        self.vgap = vgap
        self._boxes = []

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(12, 12, 12, 12)
        self.grid.setHorizontalSpacing(self.hgap)
        self.grid.setVerticalSpacing(self.vgap)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def addTaskWidget(self, w):
        if w and w not in self._boxes:
            w.setParent(self)
            self._boxes.append(w)
            self._relayout()

    def removeTaskWidget(self, w):
        if w in self._boxes:
            self._boxes.remove(w)
            w.setParent(None)
            w.deleteLater()
            self._relayout()

    def clear(self):
        for b in list(self._boxes):
            self.removeTaskWidget(b)

    def _columns(self):
        w = max(1, self.width())
        return max(1, int((w - self.hgap) // (self.minTileWidth + self.hgap)))

    def _relayout(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it and it.widget():
                it.widget().setParent(self)
        cols = self._columns()
        for i, b in enumerate(self._boxes):
            r, c = divmod(i, cols)
            self.grid.addWidget(b, r, c)
        for c in range(cols):
            self.grid.setColumnStretch(c, 1)
        self.grid.setRowStretch(self.grid.rowCount(), 1)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._relayout()


class testWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitoring Window")
        self.resize(1280, 720)

        self.sTask = None
        self._last_ocs = {}
        self._taskStartedOnce = False  # first run vs resume

        # UI shell
        top = QWidget(); top_l = QHBoxLayout(top); top_l.setContentsMargins(8, 8, 8, 8)
        root = QWidget(); root_l = QVBoxLayout(root); root_l.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(root)
        root_l.addWidget(top)

        self.grid = taskGrid(600, 10, 10)
        root_l.addWidget(self.grid)

        btnOpenOCS = QPushButton("Open OCS")
        btnOpenOCS.clicked.connect(self.showOCSWindow)
        top_l.addWidget(btnOpenOCS)

        self.OCSWindow = None
        self.showOCSWindow()

    # ---------- OCS ----------
    def showOCSWindow(self):
        if self.OCSWindow is None:
            self.OCSWindow = OCSWindow()
            # OCS buttons → local handlers
            self.OCSWindow.playClicked.connect(self.play)
            self.OCSWindow.pauseClicked.connect(self.pause)
            self.OCSWindow.stopClicked.connect(self.stop)

            # Optional settings sync (kept safe for now)
            if not SAFE_MODE_IGNORE_SETTINGS and hasattr(self.OCSWindow, "settingsChanged"):
                self.OCSWindow.settingsChanged.connect(
                    lambda s: QTimer.singleShot(0, lambda: self._apply_settings_from_ocs(dict(s)))
                )
            elif hasattr(self.OCSWindow, "settingsChanged"):
                self.OCSWindow.settingsChanged.connect(
                    lambda s: QTimer.singleShot(0, lambda: self._cache_settings_only(dict(s)))
                )

        self.OCSWindow.show()
        self.OCSWindow.raise_()
        self.OCSWindow.activateWindow()

    # ---------- small helper ----------
    def _call_if(self, obj, name):
        try:
            fn = getattr(obj, name, None)
            if callable(fn):
                fn()
                return True
        except Exception as e:
            print(f"[testWindow] _call_if {name} error:", e)
        return False

    # ---------- Controls ----------
    def play(self):
        """
        Start/resume behaviour:
          - If no task: create + start via startTask() (first run).
          - If task exists:
                if first run already happened → resume via renableTimer()/resumeTimer()/resume
                else → start via startTask()
        """
        print("[testWindow] Play clicked")
        try:
            if self.sTask is None:
                settings = getattr(self, "lastOCSSettings", {
                    "errorRate": 0.1,
                    "speed": 8000,
                    "numColours": 3
                })
                print("[testWindow] Creating SortingTask:", settings["errorRate"], settings["speed"], settings["numColours"])
                self.sTask = SortingTask(settings["errorRate"], settings["speed"], settings["numColours"])
                self.grid.addTaskWidget(self.sTask.renderWindow)
                QTimer.singleShot(200, lambda: self._start_or_resume(first_time=True))
            else:
                QTimer.singleShot(0, lambda: self._start_or_resume(first_time=False))
        except Exception as e:
            print("[ERROR in play()]:", e)

    def _start_or_resume(self, first_time: bool):
        try:
            if not self.sTask:
                return

            # First run prefers startTask()
            if first_time or not self._taskStartedOnce:
                if self._call_if(self.sTask, "startTask"):
                    self._taskStartedOnce = True
                    print("[testWindow] SortingTask started.")
                    return
                # Fallback resume names
                for name in ("renableTimer", "resumeTimer", "resume"):
                    if self._call_if(self.sTask, name):
                        self._taskStartedOnce = True
                        print(f"[testWindow] SortingTask resumed via {name}.")
                        return
                print("[testWindow] No start/resume method found.")
            else:
                for name in ("renableTimer", "resumeTimer", "resume"):
                    if self._call_if(self.sTask, name):
                        print(f"[testWindow] SortingTask resumed via {name}.")
                        return
                print("[testWindow] No resume method found.")
        except Exception as e:
            print("[ERROR in _start_or_resume]:", e)

    def pause(self):
        """
        Pause:
          1) Try common pause method names if present.
          2) Stop ALL QTimers owned by the task (findChildren(QTimer)).
          3) Fallback: try common timer attribute names.
        This freezes movement so the next Start (resume) continues correctly.
        """
        print("[testWindow] Pause clicked")
        if not self.sTask:
            return
        try:
            # 1) Named pause methods
            for name in ("stopTimer", "pauseTimer", "pauseTask", "pause"):
                if self._call_if(self.sTask, name):
                    print(f"[testWindow] Pause used {name}()")
                    return

            # 2) Stop any QTimer children attached to SortingTask
            timers = self.sTask.findChildren(QTimer)
            if timers:
                stopped = 0
                for t in timers:
                    try:
                        t.stop()
                        stopped += 1
                    except Exception:
                        pass
                print(f"[testWindow] Pause: stopped {stopped} internal timers via findChildren(QTimer).")
                return

            # 3) Common timer attributes fallback
            for attr in ("timer", "animTimer", "movementTimer", "updateTimer", "mainTimer"):
                t = getattr(self.sTask, attr, None)
                if isinstance(t, QTimer):
                    t.stop()
                    print(f"[testWindow] Pause used {attr}.stop()")
                    return

            print("[testWindow] No pause method/timer found on SortingTask.")
        except Exception as e:
            print("[ERROR in pause()]:", e)

    def stop(self):
        """
        Full teardown so the next Start is a truly fresh run.
        """
        print("[testWindow] Stop clicked")
        if not self.sTask:
            return
        try:
            # Prefer full stop, else stopTimer
            if not self._call_if(self.sTask, "stopTask"):
                self._call_if(self.sTask, "stopTimer")

            # Remove widget from UI
            try:
                if hasattr(self.sTask, "renderWindow") and self.sTask.renderWindow:
                    self.grid.removeTaskWidget(self.sTask.renderWindow)
            except Exception as e:
                print("[testWindow] stop(): remove widget error:", e)

            # Dispose so next Start creates new task with clean state
            self.sTask = None
            self._taskStartedOnce = False
            print("[testWindow] SortingTask fully stopped and disposed.")
        except Exception as e:
            print("[ERROR in stop()]:", e)

    # ---------- Settings handling (kept simple while SAFE mode) ----------
    def _cache_settings_only(self, s: dict):
        print("[testWindow] (cached) OCS settings:", s)
        self._last_ocs = dict(s)

    def _apply_settings_from_ocs(self, s: dict):
        if SAFE_MODE_IGNORE_SETTINGS:
            return
        print("[testWindow] OCS settings:", s)
        self._last_ocs = dict(s)
        enabled = bool(s.get("sortingEnabled", False))

        if self.sTask is not None:
            if not enabled:
                try:
                    self._call_if(self.sTask, "stopTask")
                    self.grid.removeTaskWidget(self.sTask.renderWindow)
                except Exception as e:
                    print("[testWindow] Error removing SortingTask:", e)
                self.sTask = None
                self._taskStartedOnce = False
                print("[testWindow] Removed SortingTask")
                return

            if "speed" in s and hasattr(self.sTask, "setSpeed"):
                self.sTask.setSpeed(int(s["speed"]))
            if "errorRate" in s and hasattr(self.sTask, "setErrorRate"):
                self.sTask.setErrorRate(float(s["errorRate"]) / 100.0)
            if "numColours" in s and hasattr(self.sTask, "setNumColours"):
                self.sTask.setNumColours(int(s["numColours"]))
            if "distractions" in s and hasattr(self.sTask, "setDistractions"):
                self.sTask.setDistractions(list(s["distractions"]))
        # If no task exists, Play() will create it.

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = testWindow()
    w.show()
    sys.exit(app.exec())








# Everything stops here? Cool whatever


################
# IN CODE DOCO #
################

''' 
This here is to put my thoughts and 'documentation' as I do things. Will be removed or moved at a later date
You don't have to do this! This is a messy way to communicate my thoughts as I won't be able to remember them by
next meeting

8/09/2025
Anim idea won't work out, as convenient as it'd be for two reasons
1) hard to make a queue for interruptions for error corrections
2) Anims are basically CSS properties and don't really have the capabilitiy to trigger an event when completed 

Good news! I missed a great feature that solves all of these; QTimers. It's literally a timer lmao

Current Idea:
* Keep track of the current state somehow. Via abstract number or something else. When the timer completes, switch to 
the next stage based on the stored state.

This allows for 'interrupts' where we can make it do some error correction anim. Throughput would be constant if we 
didn't do this so I assume we need to have the error correction take some time.

Two numbers? Current state and prior state. Mainly for interrupt purposes, since the user controls provide another
action that needs to be done before everything, but we don't want to just switch the action and stop the arm
from doing whatever. Prior state is checked after the interrupt/error action is called and then we go back to that after
interrupt completion. 



We can use this to tie pretty much everything to the AdvBoxQueue and a few other anim components. 

Timer (1s)
Box elements move to arm (or to appropriate space on the line) 
Timer (1s)
Arm grabs box and moves to the box. 
Timer (1s) 
Arm moves back to position 
Timer (1s) 
Box elements move to arm

(Not exactly like this, since we likely want the boxes to move to the correct space. Just an illustration of the 
process) 


Currently, timer process is stored on the individual task, so timers can run seperately. Will need to thread tasks

20/09/2025
Rendering is fun, I lied effortlessly.

Using QGraphics for it, meaning that I have to learn how to anim components which may have to be done on a seperate timer
Resizing is extremely annoying due to the way that this works, essentially I have to figure out how to restrict it from
having a scrollable area because it really wants to be dynamic in a way we cant let it

It also is statically sized by PIXELS. everything in it is fucking static. Which is great but the second the screen is resized we have to
redo every fucking calculation. FUN.fuckkk i hate UI

Question for next time
* Does resizing have to be done dynamically or can we implement an option to select window size manually between several
common resolution sizes? 

You know like in a video game. Because the alternative is I get to have a fun minigame while coding where I get to try
to avoid blowing my fucking brains out. 
'''
