from collections import deque
from threading import Lock
import time

data_lock = Lock()

gaze_history = deque(maxlen=50)
blink_history = deque(maxlen=50)
genai_history = deque(maxlen=20)

latest = {
    "gaze": "UNKNOWN",
    "blink_count": 0,
    "blink_rate": 0,
    "timestamp": None,
    "genai": None
}