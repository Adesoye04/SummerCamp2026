"""Quick camera diagnostic — run with: python3 test_camera.py"""
import base64
import requests
import cv2
import numpy as np
from misty import MISTY_IP

URL = f"http://{MISTY_IP}/api/cameras/rgb"

print(f"Testing camera on Misty at {MISTY_IP} ...")

try:
    r = requests.get(URL, params={"Base64": "true"}, timeout=10)
    print(f"  Status : {r.status_code}")
    body = r.json()
    print(f"  Keys   : {list(body.keys())}")
    result = body.get("result")
    print(f"  result type : {type(result)}")

    # Handle two known response shapes
    if isinstance(result, dict):
        img_b64 = result.get("base64", "")
        print(f"  base64 length : {len(img_b64)}")
    elif isinstance(result, str):
        img_b64 = result
        print(f"  base64 length (str) : {len(img_b64)}")
    else:
        print(f"  Unexpected result shape: {result}")
        img_b64 = ""

    if img_b64:
        img_bytes = base64.b64decode(img_b64)
        frame = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        if frame is not None:
            print(f"  Frame  : {frame.shape}  ✓")
            cv2.imwrite("test_frame.jpg", frame)
            print("  Saved  : test_frame.jpg")
        else:
            print("  cv2.imdecode returned None — bad image data")
    else:
        print("  No base64 data in response")
        print(f"  Full body: {str(body)[:500]}")

except Exception as e:
    print(f"  ERROR: {e}")
