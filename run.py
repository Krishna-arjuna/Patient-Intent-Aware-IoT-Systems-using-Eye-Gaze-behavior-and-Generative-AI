import subprocess
import sys

# Start Flask backend
backend = subprocess.Popen([sys.executable, "backend/app.py"])

# Start AI Engine (your main.py untouched)
ai = subprocess.Popen([sys.executable, "ai-engine/main.py"])

try:
    backend.wait()
    ai.wait()
except KeyboardInterrupt:
    backend.kill()
    ai.kill()