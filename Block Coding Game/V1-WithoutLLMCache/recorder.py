"""
recorder.py — Records webcam video of the game session.

Start recording as soon as both ArUco IDs are confirmed.
Stop recording when the game ends.

Usage:
    from recorder import GameRecorder
    rec = GameRecorder(session_id="20260706T120000_200_201")
    rec.start()
    ...game runs...
    rec.stop()
"""

import threading
import time
from datetime import datetime
from pathlib import Path

import cv2

# ── Config ────────────────────────────────────────────────────────────────────

RECORDINGS_DIR = Path(__file__).parent / "recordings"
WEBCAM_INDEX   = 0        # change if the wrong camera is used
FPS            = 20.0
RESOLUTION     = (1280, 720)

# ── Recorder ─────────────────────────────────────────────────────────────────

class GameRecorder:
    """Captures webcam video for one game session in a background thread."""

    def __init__(self, session_id: str):
        RECORDINGS_DIR.mkdir(exist_ok=True)
        safe_id        = session_id.replace(":", "-")
        self._path     = RECORDINGS_DIR / f"{safe_id}.avi"
        self._stop     = threading.Event()
        self._thread:  threading.Thread | None = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._record, daemon=True)
        self._thread.start()
        print(f"  [recorder] Recording started → {self._path.name}")

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        print(f"  [recorder] Recording saved → {self._path}")

    def _record(self):
        cap = cv2.VideoCapture(WEBCAM_INDEX)
        if not cap.isOpened():
            print("  [recorder] Webcam not found — recording skipped.")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  RESOLUTION[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        writer = cv2.VideoWriter(str(self._path), fourcc, FPS, RESOLUTION)

        frame_time = 1.0 / FPS
        while not self._stop.is_set():
            t0 = time.time()
            ret, frame = cap.read()
            if ret:
                writer.write(frame)
            elapsed = time.time() - t0
            sleep   = frame_time - elapsed
            if sleep > 0:
                time.sleep(sleep)

        writer.release()
        cap.release()
