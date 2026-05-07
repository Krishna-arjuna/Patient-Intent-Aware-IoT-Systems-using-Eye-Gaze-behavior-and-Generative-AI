import cv2
import mediapipe as mp
import numpy as np
import time
import requests
import serial

# ---------------- CONFIG ----------------
FLASK_URL = "http://127.0.0.1:5000"
person_id = 1

# ---------------- SERIAL ----------------
try:
    arduino = serial.Serial('COM11', 9600, timeout=1)
    time.sleep(2)
    print("✅ Arduino connected")
except:
    arduino = None
    print("⚠️ Arduino not connected")

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

LEFT_EYE = [33,160,158,133,153,144]

# ---------------- FUNCTIONS ----------------
def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1]-eye[5])
    B = np.linalg.norm(eye[2]-eye[4])
    C = np.linalg.norm(eye[0]-eye[3])
    return (A+B)/(2*C)

def get_gaze(lm):
    center = (lm[33].x + lm[133].x)/2
    if center < 0.4: return "LEFT"
    elif center > 0.6: return "RIGHT"
    return "CENTER"

# 🔥 RULE-BASED GENAI (NO ML)
def genai_logic(data):
    if data["blink_rate"] > 15:
        return {
            "intent": "discomfort",
            "urgency": "HIGH",
            "action": "High blink rate detected",
            "anomaly_score": 0.9,
            "anomaly_level": "HIGH",
            "reasons": ["High blink rate"]
        }

    elif data["dominant_region"] in ["LEFT", "RIGHT"] and data["repeated_focus"] > 5:
        return {
            "intent": "attention_loss",
            "urgency": "MEDIUM",
            "action": "Patient not focusing",
            "anomaly_score": 0.6,
            "anomaly_level": "MEDIUM",
            "reasons": ["Gaze deviation"]
        }

    return {
        "intent": "normal",
        "urgency": "LOW",
        "action": "Patient stable",
        "anomaly_score": 0.2,
        "anomaly_level": "LOW",
        "reasons": []
    }

# ---------------- VARIABLES ----------------
blink_count = 0
blink_active = False
gaze_history = []
start_time = time.time()

EAR_THRESHOLD = 0.23

# ---------------- MAIN LOOP ----------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    gaze = "UNKNOWN"

    if result.multi_face_landmarks:
        for face_landmarks in result.multi_face_landmarks:
            lm = face_landmarks.landmark

            gaze = get_gaze(lm)

            eye_pts = []
            for idx in LEFT_EYE:
                p = lm[idx]
                h,w,_ = frame.shape
                eye_pts.append([p.x*w, p.y*h])

            eye_pts = np.array(eye_pts)
            ear = eye_aspect_ratio(eye_pts)

            if ear < EAR_THRESHOLD and not blink_active:
                blink_count += 1
                blink_active = True
            elif ear >= EAR_THRESHOLD:
                blink_active = False

    gaze_history.append(gaze)

    # Display
    cv2.putText(frame, f"Gaze: {gaze}", (20,50),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)
    cv2.putText(frame, f"Blinks: {blink_count}", (20,90),
                cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2)

    # -------- EVERY 10 SEC --------
    if time.time() - start_time > 10:

        dominant = max(set(gaze_history), key=gaze_history.count)
        duration = time.time() - start_time
        blink_rate = (blink_count / duration) * 60

        data = {
            "person_id": person_id,
            "dominant_region": dominant,
            "repeated_focus": gaze_history.count(dominant),
            "blink_rate": blink_rate,
            "blink_count": blink_count
        }

        print("Blink Rate:", round(blink_rate,2))

        # 🔥 GENAI
        genai_output = genai_logic(data)

        # 🔥 SEND TO BACKEND
        try:
            requests.post(f"{FLASK_URL}/api/update", json=data)
            requests.post(f"{FLASK_URL}/api/genai", json=genai_output)
        except:
            print("⚠️ Flask not running")

        # 🔥 ARDUINO CONTROL
        if arduino:
            if genai_output["urgency"] == "HIGH":
                arduino.write(b'H')
            elif genai_output["urgency"] == "MEDIUM":
                arduino.write(b'M')
            else:
                arduino.write(b'N')

        # RESET
        gaze_history = []
        blink_count = 0
        start_time = time.time()

    cv2.imshow("Monitoring", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()