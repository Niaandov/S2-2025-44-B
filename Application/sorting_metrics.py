# sorting_metrics.py
from collections import deque
import time

VALID_COLOURS = {"green", "red", "blue"}

class SortingMetrics:
    def __init__(self):
        self.total_sorted = 0
        self.correct_sorted = 0
        self.error_count = {"green": 0, "red": 0, "blue": 0}
        self.timestamps = deque()  # event times (seconds)

    # ---- record events ----
    def record_correct(self):
        self.total_sorted += 1
        self.correct_sorted += 1
        self.timestamps.append(time.time())

    def record_error(self, colour: str):
        self.total_sorted += 1
        if colour not in self.error_count:
            self.error_count[colour] = 0  # guard for unexpected values
        self.error_count[colour] += 1
        self.timestamps.append(time.time())

    # ---- keep a 60s window for throughput ----
    def _prune_old(self, window_secs=60):
        cutoff = time.time() - window_secs
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

    # ---- derived metrics ----
    @property
    def accuracy(self) -> float:
        return self.correct_sorted / max(1, self.total_sorted)

    @property
    def actual_error_rate(self) -> float:
        return sum(self.error_count.values()) / max(1, self.total_sorted)

    @property
    def throughput_per_min(self) -> int:
        self._prune_old(60)
        return len(self.timestamps)

    # ---- manual fix for a logged error ----
    def fix_error(self, colour: str) -> bool:
        if colour in VALID_COLOURS and self.error_count.get(colour, 0) > 0:
            self.error_count[colour] -= 1
            self.correct_sorted += 1
            return True
        return False

    def reset(self):
        self.total_sorted = 0
        self.correct_sorted = 0
        self.error_count = {"green": 0, "red": 0, "blue": 0}
        self.timestamps.clear()

# shared instance (import this where needed)
metrics = SortingMetrics()