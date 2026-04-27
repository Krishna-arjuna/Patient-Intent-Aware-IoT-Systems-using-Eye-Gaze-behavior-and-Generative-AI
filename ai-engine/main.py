import cv2
import mediapipe as mp
import numpy as np
import time
import requests
import serial

# ---------------- CONFIG ----------------
FLASK_URL = "http://127.0.0.1:5000"

# 🔥 ARDUINO SERIAL
arduino = serial.Serial('COM3', 9600)  # change COM port
time.sleep(2)

# ---------------- CAMERA AUTO DETECT ----------------
def get_camera():
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print(f"✅ Using camera index {i}")
                return cap
    return None

cap = get_camera()
if cap is None:
    exit()

# ---------------- MEDIAPIPE ----------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1)

# ---------------- BLINK ----------------
LEFT_EYE = [33,160,158,133,153,144]

def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1]-eye[5])
    B = np.linalg.norm(eye[2]-eye[4])
    C = np.linalg.norm(eye[0]-eye[3])
    return (A+B)/(2*C)

blink_count = 0
blink_active = False

# ---------------- GAZE ----------------
def get_gaze_direction(lm):
    center = (lm[33].x + lm[133].x)/2
    if center < 0.4: return "LEFT"
    elif center > 0.6: return "RIGHT"
    return "CENTER"

# ---------------- ANOMALY ----------------
def analyze_behavior(data):
    score = 0

    if data["blink_rate"] > 10:
        score += 50

    if data["dominant_region"] in ["LEFT","RIGHT"] and data["repeated_focus"] > 2:
        score += 40

    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return level

# ---------------- MAIN ----------------
gaze_history = []
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    small = cv2.resize(frame, (320,240))
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    result = face_mesh.process(rgb)
    gaze = "UNKNOWN"

    if result.multi_face_landmarks:
        for face_landmarks in result.multi_face_landmarks:
            lm = face_landmarks.landmark

            gaze = get_gaze_direction(lm)

            eye_pts = []
            for idx in LEFT_EYE:
                p = lm[idx]
                h,w,_ = frame.shape
                eye_pts.append([p.x*w, p.y*h])

            eye_pts = np.array(eye_pts)
            ear = eye_aspect_ratio(eye_pts)

            if ear < 0.20 and not blink_active:
                blink_count += 1
                blink_active = True
            elif ear >= 0.20:
                blink_active = False

    gaze_history.append(gaze)

    cv2.putText(frame, f"Gaze: {gaze}", (20,50),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)

    # -------- EVERY 10s --------
    if time.time() - start_time > 10:

        dominant = max(set(gaze_history), key=gaze_history.count)

        data = {
            "dominant_region": dominant,
            "repeated_focus": gaze_history.count(dominant),
            "blink_rate": blink_count
        }

        print("🧠 Behavior:", data)

        # 🔥 ANALYZE
        level = analyze_behavior(data)

        # 🔥 SEND TO ARDUINO
        try:
            if level == "HIGH":
                arduino.write(b'H')
            elif level == "MEDIUM":
                arduino.write(b'M')
            else:
                arduino.write(b'N')
        except:
            pass

        # 🔥 SEND TO FLASK
        try:
            requests.post(f"{FLASK_URL}/api/update", json=data)
        except:
            pass

        gaze_history = []
        blink_count = 0
        start_time = time.time()

    cv2.imshow("Patient Monitoring", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()