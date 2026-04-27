from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import time
import uuid

from state import latest, gaze_history, blink_history, genai_history, data_lock

# ---------------- INIT ----------------

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "supersecretkey123"

CORS(app)

# ---------------- IN-MEMORY DB ----------------

patients = {}
patient_history = {}

# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return redirect("/login")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["user"],
        role=session["role"]
    )


@app.route("/admin")
def admin():
    if "user" not in session or session.get("role") != "admin":
        return redirect("/login")

    return render_template("admin.html")



@app.route("/patient/<pid>")
def patient(pid):
    if "user" not in session:
        return redirect("/login")

    patient = patients.get(pid)

    # 🔥 FIX: avoid crash if patient not found
    if not patient:
        return "Patient not found", 404

    history = patient_history.get(pid, [])

    return render_template(
        "patient.html",
        patient=patient,
        history=history,
        name=session["user"],
        role=session["role"]
    )


# ---------------- AUTH ----------------

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    role = data.get("role", "viewer")

    if not username:
        return jsonify({"success": False, "error": "Username required"})

    session["user"] = username
    session["role"] = role

    return jsonify({
        "success": True,
        "name": username,
        "role": role
    })


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- PATIENT APIs ----------------

@app.route("/api/patients")
def get_patients():
    return jsonify(list(patients.values()))


@app.route("/api/patient/add", methods=["POST"])
def add_patient():
    data = request.get_json()

    name = data.get("name")
    age = data.get("age")
    disease = data.get("disease")

    # 🔥 VALIDATION
    if not name or not disease:
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    pid = str(uuid.uuid4())[:8]

    patients[pid] = {
        "id": pid,
        "name": name,
        "age": age,
        "disease": disease,
        "status": "Monitoring"
    }

    patient_history[pid] = []

    return jsonify({"status": "ok", "id": pid})


@app.route("/api/patient/history", methods=["POST"])
def add_history():
    data = request.get_json()

    pid = data.get("id")
    text = data.get("text")

    if not pid or not text:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    if pid not in patient_history:
        return jsonify({"status": "error", "message": "Patient not found"}), 404

    entry = {
        "time": time.time(),
        "text": text
    }

    patient_history[pid].append(entry)

    return jsonify({"status": "ok"})


# ---------------- DATA APIs (UNCHANGED) ----------------

@app.route("/api/update", methods=["POST"])
def update():
    data = request.get_json()
    ts = time.time()

    with data_lock:
        latest["gaze"] = data.get("dominant_region", "UNKNOWN")
        latest["blink_count"] = data.get("blink_count", 0)
        latest["blink_rate"] = data.get("blink_rate", 0)
        latest["timestamp"] = ts

        gaze_history.append({"t": ts, "gaze": latest["gaze"]})
        blink_history.append({"t": ts, "blinks": latest["blink_rate"]})

    return jsonify({"status": "ok"})

@app.route("/api/genai", methods=["POST"])
def genai():
    data = request.get_json()
    ts = time.time()

    entry = {
    "t": ts,
    "intent": data.get("intent", ""),
    "urgency": data.get("urgency", ""),
    "action": data.get("action", ""),
    "anomaly_score": data.get("anomaly_score", 0),
    "anomaly_level": data.get("anomaly_level", "LOW"),
    "reasons": data.get("reasons", [])
}

    with data_lock:
        latest["genai"] = entry
        genai_history.append(entry)

    return jsonify({"status": "ok"})


@app.route("/api/state")
def state():
    with data_lock:
        return jsonify({
            "latest": latest,
            "gaze_history": list(gaze_history)[-20:],
            "blink_history": list(blink_history)[-20:],
            "genai_history": list(genai_history)[-5:]
        })


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)