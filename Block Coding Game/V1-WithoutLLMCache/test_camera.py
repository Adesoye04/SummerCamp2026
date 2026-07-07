"""Quick camera + ArUco diagnostic — run with: python3 test_camera.py"""
import base64
import json
import time
import requests
import cv2
import numpy as np
from pathlib import Path
from misty import MISTY_IP

URL        = f"http://{MISTY_IP}/api/cameras/rgb"
USERS_PATH = Path(__file__).parent.parent.parent / "Documents" / "users.json"
ARUCO_DICT = cv2.aruco.DICT_6X6_1000


def grab_frame():
    r = requests.get(URL, params={"Base64": "true"}, timeout=10)
    r.raise_for_status()
    body   = r.json()
    result = body.get("result")
    img_b64 = result.get("base64", "") if isinstance(result, dict) else result or ""
    img_bytes = base64.b64decode(img_b64)
    return cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)


def detect(frame):
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    detector   = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())
    _, ids, _  = detector.detectMarkers(frame)
    return [int(i[0]) for i in ids] if ids is not None else []


try:
    users = json.loads(USERS_PATH.read_text(encoding="utf-8"))
    print(f"users.json — {len(users)} entries: {list(users.keys())}")
except Exception as e:
    users = {}
    print(f"Could not load users.json: {e}")

print(f"\nScanning continuously — hold a card up to Misty's camera.")
print(f"Press Ctrl+C to stop.\n")

while True:
    try:
        frame = grab_frame()
        if frame is None:
            print("  No frame")
            time.sleep(0.5)
            continue

        ids = detect(frame)
        if ids:
            for aruco_id in ids:
                entry = users.get(str(aruco_id))
                if entry is None:
                    print(f"  Detected ID {aruco_id} — NOT in users.json")
                elif not entry.get("consent", False):
                    print(f"  Detected ID {aruco_id} ({entry.get('name')}) — consent=false, skipped")
                else:
                    print(f"  Detected ID {aruco_id} — name={entry.get('name')}  ✓ VALID PLAYER")
        else:
            print("  No markers detected")

        time.sleep(0.4)

    except KeyboardInterrupt:
        print("\nDone.")
        break
    except Exception as e:
        print(f"  Error: {e}")
        time.sleep(0.5)
